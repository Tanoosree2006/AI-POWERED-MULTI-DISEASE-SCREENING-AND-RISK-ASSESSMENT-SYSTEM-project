import { createApi } from './apiClient'

const TOKEN_KEY = 'token'
export const tokenStore = {
  get: () => sessionStorage.getItem(TOKEN_KEY),      // sessionStorage: cleared when the tab closes
  set: (t) => sessionStorage.setItem(TOKEN_KEY, t),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
}

export const api = createApi(import.meta.env.VITE_API_URL || 'http://localhost:8000', {
  getToken: tokenStore.get,
  onUnauthorized: () => {
    if (tokenStore.get()) {
      tokenStore.clear()
      window.dispatchEvent(new Event('auth:logout'))
    }
  },
})
