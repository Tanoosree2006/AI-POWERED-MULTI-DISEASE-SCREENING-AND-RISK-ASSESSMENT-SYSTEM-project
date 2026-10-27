import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { Activity, LogOut } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

const link = ({ isActive }) =>
  `rounded-md px-3 py-2 text-sm font-medium ${isActive ? 'bg-brand-100 text-brand-900' : 'text-slate-600 hover:bg-slate-100'}`

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-slate-200 bg-white">
        <nav aria-label="Main" className="mx-auto flex max-w-6xl flex-wrap items-center gap-1 px-4 py-3">
          <Link to="/" className="mr-4 flex items-center gap-2 font-bold text-brand-900">
            <Activity className="h-5 w-5 text-brand-600" aria-hidden="true" /> AI Screening
          </Link>
          {user && (
            <>
              <NavLink to="/dashboard" className={link}>Dashboard</NavLink>
              <NavLink to="/screen" className={link}>Screening</NavLink>
              <NavLink to="/image" className={link}>Image</NavLink>
              <NavLink to="/history" className={link}>History</NavLink>
            </>
          )}
          <NavLink to="/metrics" className={link}>Model performance</NavLink>
          <NavLink to="/about" className={link}>About</NavLink>
          <div className="ml-auto flex items-center gap-2">
            {user ? (
              <>
                <span className="text-sm text-slate-600">Signed in as <strong>{user.username}</strong></span>
                <button className="btn btn-secondary" onClick={() => { logout(); navigate('/') }}>
                  <LogOut className="h-4 w-4" aria-hidden="true" /> Sign out
                </button>
              </>
            ) : (
              <>
                <Link className="btn btn-secondary" to="/login">Sign in</Link>
                <Link className="btn btn-primary" to="/register">Register</Link>
              </>
            )}
          </div>
        </nav>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8"><Outlet /></main>
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        Academic research prototype. Not a medical device. Not clinically validated. Aditya University, CSE 2026-27.
      </footer>
    </div>
  )
}
