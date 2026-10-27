import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { Disclaimer, EmptyState, ErrorBanner, FlagBadge, PageTitle, Spinner } from '../components/UI'
import { diseaseLabel, formatDate, formatScore } from '../utils/format'

const Stat = ({ label, value }) => (
  <div className="card"><p className="text-sm text-slate-500">{label}</p><p className="mt-1 text-3xl font-bold text-slate-900">{value}</p></div>
)

export default function Dashboard() {
  const { data, error, loading, reload } = useAsync(() => api.dashboard({ days: 90 }), [])
  if (loading) return <Spinner label="Loading your dashboard…" />
  if (error) return <ErrorBanner error={error} onRetry={reload} />
  if (data.total_screenings === 0)
    return (
      <>
        <PageTitle title="Dashboard" />
        <EmptyState title="No screenings yet" action={<Link className="btn btn-primary" to="/screen">Run your first screening</Link>}>
          Your totals and trends will appear here after you run a screening. Nothing on this page is sample data.
        </EmptyState>
      </>
    )
  const byDisease = Object.entries(data.by_disease).map(([k, v]) => ({ name: diseaseLabel(k), count: v }))
  return (
    <div className="space-y-6">
      <PageTitle title="Dashboard" subtitle={`Your screenings in the last ${data.window_days} days (computed from stored records).`} />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Total screenings" value={data.total_screenings} />
        <Stat label="Elevated screening score" value={data.flagged_elevated} />
        <Stat label="Lower screening score" value={data.flagged_lower} />
        <Stat label="Mean score" value={formatScore(data.mean_score)} />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card" aria-labelledby="trend-title">
          <h2 id="trend-title" className="mb-3 font-semibold">Screenings per day</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.trend}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" /><YAxis allowDecimals={false} /><Tooltip /><Legend />
                <Line type="monotone" dataKey="count" name="Screenings" stroke="#0f766e" strokeWidth={2} />
                <Line type="monotone" dataKey="flagged" name="Elevated" stroke="#dc2626" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
        <section className="card" aria-labelledby="mod-title">
          <h2 id="mod-title" className="mb-3 font-semibold">By module</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byDisease}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis allowDecimals={false} /><Tooltip /><Bar dataKey="count" fill="#0f766e" /></BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>
      <section className="card" aria-labelledby="recent-title">
        <h2 id="recent-title" className="mb-3 font-semibold">Recent screenings</h2>
        <ul className="divide-y">
          {data.recent.map((r) => (
            <li key={r.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
              <span>{diseaseLabel(r.disease)} · {formatDate(r.created_at)}</span>
              <span className="flex items-center gap-3"><span>score {formatScore(r.screening_score)}</span><FlagBadge flag={r.screening_flag} /><Link className="font-medium text-brand-700 underline" to={`/results/${r.id}`}>Open</Link></span>
            </li>
          ))}
        </ul>
      </section>
      <p className="text-xs text-slate-500">{data.note}</p>
      <Disclaimer />
    </div>
  )
}
