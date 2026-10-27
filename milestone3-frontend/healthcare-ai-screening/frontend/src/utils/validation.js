/** Client-side validation. The server validates again; this only gives quick, clear feedback. */
export function validateField(feature, raw) {
  const text = (raw ?? '').toString().trim()
  if (text === '') return feature.nullable ? null : `${feature.label} is required`
  const n = Number(text)
  if (!Number.isFinite(n)) return `${feature.label} must be a number`
  if (feature.min != null && n < feature.min) return `${feature.label} must be at least ${feature.min}`
  if (feature.max != null && n > feature.max) return `${feature.label} must be at most ${feature.max}`
  if (feature.allowed && !feature.allowed.includes(n)) return `${feature.label} must be one of ${feature.allowed.join(', ')}`
  return null
}

export function validateForm(features, values) {
  const errors = {}
  for (const f of features) {
    const e = validateField(f, values[f.name])
    if (e) errors[f.name] = e
  }
  return errors
}

/** Blank optional fields become null (the model fills them with the training median). */
export function buildPayload(features, values) {
  const out = {}
  for (const f of features) {
    const text = (values[f.name] ?? '').toString().trim()
    out[f.name] = text === '' ? null : Number(text)
  }
  return out
}

export const IMAGE_MAX_BYTES = 5 * 1024 * 1024
export function validateImageFile(file) {
  if (!file) return 'Choose an image file'
  if (!['image/png', 'image/jpeg'].includes(file.type)) return 'Only PNG and JPEG images are supported'
  if (file.size > IMAGE_MAX_BYTES) return 'Image must be smaller than 5 MB'
  if (file.size === 0) return 'The file is empty'
  return null
}
