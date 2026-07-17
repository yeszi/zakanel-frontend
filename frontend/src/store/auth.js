// src/store/auth.js
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
    
    // 🔥 CEK: Apakah user masih aktif?
    if (response.data.user.status === 'inactive' || response.data.user.status === 'revoked' || response.data.user.is_active === false) {
      return { 
        success: false, 
        message: '⚠️ Akun Anda telah dinonaktifkan oleh admin. Hubungi admin untuk informasi lebih lanjut.' 
      }
    }
    
    user.value = response.data.user
    token.value = response.data.token
    
    localStorage.setItem('token', response.data.token)
    localStorage.setItem('user', JSON.stringify(response.data.user))
    
    return { success: true, user: user.value }
  } catch (err) {
    // 🔥 Tangani error 403 dari backend
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

  // Init Auth (dari localStorage)
  const initAuth = () => {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    
    if (savedToken && savedUser) {
      token.value = savedToken
      user.value = JSON.parse(savedUser)
    }
  }

  // Check if user is admin
  const isAdmin = computed(() => {
    return user.value?.role === 'admin'
  })

  // Check if user is penerbit
  const isPenerbit = computed(() => {
    return user.value?.role === 'penerbit'
  })

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
      const response = await api.get('/penerbit')
      publishers.value = response.data.penerbit || []
    } catch (error) {
      console.error('Gagal load penerbit:', error)
      publishers.value = []
    } finally {
      loading.value = false
    }
  }

  // Semua penerbit
  const allPublishers = computed(() => publishers.value)

  // Total penerbit aktif
  const totalActive = computed(() => {
    return publishers.value.filter(p => p.status === 'active' || p.is_active === true).length
  })

  // Cabut hak penerbit (revoke)
  const revokePublisher = async (id) => {
    try {
      await api.post(`/penerbit/${id}/revoke`)
      await refreshData()
      return true
    } catch (error) {
      console.error('Gagal revoke:', error)
      return false
    }
  }

  // Aktifkan kembali penerbit
  const activatePublisher = async (id) => {
    try {
      await api.post(`/penerbit/${id}/activate`)
      await refreshData()
      return true
    } catch (error) {
      console.error('Gagal activate:', error)
      return false
    }
  }

  // Tambah penerbit baru
  const addPublisher = async (data) => {
  try {
    // Hapus is_active dari data yang dikirim
    const sendData = { ...data }
    delete sendData.is_active  
    
    const response = await api.post('/penerbit', sendData)
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