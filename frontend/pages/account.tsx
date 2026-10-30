import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import Layout from '../components/Layout'
import PasswordInput from '../components/PasswordInput'
import { Notice, PageSpinner, Spinner } from '../components/ui'
import { api } from '../lib/api'
import { displayName, getStoredUser, roleLabel, SessionUser } from '../lib/auth'

/** Route: /account. Lets a signed-in user change their own password. */
export default function AccountPage() {
  const router = useRouter()
  const [user, setUser] = useState<SessionUser | null>(null)
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)

  useEffect(() => {
    const stored = getStoredUser()
    if (!stored) {
      router.replace('/auth/login')
      return
    }
    setUser(stored)
  }, [router])

  if (!user) return <PageSpinner />

  const mismatch = confirm.length > 0 && next !== confirm

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setDone(false)
    if (next !== confirm) {
      setError('The new password and its confirmation do not match.')
      return
    }

    setSaving(true)
    try {
      await api.post('/auth/change-password', { current_password: current, new_password: next })
      setDone(true)
      setCurrent('')
      setNext('')
      setConfirm('')
    } catch (err: any) {
      const status = err.response?.status
      const detail = err.response?.data?.detail
      if (status === 401) {
        setError('Your session has ended. Please sign in again.')
      } else if (typeof detail === 'string') {
        setError(detail.charAt(0).toUpperCase() + detail.slice(1) + '.')
      } else {
        setError('We could not update your password. Please check the details and try again.')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <Layout title="Account">
      <div className="mx-auto max-w-xl">
        <p className="eyebrow">Account</p>
        <h1 className="mt-2 text-3xl font-medium sm:text-4xl">Your account</h1>

        <div className="card mt-8 flex items-center gap-4 p-5">
          <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-soft font-display text-lg font-semibold text-brand">
            {displayName(user).charAt(0).toUpperCase()}
          </span>
          <div className="min-w-0">
            <p className="truncate font-semibold text-ink">{displayName(user)}</p>
            <p className="truncate text-sm text-muted">{user.username}</p>
          </div>
          <span className="badge-brand ml-auto">{roleLabel(user.role)}</span>
        </div>

        <form onSubmit={submit} className="card mt-6 space-y-5 p-6 sm:p-8">
          <div>
            <h2 className="text-xl font-medium">Change password</h2>
            <p className="mt-1 text-sm text-muted">Choose a password you do not use anywhere else. At least 8 characters.</p>
          </div>

          <div>
            <label htmlFor="current" className="label">
              Current password
            </label>
            <PasswordInput id="current" autoComplete="current-password" value={current} onChange={(e) => setCurrent(e.target.value)} required />
          </div>
          <div>
            <label htmlFor="next" className="label">
              New password
            </label>
            <PasswordInput id="next" autoComplete="new-password" value={next} onChange={(e) => setNext(e.target.value)} required minLength={8} />
          </div>
          <div>
            <label htmlFor="confirm" className="label">
              Confirm new password
            </label>
            <PasswordInput id="confirm" autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required minLength={8} />
            {mismatch ? <p className="mt-1.5 text-xs font-medium text-danger">The passwords do not match yet.</p> : null}
          </div>

          {error ? <Notice tone="danger">{error}</Notice> : null}
          {done ? <Notice tone="success">Your password has been updated.</Notice> : null}

          <button type="submit" disabled={saving || !current || !next || !confirm} className="btn-primary w-full sm:w-auto">
            {saving ? (
              <>
                <Spinner className="h-4 w-4" /> Saving
              </>
            ) : (
              'Update password'
            )}
          </button>
        </form>
      </div>
    </Layout>
  )
}
