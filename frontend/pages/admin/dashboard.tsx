/**
 * Administration dashboard.
 *
 * - Overview of documents and people
 * - Upload documents and choose which roles may read them
 * - Activate, deactivate and delete documents
 * - Invite staff and board members with single-use links
 */

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../components/Layout';
import AdminSidebar, { AdminTab } from '../../components/AdminSidebar';
import { ArrowRightIcon, BookIcon, CheckIcon, CopyIcon, FileIcon, MailIcon, UploadIcon, UsersIcon } from '../../components/icons';
import { EmptyState, Notice, PageSpinner, Spinner } from '../../components/ui';
import { api } from '../../lib/api';
import { roleLabel } from '../../lib/auth';

interface Document {
  id: string;
  name: string;
  type?: string | null;
  allowed_roles?: string[] | string | null;
  status?: string | null;
  created_at?: string | null;
  file_size?: number | null;
  uploaded_at?: string | null;
  active?: boolean | null;
  indexing_state?: 'queued' | 'processing' | 'indexed' | 'failed' | string | null;
  indexing_message?: string | null;
  indexed_at?: string | null;
}

interface User {
  id: string;
  username: string;
  role: string;
  full_name: string | null;
  created_at: string | null;
}

interface InviteRecord {
  email: string;
  role: string;
  expires_at: string;
  used: boolean;
  created_at: string | null;
}

interface InviteResult {
  invite_url: string;
  token: string;
  role: string;
  expires_at: string;
  email: string;
}

const ROLES = ['student', 'staff', 'board_member', 'admin'] as const;

const tabCopy: Record<AdminTab, { title: string; text: string }> = {
  overview: { title: 'Overview', text: 'A quick look at what is published and who is using it.' },
  documents: { title: 'Documents', text: 'Upload documents, choose who can read them, and switch them on or off.' },
  users: { title: 'People', text: 'Everyone who has an account.' },
  invites: { title: 'Invitations', text: 'Invite staff and board members with a personal, single-use link.' },
};

const parseAllowedRoles = (allowedRoles: string[] | string | null | undefined): string[] => {
  if (Array.isArray(allowedRoles)) return allowedRoles;
  if (!allowedRoles) return [];
  try {
    const parsed = JSON.parse(allowedRoles);
    return Array.isArray(parsed) ? parsed.filter((role): role is string => typeof role === 'string') : [];
  } catch {
    return [];
  }
};

const safeDate = (value?: string | null, withTime = true): string => {
  if (!value) return 'Unknown';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Unknown';
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...(withTime ? { hour: '2-digit', minute: '2-digit' } : {}),
  });
};

