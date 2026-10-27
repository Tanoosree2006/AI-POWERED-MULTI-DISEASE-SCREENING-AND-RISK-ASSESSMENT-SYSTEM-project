export const formatScore = (s) => (typeof s === 'number' ? s.toFixed(3) : '-')
export const formatDate = (iso) => {
  if (!iso) return '-'
  const d = new Date(iso.endsWith('Z') || /[+-]\d\d:\d\d$/.test(iso) ? iso : iso + 'Z')
  return Number.isNaN(d.getTime()) ? '-' : d.toLocaleString()
}
export const flagText = (flag) => (flag === 'elevated' ? 'Elevated screening score' : 'Lower screening score')
export const pct = (v) => (typeof v === 'number' ? `${(v * 100).toFixed(1)}%` : '-')
export const num4 = (v) => (typeof v === 'number' ? v.toFixed(4) : '-')
export const diseaseLabel = (slug) =>
  ({ breast_cancer: 'Breast cancer', diabetes: 'Diabetes', heart_disease: 'Heart disease', image_screening: 'Image screening' }[slug] || slug)
