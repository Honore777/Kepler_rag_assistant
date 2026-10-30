import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { api } from '../../lib/api'
import { homeFor, roleLabel } from '../../lib/auth'
import { site } from '../../lib/site'
import AuthShell from '../../components/AuthShell'
import PasswordInput from '../../components/PasswordInput'
import { Notice, Spinner } from '../../components/ui'

type InviteInfo = { valid: boolean; reason?: string | null; email?: string; role?: string }

const reasonText: Record<string, string> = {
  not_found: 'This invitation link is not valid. Ask the administration to send you a new one.',
  used: 'This invitation has already been used. If that was you, sign in instead.',
  expired: 'This invitation has expired. Ask the administration to send you a new one.',
}

const RegisterPage: React.FC = () => {
  const router = useRouter()
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    full_name: '',
    role: 'student',
    registration_code: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [invite, setInvite] = useState<InviteInfo | null>(null)
  const [checkingInvite, setCheckingInvite] = useState(false)

  const inviteToken = typeof router.query.token === 'string' ? router.query.token : ''

  useEffect(() => {
    if (!router.isReady || !inviteToken) return
    setCheckingInvite(true)
    api
      .get<InviteInfo>(`/invites/validate-token/${encodeURIComponent(inviteToken)}`)
      .then((res) => {
        setInvite(res.data)
        if (res.data.valid && res.data.email) {
          setFormData((prev) => ({ ...prev, username: res.data.email as string }))
        }
      })
      .catch(() => setInvite({ valid: false, reason: 'not_found' }))
      .finally(() => setCheckingInvite(false))
  }, [router.isReady, inviteToken])

  const invitedOk = !!inviteToken && invite?.valid === true
  const invitedBad = !!inviteToken && invite !== null && invite.valid === false

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      if (invitedOk) {
        await api.post('/invites/register-with-invite', {
          invite_token: inviteToken,
          username: formData.username,
          password: formData.password,
          full_name: formData.full_name,
        })
      } else {
        await api.post('/auth/register', formData)
      }

      const login = await api.post('/auth/login', { username: formData.username, password: formData.password })
      const userInfo = login.data?.user
      if (userInfo) localStorage.setItem('userInfo', JSON.stringify(userInfo))
      router.push(homeFor(userInfo?.role))
    } catch (err: any) {
      const detail = err.response?.data?.detail
      setError(typeof detail === 'string' ? detail : 'We could not create your account. Please check your details and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Create account"
      heading={invitedOk ? 'Accept your invitation' : 'Create your account'}
      subheading={
        invitedOk
          ? `You have been invited to join as ${roleLabel(invite?.role).toLowerCase()}.`
          : `Students register with their @${site.studentDomain} email.`
      }
      image="/images/enhanced/student-learning.webp"
      imageAlt="A speaker addressing students at Kepler College"
      panelTitle="Your handbook, one question away."
      panelText="Students sign up in a minute. Staff and board members join through the invitation link sent by the administration."
      footer={
        <>
          Already have an account?{' '}
          <Link href="/auth/login" className="font-semibold text-brand hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      {checkingInvite ? (
        <div className="flex items-center gap-3 text-sm text-muted">
          <Spinner className="h-4 w-4" /> Checking your invitation
        </div>
      ) : invitedBad ? (
        <div className="space-y-5">
          <Notice tone="danger">{reasonText[invite?.reason || 'not_found'] || reasonText.not_found}</Notice>
          <Link href="/auth/login" className="btn-secondary w-full">
            Go to sign in
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="full_name" className="label">
              Full name
            </label>
            <input
              id="full_name"
              type="text"
              autoComplete="name"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              className="input"
              placeholder="As you would like it to appear"
              required
            />
          </div>

          <div>
            <label htmlFor="email" className="label">
              Email address
            </label>
            <input
              id="email"
              type="email"
              autoComplete="username"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              className="input"
              placeholder={`name@${site.studentDomain}`}
              required
              readOnly={invitedOk}
              disabled={invitedOk}
            />
            {invitedOk ? <p className="hint">This is the address your invitation was sent to.</p> : null}
          </div>

          <div>
            <label htmlFor="password" className="label">
              Password
            </label>
            <PasswordInput
              id="password"
              autoComplete="new-password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              placeholder="At least 8 characters"
              required
              minLength={8}
            />
          </div>

          {!invitedOk ? (
            <fieldset>
              <legend className="label">I am registering as</legend>
              <div className="grid grid-cols-2 gap-2 rounded-xl bg-raised p-1" role="radiogroup">
                {[
                  { value: 'student', label: 'A student' },
                  { value: 'staff', label: 'Staff or board' },
                ].map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    role="radio"
                    aria-checked={formData.role === opt.value}
                    onClick={() => setFormData({ ...formData, role: opt.value })}
                    className={`rounded-lg px-3 py-2 text-sm font-semibold transition-colors ${
                      formData.role === opt.value ? 'bg-surface text-ink shadow-sm' : 'text-muted hover:text-ink'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </fieldset>
          ) : null}

          {!invitedOk && formData.role === 'staff' ? (
            <div>
              <label htmlFor="code" className="label">
                Registration code
              </label>
              <input
                id="code"
                type="text"
                value={formData.registration_code}
                onChange={(e) => setFormData({ ...formData, registration_code: e.target.value })}
                className="input"
                placeholder="Provided by the administration"
                required
              />
              <p className="hint">Prefer a personal invitation link? Ask the administration to send you one.</p>
            </div>
          ) : null}

          {error ? <Notice tone="danger">{error}</Notice> : null}

          <button type="submit" disabled={loading} className="btn-primary btn-lg w-full">
            {loading ? (
              <>
                <Spinner className="h-5 w-5" /> Creating account
              </>
            ) : (
              'Create account'
            )}
          </button>
        </form>
      )}
    </AuthShell>
  )
}

export default RegisterPage
