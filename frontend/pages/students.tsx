import { useEffect } from 'react'
import { useRouter } from 'next/router'
import { PageSpinner } from '../components/ui'

/**
 * Route: /students
 * Redirects to admin dashboard - only admins can manage students.
 */
export default function StudentsRedirect() {
  const router = useRouter()

  useEffect(() => {
    router.replace('/admin/dashboard')
  }, [router])

  return <PageSpinner label="Redirecting" />
}
