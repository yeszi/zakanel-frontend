<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Sidebar -->
    <div class="w-64 bg-white border-r border-gray-200 p-4 min-h-screen flex flex-col">
      <h1 class="text-lg font-bold text-blue-700">MENU</h1>
      <p class="text-xs text-gray-400 mt-1">Admin</p>
      <nav class="mt-8 space-y-2 flex-1">
        <router-link to="/admin" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50">Dashboard</router-link>
        <router-link to="/admin/tambah-penerbit" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50">(+) Tambahkan Penerbit</router-link>
        <router-link to="/admin/data-penerbit" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50">(=) Data Penerbit</router-link>
        <router-link to="/admin/audit-log" class="block px-3 py-2 rounded-lg bg-blue-50 text-blue-700 font-medium">(≡) Audit Log</router-link>
      </nav>
      <button @click="logout" class="block w-full text-left px-3 py-2 rounded-lg text-red-600 hover:bg-red-50">Logout</button>
    </div>

    <!-- Content -->
    <div class="flex-1 p-8 min-w-0">
      <div class="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 class="text-2xl font-bold text-gray-800">Audit Log</h1>
          <p class="text-sm text-gray-500">Riwayat aktivitas sistem yang dirantai dengan hash SHA-256 (tamper-evident)</p>
        </div>
        <button @click="verifyChain" :disabled="verifying" class="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
          {{ verifying ? 'Memeriksa...' : '🔒 Verifikasi Integritas Log' }}
        </button>
      </div>

      <!-- Hasil verifikasi rantai -->
      <div v-if="chain" class="mb-4 p-4 rounded-lg border" :class="chain.valid ? 'bg-green-50 border-green-200 text-green-800' : 'bg-red-50 border-red-200 text-red-800'">
        <p class="font-semibold">{{ chain.valid ? '✅ Rantai audit log utuh' : '❌ Rantai audit log RUSAK' }}</p>
        <p class="text-sm mt-1">{{ chain.checked }} dari {{ chain.total }} entri diperiksa.</p>
        <p v-if="!chain.valid" class="text-sm">Kerusakan pada entri ID <b>{{ chain.broken_at_id }}</b>: {{ chain.reason }}</p>
        <p v-if="chain.valid" class="text-xs font-mono mt-1 break-all">Head hash: {{ chain.head_hash }}</p>
      </div>

      <!-- Filter -->
      <div class="card mb-4 flex flex-wrap gap-3 items-end">
        <div>
          <label class="form-label">Aksi</label>
          <select v-model="filter.action" class="form-input">
            <option value="">Semua</option>
            <option v-for="a in actions" :key="a" :value="a">{{ a }}</option>
          </select>
        </div>
        <div>
          <label class="form-label">Status</label>
          <select v-model="filter.status" class="form-input">
            <option value="">Semua</option>
            <option value="success">success</option>
            <option value="failed">failed</option>
            <option value="denied">denied</option>
          </select>
        </div>
        <div>
          <label class="form-label">Jumlah</label>
          <select v-model.number="filter.limit" class="form-input">
            <option :value="50">50</option>
            <option :value="100">100</option>
            <option :value="500">500</option>
          </select>
        </div>
        <button @click="load" class="px-4 py-2 rounded-lg bg-gray-100 text-gray-700 text-sm hover:bg-gray-200">↻ Tampilkan</button>
      </div>

      <div class="card overflow-x-auto">
        <p v-if="loading" class="text-center text-gray-500 py-6">Memuat...</p>
        <p v-else-if="errorMsg" class="text-center text-red-600 py-6">{{ errorMsg }}</p>
        <table v-else class="w-full text-sm">
          <thead>
            <tr class="text-left text-xs text-gray-500 uppercase border-b">
              <th class="py-2 pr-3">ID</th>
              <th class="py-2 pr-3">Waktu</th>
              <th class="py-2 pr-3">Aktor</th>
              <th class="py-2 pr-3">Aksi</th>
              <th class="py-2 pr-3">Target</th>
              <th class="py-2 pr-3">Status</th>
              <th class="py-2 pr-3">Tx / Detail</th>
              <th class="py-2 pr-3">Hash</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in logs" :key="log.id" class="border-b align-top">
              <td class="py-2 pr-3 text-gray-500">{{ log.id }}</td>
              <td class="py-2 pr-3 whitespace-nowrap">{{ formatDate(log.logged_at) }}</td>
              <td class="py-2 pr-3">
                <div class="font-medium">{{ log.actor_username || '-' }}</div>
                <div class="text-xs text-gray-400">{{ log.actor_role }} · {{ log.ip_address || '-' }}</div>
              </td>
              <td class="py-2 pr-3 font-mono text-xs">{{ log.action }}</td>
              <td class="py-2 pr-3 text-xs">{{ log.target_type }}<br><span class="font-mono text-gray-500 break-all">{{ log.target_id }}</span></td>
              <td class="py-2 pr-3">
                <span class="px-2 py-0.5 rounded text-xs" :class="badge(log.status)">{{ log.status }}</span>
              </td>
              <td class="py-2 pr-3 text-xs max-w-xs">
                <a v-if="log.tx_hash" :href="`https://sepolia.etherscan.io/tx/${log.tx_hash}`" target="_blank" class="text-blue-600 hover:underline font-mono">{{ short(log.tx_hash) }}</a>
                <div class="text-gray-500 break-all">{{ prettyDetail(log.detail) }}</div>
              </td>
              <td class="py-2 pr-3 font-mono text-xs text-gray-500" :title="log.entry_hash">{{ short(log.entry_hash) }}</td>
            </tr>
            <tr v-if="!logs.length"><td colspan="8" class="text-center text-gray-400 py-6">Belum ada log</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import api from '../services/api'

