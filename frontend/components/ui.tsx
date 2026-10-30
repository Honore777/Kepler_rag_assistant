import React from 'react'

export const Spinner = ({ className = 'h-5 w-5' }: { className?: string }) => (
  <svg className={`${className} animate-spin`} viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.25" strokeWidth="3" />
    <path d="M21 12a9 9 0 00-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
  </svg>
)

/** Full-page loading state used while a route checks the session or redirects. */
export const PageSpinner = ({ label = 'Loading' }: { label?: string }) => (
  <div className="flex min-h-screen items-center justify-center bg-canvas text-brand" role="status">
    <Spinner className="h-8 w-8" />
    <span className="sr-only">{label}</span>
  </div>
)

type NoticeProps = {
  tone?: 'success' | 'danger' | 'info' | 'warn'
  children: React.ReactNode
  className?: string
}

const noticeStyles: Record<NonNullable<NoticeProps['tone']>, string> = {
  success: 'border-leaf/30 bg-leaf-soft text-leaf',
  danger: 'border-danger/30 bg-danger-soft text-danger',
  info: 'border-brand/25 bg-brand-soft text-brand',
  warn: 'border-warn/30 bg-warn-soft text-warn',
}

export const Notice = ({ tone = 'info', children, className = '' }: NoticeProps) => (
  <div
    role={tone === 'danger' ? 'alert' : 'status'}
    className={`rounded-xl border px-4 py-3 text-sm font-medium ${noticeStyles[tone]} ${className}`}
  >
    {children}
  </div>
)

export const EmptyState = ({
  icon,
  title,
  children,
}: {
  icon?: React.ReactNode
  title: string
  children?: React.ReactNode
}) => (
  <div className="flex flex-col items-center px-6 py-14 text-center">
    {icon ? <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-raised text-muted">{icon}</div> : null}
    <p className="font-display text-lg text-ink">{title}</p>
    {children ? <p className="mt-1 max-w-sm text-sm text-muted">{children}</p> : null}
  </div>
)
