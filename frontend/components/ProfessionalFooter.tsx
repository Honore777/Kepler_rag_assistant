import React from 'react'
import Link from 'next/link'
import Logo from './Logo'
import { site } from '../lib/site'

const ProfessionalFooter: React.FC = () => {
  const year = new Date().getFullYear()

  return (
    <footer className="relative bg-footer text-footer-ink">
      <div className="relative h-24 overflow-hidden bg-footer" aria-hidden="true">
        <div className="imigongo-photo absolute inset-0" />
        <div className="absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-footer to-transparent" />
      </div>

      <div className="container-page pb-10 pt-12">
        <div className="grid gap-10 md:grid-cols-[1.4fr_1fr_1fr]">
          <div>
            <Logo onDark href="/landing" />
            <p className="mt-5 max-w-sm text-sm leading-7 text-footer-ink/80">
              Everything the college has written down, easy to find for the people who learn and work here.
            </p>
            <p className="mt-5 text-sm text-footer-ink/80">{site.city}</p>
            <a href={`mailto:${site.email}`} className="text-sm text-white underline decoration-white/30 underline-offset-4 hover:decoration-white">
              {site.email}
            </a>
          </div>

          <div>
            <h3 className="font-sans text-xs font-semibold uppercase text-footer-ink/60" style={{ letterSpacing: '0.14em' }}>
              Get started
            </h3>
            <ul className="mt-4 space-y-3 text-sm">
              <li>
                <Link href="/auth/register" className="text-footer-ink/90 hover:text-white">
                  Create a student account
                </Link>
              </li>
              <li>
                <Link href="/auth/login" className="text-footer-ink/90 hover:text-white">
                  Sign in
                </Link>
              </li>
              <li>
                <Link href="/chat" className="text-footer-ink/90 hover:text-white">
                  Ask a question
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="font-sans text-xs font-semibold uppercase text-footer-ink/60" style={{ letterSpacing: '0.14em' }}>
              About
            </h3>
            <ul className="mt-4 space-y-3 text-sm">
              <li>
                <Link href="/landing#how" className="text-footer-ink/90 hover:text-white">
                  How it works
                </Link>
              </li>
              <li>
                <Link href="/landing#roles" className="text-footer-ink/90 hover:text-white">
                  Students, staff and administration
                </Link>
              </li>
              <li>
                <Link href="/landing#access" className="text-footer-ink/90 hover:text-white">
                  Who can see what
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 flex flex-col gap-2 border-t border-white/10 pt-6 text-xs text-footer-ink/65 sm:flex-row sm:items-center sm:justify-between">
          <p>
            &copy; {year} {site.name}. All rights reserved.
          </p>
          <p>Kepler College 2025 Business Analytics Class</p>
        </div>
      </div>
    </footer>
  )
}

export default ProfessionalFooter
