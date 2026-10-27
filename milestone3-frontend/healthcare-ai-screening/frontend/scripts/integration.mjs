// Live end-to-end check: the SAME API client the React app uses, against a running backend.
// Usage: node scripts/integration.mjs http://127.0.0.1:8770
import { createApi } from '../src/services/apiClient.js'
import { deflateSync } from 'node:zlib'

const base = process.argv[2] || 'http://127.0.0.1:8000'
let token = null
const api = createApi(base, { getToken: () => token })
let passed = 0
const check = (name, cond, extra = '') => { if (!cond) { console.error(`FAIL  ${name} ${extra}`); process.exitCode = 1 } else { passed++; console.log(`ok    ${name} ${extra}`) } }

// minimal valid PNG (random-looking pixels) built without external libraries
function makePng(w = 64, h = 64) {
  const crcTable = Array.from({ length: 256 }, (_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c >>> 0 })
  const crc = (buf) => { let c = 0xffffffff; for (const b of buf) c = crcTable[(c ^ b) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0 }
  const chunk = (type, data) => { const t = Buffer.from(type); const len = Buffer.alloc(4); len.writeUInt32BE(data.length); const c = Buffer.alloc(4); c.writeUInt32BE(crc(Buffer.concat([t, data]))); return Buffer.concat([len, t, data, c]) }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 2
  const raw = Buffer.alloc((w * 3 + 1) * h); let seed = 7
  for (let y = 0; y < h; y++) for (let x = 0; x < w * 3; x++) { seed = (seed * 1103515245 + 12345) & 0x7fffffff; raw[y * (w * 3 + 1) + 1 + x] = seed >> 16 & 255 }
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr), chunk('IDAT', deflateSync(raw)), chunk('IEND', Buffer.alloc(0))])
}

const user = `it_${Date.now()}`
const pw = 'integration-pass-1'
const h = await api.health(); check('health', h.status === 'ok', JSON.stringify(h.models))
const diseases = await api.diseases()
const tabular = diseases.filter((d) => d.data_type === 'tabular' && d.status === 'available')
check('diseases: 3 tabular modules available', tabular.length === 3, tabular.map((d) => d.id).join(','))
check('every field has label/kind metadata for the form', tabular.every((d) => d.features.every((f) => f.label && f.kind)))

try { await api.screen('diabetes', {}); check('unauthenticated screening rejected', false) } catch (e) { check('unauthenticated screening rejected', e.status === 401, e.message) }
await api.register(user, pw)
try { await api.register(user, pw); check('duplicate registration rejected', false) } catch (e) { check('duplicate registration rejected', e.status === 409) }
try { await api.login(user, 'wrong-password-x'); check('bad password rejected', false) } catch (e) { check('bad password rejected', e.status === 401 && e.message === 'Invalid username or password') }
token = (await api.login(user, pw)).access_token
const me = await api.me(); check('login + me', me.username === user && me.role === 'user')

const ids = []
for (const d of tabular) {
  const ex = await api.examples(d.id)
  for (const key of ['dataset_positive_example', 'dataset_negative_example']) {
    const r = await api.screen(d.id, ex[key])
    ids.push(r.id)
    check(`screen ${d.id} (${key})`, r.screening_score >= 0 && r.screening_score <= 1 && r.explanation.top_features.length === 5, `score=${r.screening_score} flag=${r.screening_flag}`)
  }
}
try { await api.screen('diabetes', { age: 5 }); check('invalid input rejected', false) } catch (e) { check('invalid input rejected with message', e.status === 422, e.message) }

const hist = await api.history({ limit: 3, offset: 0 })
check('history pagination', hist.total === ids.length && hist.items.length === 3, `total=${hist.total}`)
const rec = await api.record(ids[0]); check('record fetch', rec.id === ids[0] && rec.explanation.top_features)
const dash = await api.dashboard({ days: 90 })
check('dashboard from real records', dash.total_screenings === ids.length && Object.keys(dash.by_disease).length === 3, JSON.stringify(dash.by_disease))
const met = await api.metrics(); check('metrics for all tabular modules', ['breast_cancer', 'diabetes', 'heart_disease'].every((k) => met[k] && met[k].test))

const imageMod = diseases.find((d) => d.id === 'image_screening')
if (process.env.EXPECT_IMAGE === '1') {
  check('image module reported available', imageMod.status === 'available')
  const r = await api.screenImage(new File([makePng()], 'scan.png', { type: 'image/png' }))
  ids.push(r.id)
  check('image upload (multipart) returns score + Grad-CAM', r.screening_score >= 0 && r.gradcam && r.gradcam.overlay_png_base64.length > 100, `score=${r.screening_score}`)
  try { await api.screenImage(new File(['not an image'], 'x.png', { type: 'image/png' })); check('bad image rejected', false) } catch (e) { check('bad image rejected', e.status === 422, e.message) }
} else {
  check('image module honestly reported unavailable', imageMod.status === 'unavailable')
}

await api.deleteRecord(ids[0])
try { await api.record(ids[0]); check('deleted record is gone', false) } catch (e) { check('deleted record is gone', e.status === 404) }
console.log(`\n${passed} checks passed${process.exitCode ? ' (WITH FAILURES)' : ''}`)
