import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import FeatureField from '../components/FeatureField'
import { Disclaimer, ErrorBanner, PageTitle, Spinner } from '../components/UI'
import { buildPayload, validateForm } from '../utils/validation'

export default function Screening() {
  const { disease } = useParams()
  const navigate = useNavigate()
  const { data: all, error, loading, reload } = useAsync(() => api.diseases(), [])
  const [values, setValues] = useState({})
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState(null)
  const [busy, setBusy] = useState(false)
  const summary = useRef(null)

  useEffect(() => { setValues({}); setErrors({}); setServerError(null) }, [disease])
  if (loading) return <Spinner label="Loading the form…" />
  if (error) return <ErrorBanner error={error} onRetry={reload} />
  const module = all.find((d) => d.id === disease && d.data_type === 'tabular')
  if (!module) return <ErrorBanner error={{ message: 'Unknown screening module.' }} />
  if (module.status !== 'available')
    return <ErrorBanner error={{ message: 'This module is not available: its model has not been trained on the server.' }} />

  const onChange = (name, v) => { setValues((s) => ({ ...s, [name]: v })); if (errors[name]) setErrors((e) => ({ ...e, [name]: undefined })) }
  const fillExample = async (key) => {
    try {
      const ex = await api.examples(disease)
      const row = ex[key]
      setValues(Object.fromEntries(Object.entries(row).map(([k, v]) => [k, v == null ? '' : String(v)])))
      setErrors({})
    } catch (e) { setServerError(e) }
  }
  const submit = async (ev) => {
    ev.preventDefault()
    setServerError(null)
    const errs = validateForm(module.features, values)
    setErrors(errs)
    if (Object.keys(errs).length) { summary.current && summary.current.focus(); return }
    setBusy(true)
    try {
      const res = await api.screen(disease, buildPayload(module.features, values))
      navigate(`/results/${res.id}`)
    } catch (e) { setServerError(e) } finally { setBusy(false) }
  }
  const errorList = Object.values(errors).filter(Boolean)

  return (
    <form onSubmit={submit} noValidate aria-label={`${module.name} input form`}>
      <PageTitle title={module.name} subtitle={module.description} />
      <Disclaimer className="mb-6" />
      <div className="mb-4 flex flex-wrap gap-2">
        <button type="button" className="btn btn-secondary" onClick={() => fillExample('dataset_positive_example')}>Fill with a real example labelled positive in the dataset</button>
        <button type="button" className="btn btn-secondary" onClick={() => fillExample('dataset_negative_example')}>Fill with a real example labelled negative in the dataset</button>
        <button type="button" className="btn btn-secondary" onClick={() => { setValues({}); setErrors({}) }}>Clear</button>
      </div>
      <p className="mb-4 text-xs text-slate-500">The examples are rows from the public research dataset's held-out test split, not patient data. The model can disagree with the dataset label: no model is perfect. Do not enter real patient information.</p>
      {errorList.length > 0 && (
        <div ref={summary} tabIndex={-1} role="alert" className="mb-4 rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-800">
          <p className="font-semibold">Please fix {errorList.length} {errorList.length === 1 ? 'problem' : 'problems'} before submitting:</p>
          <ul className="mt-1 list-disc pl-5">{errorList.slice(0, 5).map((m) => <li key={m}>{m}</li>)}{errorList.length > 5 && <li>…and {errorList.length - 5} more</li>}</ul>
        </div>
      )}
      <ErrorBanner error={serverError} />
      <div className="card mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {module.features.map((f) => <FeatureField key={f.name} feature={f} value={values[f.name]} error={errors[f.name]} onChange={onChange} />)}
      </div>
      <div className="mt-6 flex items-center gap-3">
        <button className="btn btn-primary" disabled={busy}>{busy ? 'Scoring…' : 'Run screening'}</button>
        <Link to="/screen" className="btn btn-secondary">Back</Link>
      </div>
    </form>
  )
}
