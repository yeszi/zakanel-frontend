import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// 🔥 INTERCEPTOR REQUEST - KIRIM USER ID & ROLE
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
  
  // 🔥 KIRIM user_id DAN role KE BACKEND
  if (user && user.id) {
    config.headers['X-User-ID'] = user.id
    config.headers['X-User-Role'] = user.role || 'penerbit'
  }
  
  return config
})

api.interceptors.response.use(
  (response) => response,
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