const safeSize = (value?: number | null): string => {
  if (typeof value !== 'number' || !Number.isFinite(value) || value <= 0) return 'Unknown';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(value) / Math.log(k));
  return parseFloat((value / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const docStatus = (doc: Document): string => doc.status ?? (doc.active ? 'active' : 'inactive');

const roleBadge = (role: string): string => {
  switch (role) {
    case 'student':
      return 'badge-brand';
    case 'staff':
      return 'badge-leaf';
    case 'board_member':
      return 'badge-warn';
    default:
      return 'badge-neutral';
  }
};

const indexingBadge = (state?: string | null): { className: string; label: string } => {
  switch (state) {
    case 'indexed':
      return { className: 'badge-leaf', label: 'Ready' };
    case 'failed':
      return { className: 'badge-danger', label: 'Failed' };
    case 'processing':
      return { className: 'badge-warn', label: 'Indexing' };
    default:
      return { className: 'badge-neutral', label: 'Queued' };
  }
};

function StatCard({ label, value, hint, icon }: { label: string; value: number | string; hint?: string; icon: React.ReactNode }) {
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-muted">{label}</p>
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-soft text-brand">{icon}</span>
      </div>
      <p className="mt-3 font-display text-4xl font-medium text-ink">{value}</p>
      {hint ? <p className="mt-1 text-xs text-muted">{hint}</p> : null}
    </div>
  );
}

export default function AdminDashboard() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<AdminTab>('overview');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [usersAvailable, setUsersAvailable] = useState(true);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadActive, setUploadActive] = useState(true);
  const [uploadDocType, setUploadDocType] = useState<'policy' | 'research' | 'handbook' | 'procedure' | 'other'>('policy');
  const [uploadRoles, setUploadRoles] = useState<string[]>(['student']);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [pendingUploadDocId, setPendingUploadDocId] = useState<string | null>(null);

  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'staff' | 'board_member'>('staff');
  const [inviteHours, setInviteHours] = useState(72);
  const [inviting, setInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviteResult, setInviteResult] = useState<InviteResult | null>(null);
  const [invites, setInvites] = useState<InviteRecord[]>([]);
  const [copied, setCopied] = useState(false);

  const loadInvites = useCallback(async () => {
    try {
      const res = await api.get('/invites/my-invites');
      setInvites(res.data?.invites || []);
    } catch {
      setInvites([]);
    }
  }, []);

  const loadDashboardData = useCallback(async (silent = false) => {
    try {
      if (!silent) setLoading(true);

      const docsRes = await api.get('/documents');
      setDocuments(docsRes.data || []);

      try {
        const usersRes = await api.get('/admin/users');
        setUsers(usersRes.data || []);
        setUsersAvailable(true);
      } catch {
        setUsersAvailable(false);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  // Admin-only access
  useEffect(() => {
    const userInfo = localStorage.getItem('userInfo');
    if (!userInfo) {
      router.push('/auth/login');
      return;
    }

    const parsedUser = JSON.parse(userInfo);
    if (parsedUser.role !== 'admin') {
      router.push('/chat');
      return;
    }

    setUser(parsedUser);
    setAuthChecked(true);
    loadDashboardData();
  }, []);

  useEffect(() => {
    if (activeTab === 'invites') loadInvites();
  }, [activeTab, loadInvites]);

  // Poll while a freshly uploaded document is being indexed
  useEffect(() => {
    if (!pendingUploadDocId) return;
    const timer = window.setInterval(() => {
      loadDashboardData(true).catch(() => undefined);
    }, 2500);
    return () => window.clearInterval(timer);
  }, [pendingUploadDocId, loadDashboardData]);

  useEffect(() => {
    if (!pendingUploadDocId) return;
    const tracked = documents.find((d) => d.id === pendingUploadDocId);
    if (!tracked) return;

    if (tracked.indexing_state === 'indexed') {
      setUploadSuccess(tracked.indexing_message || `"${tracked.name}" is indexed and ready.`);
      setUploadError(null);
      setPendingUploadDocId(null);
    } else if (tracked.indexing_state === 'failed') {
      setUploadError(tracked.indexing_message || `Indexing failed for "${tracked.name}".`);
      setUploadSuccess(null);
      setPendingUploadDocId(null);
    }
  }, [documents, pendingUploadDocId]);

  const handleUploadDocument = async () => {
    if (!uploadFile) return;
    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const fd = new FormData();
      fd.append('file', uploadFile);
      fd.append('active', String(uploadActive));
      fd.append('document_type', uploadDocType);
      fd.append('allowed_roles', JSON.stringify(uploadRoles));

      const response = await api.post('/documents/upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const uploadedDocId = response?.data?.id as string | undefined;
      setUploadSuccess(response?.data?.message || 'Upload received. Indexing is queued.');
      if (uploadedDocId) setPendingUploadDocId(uploadedDocId);
      setUploadFile(null);
      await loadDashboardData(true);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setUploadError(typeof detail === 'string' ? detail : 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const toggleDocumentStatus = async (docId: string, currentStatus: string) => {
    setActionError(null);
    try {
      const newStatus = currentStatus === 'active' ? 'inactive' : 'active';
      await api.post(`/documents/${docId}/activate`, null, { params: { active: newStatus === 'active' } });
      setDocuments((prev) => prev.map((doc) => (doc.id === docId ? { ...doc, status: newStatus } : doc)));
    } catch {
      setActionError('The document status could not be changed. Please try again.');
    }
  };

  const deleteDocument = async (doc: Document) => {
    if (!confirm(`Delete "${doc.name}"? This also removes it from search and cannot be undone.`)) return;
    setActionError(null);
    try {
      await api.delete(`/documents/${doc.id}`);
      setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
    } catch {
      setActionError('The document could not be deleted. Please try again.');
    }
  };

  const generateInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviting(true);
    setInviteError(null);
    setInviteResult(null);
    setCopied(false);

    try {
      const response = await api.post('/invites/generate', { email: inviteEmail, role: inviteRole, expires_hours: inviteHours });
      setInviteResult({ ...response.data, email: inviteEmail.trim().toLowerCase() });
      setInviteEmail('');
      loadInvites();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setInviteError(
        typeof detail === 'string' ? detail : 'The invitation could not be created. Check the email address and try again.'
      );
    } finally {
      setInviting(false);
    }
  };

  const copyInvite = async () => {
    if (!inviteResult) return;
    try {
      await navigator.clipboard.writeText(inviteResult.invite_url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setInviteError('Copying was blocked by the browser. Select the link and copy it manually.');
    }
  };

  if (!authChecked) return <PageSpinner />;

  const activeDocs = documents.filter((d) => docStatus(d) === 'active').length;
  const readyDocs = documents.filter((d) => d.indexing_state === 'indexed').length;
  const needAttention = documents.filter((d) => d.indexing_state === 'failed').length;
  const usersByRole = users.reduce((acc, u) => {
    acc[u.role] = (acc[u.role] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  const recentDocs = [...documents]
    .sort((a, b) => new Date(b.created_at || b.uploaded_at || 0).getTime() - new Date(a.created_at || a.uploaded_at || 0).getTime())
    .slice(0, 5);

  const inviteStatus = (inv: InviteRecord): { className: string; label: string } => {
    if (inv.used) return { className: 'badge-leaf', label: 'Accepted' };
    if (new Date(inv.expires_at).getTime() < Date.now()) return { className: 'badge-neutral', label: 'Expired' };
    return { className: 'badge-warn', label: 'Waiting' };
  };

  return (
    <Layout title="Administration" footer={false} bleed>
      <div className="mx-auto flex w-full max-w-[88rem] flex-col lg:flex-row">
        <AdminSidebar activeTab={activeTab} onTabChange={setActiveTab} user={user} />

        <div className="min-w-0 flex-1 px-5 py-8 sm:px-8 lg:px-10 lg:py-10">
          <header className="mb-8">
            <p className="eyebrow">Administration</p>
            <h1 className="mt-2 text-3xl font-medium sm:text-4xl">{tabCopy[activeTab].title}</h1>
            <p className="mt-2 text-muted">{tabCopy[activeTab].text}</p>
          </header>

          {loading ? (
            <div className="flex h-64 items-center justify-center text-brand" role="status">
              <Spinner className="h-8 w-8" />
            </div>
          ) : null}

          {/* Overview */}
          {!loading && activeTab === 'overview' && (
            <div className="space-y-8">
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <StatCard label="Documents" value={documents.length} hint="Uploaded in total" icon={<BookIcon className="h-[18px] w-[18px]" />} />
                <StatCard label="Active" value={activeDocs} hint="Available to search" icon={<CheckIcon className="h-[18px] w-[18px]" />} />
                <StatCard
                  label="Ready to answer"
                  value={readyDocs}
                  hint={needAttention ? `${needAttention} failed to index` : 'Indexed successfully'}
                  icon={<FileIcon className="h-[18px] w-[18px]" />}
                />
                <StatCard
                  label="People"
                  value={usersAvailable ? users.length : '—'}
                  hint={usersAvailable ? 'Registered accounts' : 'Not available right now'}
                  icon={<UsersIcon className="h-[18px] w-[18px]" />}
                />
              </div>

              <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
                <section className="card p-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-xl font-medium">Recently added</h2>
                    <button type="button" onClick={() => setActiveTab('documents')} className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand hover:underline">
                      All documents <ArrowRightIcon className="h-4 w-4" />
                    </button>
                  </div>
                  {recentDocs.length === 0 ? (
                    <EmptyState icon={<UploadIcon />} title="No documents yet">
                      Upload the first handbook or policy to start answering questions.
                    </EmptyState>
                  ) : (
                    <ul className="mt-4 divide-y divide-line">
                      {recentDocs.map((doc) => (
                        <li key={doc.id} className="flex items-center justify-between gap-4 py-3.5">
                          <div className="flex min-w-0 items-center gap-3">
                            <FileIcon className="h-5 w-5 shrink-0 text-muted" />
                            <div className="min-w-0">
                              <p className="truncate text-sm font-medium text-ink">{doc.name}</p>
                              <p className="text-xs text-muted">{safeDate(doc.created_at || doc.uploaded_at, false)}</p>
                            </div>
                          </div>
                          <span className={indexingBadge(doc.indexing_state).className}>{indexingBadge(doc.indexing_state).label}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>

                <section className="card p-6">
                  <h2 className="text-xl font-medium">People by role</h2>
                  {!usersAvailable || users.length === 0 ? (
                    <p className="mt-4 text-sm text-muted">No account data to show yet.</p>
                  ) : (
                    <ul className="mt-5 space-y-4">
                      {Object.entries(usersByRole).map(([role, count]) => (
                        <li key={role}>
                          <div className="mb-1.5 flex items-center justify-between text-sm">
                            <span className={roleBadge(role)}>{roleLabel(role)}</span>
                            <span className="font-medium text-ink">{count}</span>
                          </div>
                          <div className="h-2 rounded-full bg-raised">
                            <div className="h-2 rounded-full bg-brand-solid" style={{ width: `${(count / users.length) * 100}%` }} />
                          </div>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              </div>
            </div>
          )}

          {/* Documents */}
          {!loading && activeTab === 'documents' && (
            <div className="space-y-6">
              <section className="card p-6 sm:p-8">
                <h2 className="text-xl font-medium">Upload a document</h2>
                <p className="mt-1 text-sm text-muted">The document is split into passages and indexed so the assistant can search it.</p>

                <div className="mt-6 grid gap-6">
                  <div>
                    <span className="label">File</span>
                    <label
                      htmlFor="upload-file"
                      className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-line-strong bg-raised/60 px-6 py-8 text-center transition-colors hover:border-brand hover:bg-brand-soft/50"
                    >
                      <UploadIcon className="h-7 w-7 text-brand" />
                      <span className="mt-3 text-sm font-medium text-ink">{uploadFile ? uploadFile.name : 'Choose a file to upload'}</span>
                      <span className="mt-1 text-xs text-muted">
                        {uploadFile ? safeSize(uploadFile.size) : 'PDF, Word or text documents'}
                      </span>
                      <input
                        id="upload-file"
                        type="file"
                        className="sr-only"
                        onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                      />
                    </label>
                  </div>

                  <div className="grid gap-6 md:grid-cols-[14rem_1fr]">
                    <div>
                      <label htmlFor="doc-type" className="label">
                        Document type
                      </label>
                      <select id="doc-type" value={uploadDocType} onChange={(e) => setUploadDocType(e.target.value as any)} className="input">
                        <option value="policy">Policy</option>
                        <option value="handbook">Handbook</option>
                        <option value="procedure">Procedure</option>
                        <option value="research">Research</option>
                        <option value="other">Other</option>
                      </select>
                    </div>

                    <div>
                      <span className="label">Who can read it</span>
                      <div className="flex flex-wrap gap-2" role="group" aria-label="Roles allowed to read this document">
                        {ROLES.map((role) => {
                          const on = uploadRoles.includes(role);
                          return (
                            <button
                              key={role}
                              type="button"
                              aria-pressed={on}
                              onClick={() =>
                                setUploadRoles((prev) => {
                                  if (!on) return Array.from(new Set([...prev, role]));
                                  const next = prev.filter((r) => r !== role);
                                  return next.length ? next : prev;
                                })
                              }
                              className={`inline-flex items-center gap-2 rounded-xl border px-3.5 py-2 text-sm font-medium transition-colors ${
                                on ? 'border-brand bg-brand-soft text-brand' : 'border-line-strong bg-surface text-ink-soft hover:bg-raised'
                              }`}
                            >
                              {on ? <CheckIcon className="h-4 w-4" /> : null}
                              {roleLabel(role)}
                            </button>
                          );
                        })}
                      </div>
                      <label className="mt-4 inline-flex cursor-pointer items-center gap-2.5 text-sm text-ink-soft">
                        <input
                          type="checkbox"
                          checked={uploadActive}
                          onChange={(e) => setUploadActive(e.target.checked)}
                          className="h-4 w-4 rounded border-line-strong accent-[rgb(var(--brand-solid))]"
                        />
                        Make it available as soon as it is indexed
                      </label>
                    </div>
                  </div>

                  {uploadError ? <Notice tone="danger">{uploadError}</Notice> : null}
                  {uploadSuccess ? <Notice tone="success">{uploadSuccess}</Notice> : null}
                  {pendingUploadDocId ? (
                    <p className="flex items-center gap-2 text-sm text-muted">
                      <Spinner className="h-4 w-4" /> Indexing in progress. This page updates automatically.
                    </p>
                  ) : null}

                  <div>
                    <button type="button" className="btn-primary" onClick={handleUploadDocument} disabled={!uploadFile || uploading}>
                      {uploading ? (
                        <>
                          <Spinner className="h-4 w-4" /> Uploading
                        </>
                      ) : (
                        'Upload and index'
                      )}
                    </button>
                  </div>
                </div>
              </section>

              {actionError ? <Notice tone="danger">{actionError}</Notice> : null}

              <div className="table-wrap">
                {documents.length === 0 ? (
                  <EmptyState icon={<FileIcon />} title="Nothing uploaded yet">
                    Documents you upload will be listed here with their access and indexing status.
                  </EmptyState>
                ) : (
                  <table className="table-base">
                    <thead>
                      <tr>
                        <th>Document</th>
                        <th>Who can read it</th>
                        <th>Status</th>
                        <th>Indexing</th>
                        <th>Size</th>
                        <th>Added</th>
                        <th className="text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {documents.map((doc) => {
                        const status = docStatus(doc);
                        const idx = indexingBadge(doc.indexing_state);
                        const roles = parseAllowedRoles(doc.allowed_roles);
                        return (
                          <tr key={doc.id}>
                            <td>
                              <div className="flex items-center gap-3">
                                <FileIcon className="h-5 w-5 shrink-0 text-muted" />
                                <div className="max-w-[15rem]">
                                  <p className="truncate font-medium text-ink" title={doc.name}>
                                    {doc.name}
                                  </p>
                                  <p className="text-xs capitalize text-muted">{doc.type || 'Unspecified'}</p>
                                </div>
                              </div>
                            </td>
                            <td>
                              <div className="flex flex-wrap gap-1.5">
                                {roles.map((role) => (
                                  <span key={role} className={roleBadge(role)}>
                                    {roleLabel(role)}
                                  </span>
                                ))}
                                {roles.length === 0 ? <span className="text-muted">Everyone</span> : null}
                              </div>
                            </td>
                            <td>
                              <span className={status === 'active' ? 'badge-leaf' : 'badge-neutral'}>{status === 'active' ? 'Active' : 'Inactive'}</span>
                            </td>
                            <td>
                              <span className={idx.className} title={doc.indexing_message || undefined}>
                                {idx.label}
                              </span>
                            </td>
                            <td className="whitespace-nowrap text-muted">{safeSize(doc.file_size)}</td>
                            <td className="whitespace-nowrap text-muted">{safeDate(doc.created_at || doc.uploaded_at, false)}</td>
                            <td className="whitespace-nowrap">
                              <div className="flex justify-end gap-1">
                                <button type="button" onClick={() => toggleDocumentStatus(doc.id, status)} className="btn-ghost btn-sm">
                                  {status === 'active' ? 'Deactivate' : 'Activate'}
                                </button>
                                <button type="button" onClick={() => deleteDocument(doc)} className="btn-ghost btn-sm !text-danger hover:!bg-danger-soft">
                                  Delete
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}

          {/* People */}
          {!loading && activeTab === 'users' && (
            <div className="space-y-6">
              <div className="flex justify-end">
                <button type="button" onClick={() => setActiveTab('invites')} className="btn-primary">
                  <MailIcon className="h-4 w-4" /> Invite a colleague
                </button>
              </div>

              <div className="table-wrap">
                {!usersAvailable ? (
                  <EmptyState icon={<UsersIcon />} title="The list could not be loaded">
                    Check that the API is running and that you are signed in as an administrator.
                  </EmptyState>
                ) : users.length === 0 ? (
                  <EmptyState icon={<UsersIcon />} title="No accounts yet" />
                ) : (
                  <table className="table-base">
                    <thead>
                      <tr>
                        <th>Person</th>
                        <th>Role</th>
                        <th>Joined</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((u) => (
                        <tr key={u.id}>
                          <td>
                            <p className="font-medium text-ink">{u.full_name || u.username}</p>
                            <p className="text-xs text-muted">{u.username}</p>
                          </td>
                          <td>
                            <span className={roleBadge(u.role)}>{roleLabel(u.role)}</span>
                          </td>
                          <td className="text-muted">{safeDate(u.created_at, false)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}

          {/* Invitations */}
          {!loading && activeTab === 'invites' && (
            <div className="space-y-6">
              <div className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
                <form onSubmit={generateInvite} className="card space-y-5 p-6 sm:p-8">
                  <div>
                    <h2 className="text-xl font-medium">Invite someone</h2>
                    <p className="mt-1 text-sm text-muted">
                      They receive a personal link. It works once, only for this email address, and only until it expires.
                    </p>
                  </div>

                  <div>
                    <label htmlFor="invite-email" className="label">
                      Their email address
                    </label>
                    <input
                      id="invite-email"
                      type="email"
                      required
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      className="input"
                      placeholder="name@example.com"
                    />
                  </div>

                  <div className="grid gap-5 sm:grid-cols-2">
                    <div>
                      <label htmlFor="invite-role" className="label">
                        Role
                      </label>
                      <select id="invite-role" value={inviteRole} onChange={(e) => setInviteRole(e.target.value as any)} className="input">
                        <option value="staff">Staff</option>
                        <option value="board_member">Board member</option>
                      </select>
                    </div>
                    <div>
                      <label htmlFor="invite-hours" className="label">
                        Link stays valid for
                      </label>
                      <select id="invite-hours" value={inviteHours} onChange={(e) => setInviteHours(Number(e.target.value))} className="input">
                        <option value={24}>1 day</option>
                        <option value={72}>3 days</option>
                        <option value={168}>7 days</option>
                      </select>
                    </div>
                  </div>

                  {inviteError ? <Notice tone="danger">{inviteError}</Notice> : null}

                  <button type="submit" className="btn-primary" disabled={inviting || !inviteEmail}>
                    {inviting ? (
                      <>
                        <Spinner className="h-4 w-4" /> Creating
                      </>
                    ) : (
                      'Create invitation link'
                    )}
                  </button>
                </form>

                <section className="card p-6 sm:p-8">
                  <h2 className="text-xl font-medium">How it works</h2>
                  <ol className="mt-5 space-y-5 text-sm leading-6 text-ink-soft">
                    {[
                      'Enter the email address and role, then create the link.',
                      'Send the link to that person yourself, by email or message.',
                      'They open it, set a password, and are signed in with the role you chose.',
                    ].map((text, i) => (
                      <li key={text} className="flex gap-4">
                        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-soft text-sm font-semibold text-brand">{i + 1}</span>
                        <span className="pt-0.5">{text}</span>
                      </li>
                    ))}
                  </ol>
                </section>
              </div>

              {inviteResult ? (
                <section className="card border-leaf/40 p-6 sm:p-8">
                  <div className="flex items-center gap-3">
                    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-leaf-soft text-leaf">
                      <CheckIcon className="h-5 w-5" />
                    </span>
                    <div>
                      <h2 className="text-lg font-medium">Invitation ready for {inviteResult.email}</h2>
                      <p className="text-sm text-muted">
                        {roleLabel(inviteResult.role)} · expires {safeDate(inviteResult.expires_at)}
                      </p>
                    </div>
                  </div>
                  <div className="mt-5 flex flex-col gap-3 sm:flex-row">
                    <input readOnly value={inviteResult.invite_url} onFocus={(e) => e.currentTarget.select()} className="input flex-1 font-mono text-[13px]" aria-label="Invitation link" />
                    <button type="button" onClick={copyInvite} className="btn-secondary shrink-0">
                      {copied ? <CheckIcon className="h-4 w-4 text-leaf" /> : <CopyIcon className="h-4 w-4" />}
                      {copied ? 'Copied' : 'Copy link'}
                    </button>
                  </div>
                  <p className="hint">Keep this link private. Anyone who has it can use it until it expires, but only with the email address above.</p>
                </section>
              ) : null}

              <div className="table-wrap">
                {invites.length === 0 ? (
                  <EmptyState icon={<MailIcon />} title="No invitations yet">
                    Invitations you create will be listed here so you can see who has joined.
                  </EmptyState>
                ) : (
                  <table className="table-base">
                    <thead>
                      <tr>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th>Expires</th>
                      </tr>
                    </thead>
                    <tbody>
                      {invites.map((inv, i) => {
                        const st = inviteStatus(inv);
                        return (
                          <tr key={`${inv.email}-${i}`}>
                            <td className="font-medium text-ink">{inv.email}</td>
                            <td>
                              <span className={roleBadge(inv.role)}>{roleLabel(inv.role)}</span>
                            </td>
                            <td>
                              <span className={st.className}>{st.label}</span>
                            </td>
                            <td className="text-muted">{safeDate(inv.expires_at)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
