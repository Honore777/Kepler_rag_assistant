import React, { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import Logo from './Logo'
import ThemeToggle from './ThemeToggle'
import { ChevronDownIcon, CloseIcon, KeyIcon, LogoutIcon, MenuIcon } from './icons'
import { displayName, homeFor, initialsOf, logout, roleLabel, useSessionUser } from '../lib/auth'

type NavItem = { label: string; href: string }

const publicNav: NavItem[] = [
  { label: 'How it works', href: '/landing#how' },
  { label: 'Who it is for', href: '/landing#roles' },
  { label: 'Access', href: '/landing#access' },
]

const ProfessionalHeader: React.FC = () => {
  const router = useRouter()
  const { user, ready } = useSessionUser()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const nav: NavItem[] = user
    ? [
        { label: 'Assistant', href: '/chat' },
        ...(user.role === 'admin' ? [{ label: 'Administration', href: '/admin/dashboard' }] : []),
      ]
    : publicNav

  useEffect(() => {
    const close = () => {
      setMobileOpen(false)
      setMenuOpen(false)
    }
    router.events.on('routeChangeStart', close)
    return () => router.events.off('routeChangeStart', close)
  }, [router.events])

  useEffect(() => {
    if (!menuOpen) return
    const onPointer = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false)
    }
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setMenuOpen(false)
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [menuOpen])

  const isActive = (href: string) => !href.includes('#') && router.pathname.startsWith(href)

  const linkClass = (href: string) =>
    `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
      isActive(href) ? 'bg-raised text-ink' : 'text-ink-soft hover:bg-raised hover:text-ink'
    }`

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-canvas/90 backdrop-blur-md">
      <div className="imigongo-band" aria-hidden="true" />
      <div className="container-page">
        <div className="flex h-16 items-center justify-between gap-4">
          <Logo href={user ? homeFor(user.role) : '/landing'} />

          <nav className="hidden items-center gap-1 md:flex" aria-label="Main">
            {nav.map((item) => (
              <Link key={item.href} href={item.href} className={linkClass(item.href)}>
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <ThemeToggle />

            {ready && user ? (
              <div className="relative" ref={menuRef}>
                <button
                  type="button"
                  onClick={() => setMenuOpen((v) => !v)}
                  className="flex h-10 items-center gap-2 rounded-xl border border-line pl-1.5 pr-2.5 transition-colors hover:bg-raised"
                  aria-haspopup="menu"
                  aria-expanded={menuOpen}
                >
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-soft text-xs font-semibold text-brand">
                    {initialsOf(user)}
                  </span>
                  <span className="hidden max-w-[10rem] truncate text-sm font-medium text-ink sm:block">{displayName(user)}</span>
                  <ChevronDownIcon className="h-4 w-4 text-muted" />
                </button>

                {menuOpen ? (
                  <div role="menu" className="absolute right-0 mt-2 w-64 overflow-hidden rounded-2xl border border-line bg-surface shadow-lift">
                    <div className="border-b border-line px-4 py-3">
                      <p className="truncate text-sm font-semibold text-ink">{displayName(user)}</p>
                      <p className="truncate text-xs text-muted">{user.username}</p>
                      <span className="badge-brand mt-2">{roleLabel(user.role)}</span>
                    </div>
                    <div className="p-1.5">
                      <Link
                        href="/account"
                        role="menuitem"
                        className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-ink-soft hover:bg-raised hover:text-ink"
                      >
                        <KeyIcon className="h-4 w-4" /> Change password
                      </Link>
                      <button
                        type="button"
                        role="menuitem"
                        onClick={() => logout()}
                        className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-ink-soft hover:bg-raised hover:text-ink"
                      >
                        <LogoutIcon className="h-4 w-4" /> Sign out
                      </button>
                    </div>
                  </div>
                ) : null}
              </div>
            ) : ready ? (
              <div className="hidden items-center gap-2 sm:flex">
                <Link href="/auth/login" className="btn-ghost">
                  Sign in
                </Link>
                <Link href="/auth/register" className="btn-primary">
                  Create account
                </Link>
              </div>
            ) : null}

            <button
              type="button"
              onClick={() => setMobileOpen((v) => !v)}
              className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-line text-ink-soft hover:bg-raised md:hidden"
              aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileOpen}
            >
              {mobileOpen ? <CloseIcon className="h-5 w-5" /> : <MenuIcon className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </div>

      {mobileOpen ? (
        <div className="border-t border-line bg-canvas md:hidden">
          <div className="container-page space-y-1 py-3">
            {nav.map((item) => (
              <Link key={item.href} href={item.href} className="block rounded-lg px-3 py-3 text-[15px] font-medium text-ink hover:bg-raised">
                {item.label}
              </Link>
            ))}
            {!user ? (
              <div className="grid grid-cols-2 gap-2 pt-2">
                <Link href="/auth/login" className="btn-secondary">
                  Sign in
                </Link>
                <Link href="/auth/register" className="btn-primary">
                  Create account
                </Link>
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </header>
  )
}

export default ProfessionalHeader
