import { useEffect } from 'react'
import '../styles/globals.css'
import type { AppProps } from 'next/app'
import Head from 'next/head'
import { Provider } from 'react-redux'
import store from '../store'
import { initializeTheme } from '../lib/theme'

// Global app entrypoint. Wraps all pages with Redux provider.
export default function App({ Component, pageProps }: AppProps) {
  useEffect(() => {
    initializeTheme()
  }, [])

  useEffect(() => {
    if (process.env.NODE_ENV === 'production') return
    if (!('serviceWorker' in navigator)) return

    navigator.serviceWorker.getRegistrations().then((registrations) => {
      registrations.forEach((registration) => {
        registration.unregister()
      })
    })
  }, [])

  return (
    <Provider store={store}>
      <Head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="description" content="Ask questions about Kepler College policies, handbooks and procedures and get answers with their sources." />
        <title>Kepler College Knowledge Assistant</title>
      </Head>
      <Component {...pageProps} />
    </Provider>
  )
}
