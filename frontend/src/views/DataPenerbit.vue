<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Sidebar -->
    <div class="w-64 bg-white border-r border-gray-200 p-4 min-h-screen flex flex-col">
      <h1 class="text-lg font-bold text-blue-700">MENU</h1>
      <p class="text-xs text-gray-400 mt-1">Admin</p>
      
      <nav class="mt-8 space-y-2 flex-1">
        <router-link to="/admin" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50">Dashboard</router-link>
        <router-link to="/admin/tambah-penerbit" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50">(+) Tambahkan Penerbit</router-link>
        <router-link to="/admin/data-penerbit" class="block px-3 py-2 rounded-lg bg-blue-50 text-blue-700 font-medium">(=) Data Penerbit</router-link>
      </nav>
      
      <button @click="logout" class="block w-full text-left px-3 py-2 rounded-lg text-red-600 hover:bg-red-50">Logout</button>
    </div>
    
    <!-- Content -->
    <div class="flex-1 p-8">
      <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-gray-800 mb-6">Data Penerbit</h1>

    </div>

      <div class="card">
        <!-- Status MetaMask -->
        <div class="mb-4 p-3 rounded-lg" :class="isConnected ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'">
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

        <!-- Loading -->
        <div v-if="loading" class="text-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p class="text-gray-400 mt-2">Memuat data...</p>
        </div>

        <!-- Tabel -->
        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="text-left border-b border-gray-200">
                <th class="py-3 px-4 text-xs font-semibold text-gray-500 uppercase">ID</th>
                <th class="py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Username</th>
                <th class="py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Nama Lengkap</th>
                <th class="py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Wallet Address</th>
                <th class="py-3 px-4 text-xs font-semibold text-gray-500 uppercase">Status</th>
                <th class="py-3 px-4 text-xs font-semibold text-gray-500 uppercase text-center">Aksi</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="penerbit in penerbitList" :key="penerbit.id" class="border-b border-gray-100 hover:bg-gray-50">
                <td class="py-3 px-4 text-sm text-gray-600">{{ penerbit.id }}</td>
                <td class="py-3 px-4 text-sm font-medium text-gray-800">{{ penerbit.username }}</td>
                <td class="py-3 px-4 text-sm text-gray-600">{{ penerbit.nama_lengkap }}</td>
                <td class="py-3 px-4 text-sm font-mono text-gray-500 truncate max-w-[120px]">{{ penerbit.wallet_address || '-' }}</td>
                <td class="py-3 px-4">
                  <span :class="penerbit.status === 'active' ? 'badge-success' : 'badge-danger'">
                    {{ penerbit.status === 'active' ? '✅ Aktif' : '❌ Dicabut' }}
                  </span>
                </td>
                <td class="py-3 px-4 text-center">
                  <button v-if="penerbit.status === 'active'" @click="handleRevoke(penerbit)" class="text-red-600 hover:text-red-800 text-sm font-medium" :disabled="loading">
                    🚫 Cabut Hak
                  </button>
                  <button v-else @click="handleActivate(penerbit)" class="text-green-600 hover:text-green-800 text-sm font-medium" :disabled="loading">
                    ✅ Aktifkan Kembali
                  </button>
                </td>
              </tr>
              <tr v-if="penerbitList.length === 0">
                <td colspan="6" class="py-8 text-center text-gray-400">Belum ada data penerbit</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import api from '../services/api'
import { useContract } from '../composables/useContract'

const router = useRouter()
const authStore = useAuthStore()
const contract = useContract()

const penerbitList = ref([])
const loading = ref(false)

// MetaMask
const isConnected = contract.isConnected
const walletAddress = contract.walletAddress

// Ambil data penerbit
const loadPenerbit = async () => {
  loading.value = true
  try {
    const res = await api.get('/penerbit')
    penerbitList.value = res.data.penerbit || []
  } catch (err) {
    console.error('Gagal load penerbit:', err)
  }
  loading.value = false
}

// 🔥 CABUT HAK (dengan MetaMask + Gas Fee)
const handleRevoke = async (penerbit) => {
  if (!penerbit) return
  
  if (!confirm(`⚠️ Yakin cabut hak "${penerbit.nama_lengkap}"?\n\nTransaksi ini akan membutuhkan GAS FEE di MetaMask!`)) return

  if (!window.ethereum) {
    alert('⚠️ MetaMask tidak terdeteksi!')
    return
  }

  if (!isConnected.value) {
    alert('⏳ Hubungkan MetaMask dulu!')
    await connectWallet()
    if (!isConnected.value) return
  }

  if (authStore.user?.role !== 'admin') {
    alert('❌ Hanya admin!')
    return
  }

  loading.value = true

  try {
    // 🔥 STEP 1: Cabut di blockchain (via MetaMask) - GAS FEE!
    const txSuccess = await contract.cabutPenerbit(penerbit.wallet_address)
    if (!txSuccess) {
      alert('❌ Gagal di blockchain: ' + contract.error.value)
      loading.value = false
      return
    }

    // 🔥 STEP 2: Update di database
    await api.post(`/penerbit/${penerbit.id}/revoke`)

    // 🔥 STEP 3: Refresh
    await loadPenerbit()

    alert(`✅ Hak "${penerbit.nama_lengkap}" dicabut!\n🔗 TX: ${contract.txHash.value}`)
  } catch (err) {
    alert('❌ Gagal: ' + err.message)
  }

  loading.value = false
}

// AKTIFKAN KEMBALI (HARUS BAYAR GAS FEE)
const handleActivate = async (penerbit) => {
  if (!penerbit) return

  if (!confirm(`⚠️ Aktifkan kembali "${penerbit.nama_lengkap}"?\n\nTransaksi ini akan membutuhkan GAS FEE di MetaMask!`)) return

  if (!window.ethereum) {
    alert('⚠️ MetaMask tidak terdeteksi!')
    return
  }

  if (!isConnected.value) {
    alert('⏳ Hubungkan MetaMask dulu!')
    await connectWallet()
    if (!isConnected.value) return
  }

  if (authStore.user?.role !== 'admin') {
    alert('❌ Hanya admin!')
    return
  }

  loading.value = true

  try {
    // 🔥 STEP 1: Daftarkan ulang wallet ke blockchain (via MetaMask) - GAS FEE!
    const txSuccess = await contract.tambahPenerbit(penerbit.wallet_address)
    if (!txSuccess) {
      alert('❌ Gagal daftar ulang di blockchain: ' + contract.error.value)
      loading.value = false
      return
    }

    // 🔥 STEP 2: Update status di database
    await api.post(`/penerbit/${penerbit.id}/activate`)

    // 🔥 STEP 3: Refresh data
    await loadPenerbit()

    alert(`✅ "${penerbit.nama_lengkap}" berhasil diaktifkan kembali!\n🔗 TX: ${contract.txHash.value}`)

  } catch (err) {
    alert('❌ Gagal: ' + err.message)
  }

  loading.value = false
}

// Konek MetaMask
const connectWallet = async () => {
  await contract.connectWallet()
}

const logout = () => {
  authStore.logout()
  router.push('/')
}

onMounted(async () => {
  await loadPenerbit()
  await contract.connectWallet()
})
</script>