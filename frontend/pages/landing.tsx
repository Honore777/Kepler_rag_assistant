import React from 'react'
import Link from 'next/link'
import Layout from '../components/Layout'
import { ArrowRightIcon, BookIcon, CheckIcon, FileIcon, SearchIcon, ShieldIcon } from '../components/icons'
import { sampleConversation, site } from '../lib/site'

const steps = [
  {
    icon: SearchIcon,
    title: 'Ask in your own words',
    text: 'Type the question the way you would ask a person, such as “Can I defer a semester?”. No keywords, no folders to open.',
  },
  {
    icon: BookIcon,
    title: 'The assistant reads the documents',
    text: 'It looks through the handbooks and policies Kepler has published, limited to the ones shared with your role.',
  },
  {
    icon: FileIcon,
    title: 'Check the source yourself',
    text: 'Every answer lists the documents it came from, so you can open the original and read the full wording.',
  },
]

const audiences = [
  {
    kicker: 'Students',
    title: 'Handbook answers when the office is closed',
    text: `Register with your @${site.studentDomain} email and ask about anything the college has published for students. The answer comes from the handbook, not from guesswork.`,
    image: '/images/enhanced/library.webp',
    alt: 'Shelves of books in a library',
    cta: { label: 'Create a student account', href: '/auth/register' },
  },
  {
    kicker: 'Staff and board',
    title: 'Internal procedures, shared with the right people',
    text: 'Staff and board members are invited by the administration. Once in, you can reach the documents shared with your role, and nothing that was meant for someone else.',
    image: '/images/enhanced/faculty-teaching.webp',
    alt: 'Colleagues meeting around a table',
    cta: { label: 'Sign in', href: '/auth/login' },
  },
  {
    kicker: 'Administration',
    title: 'You decide what is published, and to whom',
    text: 'Upload a document, choose which roles may read it, and switch it off the day it goes out of date. Invite staff and board members from the same dashboard.',
    image: '/images/enhanced/event-second.webp',
    alt: 'A graduating class gathered in a hall',
    cta: { label: 'Administrator sign in', href: '/auth/login' },
  },
]

const assurances = [
  'Every answer shows the documents it was taken from.',
  'Staff and board accounts are created by invitation only.',
  'Your session is protected and expires on its own.',
]

