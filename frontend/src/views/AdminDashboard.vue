<template>
  <div class="min-h-screen bg-gray-50 flex">
    <div class="w-64 bg-white border-r border-gray-200 p-4 min-h-screen flex flex-col">
      <h1 class="text-lg font-bold text-blue-700">MENU</h1>
      <p class="text-xs text-gray-400 mt-1">Admin</p>
      <nav class="mt-8 space-y-2 flex-1">
        <router-link to="/admin" class="block px-3 py-2 rounded-lg bg-blue-50 text-blue-700 font-medium">Dashboard</router-link>
        <router-link to="/admin/tambah-penerbit" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors">(+) Tambahkan Penerbit</router-link>
        <router-link to="/admin/data-penerbit" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors">(=) Data Penerbit</router-link>
      </nav>
      <button @click="logout" class="block w-full text-left px-3 py-2 rounded-lg text-red-600 hover:bg-red-50 transition-colors">Logout</button>
    </div>
    
    <div class="flex-1 p-8">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold text-gray-800">Selamat Datang!!</h1>
        <span class="text-sm text-gray-500">{{ userNama }}</span>
      </div>

      <!-- Status MetaMask (sesuai alur sistem: Admin melakukan Koneksi MetaMask setelah masuk Dashboard) -->
      <div class="mb-6 p-3 rounded-lg" :class="isConnected ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'">
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium" :class="isConnected ? 'text-green-700' : 'text-yellow-700'">
            {{ isConnected ? '✅ MetaMask Terhubung' : '⚠️ MetaMask Belum Terhubung' }}
          </span>
          <button @click="connectWallet" class="text-xs px-3 py-1 rounded-lg" :class="isConnected ? 'bg-green-200 text-green-800' : 'bg-yellow-200 text-yellow-800'">
            {{ isConnected ? walletAddress.slice(0,6) + '...' + walletAddress.slice(-4) : 'Hubungkan' }}
          </button>
        </div>
        <p v-if="walletAddress" class="text-xs text-gray-500 mt-1 font-mono">{{ walletAddress }}</p>
      </div>

      <div v-if="loading" class="text-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="text-gray-400 mt-2">Memuat data...</p>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500 font-medium">Total Data</p>
              <h2 class="text-3xl font-bold text-gray-800 mt-1">{{ totalSemua }}</h2>
            </div>
          </div>
          <p class="text-xs text-gray-400 mt-2">Tercatat Di Supabase</p>
        </div>
        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500 font-medium">Terbitan</p>
              <h2 class="text-3xl font-bold text-green-600 mt-1">{{ totalTerbit }}</h2>
            </div>
          </div>
          <p class="text-xs text-gray-400 mt-2">Tercatat Di Blockchain</p>
        </div>
        <div class="card">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500 font-medium">Penerbit Aktif</p>
              <h2 class="text-3xl font-bold text-purple-600 mt-1">{{ totalPenerbitAktif }}</h2>
            </div>
          </div>
          <p class="text-xs text-gray-400 mt-2">Penerbit Yang Aktif</p>
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
import { useContract } from '../composables/useContract'

const router = useRouter()
const authStore = useAuthStore()
const publisherStore = usePublisherStore()
const contract = useContract()

const certificates = ref([])
const loading = ref(false)

// MetaMask
const isConnected = contract.isConnected
const walletAddress = contract.walletAddress
const connectWallet = async () => {
  await contract.connectWallet()
}

const userNama = computed(() => authStore.user?.nama_lengkap || authStore.user?.username || 'Admin')
const totalSemua = computed(() => certificates.value.length)
const totalTerbit = computed(() => certificates.value.filter(c => c.tx_hash).length)
const totalPenerbitAktif = computed(() => publisherStore.totalActive)

const fetchCertificates = async () => {
  loading.value = true
  try {
    const response = await api.get('/sertifikat')
    certificates.value = response.data.sertifikat || []
  } catch (error) {
    console.error('Gagal:', error)
  } finally {
    loading.value = false
  }
}

const logout = () => {
  authStore.logout()
  router.push('/')
}

onMounted(async () => {
  await fetchCertificates()
  await publisherStore.refreshData()
  await contract.connectWallet()
})
</script>