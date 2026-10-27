import { Link, useParams } from 'react-router-dom'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import ShapChart from '../components/ShapChart'
import { Disclaimer, ErrorBanner, FlagBadge, PageTitle, Spinner } from '../components/UI'
import { diseaseLabel, formatDate, formatScore } from '../utils/format'

export default function Result() {
  const { id } = useParams()
  const { data: r, error, loading, reload } = useAsync(() => api.record(id), [id])
  if (loading) return <Spinner label="Loading the result…" />
  if (error) return <ErrorBanner error={error} onRetry={reload} />
  return (
    <div className="space-y-6">
      <PageTitle title="Screening result" subtitle={`${diseaseLabel(r.disease)} · ${formatDate(r.created_at)} · record #${r.id}`} />
      <section className="card" aria-labelledby="score-title">
        <h2 id="score-title" className="text-sm font-medium text-slate-500">Model-estimated screening score</h2>
        <div className="mt-2 flex flex-wrap items-center gap-4">
          <p className="text-5xl font-bold text-slate-900">{formatScore(r.screening_score)}</p>
          <FlagBadge flag={r.screening_flag} />
        </div>
        <p className="mt-3 text-sm text-slate-600">
          The score is flagged "elevated" when it is at least {r.threshold}. It is an uncalibrated model score, not a probability of
          disease and not a diagnosis. Model: {r.model} (version {r.model_version}). A "lower" score does not rule out disease.
        </p>
        {r.warnings.length > 0 && (
          <ul role="alert" className="mt-4 list-disc space-y-1 rounded-lg border border-amber-300 bg-amber-50 p-4 pl-8 text-sm text-amber-900">
            {r.warnings.map((w) => <li key={w}>{w}</li>)}
          </ul>
        )}
      </section>
      {r.explanation && r.explanation.top_features ? <ShapChart explanation={r.explanation} />
        : <p className="card text-sm text-slate-600">{r.explanation && r.explanation.note ? r.explanation.note : 'No explanation stored for this record.'}</p>}
      <Disclaimer />
      <div className="flex gap-3"><Link className="btn btn-primary" to="/screen">New screening</Link><Link className="btn btn-secondary" to="/history">View history</Link></div>
    </div>
  )
}
