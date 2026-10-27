/** One input of the screening form: number, binary (0/1) or coded category, with an accessible error message. */
export default function FeatureField({ feature, value, error, onChange }) {
  const id = `f-${feature.name}`
  const helpId = `${id}-help`
  const errId = `${id}-err`
  const describedBy = [feature.help || feature.unit ? helpId : null, error ? errId : null].filter(Boolean).join(' ') || undefined
  const common = {
    id, name: feature.name, value: value ?? '', 'aria-invalid': error ? 'true' : 'false', 'aria-describedby': describedBy,
    className: `input ${error ? 'input-error' : ''}`,
    onChange: (e) => onChange(feature.name, e.target.value),
  }
  return (
    <div>
      <label htmlFor={id} className="label">
        {feature.label}{feature.unit ? ` (${feature.unit})` : ''}{feature.nullable ? ' – optional' : ''}
      </label>
      {feature.allowed ? (
        <select {...common}>
          <option value="">{feature.nullable ? 'Leave blank' : 'Select…'}</option>
          {feature.allowed.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      ) : (
        <input {...common} type="number" step="any" inputMode="decimal" min={feature.min ?? undefined} max={feature.max ?? undefined} />
      )}
      {(feature.help || feature.min != null) && (
        <p id={helpId} className="mt-1 text-xs text-slate-500">
          {feature.help}{feature.help && feature.max != null ? ' ' : ''}{feature.max != null ? `Accepted range: ${feature.min} to ${feature.max}.` : ''}
        </p>
      )}
      {error && <p id={errId} role="alert" className="mt-1 text-xs font-medium text-red-700">{error}</p>}
    </div>
  )
}
