import { Bar, BarChart, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

/** Per-prediction SHAP explanation: bars plus an accessible table with the same numbers. */
export default function ShapChart({ explanation }) {
  if (!explanation || !explanation.top_features) return null
  const rows = explanation.top_features.map((t) => ({ ...t, label: t.feature }))
  const chartData = [...rows].reverse()
  return (
    <section aria-labelledby="shap-title" className="card">
      <h2 id="shap-title" className="text-lg font-semibold">Why did the model give this score?</h2>
      <p className="mt-1 text-sm text-slate-600">
        Top contributing inputs for this record (SHAP values, in {explanation.unit}). Red bars push the score up, blue
        bars push it down.
      </p>
      <div className="mt-4 h-64" aria-hidden="true">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 20 }}>
            <XAxis type="number" />
            <YAxis type="category" dataKey="label" width={150} tick={{ fontSize: 12 }} />
            <Tooltip formatter={(v) => [v, 'SHAP value']} />
            <ReferenceLine x={0} stroke="#64748b" />
            <Bar dataKey="shap">
              {chartData.map((r, i) => <Cell key={i} fill={r.shap > 0 ? '#dc2626' : '#2563eb'} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <table className="mt-4 w-full text-left text-sm">
        <caption className="sr-only">SHAP contributions for the top features</caption>
        <thead>
          <tr className="border-b text-slate-500"><th className="py-1 pr-2">Input</th><th className="pr-2">Value</th><th className="pr-2">SHAP</th><th>Effect</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.feature} className="border-b border-slate-100">
              <td className="py-1 pr-2 font-medium">{r.feature}</td>
              <td className="pr-2">{Number(r.value).toPrecision(4)}</td>
              <td className="pr-2">{r.shap > 0 ? '+' : ''}{r.shap}</td>
              <td>{r.effect}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-3 text-xs text-slate-500">
        Base value {explanation.base_value}. {explanation.caveat} Individual explanations differ from the population-level
        importance shown on the Model performance page.
      </p>
    </section>
  )
}
