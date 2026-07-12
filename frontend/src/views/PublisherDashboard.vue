<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Sidebar -->
    <div class="w-64 bg-white border-r border-gray-200 p-4 min-h-screen flex flex-col">
      <h1 class="text-lg font-bold text-blue-700">MENU</h1>
      <p class="text-xs text-gray-400 mt-1">Penerbit</p>
      
      <nav class="mt-8 space-y-2 flex-1">
        <router-link to="/publisher" class="block px-3 py-2 rounded-lg bg-blue-50 text-blue-700 font-medium">
          Dashboard
        </router-link>
        <router-link to="/publisher/terbitkan" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors">
          (+) Terbitkan Sertifikat
        </router-link>
        <router-link to="/publisher/monitoring" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors">
          (=) Monitoring Data
        </router-link>
      </nav>
      <button @click="logout" class="block w-full text-left px-3 py-2 rounded-lg text-red-600 hover:bg-red-50 transition-colors mt-8">
          Logout
        </button>
    </div>
    
    <!-- Content -->
    <div class="flex-1 p-8">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold text-gray-800"> Selamat Datang !!</h1>
        <span class="text-sm text-gray-500">{{ userNama }}</span>
      </div>
      
      <!-- 🔥 STATISTIK DINAMIS -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div class="card">
          <p class="text-sm text-gray-500 font-medium">Total Data Terbitan</p>
          <h2 class="text-3xl font-bold text-gray-800 mt-1">{{ totalSertifikat }}</h2>
          <p class="text-xs text-gray-400 mt-2">Sertifikat </p>
        </div>
        <div class="card">
          <p class="text-sm text-gray-500 font-medium">Wallet Address</p>
          <h2 class="text-sm font-mono font-bold text-gray-800 mt-1 break-all">{{ walletAddress || '-' }}</h2>
          <p class="text-xs text-gray-400 mt-2">Wallet Terdaftar</p>
        </div>
        <div class="card">
          <p class="text-sm text-gray-500 font-medium">Status</p>
          <h2 class="text-3xl font-bold" :class="isActive ? 'text-green-600' : 'text-red-600'">
            {{ isActive ? '✅ Terdaftar' : '❌ Belum Terdaftar' }}
          </h2>
          <p class="text-xs text-gray-400 mt-2">Status di Smart Contract</p>
        </div>
      </div>

      <div class="card">
        <h3 class="text-lg font-semibold text-gray-800 mb-4">Menu Penerbit</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <router-link to="/publisher/terbitkan" class="p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors">
            <p class="font-medium text-blue-700">Terbitkan Sertifikat</p>
            <p class="text-sm text-gray-500">Buat sertifikat baru</p>
          </router-link>
          <router-link to="/publisher/monitoring" class="p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors">
            <p class="font-medium text-green-700">Monitoring Data</p>
            <p class="text-sm text-gray-500">Lihat semua sertifikat</p>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { useContract } from '../composables/useContract'
import api from '../services/api'

const router = useRouter()
const authStore = useAuthStore()
const contract = useContract()

const certificates = ref([])

const userNama = computed(() => {
  return authStore.user?.nama_lengkap || authStore.user?.username || 'Penerbit'
})

// 🔥 TOTAL SERTIFIKAT DARI API
const totalSertifikat = computed(() => {
  return certificates.value.length
})

// 🔥 WALLET ADDRESS
const walletAddress = computed(() => {
  return authStore.user?.wallet_address || contract.walletAddress.value || '-'
})

// 🔥 STATUS AKTIF DI BLOCKCHAIN
const isActive = ref(false)

// 🔥 AMBIL DATA SERTIFIKAT
const fetchCertificates = async () => {
  try {
    const response = await api.get('/sertifikat')
    certificates.value = response.data.sertifikat || []
  } catch (error) {
    console.error('Gagal mengambil data sertifikat:', error)
  }
}

// 🔥 CEK STATUS WALLET DI BLOCKCHAIN
const checkBlockchainStatus = async () => {
  if (!walletAddress.value || walletAddress.value === '-') return
  
  try {
    const status = await contract.cekStatusPenerbit(walletAddress.value)
    isActive.value = status
  } catch (error) {
    console.error('Gagal cek status blockchain:', error)
    isActive.value = false
  }
}

const logout = () => {
  authStore.logout()
  router.push('/')
}

onMounted(async () => {
  await fetchCertificates()
  await contract.connectWallet()
  await checkBlockchainStatus()
})
</script>