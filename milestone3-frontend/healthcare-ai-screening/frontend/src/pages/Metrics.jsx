import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { ErrorBanner, PageTitle, Spinner } from '../components/UI'
import { diseaseLabel, num4, pct } from '../utils/format'

const COLS = [['accuracy', 'Accuracy'], ['precision', 'Precision'], ['recall_sensitivity', 'Recall (sensitivity)'], ['specificity', 'Specificity'], ['f1', 'F1'], ['roc_auc', 'ROC-AUC'], ['brier_score', 'Brier'], ['ece_10bin', 'Calib. error']]

function ConfusionMatrix({ cm }) {
  const cell = 'flex h-20 w-28 flex-col items-center justify-center rounded-md text-center'
  return (
    <div aria-label="Confusion matrix" className="inline-grid grid-cols-2 gap-2 text-sm">
      <div className={`${cell} bg-emerald-100`}><strong className="text-xl">{cm.tn}</strong>true negative</div>
      <div className={`${cell} bg-amber-100`}><strong className="text-xl">{cm.fp}</strong>false positive</div>
      <div className={`${cell} bg-red-100`}><strong className="text-xl">{cm.fn}</strong>false negative</div>
      <div className={`${cell} bg-emerald-100`}><strong className="text-xl">{cm.tp}</strong>true positive</div>
    </div>
  )
}

function ModulePanel({ slug, m }) {
  const models = Object.keys(m.test)
  const selected = m.selected_model || models[0]
  const sel = m.test[selected]
  const chart = models.map((n) => ({ name: n.replace('_', ' '), Recall: m.test[n].recall_sensitivity, Specificity: m.test[n].specificity, 'ROC-AUC': m.test[n].roc_auc }))
  const nTestPos = sel.confusion_matrix.tp + sel.confusion_matrix.fn
  const hs = m.high_sensitivity_operating_point
  return (
    <div className="space-y-6">
      <section className="card">
        <h2 className="text-lg font-semibold">{diseaseLabel(slug)}: test-set results</h2>
        <p className="mt-1 text-sm text-slate-600">
          Selected model (chosen on the validation set): <strong>{selected}</strong>. Split: train {m.split.train}, validation {m.split.val}, test {m.split.test}
          {' '}({nTestPos} positive cases in the test set). The test set was used once.
        </p>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Test metrics for each model</caption>
            <thead><tr className="border-b text-slate-500"><th className="py-2 pr-3">Model</th>{COLS.map(([, l]) => <th key={l} className="pr-3">{l}</th>)}</tr></thead>
            <tbody>
              {models.map((n) => (
                <tr key={n} className={`border-b border-slate-100 ${n === selected ? 'bg-brand-50 font-semibold' : ''}`}>
                  <td className="py-2 pr-3">{n}{n === selected ? ' *' : ''}</td>{COLS.map(([k]) => <td key={k} className="pr-3">{num4(m.test[n][k])}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-slate-500">* selected on validation data. Threshold {m.threshold ?? 0.5}. Small test sets make these numbers noisy: one patient can shift sensitivity by several points.</p>
      </section>
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card" aria-labelledby={`cmp-${slug}`}>
          <h3 id={`cmp-${slug}`} className="mb-3 font-semibold">Model comparison</h3>
          <div className="h-64"><ResponsiveContainer width="100%" height="100%"><BarChart data={chart}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis domain={[0, 1]} /><Tooltip /><Legend />
            <Bar dataKey="Recall" fill="#dc2626" /><Bar dataKey="Specificity" fill="#2563eb" /><Bar dataKey="ROC-AUC" fill="#0f766e" /></BarChart></ResponsiveContainer></div>
        </section>
        <section className="card"><h3 className="mb-3 font-semibold">Confusion matrix ({selected})</h3><ConfusionMatrix cm={sel.confusion_matrix} />
          <p className="mt-3 text-sm text-slate-600">Sensitivity {pct(sel.recall_sensitivity)} ({sel.confusion_matrix.tp} of {nTestPos} positives found); specificity {pct(sel.specificity)}.</p></section>
      </div>
      {m.repeated_cv_train_plus_val && (
        <section className="card"><h3 className="font-semibold">Repeated 5-fold cross-validation (train + validation data, 3 repeats)</h3>
          <p className="mt-1 text-sm text-slate-600">A steadier estimate than a single small test split. Mean ± standard deviation.</p>
          <table className="mt-3 w-full text-left text-sm"><thead><tr className="border-b text-slate-500"><th className="py-1">Model</th><th>ROC-AUC</th><th>Recall</th><th>Specificity</th></tr></thead><tbody>
            {Object.entries(m.repeated_cv_train_plus_val).map(([n, v]) => (
              <tr key={n} className="border-b border-slate-100"><td className="py-1">{n}</td>
                <td>{v.roc_auc.mean.toFixed(3)} ± {v.roc_auc.std.toFixed(3)}</td><td>{v.recall.mean.toFixed(3)} ± {v.recall.std.toFixed(3)}</td><td>{v.specificity.mean.toFixed(3)} ± {v.specificity.std.toFixed(3)}</td></tr>))}
          </tbody></table></section>
      )}
      {hs && (
        <section className="card"><h3 className="font-semibold">Higher-sensitivity operating point</h3>
          <p className="mt-1 text-sm text-slate-600">Threshold {hs.threshold} ({hs.chosen_on}). On the test set: sensitivity {pct(hs.test.recall_sensitivity)}, specificity {pct(hs.test.specificity)}
            {' '}({hs.test.confusion_matrix.fn} missed, {hs.test.confusion_matrix.fp} false alarms). Catching more cases costs more false alarms; the trade-off is a clinical decision.</p></section>
      )}
      {m.limitations && <ul className="list-disc pl-6 text-sm text-slate-600">{m.limitations.map((l) => <li key={l}>{l}</li>)}</ul>}
    </div>
  )
}

export default function Metrics() {
  const { data, error, loading, reload } = useAsync(() => api.metrics(), [])
  const [tab, setTab] = useState(null)
  if (loading) return <Spinner label="Loading model results…" />
  if (error) return <ErrorBanner error={error} onRetry={reload} />
  const slugs = Object.keys(data)
  const active = tab && data[tab] ? tab : slugs[0]
  return (
    <>
      <PageTitle title="Model performance" subtitle="Real evaluation results written by the training scripts. Nothing on this page is typed in by hand." />
      <div role="tablist" aria-label="Modules" className="mb-6 flex flex-wrap gap-2">
        {slugs.map((s) => <button key={s} role="tab" aria-selected={s === active} className={`btn ${s === active ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setTab(s)}>{diseaseLabel(s)}</button>)}
      </div>
      <ModulePanel slug={active} m={data[active]} />
    </>
  )
}
