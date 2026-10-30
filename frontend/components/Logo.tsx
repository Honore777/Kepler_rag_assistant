import React from 'react'
import Link from 'next/link'
import { site } from '../lib/site'

type LogoProps = {
  href?: string
  /** Use light text, for placement on the dark footer. */
  onDark?: boolean
  compact?: boolean
}

export default function Logo({ href = '/landing', onDark = false, compact = false }: LogoProps) {
  return (
    <Link href={href} className="group inline-flex items-center gap-3" aria-label={`${site.name} home`}>
      <img
        src="/images/enhanced/logo.png"
        alt=""
        width={40}
        height={40}
        className="h-10 w-10 rounded-xl ring-1 ring-black/10"
      />
      <span className="leading-tight">
        <span className={`block font-display text-[1.15rem] font-semibold ${onDark ? 'text-white' : 'text-ink'}`}>{site.name}</span>
        {compact ? null : (
          <span className={`block text-[11px] font-medium uppercase ${onDark ? 'text-footer-ink/70' : 'text-muted'}`} style={{ letterSpacing: '0.14em' }}>
            {site.product}
          </span>
        )}
      </span>
    </Link>
  )
}