const LandingPage: React.FC = () => {
  return (
    <Layout bleed>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="container-page grid items-center gap-14 pb-24 pt-14 lg:grid-cols-[1.05fr_0.95fr] lg:gap-16 lg:pb-32 lg:pt-20">
          <div>
            <p className="eyebrow animate-fade-up">
              <span className="h-px w-8 bg-brand" /> {site.name}, {site.city.split(',')[0]}
            </p>
            <h1
              className="mt-5 animate-fade-up text-[2.75rem] font-medium leading-[1.05] sm:text-6xl lg:text-[4.1rem]"
              style={{ animationDelay: '60ms' }}
            >
              Find <span className="text-brand">the answer</span>, not the right PDF.
            </h1>
            <p className="lead mt-6 max-w-xl animate-fade-up" style={{ animationDelay: '120ms' }}>
              Ask a question about a policy, a deadline or a procedure. The assistant reads Kepler College&apos;s own handbooks and
              documents, answers in plain language, and shows you where each answer came from.
            </p>

            <div className="mt-9 flex flex-col gap-3 animate-fade-up sm:flex-row" style={{ animationDelay: '180ms' }}>
              <Link href="/auth/register" className="btn-primary btn-lg">
                Create a student account <ArrowRightIcon className="h-5 w-5" />
              </Link>
              <Link href="/auth/login" className="btn-secondary btn-lg">
                Sign in
              </Link>
            </div>
            <p className="mt-5 animate-fade-up text-sm text-muted" style={{ animationDelay: '240ms' }}>
              Staff or board member? Use the invitation link from the administration, or{' '}
              <Link href="#access" className="font-medium text-brand underline underline-offset-4">
                see how access works
              </Link>
              .
            </p>
          </div>

          <div className="relative animate-fade-up pb-10 sm:pb-0" style={{ animationDelay: '140ms' }}>
            <div className="photo-frame aspect-[5/4] rounded-[2rem] shadow-lift lg:aspect-[4/5]">
              <img src="/images/enhanced/student-learning.webp" alt="A speaker addressing students in a library at Kepler College" />
            </div>

            <div className="card absolute -bottom-2 left-3 right-3 p-5 sm:-bottom-8 sm:-left-10 sm:right-auto sm:w-[23rem] lg:-left-14">
              <span className="badge-neutral mb-3">Example</span>
              <div className="flex justify-end">
                <p className="max-w-[85%] rounded-2xl rounded-br-md bg-brand-soft px-4 py-2.5 text-sm font-medium text-ink">
                  {sampleConversation.question}
                </p>
              </div>
              <p className="mt-3 text-sm leading-6 text-ink">{sampleConversation.answer}</p>
              <p className="mt-3 flex items-center gap-2 border-t border-line pt-3 text-xs font-medium text-muted">
                <FileIcon className="h-4 w-4 text-brand" /> Source: {sampleConversation.source}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="border-y border-line bg-surface">
        <div className="container-page py-20 md:py-24">
          <div className="max-w-2xl">
            <p className="eyebrow">How it works</p>
            <h2 className="mt-3 text-3xl font-medium sm:text-4xl">Three steps, and no searching.</h2>
          </div>
          <ol className="mt-12 grid gap-10 md:grid-cols-3 md:gap-8">
            {steps.map((step, i) => (
              <li key={step.title} className="relative">
                <div className="flex items-center gap-4">
                  <span className="font-display text-5xl font-medium leading-none text-brand/30">{i + 1}</span>
                  <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-soft text-brand">
                    <step.icon className="h-5 w-5" />
                  </span>
                </div>
                <h3 className="mt-5 text-xl font-medium">{step.title}</h3>
                <p className="mt-2 leading-7 text-ink-soft">{step.text}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Audiences */}
      <section id="roles" className="container-page py-20 md:py-28">
        <div className="max-w-2xl">
          <p className="eyebrow">Who it is for</p>
          <h2 className="mt-3 text-3xl font-medium sm:text-4xl">One place, built around who you are.</h2>
          <p className="lead mt-4">What you can ask depends on your role, so each person sees the documents meant for them.</p>
        </div>

        <div className="mt-12 grid gap-6 lg:grid-cols-3">
          {audiences.map((a) => (
            <article key={a.kicker} className="card-flat group flex flex-col overflow-hidden transition-shadow duration-200 hover:shadow-lift">
              <div className="photo-frame aspect-[4/3]">
                <img src={a.image} alt={a.alt} loading="lazy" className="transition-transform duration-500 group-hover:scale-[1.03]" />
              </div>
              <div className="flex flex-1 flex-col p-7">
                <p className="eyebrow">{a.kicker}</p>
                <h3 className="mt-3 text-2xl font-medium leading-snug">{a.title}</h3>
                <p className="mt-3 flex-1 leading-7 text-ink-soft">{a.text}</p>
                <Link href={a.cta.href} className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-brand hover:underline">
                  {a.cta.label} <ArrowRightIcon className="h-4 w-4" />
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>

      <div className="imigongo-divider" aria-hidden="true">
        <img src="/images/enhanced/imigongo-strip.webp" alt="" loading="lazy" />
      </div>

      {/* Access */}
      <section id="access" className="container-page py-20 md:py-28">
        <div className="grid gap-12 rounded-3xl bg-footer p-8 text-footer-ink shadow-lift sm:p-12 lg:grid-cols-2 lg:gap-16 lg:p-16">
          <div>
            <p className="eyebrow !text-leaf">Who can see what</p>
            <h2 className="mt-3 text-3xl font-medium !text-white sm:text-4xl">Your role decides what you can read.</h2>
            <p className="mt-5 leading-8 text-footer-ink/85">
              Each document is published with a list of the roles that may read it. The assistant only searches the documents your role
              is allowed to see, so a student never receives an answer drawn from a staff-only file.
            </p>
          </div>
          <ul className="space-y-5 self-center">
            {assurances.map((item) => (
              <li key={item} className="flex items-start gap-4 rounded-2xl border border-white/10 bg-white/[0.04] p-5">
                <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-leaf/20 text-leaf">
                  <CheckIcon className="h-4 w-4" />
                </span>
                <span className="leading-7 text-white/90">{item}</span>
              </li>
            ))}
            <li className="flex items-center gap-3 px-1 text-sm text-footer-ink/70">
              <ShieldIcon className="h-5 w-5 text-leaf" /> Sign-in is required before any document is searched.
            </li>
          </ul>
        </div>
      </section>

      {/* Campus */}
      <section className="container-page pb-20 md:pb-28">
        <div className="max-w-2xl">
          <p className="eyebrow">On campus</p>
          <h2 className="mt-3 text-3xl font-medium sm:text-4xl">Made for the people of this campus.</h2>
          <p className="lead mt-4">
            {site.name} is in {site.city}. The assistant exists so that everything the college has written down is easy to find for the
            people who learn and work here.
          </p>
        </div>

        <div className="mt-10 grid grid-cols-2 gap-4 md:grid-cols-4">
          <figure className="photo-frame col-span-2 aspect-[4/3] rounded-2xl md:row-span-2 md:aspect-auto md:min-h-[26rem]">
            <img src="/images/enhanced/campus-hero.webp" alt="Kepler College campus buildings among trees" loading="lazy" />
            <figcaption className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/65 to-transparent p-4 pt-12 text-sm font-medium text-white">
              The campus
            </figcaption>
          </figure>
          <figure className="photo-frame aspect-square rounded-2xl">
            <img src="/images/enhanced/campus-life.webp" alt="Students playing basketball" loading="lazy" />
            <figcaption className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/65 to-transparent p-3 pt-10 text-sm font-medium text-white">
              Campus life
            </figcaption>
          </figure>
          <figure className="photo-frame aspect-square rounded-2xl">
            <img src="/images/enhanced/tech-lab.webp" alt="A student working on an electronics project" loading="lazy" />
            <figcaption className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/65 to-transparent p-3 pt-10 text-sm font-medium text-white">
              In the lab
            </figcaption>
          </figure>
          <figure className="photo-frame col-span-2 aspect-[2/1] rounded-2xl">
            <img src="/images/enhanced/graduation.webp" alt="Graduates in green stoles at a ceremony" loading="lazy" />
            <figcaption className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/65 to-transparent p-4 pt-12 text-sm font-medium text-white">
              Graduation
            </figcaption>
          </figure>
        </div>
      </section>

      {/* Closing call to action */}
      <section className="container-page pb-24">
        <div className="rounded-3xl border border-brand/15 bg-brand-soft px-6 py-14 text-center sm:px-12">
          <h2 className="text-3xl font-medium sm:text-4xl">Ready when you are.</h2>
          <p className="mx-auto mt-4 max-w-xl text-lg leading-8 text-ink-soft">
            Create your student account in a minute, or sign in if you already have one.
          </p>
          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            <Link href="/auth/register" className="btn-primary btn-lg">
              Create a student account
            </Link>
            <Link href="/auth/login" className="btn-secondary btn-lg">
              Sign in
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  )
}

export default LandingPage
