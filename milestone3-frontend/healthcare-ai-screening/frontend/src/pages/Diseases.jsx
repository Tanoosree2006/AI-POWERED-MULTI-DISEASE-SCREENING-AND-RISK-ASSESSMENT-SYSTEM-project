import { Link } from 'react-router-dom'
import { Droplets, HeartPulse, Microscope, ScanLine } from 'lucide-react'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { ErrorBanner, PageTitle, Spinner } from '../components/UI'

const icons = { breast_cancer: Microscope, diabetes: Droplets, heart_disease: HeartPulse, image_screening: ScanLine }

export default function Diseases() {
  const { data, error, loading, reload } = useAsync(() => api.diseases(), [])
  if (loading) return <Spinner label="Loading disease modules…" />
  if (error) return <ErrorBanner error={error} onRetry={reload} />
  return (
    <>
      <PageTitle title="Choose a screening module" subtitle="Only modules whose trained model is installed on this server can be used." />
      <div className="grid gap-4 sm:grid-cols-2">
        {data.map((d) => {
          const Icon = icons[d.id] || Microscope
          const ok = d.status === 'available'
          const to = d.data_type === 'image' ? '/image' : `/screen/${d.id}`
          return (
            <div key={d.id} className={`card flex flex-col ${ok ? '' : 'opacity-70'}`}>
              <div className="flex items-start gap-3">
                <Icon className="h-8 w-8 shrink-0 text-brand-600" aria-hidden="true" />
                <div>
                  <h2 className="font-semibold">{d.name}</h2>
                  <p className="mt-1 text-sm text-slate-600">{d.description}</p>
                  {ok && d.dataset && <p className="mt-2 text-xs text-slate-500">Trained on: {d.dataset}</p>}
                  {ok && d.n_features && <p className="text-xs text-slate-500">{d.n_features} inputs · model: {d.model}</p>}
                </div>
              </div>
              <div className="mt-4">
                {ok ? <Link className="btn btn-primary" to={to}>Start screening</Link>
                    : <span className="inline-block rounded-full bg-slate-200 px-3 py-1 text-xs font-semibold text-slate-700">Not available: model not trained on this server</span>}
              </div>
            </div>
          )
        })}
      </div>
    </>
  )
}
