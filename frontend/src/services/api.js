import axios from 'axios'

let baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
if (baseURL.endsWith('/')) baseURL = baseURL.slice(0, -1)

const api = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

// Kirim HANYA token JWT. Peran & ID pengguna dibaca server dari token,
// bukan dari header yang bisa dipalsukan (X-User-Role / X-User-ID sudah dihapus).
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  if (config.url && !config.url.startsWith('/api')) {
    config.url = '/api' + (config.url.startsWith('/') ? '' : '/') + config.url
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status
    const isLogin = err.config?.url?.includes('/auth/login')
    // 401 = token tidak ada/kedaluwarsa/tidak valid; 403 karena akun dinonaktifkan
    const inactive = status === 403 && /dinonaktifkan/i.test(err.response?.data?.error || '')
    if (!isLogin && (status === 401 || inactive)) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/') window.location.href = '/'
    }
    return Promise.reject(err)
  }
)

export default api
