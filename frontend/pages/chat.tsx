/**
 * Chat screen.
 *
 * - Conversation history in a sidebar (stored per user in localStorage)
 * - Role-based answers: the API only searches documents the user's role may read
 * - Every answer lists the documents it was drawn from
 */

import { FormEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import { CloseIcon, FileIcon, PlusIcon, SendIcon, SidebarIcon, TrashIcon } from '../components/icons';
import { Notice, PageSpinner } from '../components/ui';
import { api } from '../lib/api';
import { displayName, roleLabel } from '../lib/auth';
import { suggestedQuestions } from '../lib/site';
import { QueryResponse, SourceItem } from '../lib/types';

interface ChatMessage {
  id: string;
  question: string;
  answer: string;
  timestamp: Date;
  sources?: SourceItem[];
}

interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}

const MAX_HISTORY_TURNS = 6;

const sourceName = (source: SourceItem): string => {
  const name = source.metadata?.doc_name;
  return typeof name === 'string' && name ? name : 'Document';
};

/**
 * Answers arrive as plain text. This formatter recovers structure so a rule
 * like "... classroom. 5. A student arriving ..." renders as a real numbered
 * list, bullet lines become a list, and long runs are broken into paragraphs.
 */
interface AnswerBlock {
  kind: 'p' | 'ol' | 'ul';
  text?: string;
  items?: string[];
}

