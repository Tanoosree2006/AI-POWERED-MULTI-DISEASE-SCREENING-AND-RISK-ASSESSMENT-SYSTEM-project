import axios from 'axios'

export class ApiError extends Error {
  constructor(message, status, details) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details || []
  }
}

/** Factory so the same code runs in the browser, in tests (custom adapter) and in the integration script. */
export function createApi(baseURL, { getToken = () => null, onUnauthorized = () => {}, axiosConfig = {} } = {}) {
  const http = axios.create({ baseURL, timeout: 60000, ...axiosConfig })
  http.interceptors.request.use((cfg) => {
    const t = getToken()
    if (t) cfg.headers.Authorization = `Bearer ${t}`
    return cfg
  })
  http.interceptors.response.use(
    (r) => r,
    (err) => {
      if (!err.response) throw new ApiError('Cannot reach the server. Check that the backend is running.', 0)
      const { status, data } = err.response
      const e = data && data.error
      if (status === 401) onUnauthorized()
      throw new ApiError((e && e.message) || `Request failed (${status})`, status, e && e.details)
    },
  )
  const get = (url, params) => http.get(url, { params }).then((r) => r.data)
  const post = (url, body, cfg) => http.post(url, body, cfg).then((r) => r.data)
  return {
    health: () => get('/health'),
    register: (username, password) => post('/api/v1/auth/register', { username, password }),
    login: (username, password) => post('/api/v1/auth/login', { username, password }),
    me: () => get('/api/v1/auth/me'),
    diseases: () => get('/api/v1/diseases').then((d) => d.diseases),
    examples: (disease) => get(`/api/v1/diseases/${disease}/examples`),
    screen: (disease, features) => post(`/api/v1/screening/${disease}`, { features }),
    screenImage: (file) => {
      const form = new FormData()
      form.append('file', file)
      return post('/api/v1/images/screening', form)
    },
    history: (params) => get('/api/v1/screening/history', params),
    record: (id) => get(`/api/v1/screening/record/${id}`),
    deleteRecord: (id) => http.delete(`/api/v1/screening/record/${id}`).then(() => true),
    dashboard: (params) => get('/api/v1/dashboard/summary', params),
    metrics: () => get('/api/v1/models/metrics').then((d) => d.metrics),
  }
}
