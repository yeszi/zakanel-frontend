import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Login
  const login = async (username, password) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.post('/auth/login', { username, password })
      
      // CEK status aktif
      if (response.data.user.status === 'inactive' || response.data.user.status === 'revoked' || response.data.user.is_active === false) {
        return { 
          success: false, 
          message: '⚠️ Akun Anda telah dinonaktifkan oleh admin. Hubungi admin untuk informasi lebih lanjut.' 
        }
      }
      
      const userData = response.data.user
      // Pastikan ada role
      if (!userData.role) {
        console.warn('[Auth] User role tidak ditemukan, set default "penerbit"')
        userData.role = 'penerbit'
      }
      
      user.value = userData
      token.value = response.data.token
      
      localStorage.setItem('token', response.data.token)
      localStorage.setItem('user', JSON.stringify(userData))
      
      console.log('[Auth] Login success, user:', userData)
      
      return { success: true, user: userData }
    } catch (err) {
      if (err.response?.status === 403) {
        error.value = err.response?.data?.message || 'Akun Anda telah dinonaktifkan!'
      } else {
        error.value = err.response?.data?.message || 'Login gagal'
      }
      return { success: false, message: error.value }
    } finally {
      loading.value = false
    }
  }

  // Logout
  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  // Init Auth
  const initAuth = () => {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    
    if (savedToken && savedUser) {
      token.value = savedToken
      user.value = JSON.parse(savedUser)
      console.log('[Auth] Init from localStorage, user:', user.value)
    }
  }

  const isAdmin = computed(() => user.value?.role === 'admin')
  const isPenerbit = computed(() => user.value?.role === 'penerbit')

  return {
    user,
    token,
    loading,
    error,
    login,
    logout,
    initAuth,
    isAdmin,
    isPenerbit
  }
})

// ============================================
// PUBLISHER STORE
// ============================================
export const usePublisherStore = defineStore('publisher', () => {
  const publishers = ref([])
  const loading = ref(false)

  // Ambil semua penerbit dari backend
  const refreshData = async () => {
    loading.value = true
    try {
      // 🔥 PERBAIKAN: tambahkan prefix /api
      const response = await api.get('/api/penerbit')
      publishers.value = response.data.penerbit || []
      console.log('[PublisherStore] Loaded publishers:', publishers.value)
    } catch (error) {
      console.error('Gagal load penerbit:', error)
      publishers.value = []
    } finally {
      loading.value = false
    }
  }

  const allPublishers = computed(() => publishers.value)

  const totalActive = computed(() => {
    return publishers.value.filter(p => p.status === 'active' || p.is_active === true).length
  })

  const revokePublisher = async (id) => {
    try {
      await api.post(`/api/penerbit/${id}/revoke`)
      await refreshData()
      return true
    } catch (error) {
      console.error('Gagal revoke:', error)
      return false
    }
  }

  const activatePublisher = async (id) => {
    try {
      await api.post(`/api/penerbit/${id}/activate`)
      await refreshData()
      return true
    } catch (error) {
      console.error('Gagal activate:', error)
      return false
    }
  }

  const addPublisher = async (data) => {
    try {
      const sendData = { ...data }
      delete sendData.is_active  
      
      const response = await api.post('/api/penerbit', sendData)
      await refreshData()
      return { success: true, data: response.data }
    } catch (error) {
      return { 
        success: false, 
        message: error.response?.data?.error || 'Gagal tambah penerbit' 
      }
    }
  }

  return {
    publishers,
    allPublishers,
    totalActive,
    loading,
    refreshData,
    revokePublisher,
    activatePublisher,
    addPublisher
  }
})