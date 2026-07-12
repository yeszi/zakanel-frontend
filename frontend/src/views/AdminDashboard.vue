<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Sidebar -->
    <div class="w-64 bg-white border-r border-gray-200 p-4 min-h-screen flex flex-col">
      <h1 class="text-lg font-bold text-blue-700">MENU</h1>
      <p class="text-xs text-gray-400 mt-1">Admin</p>
      
      <nav class="mt-8 space-y-2 flex-1">
        <router-link to="/admin" class="block px-3 py-2 rounded-lg bg-blue-50 text-blue-700 font-medium">
          Dashboard
        </router-link>
        <router-link to="/admin/tambah-penerbit" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors">
          (+) Tambahkan Penerbit
        </router-link>
        <router-link to="/admin/data-penerbit" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors">
          (=) Data Penerbit
        </router-link>
      </nav>
      
      <button @click="logout" class="block w-full text-left px-3 py-2 rounded-lg text-red-600 hover:bg-red-50 transition-colors">
        Logout
      </button>
    </div>
    
    <!-- Content -->
    <div class="flex-1 p-8">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold text-gray-800">Selamat Datang!!</h1>
        <span class="text-sm text-gray-500">{{ userNama }}</span>
      </div>
      
      <!-- Loading -->
      <div v-if="loading" class="text-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="text-gray-400 mt-2">Memuat data...</p>
      </div>

      <!-- STATISTIK -->
      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <!-- Total Sertifikat -->
        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500 font-medium">Total Data</p>
              <h2 class="text-3xl font-bold text-gray-800 mt-1">{{ totalSemua }}</h2>
            </div>
            <div class="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"/>
              </svg>
            </div>
          </div>
          <p class="text-xs text-gray-400 mt-2">Tercatat Di Supabase</p>
        </div>

        <!-- Sertifikat Terbit -->
        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500 font-medium">Terbitan</p>
              <h2 class="text-3xl font-bold text-green-600 mt-1">{{ totalTerbit }}</h2>
            </div>
            <div class="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/>
              </svg>
            </div>
          </div>
          <p class="text-xs text-gray-400 mt-2">Tercatat Di Blockchain</p>
        </div>

        <!-- Penerbit Aktif -->
        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500 font-medium">Penerbit Aktif</p>
              <h2 class="text-3xl font-bold text-purple-600 mt-1">{{ totalPenerbitAktif }}</h2>
            </div>
            <div class="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
              <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
              </svg>
            </div>
          </div>
          <p class="text-xs text-gray-400 mt-2">Penerbit Yang Aktif</p>
        </div>
      </div>

      <!-- Menu Admin -->
      <div class="card">
        <h3 class="text-lg font-semibold text-gray-800 mb-4">Menu Admin</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <router-link to="/admin/tambah-penerbit" class="p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors border-2 border-transparent hover:border-blue-300">
            <p class="font-medium text-blue-700">Tambahkan Penerbit</p>
            <p class="text-sm text-gray-500">form tambahkan penerbit</p>
          </router-link>
          <router-link to="/admin/data-penerbit" class="p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors border-2 border-transparent hover:border-green-300">
            <p class="font-medium text-green-700">Data Penerbit</p>
            <p class="text-sm text-gray-500">kelola akun penerbit</p>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore, usePublisherStore } from '../store/auth'
import api from '../services/api'

const router = useRouter()
const authStore = useAuthStore()
const publisherStore = usePublisherStore()

const certificates = ref([])
const loading = ref(false)

const userNama = computed(() => {
  return authStore.user?.nama_lengkap || authStore.user?.username || 'Admin'
})

// 🔥 TOTAL SERTIFIKAT DARI API
const totalSemua = computed(() => {
  return certificates.value.length
})

// 🔥 SERTIFIKAT YANG SUDAH TERBIT (punya tx_hash)
const totalTerbit = computed(() => {
  return certificates.value.filter(c => c.tx_hash).length
})

// 🔥 PENERBIT AKTIF DARI STORE
const totalPenerbitAktif = computed(() => publisherStore.totalActive)

// 🔥 AMBIL DATA SERTIFIKAT
const fetchCertificates = async () => {
  loading.value = true
  try {
    const response = await api.get('/sertifikat')
    certificates.value = response.data.sertifikat || []
  } catch (error) {
    console.error('Gagal mengambil data sertifikat:', error)
  }
  loading.value = false
}

const logout = () => {
  authStore.logout()
  router.push('/')
}

onMounted(async () => {
  await fetchCertificates()
  await publisherStore.refreshData()
})
</script>