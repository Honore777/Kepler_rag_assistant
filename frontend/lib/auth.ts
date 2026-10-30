import { useEffect, useState } from 'react'
import { api } from './api'

export type SessionUser = {
  id?: string
  username: string
  full_name?: string | null
  role: string
}

const STORAGE_KEY = 'userInfo'

export const roleLabel = (role?: string | null): string => {
  switch ((role || '').toLowerCase()) {
    case 'student':
      return 'Student'
    case 'staff':
      return 'Staff'
    case 'board_member':
      return 'Board member'
    case 'admin':
      return 'Administrator'
    default:
      return role || 'Member'
  }
}

export const homeFor = (role?: string | null): string => ((role || '').toLowerCase() === 'admin' ? '/admin/dashboard' : '/chat')

export const getStoredUser = (): SessionUser | null => {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as SessionUser) : null
  } catch {
    return null
  }
}

export const displayName = (user?: SessionUser | null): string => {
  if (!user) return ''
  return (user.full_name || user.username || '').trim()
}

export const initialsOf = (user?: SessionUser | null): string => {
  const name = displayName(user)
  if (!name) return '?'
  const parts = name.split(/[\s@.]+/).filter(Boolean)
  return ((parts[0]?.[0] || '') + (parts[1]?.[0] || '')).toUpperCase() || '?'
}

/** Ends the server session (clears the HttpOnly cookie) and the locally stored profile. */
export const logout = async (): Promise<void> => {
  try {
    await api.post('/auth/logout')
  } catch {
    // The cookie may already be gone or the API unreachable; still clear local state.
  }
  window.localStorage.removeItem(STORAGE_KEY)
  window.localStorage.removeItem('authToken')
  window.location.href = '/auth/login'
}

/** Reads the signed-in user after mount (avoids server/client markup mismatch). */
export const useSessionUser = () => {
  const [user, setUser] = useState<SessionUser | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    setUser(getStoredUser())
    setReady(true)
  }, [])

  return { user, ready }
}
