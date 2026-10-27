import { AlertTriangle, Loader2, ShieldAlert } from 'lucide-react'
import { flagText } from '../utils/format'

export function Spinner({ label = 'Loading…' }) {
  return (
    <div role="status" aria-live="polite" className="flex items-center justify-center gap-2 py-10 text-slate-600">
      <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
      <span>{label}</span>
    </div>
  )
}

export function ErrorBanner({ error, onRetry }) {
  if (!error) return null
  return (
    <div role="alert" className="flex items-start gap-3 rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-800">
      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
      <div className="flex-1">
        <p className="font-semibold">Something went wrong</p>
        <p>{error.message || String(error)}</p>
      </div>
      {onRetry && <button className="btn btn-secondary" onClick={onRetry}>Try again</button>}
    </div>
  )
}

export function EmptyState({ title, children, action }) {
  return (
    <div className="card text-center">
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mx-auto mt-2 max-w-md text-sm text-slate-600">{children}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function Disclaimer({ className = '' }) {
  return (
    <div role="note" className={`flex items-start gap-3 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 ${className}`}>
      <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
      <p>
        <strong>Research prototype, not a medical device.</strong> Results are model-estimated screening scores, not
        diagnoses, and have not been clinically validated. They must not be used to start, stop or change treatment.
        Consult a qualified healthcare professional.
      </p>
    </div>
  )
}

export function FlagBadge({ flag }) {
  const high = flag === 'elevated'
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${high ? 'bg-red-100 text-red-800' : 'bg-emerald-100 text-emerald-800'}`}>
      {flagText(flag)}
    </span>
  )
}

export function PageTitle({ title, subtitle }) {
  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-slate-600">{subtitle}</p>}
    </div>
  )
}
