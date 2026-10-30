import { useEffect } from 'react'
import { useRouter } from 'next/router'
import { PageSpinner } from '../../components/ui'

/**
 * Route: /student/dashboard
 * Redirects to chat - students only need the chat assistant.
 */
export default function StudentDashboard() {
  const router = useRouter()

  useEffect(() => {
    router.replace('/chat')
  }, [router])

  return <PageSpinner label="Redirecting" />
}
