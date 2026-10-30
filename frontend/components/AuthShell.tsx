import React from 'react'
import Head from 'next/head'
import Logo from './Logo'
import ThemeToggle from './ThemeToggle'
import { site } from '../lib/site'

type AuthShellProps = {
  title: string
  heading: string
  subheading?: string
  /** Enhanced photo shown in the side panel on large screens. */
  image: string
  imageAlt: string
  panelTitle: string
  panelText: string
  children: React.ReactNode
  footer?: React.ReactNode
}

/** Split-screen frame shared by sign-in, registration and account screens. */
export default function AuthShell({
  title,
  heading,
  subheading,
  image,
  imageAlt,
  panelTitle,
  panelText,
  children,
  footer,
}: AuthShellProps) {
  return (
    <div className="min-h-screen bg-canvas lg:grid lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]">
      <Head>
        <title>{`${title} · ${site.name}`}</title>
      </Head>

      <div className="flex min-h-screen flex-col">
        <div className="imigongo-band lg:hidden" aria-hidden="true" />
        <div className="flex items-center justify-between px-5 py-5 sm:px-10">
          <Logo />
          <ThemeToggle />
        </div>

        <div className="flex flex-1 items-center px-5 pb-12 pt-4 sm:px-10">
          <div className="mx-auto w-full max-w-md animate-fade-up">
            <h1 className="text-[2rem] font-medium leading-tight sm:text-4xl">{heading}</h1>
            {subheading ? <p className="mt-3 text-[15px] leading-7 text-muted">{subheading}</p> : null}
            <div className="mt-8">{children}</div>
            {footer ? <div className="mt-8 text-center text-sm text-muted">{footer}</div> : null}
          </div>
        </div>
      </div>

      <aside className="relative hidden overflow-hidden lg:block" aria-hidden="false">
        <div className="photo-frame absolute inset-0">
          <img src={image} alt={imageAlt} />
        </div>
        <div className="absolute inset-0 bg-gradient-to-t from-footer via-footer/55 to-footer/10" />
        <div className="imigongo-band absolute inset-x-0 top-0 !bg-white/90" />
        <div className="absolute inset-x-0 bottom-0 p-12 xl:p-16">
          <h2 className="max-w-md text-3xl font-medium leading-snug !text-white xl:text-4xl">{panelTitle}</h2>
          <p className="mt-4 max-w-md text-[15px] leading-7 text-white/80">{panelText}</p>
        </div>
      </aside>
    </div>
  )
}
