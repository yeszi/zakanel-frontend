import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'https://underwear-pentium-terms-attempts.trycloudflare.com',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Interceptor untuk token dan header user
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')
  let user = null
  
  if (userStr) {
    try {
      user = JSON.parse(userStr)
    } catch (e) {
      console.error('Error parsing user:', e)
    }
  }
  
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  
  if (user && user.id) {
    config.headers['X-User-ID'] = user.id
    // Kirim role apa adanya, fallback ke 'penerbit' jika tidak ada
    const role = user.role || 'penerbit'
    config.headers['X-User-Role'] = role
    console.log(`[API] Sending headers: X-User-ID=${user.id}, X-User-Role=${role}`)
  } else {
    console.warn('[API] No user data found in localStorage')
  }
  
  console.log(`[API] Request to: ${config.baseURL}${config.url}`)
  return config
})

api.interceptors.response.use(
  (response) => {
    console.log(`[API] Response from ${response.config.url}:`, response.data)
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

export default api