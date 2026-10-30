import Head from 'next/head'
import { ReactNode } from 'react'
import ProfessionalHeader from './ProfessionalHeader'
import ProfessionalFooter from './ProfessionalFooter'
import { site } from '../lib/site'

type LayoutProps = {
  /** Document title (browser tab). */
  title?: string
  children: ReactNode
  /** Custom header, e.g. for pages that need a different one. Defaults to the site header. */
  header?: ReactNode
  /** Show the footer (default true). Full-height app screens turn it off. */
  footer?: boolean
  /** Remove the page container and padding so the screen can use all remaining space. */
  bleed?: boolean
}

/**
 * App shell used by all pages: consistent header, optional footer, sensible spacing.
 */
export default function Layout({ title, children, header, footer = true, bleed = false }: LayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-canvas">
      <Head>
        <title>{title ? `${title} · ${site.name}` : `${site.name} ${site.product}`}</title>
      </Head>
      {header ?? <ProfessionalHeader />}
      <main className={bleed ? 'flex-1' : 'container-page flex-1 py-10 md:py-12'}>{children}</main>
      {footer ? <ProfessionalFooter /> : null}
    </div>
  )
}
