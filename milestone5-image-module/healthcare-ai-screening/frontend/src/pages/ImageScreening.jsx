import { useEffect, useState } from 'react'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import GradCamView from '../components/GradCamView'
import { Disclaimer, ErrorBanner, FlagBadge, PageTitle, Spinner } from '../components/UI'
import { validateImageFile } from '../utils/validation'
import { formatScore } from '../utils/format'

export default function ImageScreening() {
  const { data, error, loading, reload } = useAsync(() => api.diseases(), [])
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [fileError, setFileError] = useState(null)
  const [serverError, setServerError] = useState(null)
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])
  if (loading) return <Spinner label="Checking the image module…" />
  if (error) return <ErrorBanner error={error} onRetry={reload} />
  const mod = data.find((d) => d.id === 'image_screening')

  if (!mod || mod.status !== 'available')
    return (
      <>
        <PageTitle title="Image screening" />
        <div role="status" className="card">
          <h2 className="font-semibold">The image module is not available on this server</h2>
          <p className="mt-2 text-sm text-slate-600">
            No image model has been trained and installed yet. Train one with <code>ml/src/imaging/train_image.py</code> on a licensed
            public dataset, then restart the backend. Until then this page cannot produce results, and none are shown.
          </p>
        </div>
      </>
    )

  const choose = (ev) => {
    const f = ev.target.files && ev.target.files[0]
    setResult(null); setServerError(null)
    const msg = validateImageFile(f)
    setFileError(msg)
    if (preview) URL.revokeObjectURL(preview)
    if (msg) { setFile(null); setPreview(null); return }
    setFile(f); setPreview(URL.createObjectURL(f))
  }
  const submit = async (ev) => {
    ev.preventDefault()
    const msg = validateImageFile(file)
    setFileError(msg)
    if (msg) return
    setBusy(true); setServerError(null)
    try { setResult(await api.screenImage(file)) } catch (e) { setServerError(e) } finally { setBusy(false) }
  }

  return (
    <div className="space-y-6">
      <PageTitle title="Image screening" subtitle={`${mod.name}. Positive class: ${mod.positive_class}. Model: ${mod.model}.`} />
      <Disclaimer />
      <form onSubmit={submit} noValidate className="card space-y-4" aria-label="Image upload">
        <div>
          <label htmlFor="image-file" className="label">Choose a PNG or JPEG image (max 5 MB)</label>
          <input id="image-file" type="file" accept="image/png,image/jpeg" onChange={choose} aria-invalid={Boolean(fileError)}
                 aria-describedby={fileError ? 'image-err' : undefined} className="block w-full text-sm" />
          {fileError && <p id="image-err" role="alert" className="mt-1 text-xs font-medium text-red-700">{fileError}</p>}
          <p className="mt-1 text-xs text-slate-500">The image is analysed in memory and is not stored. Only a fingerprint and the score are saved. Use public research images only.</p>
        </div>
        <ErrorBanner error={serverError} />
        <button className="btn btn-primary" disabled={busy || !file}>{busy ? 'Analysing…' : 'Analyse image'}</button>
      </form>
      {result && (
        <>
          <section className="card" aria-labelledby="img-score">
            <h2 id="img-score" className="text-sm font-medium text-slate-500">Model-estimated screening score</h2>
            <div className="mt-2 flex items-center gap-4"><p className="text-5xl font-bold">{formatScore(result.screening_score)}</p><FlagBadge flag={result.screening_flag} /></div>
            <p className="mt-2 text-sm text-slate-600">Uncalibrated model score, not a diagnosis. Flagged when at least {result.threshold}.</p>
          </section>
          <GradCamView originalUrl={preview} gradcam={result.gradcam} />
        </>
      )}
    </div>
  )
}
