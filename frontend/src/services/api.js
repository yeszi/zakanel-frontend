import axios from 'axios'

let baseURL = import.meta.env.VITE_API_BASE_URL || 'https://runner-broadway-penalties-mating.trycloudflare.com'

if (baseURL.endsWith('/')) {
  baseURL = baseURL.slice(0, -1)
}

const api = axios.create({
  baseURL: baseURL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

// Interceptor Request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')
  let user = null

  if (userStr) {
    try { user = JSON.parse(userStr) } catch (e) {}
  }

  if (token) config.headers.Authorization = `Bearer ${token}`

  if (user && user.id) {
    config.headers['X-User-ID'] = user.id
    config.headers['X-User-Role'] = user.role || 'penerbit'
  }

  // Otomatis kasih prefix /api biar rapi
  if (config.url && !config.url.startsWith('/api')) {
    config.url = '/api' + (config.url.startsWith('/') ? '' : '/') + config.url;
  }

  return config
})

api.interceptors.response.use(
  (res) => {
    return res
  },
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/') {
        window.location.href = '/'
      }
    }
    return Promise.reject(err)
  }
)

export default api