import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Trash2 } from 'lucide-react'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { useAuth } from '../hooks/useAuth'
import { EmptyState, ErrorBanner, FlagBadge, PageTitle, Spinner } from '../components/UI'
import { diseaseLabel, formatDate, formatScore } from '../utils/format'

const PAGE = 10

export default function History() {
  const { user } = useAuth()
  const [offset, setOffset] = useState(0)
  const [disease, setDisease] = useState('')
  const [all, setAll] = useState(false)
  const [actionError, setActionError] = useState(null)
  const { data, error, loading, reload } = useAsync(
    () => api.history({ limit: PAGE, offset, ...(disease ? { disease } : {}), ...(all ? { scope: 'all' } : {}) }), [offset, disease, all])

  const remove = async (id) => {
    if (!window.confirm('Delete this screening record permanently? This cannot be undone.')) return
    try { await api.deleteRecord(id); setActionError(null); reload() } catch (e) { setActionError(e) }
  }
  return (
    <>
      <PageTitle title="Screening history" subtitle="Records stored in your account. You can delete any of them at any time." />
      <div className="mb-4 flex flex-wrap items-center gap-4">
        <label className="text-sm">Module{' '}
          <select className="input ml-2 inline-block w-auto" value={disease} onChange={(e) => { setOffset(0); setDisease(e.target.value) }} aria-label="Filter by module">
            <option value="">All</option><option value="breast_cancer">Breast cancer</option><option value="diabetes">Diabetes</option>
            <option value="heart_disease">Heart disease</option><option value="image_screening">Image screening</option>
          </select>
        </label>
        {user && user.role === 'admin' && (
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={all} onChange={(e) => { setOffset(0); setAll(e.target.checked) }} /> All users (admin)</label>
        )}
      </div>
      <ErrorBanner error={actionError} />
      {loading ? <Spinner label="Loading history…" /> : error ? <ErrorBanner error={error} onRetry={reload} /> : data.total === 0 ? (
        <EmptyState title="No screenings found" action={<Link className="btn btn-primary" to="/screen">Run a screening</Link>}>
          Records appear here after you run a screening{disease ? ' for this module' : ''}.
        </EmptyState>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Screening history</caption>
            <thead><tr className="border-b text-slate-500"><th className="py-2 pr-3">#</th><th className="pr-3">Date</th><th className="pr-3">Module</th><th className="pr-3">Score</th><th className="pr-3">Flag</th><th><span className="sr-only">Actions</span></th></tr></thead>
            <tbody>
              {data.items.map((r) => (
                <tr key={r.id} className="border-b border-slate-100">
                  <td className="py-2 pr-3">{r.id}</td><td className="pr-3">{formatDate(r.created_at)}</td><td className="pr-3">{diseaseLabel(r.disease)}</td>
                  <td className="pr-3">{formatScore(r.screening_score)}</td><td className="pr-3"><FlagBadge flag={r.screening_flag} /></td>
                  <td className="flex gap-2 py-2">
                    <Link className="btn btn-secondary" to={`/results/${r.id}`}>Open</Link>
                    <button className="btn btn-danger" onClick={() => remove(r.id)} aria-label={`Delete record ${r.id}`}><Trash2 className="h-4 w-4" aria-hidden="true" /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
            <span>Showing {offset + 1} to {Math.min(offset + PAGE, data.total)} of {data.total}</span>
            <span className="flex gap-2">
              <button className="btn btn-secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>Previous</button>
              <button className="btn btn-secondary" disabled={offset + PAGE >= data.total} onClick={() => setOffset(offset + PAGE)}>Next</button>
            </span>
          </div>
        </div>
      )}
    </>
  )
}