const NUMBER_MARKER = /(^|[\s(])(\d{1,2})[.)]\s+(?=[A-Z"'‘“])/g;

function longestNumberedRun(text: string): { index: number; num: number }[] {
  const markers: { index: number; num: number }[] = [];
  const re = new RegExp(NUMBER_MARKER);
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    markers.push({ index: m.index + m[1].length, num: parseInt(m[2], 10) });
  }
  let best: typeof markers = [];
  let cur: typeof markers = [];
  for (const mk of markers) {
    if (cur.length === 0 || mk.num > cur[cur.length - 1].num) {
      cur.push(mk);
    } else {
      if (cur.length > best.length) best = cur;
      cur = [mk];
    }
  }
  return cur.length > best.length ? cur : best;
}

function paragraphsFrom(text: string): AnswerBlock[] {
  const out: AnswerBlock[] = [];
  for (const chunk of text.split(/\n{2,}/).map((s) => s.trim()).filter(Boolean)) {
    const lines = chunk.split('\n').map((l) => l.trim()).filter(Boolean);
    if (lines.length > 1 && lines.every((l) => /^[-•*]\s+/.test(l))) {
      out.push({ kind: 'ul', items: lines.map((l) => l.replace(/^[-•*]\s+/, '')) });
      continue;
    }
    // Bullets embedded mid-line: "notes that: * item one * item two * item three"
    if ((chunk.match(/\s\*\s/g) ?? []).length >= 2) {
      const [intro, ...items] = chunk.split(/\s\*\s/);
      if (intro.trim()) out.push({ kind: 'p', text: intro.trim() });
      out.push({ kind: 'ul', items: items.map((s) => s.trim()).filter(Boolean) });
      continue;
    }
    const sentences = chunk.match(/[^.!?]+[.!?]+["')\]]?|\S[^.!?]*$/g) ?? [chunk];
    if (sentences.length <= 3 || chunk.length < 360) {
      out.push({ kind: 'p', text: chunk });
      continue;
    }
    let cur = '';
    for (const s of sentences) {
      if (cur.length + s.length > 360 && cur) {
        out.push({ kind: 'p', text: cur.trim() });
        cur = '';
      }
      cur += s;
    }
    if (cur.trim()) out.push({ kind: 'p', text: cur.trim() });
  }
  return out;
}

/** Renders the small markdown subset answers contain: **bold**, *italic*, `code`. */
const INLINE_MD = /(\*\*[^*]+?\*\*|\*[^*\n]+?\*|`[^`\n]+?`)/g;

function InlineText({ text }: { text: string }) {
  return (
    <>
      {text.split(INLINE_MD).map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
          return <strong key={i}>{part.slice(2, -2)}</strong>;
        }
        if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
          return <em key={i}>{part.slice(1, -1)}</em>;
        }
        if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
          return <code key={i}>{part.slice(1, -1)}</code>;
        }
        return part;
      })}
    </>
  );
}

function formatAnswer(raw: string): AnswerBlock[] {
  const text = raw.trim();
  const run = longestNumberedRun(text);
  if (run.length < 2) return paragraphsFrom(text);

  const blocks: AnswerBlock[] = [];
  const preamble = text.slice(0, run[0].index).trim();
  if (preamble) blocks.push(...paragraphsFrom(preamble));
  blocks.push({
    kind: 'ol',
    items: run.map((mk, i) => {
      const end = i + 1 < run.length ? run[i + 1].index : text.length;
      return text.slice(mk.index, end).replace(/^\d{1,2}[.)]\s*/, '').trim();
    }),
  });
  return blocks;
}

function AnswerBody({ text }: { text: string }) {
  const blocks = useMemo(() => formatAnswer(text), [text]);
  return (
    <div className="answer-text">
      {blocks.map((block, i) =>
        block.kind === 'ol' ? (
          <ol key={i}>
            {block.items!.map((item, j) => (
              <li key={j}>
                <InlineText text={item} />
              </li>
            ))}
          </ol>
        ) : block.kind === 'ul' ? (
          <ul key={i}>
            {block.items!.map((item, j) => (
              <li key={j}>
                <InlineText text={item} />
              </li>
            ))}
          </ul>
        ) : (
          <p key={i}>
            <InlineText text={block.text!} />
          </p>
        )
      )}
    </div>
  );
}

function SourceList({ sources }: { sources: SourceItem[] }) {
  const names = Array.from(new Set(sources.map(sourceName)));

  return (
    <div className="mt-4 border-t border-line pt-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase text-muted" style={{ letterSpacing: '0.1em' }}>
          Sources
        </span>
        {names.map((name) => (
          <span key={name} className="badge-brand">
            <FileIcon className="h-3.5 w-3.5" />
            {name}
          </span>
        ))}
      </div>
      <details className="group mt-2">
        <summary className="cursor-pointer text-xs font-medium text-muted hover:text-ink">
          View the {sources.length} passage{sources.length === 1 ? '' : 's'} used
        </summary>
        <ul className="mt-2 space-y-2">
          {sources.map((source, idx) => (
            <li key={`${source.id}-${idx}`} className="panel p-3 text-[13px] leading-6 text-ink-soft">
              <p className="mb-1 flex items-center justify-between gap-3 text-xs font-medium text-muted">
                <span className="truncate">{sourceName(source)}</span>
                {typeof source.score === 'number' ? <span>{Math.round(source.score * 100)}% match</span> : null}
              </p>
              {source.text.length > 320 ? `${source.text.slice(0, 320)}…` : source.text}
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}

export default function ChatPage() {
  const router = useRouter();
  const [question, setQuestion] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>('');
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);
  const [user, setUser] = useState<any>(null);
  const [authChecked, setAuthChecked] = useState<boolean>(false);
  const endRef = useRef<HTMLDivElement>(null);

  const sessionsStorageKey = user?.username ? `chatSessions:${user.username}` : 'chatSessions';

  const normalizeSessions = (raw: any[]): ChatSession[] => {
    if (!Array.isArray(raw)) return [];
    return raw.map((session) => ({
      ...session,
      createdAt: new Date(session.createdAt),
      updatedAt: new Date(session.updatedAt),
      messages: Array.isArray(session.messages)
        ? session.messages.map((message: any) => ({
            ...message,
            timestamp: new Date(message.timestamp),
          }))
        : [],
    }));
  };

  // Check authentication and load chat sessions
  useEffect(() => {
    const userInfo = localStorage.getItem('userInfo');
    if (!userInfo) {
      router.push('/auth/login');
      return;
    }
    const parsedUser = JSON.parse(userInfo);
    setUser(parsedUser);
    setSidebarOpen(window.innerWidth >= 1024);

    const savedSessions = localStorage.getItem(`chatSessions:${parsedUser.username}`) || localStorage.getItem('chatSessions');
    if (savedSessions) {
      const sessions = normalizeSessions(JSON.parse(savedSessions));
      setChatSessions(sessions);

      if (sessions.length > 0) {
        const mostRecent = [...sessions].sort(
          (a: ChatSession, b: ChatSession) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
        )[0];
        setCurrentSessionId(mostRecent.id);
      }
    }
    setAuthChecked(true);
  }, []);

  // Persist chat sessions whenever they change
  useEffect(() => {
    if (!user) return;
    localStorage.setItem(sessionsStorageKey, JSON.stringify(chatSessions));
  }, [chatSessions, sessionsStorageKey, user]);

  const currentSession = chatSessions.find((session) => session.id === currentSessionId);

  // Keep the newest message in view
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [currentSession?.messages.length, loading, currentSessionId]);

  const createNewSession = (): string => {
    const nextId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const newSession: ChatSession = {
      id: nextId,
      title: 'New conversation',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    };

    setChatSessions((prev) => [newSession, ...prev]);
    setCurrentSessionId(nextId);
    setError('');
    return nextId;
  };

  const updateSessionTitle = (sessionId: string, text: string) => {
    setChatSessions((prev) =>
      prev.map((session) =>
        session.id === sessionId ? { ...session, title: text.slice(0, 50) + (text.length > 50 ? '…' : '') } : session
      )
    );
  };

  const deleteSession = (sessionId: string) => {
    const remaining = chatSessions.filter((s) => s.id !== sessionId);
    setChatSessions(remaining);

    if (currentSessionId === sessionId) {
      if (remaining.length > 0) {
        setCurrentSessionId(remaining[0].id);
      } else {
        setCurrentSessionId('');
      }
    }
  };

  async function ask(text: string) {
    if (!text.trim() || loading) return;

    setLoading(true);
    setError('');

    const sessionId = currentSessionId || createNewSession();
    const sessionForHistory = chatSessions.find((s) => s.id === sessionId);
    const historyTurns = (sessionForHistory?.messages || [])
      .slice(-MAX_HISTORY_TURNS)
      .reverse()
      .flatMap((m) => [`User: ${m.question}`, `Assistant: ${m.answer}`]);

    try {
      const res = await api.post<QueryResponse>('/rag/query', {
        question: text,
        top_k: 4,
        history: historyTurns,
      });

      const newMessage: ChatMessage = {
        id: Date.now().toString(),
        question: text,
        answer: res.data.answer,
        timestamp: new Date(),
        sources: res.data.sources,
      };

      setChatSessions((prev) =>
        prev.map((session) =>
          session.id === sessionId
            ? { ...session, messages: [...session.messages, newMessage], updatedAt: new Date() }
            : session
        )
      );

      if ((sessionForHistory?.messages.length || 0) === 0) {
        updateSessionTitle(sessionId, text);
      }

      setQuestion('');
    } catch (err: any) {
      console.error(err);
      const status = err?.response?.status;
      setError(
        status === 401
          ? 'Your session has ended. Please sign in again.'
          : status === 429
            ? 'You are asking questions faster than the limit allows. Please wait a moment and try again.'
            : 'We could not reach the assistant. Please try again in a moment.'
      );
    } finally {
      setLoading(false);
    }
  }

  function onAsk(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    ask(question);
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      ask(question);
    }
  }

  const formatTime = (date: Date) =>
    new Date(date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  const formatDate = (date: Date) => {
    const now = new Date();
    const messageDate = new Date(date);
    const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
    const diffDays = Math.round((startOfDay(now) - startOfDay(messageDate)) / 86400000);

    if (diffDays <= 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return messageDate.toLocaleDateString();
  };

  if (!authChecked) return <PageSpinner />;

  const firstName = displayName(user).split(/[\s@]/)[0];
  const suggestions = suggestedQuestions[user?.role] || suggestedQuestions.student;
  const hasMessages = (currentSession?.messages.length || 0) > 0;

  return (
    <Layout title="Assistant" footer={false} bleed>
      <div className="relative flex h-[calc(100dvh-var(--header-h))] overflow-hidden">
        {/* Conversation list */}
        {sidebarOpen ? (
          <button
            type="button"
            aria-label="Close conversation list"
            className="absolute inset-0 z-20 bg-ink/40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        ) : null}
        <aside
          className={`absolute inset-y-0 left-0 z-30 flex w-72 flex-col border-r border-line bg-surface transition-transform duration-200 lg:static lg:z-0 ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:hidden'
          }`}
        >
          <div className="flex items-center justify-between gap-2 p-4">
            <button type="button" onClick={createNewSession} className="btn-primary flex-1">
              <PlusIcon className="h-4 w-4" /> New conversation
            </button>
            <button
              type="button"
              onClick={() => setSidebarOpen(false)}
              className="btn-ghost h-10 w-10 !px-0 lg:hidden"
              aria-label="Close conversation list"
            >
              <CloseIcon className="h-5 w-5" />
            </button>
          </div>

          <p className="px-5 pb-2 text-xs font-semibold uppercase text-muted" style={{ letterSpacing: '0.1em' }}>
            Recent
          </p>
          <nav className="flex-1 space-y-1 overflow-y-auto px-3 pb-4" aria-label="Conversations">
            {chatSessions.length === 0 ? (
              <p className="px-2 py-3 text-sm text-muted">Your conversations will appear here.</p>
            ) : null}
            {[...chatSessions]
              .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
              .map((session) => (
                <div
                  key={session.id}
                  className={`group flex items-center gap-1 rounded-xl pr-1 transition-colors ${
                    session.id === currentSessionId ? 'bg-brand-soft' : 'hover:bg-raised'
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => {
                      setCurrentSessionId(session.id);
                      setError('');
                      if (window.innerWidth < 1024) setSidebarOpen(false);
                    }}
                    className="min-w-0 flex-1 px-3 py-2.5 text-left"
                    aria-current={session.id === currentSessionId ? 'true' : undefined}
                  >
                    <span className={`block truncate text-sm font-medium ${session.id === currentSessionId ? 'text-brand' : 'text-ink'}`}>
                      {session.title}
                    </span>
                    <span className="block text-xs text-muted">{formatDate(session.updatedAt)}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteSession(session.id)}
                    className="rounded-lg p-2 text-muted opacity-0 transition hover:bg-danger-soft hover:text-danger focus:opacity-100 group-hover:opacity-100"
                    aria-label={`Delete conversation ${session.title}`}
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              ))}
          </nav>
        </aside>

        {/* Conversation */}
        <section className="flex min-w-0 flex-1 flex-col">
          <div className="flex items-center justify-between gap-3 border-b border-line bg-canvas px-4 py-3 sm:px-6">
            <div className="flex min-w-0 items-center gap-3">
              <button
                type="button"
                onClick={() => setSidebarOpen((v) => !v)}
                className="btn-ghost h-10 w-10 shrink-0 !px-0"
                aria-label={sidebarOpen ? 'Hide conversation list' : 'Show conversation list'}
                aria-expanded={sidebarOpen}
              >
                <SidebarIcon className="h-5 w-5" />
              </button>
              <h1 className="truncate font-display text-lg font-medium text-ink">{currentSession?.title || 'New conversation'}</h1>
            </div>
            <span className="badge-neutral shrink-0">{roleLabel(user?.role)}</span>
          </div>

          <div className="flex-1 overflow-y-auto">
            <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6">
              {!hasMessages ? (
                <div className="animate-fade-up pt-6 text-center sm:pt-14">
                  <img src="/images/enhanced/logo.png" alt="" className="mx-auto h-14 w-14 rounded-2xl ring-1 ring-black/10" />
                  <h2 className="mt-6 text-3xl font-medium sm:text-4xl">How can I help{firstName ? `, ${firstName}` : ''}?</h2>
                  <p className="mx-auto mt-3 max-w-md leading-7 text-muted">
                    Ask about a policy, a deadline or a procedure. I will answer from the documents shared with your role and show you the
                    sources.
                  </p>
                  <div className="mx-auto mt-8 grid max-w-xl gap-3">
                    {suggestions.map((s) => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => ask(s)}
                        disabled={loading}
                        className="card-flat px-5 py-3.5 text-left text-[15px] font-medium text-ink transition hover:border-brand/40 hover:bg-raised disabled:opacity-60"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-8">
                  {currentSession?.messages.map((message) => (
                    <div key={message.id} className="space-y-5">
                      <div className="flex justify-end">
                        <div className="max-w-[88%] sm:max-w-[80%]">
                          <p className="whitespace-pre-wrap rounded-2xl rounded-br-md bg-brand-soft px-4 py-3 text-[15px] leading-7 text-ink">
                            {message.question}
                          </p>
                          <p className="mt-1 text-right text-xs text-muted">{formatTime(message.timestamp)}</p>
                        </div>
                      </div>

                      <div className="flex gap-3">
                        <img src="/images/enhanced/logo.png" alt="" className="mt-1 h-8 w-8 shrink-0 rounded-lg ring-1 ring-black/10" />
                        <div className="min-w-0 flex-1">
                          <div className="card px-5 py-4">
                            <AnswerBody text={message.answer} />
                            {message.sources && message.sources.length > 0 ? <SourceList sources={message.sources} /> : null}
                          </div>
                          <p className="mt-1 text-xs text-muted">{formatTime(message.timestamp)}</p>
                        </div>
                      </div>
                    </div>
                  ))}

                  {loading ? (
                    <div className="flex items-center gap-3">
                      <img src="/images/enhanced/logo.png" alt="" className="h-8 w-8 shrink-0 rounded-lg ring-1 ring-black/10" />
                      <div className="card flex items-center gap-3 px-5 py-3.5" role="status">
                        <span className="flex gap-1" aria-hidden="true">
                          {[0, 1, 2].map((i) => (
                            <span key={i} className="h-2 w-2 animate-dot-pulse rounded-full bg-brand" style={{ animationDelay: `${i * 160}ms` }} />
                          ))}
                        </span>
                        <span className="text-sm text-muted">Reading the documents…</span>
                      </div>
                    </div>
                  ) : null}
                </div>
              )}
              <div ref={endRef} />
            </div>
          </div>

          <div className="border-t border-line bg-canvas px-4 py-4 sm:px-6">
            <div className="mx-auto w-full max-w-3xl">
              {error ? <Notice tone="danger" className="mb-3">{error}</Notice> : null}
              <form onSubmit={onAsk} className="flex items-end gap-3">
                <label htmlFor="question" className="sr-only">
                  Your question
                </label>
                <textarea
                  id="question"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={onKeyDown}
                  placeholder="Ask about a policy, a deadline or a procedure"
                  className="input max-h-40 min-h-[3.25rem] flex-1 resize-none"
                  rows={1}
                  disabled={loading}
                />
                <button type="submit" className="btn-primary h-[3.25rem] w-[3.25rem] shrink-0 !px-0" disabled={loading || !question.trim()} aria-label="Send question">
                  <SendIcon className="h-5 w-5" />
                </button>
              </form>
              <p className="mt-2 text-center text-xs text-muted">
                Answers come from documents shared with your role. Press Enter to send, Shift+Enter for a new line.
              </p>
            </div>
          </div>
        </section>
      </div>
    </Layout>
  );
}
