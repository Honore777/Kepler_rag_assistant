import React, { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { api } from '../../lib/api'
import { homeFor } from '../../lib/auth'
import AuthShell from '../../components/AuthShell'
import PasswordInput from '../../components/PasswordInput'
import { Notice, Spinner } from '../../components/ui'
import { site } from '../../lib/site'

const LoginPage: React.FC = () => {
  const router = useRouter()
  const [formData, setFormData] = useState({ username: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await api.post('/auth/login', formData)

      const userInfo = response.data?.user
      if (userInfo) {
        localStorage.setItem('userInfo', JSON.stringify(userInfo))
      }

      router.push(homeFor(userInfo?.role))
    } catch (err: any) {
      const status = err.response?.status
      const detail = err.response?.data?.detail
      setError(
        status === 401
          ? 'That email and password do not match. Please try again.'
          : typeof detail === 'string'
            ? detail
            : 'We could not sign you in. Please try again in a moment.'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Sign in"
      heading="Welcome back"
      subheading="Sign in to ask questions about the documents shared with your role."
      image="/images/enhanced/graduation.webp"
      imageAlt="Graduates in green stoles at a Kepler College ceremony"
      panelTitle="Pick up where you left off."
      panelText="Your recent conversations are kept on this device, so you can return to an earlier answer without asking again."
      footer={
        <>
          New to the assistant?{' '}
          <Link href="/auth/register" className="font-semibold text-brand hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-5" noValidate={false}>
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
          />
        </div>

        <div>
          <label htmlFor="password" className="label">
            Password
          </label>
          <PasswordInput
            id="password"
            autoComplete="current-password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            placeholder="Your password"
            required
          />
        </div>

        {error ? <Notice tone="danger">{error}</Notice> : null}

        <button type="submit" disabled={loading} className="btn-primary btn-lg w-full">
          {loading ? (
            <>
              <Spinner className="h-5 w-5" /> Signing in
            </>
          ) : (
            'Sign in'
          )}
        </button>
      </form>
    </AuthShell>
  )
}

export default LoginPage
