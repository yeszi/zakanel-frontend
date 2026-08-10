import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const login = async (username, password) => {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/auth/login', { username, password })

      // Jaga-jaga jika backend tidak mengembalikan field "user" seperti yang diharapkan
      if (!response.data || !response.data.user) {
        console.error('[login] Response tidak sesuai format yang diharapkan:', response.data)
        return { success: false, message: 'Format respons server tidak dikenali. Cek console/network tab.' }
      }

      if (response.data.user.status === 'inactive' || response.data.user.status === 'revoked' || response.data.user.is_active === false) {
        return { success: false, message: '⚠️ Akun dinonaktifkan oleh admin.' }
      }

      const userData = response.data.user
      if (!userData.role) userData.role = 'penerbit'

      user.value = userData
      token.value = response.data.token

      localStorage.setItem('token', response.data.token)
      localStorage.setItem('user', JSON.stringify(userData))
      return { success: true, user: userData }
    } catch (err) {
      // 🔍 Log detail lengkap ke console supaya penyebab asli terlihat, bukan tertelan jadi pesan generik
      console.error('[login] Gagal login. Detail error:', {
        message: err.message,
        code: err.code,
        status: err.response?.status,
        responseData: err.response?.data,
        requestURL: err.config ? `${err.config.baseURL}${err.config.url}` : undefined
      })

      let message
      if (err.code === 'ERR_NETWORK' || !err.response) {
        message = `Tidak bisa terhubung ke server (${err.config?.baseURL || 'baseURL tidak diketahui'}). Cek apakah backend menyala dan VITE_API_BASE_URL sudah benar.`
      } else if (err.code === 'ECONNABORTED') {
        message = 'Server tidak merespons (timeout). Backend mungkin sedang down atau lambat.'
      } else if (err.response?.status === 404) {
        message = 'Endpoint /api/auth/login tidak ditemukan (404). Cek apakah backend route-nya sesuai.'
      } else {
        message = err.response?.data?.message || err.response?.data?.error || `Login gagal (status ${err.response?.status})`
      }

      error.value = message
      return { success: false, message }
    } finally {
      loading.value = false
    }
  }

  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  const initAuth = () => {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    if (savedToken && savedUser) {
      token.value = savedToken
      user.value = JSON.parse(savedUser)
    }
  }

  const isAdmin = computed(() => user.value?.role === 'admin')
  const isPenerbit = computed(() => user.value?.role === 'penerbit')

  return { user, token, loading, error, login, logout, initAuth, isAdmin, isPenerbit }
})

export const usePublisherStore = defineStore('publisher', () => {
  const publishers = ref([])
  const loading = ref(false)

  const refreshData = async () => {
    loading.value = true
    try {
      const response = await api.get('/penerbit')
      publishers.value = response.data.penerbit || []
    } catch (error) {
      publishers.value = []
    } finally {
      loading.value = false
    }
  }

  const allPublishers = computed(() => publishers.value)
  const totalActive = computed(() => publishers.value.filter(p => p.status === 'active' || p.is_active === true).length)

  const revokePublisher = async (id) => {
    try {
      await api.post(`/penerbit/${id}/revoke`)
      await refreshData()
      return true
    } catch (error) { return false }
  }

  const activatePublisher = async (id) => {
    try {
      await api.post(`/penerbit/${id}/activate`)
      await refreshData()
      return true
    } catch (error) { return false }
  }

  const addPublisher = async (data) => {
    try {
      const sendData = { ...data }
      delete sendData.is_active  
      const response = await api.post('/penerbit', sendData)
      await refreshData()
      return { success: true, data: response.data }
    } catch (error) {
      return { success: false, message: error.response?.data?.error || 'Gagal tambah penerbit' }
    }
  }

  return { publishers, allPublishers, totalActive, loading, refreshData, revokePublisher, activatePublisher, addPublisher }
})