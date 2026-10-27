import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { ErrorBanner, PageTitle } from '../components/UI'

function AuthForm({ mode }) {
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const isRegister = mode === 'register'
  const [form, setForm] = useState({ username: '', password: '' })
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState(null)
  const [busy, setBusy] = useState(false)

  const validate = () => {
    const e = {}
    if (form.username.trim().length < 3) e.username = 'Username must be at least 3 characters'
    else if (!/^[A-Za-z0-9_.-]+$/.test(form.username)) e.username = 'Use only letters, numbers, dots, dashes and underscores'
    if (form.password.length < (isRegister ? 8 : 1)) e.password = isRegister ? 'Password must be at least 8 characters' : 'Password is required'
    if (form.password.length > 72) e.password = 'Password must be at most 72 characters'
    return e
  }

  const submit = async (ev) => {
    ev.preventDefault()
    const e = validate()
    setErrors(e)
    setServerError(null)
    if (Object.keys(e).length) return
    setBusy(true)
    try {
      await (isRegister ? register : login)(form.username.trim(), form.password)
      navigate((location.state && location.state.from) || '/dashboard', { replace: true })
    } catch (err) {
      setServerError(err)
    } finally {
      setBusy(false)
    }
  }

  const set = (k) => (ev) => setForm((f) => ({ ...f, [k]: ev.target.value }))
  return (
    <div className="mx-auto max-w-md">
      <PageTitle title={isRegister ? 'Create an account' : 'Sign in'} subtitle="Accounts keep your screening history private to you." />
      <form onSubmit={submit} noValidate className="card space-y-4" aria-label={isRegister ? 'Register' : 'Sign in'}>
        <ErrorBanner error={serverError} />
        <div>
          <label htmlFor="username" className="label">Username</label>
          <input id="username" className={`input ${errors.username ? 'input-error' : ''}`} value={form.username} onChange={set('username')}
                 autoComplete="username" aria-invalid={Boolean(errors.username)} aria-describedby={errors.username ? 'username-err' : undefined} />
          {errors.username && <p id="username-err" role="alert" className="mt-1 text-xs font-medium text-red-700">{errors.username}</p>}
        </div>
        <div>
          <label htmlFor="password" className="label">Password</label>
          <input id="password" type="password" className={`input ${errors.password ? 'input-error' : ''}`} value={form.password} onChange={set('password')}
                 autoComplete={isRegister ? 'new-password' : 'current-password'} aria-invalid={Boolean(errors.password)} aria-describedby={errors.password ? 'password-err' : undefined} />
          {errors.password && <p id="password-err" role="alert" className="mt-1 text-xs font-medium text-red-700">{errors.password}</p>}
          {isRegister && <p className="mt-1 text-xs text-slate-500">8 to 72 characters. Never reuse a real password in a demo.</p>}
        </div>
        <button className="btn btn-primary w-full" disabled={busy}>{busy ? 'Please wait…' : isRegister ? 'Create account' : 'Sign in'}</button>
        <p className="text-center text-sm text-slate-600">
          {isRegister ? <>Already registered? <Link className="font-medium text-brand-700 underline" to="/login">Sign in</Link></>
                      : <>New here? <Link className="font-medium text-brand-700 underline" to="/register">Create an account</Link></>}
        </p>
      </form>
    </div>
  )
}
export const Login = () => <AuthForm mode="login" />
export const Register = () => <AuthForm mode="register" />