const router = useRouter()
const authStore = useAuthStore()

const logs = ref([])
const loading = ref(false)
const errorMsg = ref('')
const verifying = ref(false)
const chain = ref(null)
const filter = reactive({ action: '', status: '', limit: 100 })
const actions = ['LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGIN_BLOCKED', 'LOGOUT', 'ACCESS_DENIED',
  'PENERBIT_ADD', 'PENERBIT_REVOKE', 'PENERBIT_ACTIVATE', 'CERT_PREPARE', 'CERT_PUBLISH',
  'CERT_VERIFY', 'PROOF_REBUILD', 'AUDIT_VERIFY', 'ADMIN_BOOTSTRAP']

const load = async () => {
  loading.value = true
  errorMsg.value = ''
  try {
    const params = { limit: filter.limit }
    if (filter.action) params.action = filter.action
    if (filter.status) params.status = filter.status
    const res = await api.get('/audit', { params })
    logs.value = res.data.logs || []
  } catch (err) {
    errorMsg.value = err.response?.data?.error || 'Gagal memuat audit log'
  }
  loading.value = false
}

const verifyChain = async () => {
  verifying.value = true
  try {
    const res = await api.get('/audit/verify')
    chain.value = res.data
    await load()
  } catch (err) {
    chain.value = { valid: false, checked: 0, total: 0, reason: err.response?.data?.error || err.message }
  }
  verifying.value = false
}

const short = (h) => (h ? `${h.slice(0, 10)}…${h.slice(-6)}` : '')
const badge = (s) => s === 'success' ? 'bg-green-100 text-green-700' : s === 'denied' ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-700'
const prettyDetail = (d) => {
  try {
    const o = typeof d === 'string' ? JSON.parse(d) : d
    return Object.entries(o || {}).map(([k, v]) => `${k}: ${v}`).join(' · ')
  } catch (e) { return d }
}
const formatDate = (d) => d ? new Date(d).toLocaleString('id-ID', { dateStyle: 'medium', timeStyle: 'medium' }) : '-'

const logout = () => {
  authStore.logout()
  router.push('/')
}

onMounted(load)
</script>
