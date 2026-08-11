<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Sidebar -->
    <div class="w-64 bg-white border-r border-gray-200 p-4 min-h-screen flex flex-col">
      <h1 class="text-lg font-bold text-blue-700">MENU</h1>
      <p class="text-xs text-gray-400 mt-1">Admin</p>
      
      <nav class="mt-8 space-y-2 flex-1">
        <router-link to="/admin" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50">Dashboard</router-link>
        <router-link to="/admin/tambah-penerbit" class="block px-3 py-2 rounded-lg bg-blue-50 text-blue-700 font-medium">(+) Tambah Penerbit</router-link>
        <router-link to="/admin/data-penerbit" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50">(=) Data Penerbit</router-link>
      </nav>
      
      <button @click="logout" class="block w-full text-left px-3 py-2 rounded-lg text-red-600 hover:bg-red-50">Logout</button>
    </div>
    
    <!-- Content -->
    <div class="flex-1 p-8">
      <h1 class="text-2xl font-bold text-gray-800 mb-6">Tambahkan Penerbit</h1>
      <h1 class="text-2xl font-bold text-gray-800 mb-6"> Universitas Maritim Raja Ali Haji</h1>

      <div class="max-w-2xl">
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

          <!-- Pesan -->
          <div v-if="success" class="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-lg">{{ success }}</div>
          <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg">{{ error }}</div>

          <!-- Loading Transaksi -->
          <div v-if="loading" class="mb-4 p-3 bg-blue-50 border border-blue-200 text-blue-700 rounded-lg text-center">
            <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mx-auto mb-2"></div>
            <p>⏳ Memproses transaksi di blockchain...</p>
            <p class="text-xs text-gray-500">Konfirmasi di MetaMask (Gas Fee)</p>
          </div>

          <!-- TX Hash -->
          <div v-if="txHash" class="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
            <p class="text-xs text-gray-500">🔗 TX Hash:</p>
            <p class="text-xs font-mono text-gray-700 break-all">{{ txHash }}</p>
            <a :href="`https://sepolia.etherscan.io/tx/${txHash}`" target="_blank" class="text-xs text-blue-600 hover:underline">Lihat di Etherscan →</a>
          </div>

          <!-- Form -->
          <form @submit.prevent="handleSubmit" class="space-y-4">
            <div>
              <label class="form-label">username</label>
              <input v-model="form.username" type="text" class="form-input w-full" required />
            </div>
            <div>
              <label class="form-label">password</label>
              <input v-model="form.password" type="password" class="form-input w-full" required />
            </div>
            <div>
              <label class="form-label">role</label>
              <select v-model="form.role" class="form-input w-full">
                <option value="penerbit">Penerbit</option>
              </select>
            </div>
            <div>
              <label class="form-label">wallet_address</label>
              <input v-model="form.wallet_address" type="text" class="form-input w-full" placeholder="0x..." required />
              <p class="text-xs text-gray-400 mt-1">Melakukan Transaksi</p>
            </div>
            <div>
              <label class="form-label">nama_lengkap</label>
              <input v-model="form.nama_lengkap" type="text" class="form-input w-full" required />
            </div>

            <button type="submit" :disabled="loading || !isConnected" class="w-full btn-primary py-3 disabled:opacity-50">
              {{ loading ? '⏳ Memproses...' : 'Tambahkan' }}
            </button>
            <p v-if="!isConnected" class="text-xs text-yellow-600 text-center">⚠️ Hubungkan MetaMask dulu!</p>
          </form>
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

const form = ref({
  username: '',
  password: '',
  role: 'penerbit',
  wallet_address: '',
  nama_lengkap: ''
})

const loading = ref(false)
const error = ref('')
const success = ref('')
const txHash = ref('')

// MetaMask
const isConnected = contract.isConnected
const walletAddress = contract.walletAddress

const connectWallet = async () => {
  await contract.connectWallet()
}

const handleSubmit = async () => {
  loading.value = true
  error.value = ''
  success.value = ''
  txHash.value = ''

  try {
    // STEP 1: Simpan ke database
    const res = await api.post('/penerbit', form.value)
    if (!res.data.success) {
      error.value = '❌ ' + (res.data.message || 'Gagal simpan')
      loading.value = false
      return
    }

    // STEP 2: Daftarkan ke blockchain (via MetaMask)
    const txSuccess = await contract.tambahPenerbit(form.value.wallet_address)
    if (!txSuccess) {
      error.value = '❌ Gagal di blockchain: ' + contract.error.value
      loading.value = false
      return
    }

    // STEP 3: SUKSES!
    txHash.value = contract.txHash.value
    success.value = '✅ Penerbit berhasil ditambahkan ke database & blockchain!'

    // Reset form
    form.value = { username: '', password: '', role: 'penerbit', wallet_address: '', nama_lengkap: '' }

  } catch (err) {
    error.value = '❌ Gagal: ' + err.message
  }

  loading.value = false
}

const logout = () => {
  authStore.logout()
  router.push('/')
}

onMounted(async () => {
  await contract.connectWallet()
})
</script>