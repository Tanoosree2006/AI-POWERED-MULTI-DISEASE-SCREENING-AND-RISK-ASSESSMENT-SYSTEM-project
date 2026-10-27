import { describe, expect, it } from 'vitest'
import { buildPayload, validateField, validateForm, validateImageFile } from '../utils/validation'
import { flagText, formatDate, formatScore, pct } from '../utils/format'

const age = { name: 'age', label: 'Age', min: 18, max: 100 }
const glucose = { name: 'glucose', label: 'Glucose', min: 30, max: 400, nullable: true }
const sex = { name: 'sex', label: 'Sex', allowed: [0, 1] }

describe('validateField', () => {
  it('requires non-nullable values', () => expect(validateField(age, '')).toBe('Age is required'))
  it('allows blank optional values', () => expect(validateField(glucose, '  ')).toBeNull())
  it('rejects non-numbers', () => expect(validateField(age, 'abc')).toBe('Age must be a number'))
  it('rejects Infinity-like and NaN text', () => { expect(validateField(age, 'Infinity')).toMatch(/number/); expect(validateField(age, 'NaN')).toMatch(/number/) })
  it('enforces min and max boundaries', () => {
    expect(validateField(age, '17')).toMatch(/at least 18/)
    expect(validateField(age, '18')).toBeNull()
    expect(validateField(age, '100')).toBeNull()
    expect(validateField(age, '101')).toMatch(/at most 100/)
  })
  it('enforces allowed codes', () => { expect(validateField(sex, '2')).toMatch(/one of 0, 1/); expect(validateField(sex, '1')).toBeNull() })
})

describe('form helpers', () => {
  const feats = [age, glucose, sex]
  it('collects all errors', () => expect(Object.keys(validateForm(feats, { glucose: '10' }))).toEqual(['age', 'glucose', 'sex']))
  it('builds numeric payload with null for blank optional', () =>
    expect(buildPayload(feats, { age: '40', glucose: '', sex: '1' })).toEqual({ age: 40, glucose: null, sex: 1 }))
})

describe('validateImageFile', () => {
  const f = (type, size) => ({ type, size })
  it('rejects missing, wrong type, empty and oversize files', () => {
    expect(validateImageFile(null)).toMatch(/Choose/)
    expect(validateImageFile(f('application/pdf', 10))).toMatch(/PNG and JPEG/)
    expect(validateImageFile(f('image/gif', 10))).toMatch(/PNG and JPEG/)
    expect(validateImageFile(f('image/png', 0))).toMatch(/empty/)
    expect(validateImageFile(f('image/png', 5 * 1024 * 1024 + 1))).toMatch(/smaller than 5 MB/)
  })
  it('accepts png and jpeg within the limit', () => {
    expect(validateImageFile(f('image/png', 1000))).toBeNull()
    expect(validateImageFile(f('image/jpeg', 5 * 1024 * 1024))).toBeNull()
  })
})

describe('format', () => {
  it('formats scores, percentages and flags', () => {
    expect(formatScore(0.87654)).toBe('0.877'); expect(formatScore(undefined)).toBe('-')
    expect(pct(0.9524)).toBe('95.2%'); expect(flagText('elevated')).toMatch(/Elevated/); expect(flagText('lower')).toMatch(/Lower/)
  })
  it('treats timestamps without a zone as UTC and survives bad input', () => {
    expect(formatDate('2026-10-12T10:00:00')).not.toBe('-'); expect(formatDate('garbage')).toBe('-'); expect(formatDate(null)).toBe('-')
  })
})
