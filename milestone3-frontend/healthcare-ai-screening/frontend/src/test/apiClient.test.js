import { describe, expect, it, vi } from 'vitest'
import { ApiError, createApi } from '../services/apiClient'

const respond = (status, data) => (config) =>
  status < 400
    ? Promise.resolve({ data, status, statusText: 'OK', headers: {}, config })
    : Promise.reject(Object.assign(new Error('fail'), { config, isAxiosError: true, response: { status, data, headers: {}, config } }))

describe('createApi', () => {
  it('sends the bearer token and unwraps data', async () => {
    let seen
    const api = createApi('http://x', { getToken: () => 'abc', axiosConfig: { adapter: (c) => { seen = c; return respond(200, { diseases: [{ id: 'd' }] })(c) } } })
    expect(await api.diseases()).toEqual([{ id: 'd' }])
    expect(seen.headers.Authorization).toBe('Bearer abc')
  })
  it('sends no Authorization header when signed out', async () => {
    let seen
    const api = createApi('http://x', { axiosConfig: { adapter: (c) => { seen = c; return respond(200, { status: 'ok' })(c) } } })
    await api.health()
    expect(seen.headers.Authorization).toBeUndefined()
  })
  it('turns the server error envelope into ApiError and never leaks raw data', async () => {
    const api = createApi('http://x', { axiosConfig: { adapter: respond(422, { error: { code: 422, message: 'Invalid request', details: [{ field: 'age', message: 'bad' }] } }) } })
    await expect(api.screen('diabetes', {})).rejects.toMatchObject({ name: 'ApiError', status: 422, message: 'Invalid request', details: [{ field: 'age', message: 'bad' }] })
  })
  it('calls onUnauthorized on 401', async () => {
    const onUnauthorized = vi.fn()
    const api = createApi('http://x', { onUnauthorized, axiosConfig: { adapter: respond(401, { error: { code: 401, message: 'Invalid or expired token' } }) } })
    await expect(api.me()).rejects.toBeInstanceOf(ApiError)
    expect(onUnauthorized).toHaveBeenCalledOnce()
  })
  it('reports an unreachable server clearly', async () => {
    const api = createApi('http://x', { axiosConfig: { adapter: (c) => Promise.reject(Object.assign(new Error('Network Error'), { config: c, isAxiosError: true })) } })
    await expect(api.health()).rejects.toMatchObject({ status: 0, message: expect.stringMatching(/Cannot reach the server/) })
  })
  it('posts images as multipart form data under the field name "file"', async () => {
    let body
    const api = createApi('http://x', { axiosConfig: { adapter: (c) => { body = c.data; return respond(201, { id: 1 })(c) } } })
    await api.screenImage(new File(['abc'], 'a.png', { type: 'image/png' }))
    expect(body).toBeInstanceOf(FormData); expect(body.get('file').name).toBe('a.png')
  })
})
