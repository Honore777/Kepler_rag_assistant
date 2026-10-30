import { useEffect } from 'react'
import { useRouter } from 'next/router'
import { PageSpinner } from '../components/ui'

/** Route: /login. Legacy address; sign-in lives at /auth/login. */
export default function LegacyLogin() {
  const router = useRouter()

  useEffect(() => {
    router.replace('/auth/login')
  }, [router])

  return <PageSpinner label="Redirecting to sign in" />
}
