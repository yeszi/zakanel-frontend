<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Sidebar -->
    <div class="w-64 bg-white border-r border-gray-200 p-4 min-h-screen flex flex-col">
      <h1 class="text-lg font-bold text-blue-700">MENU</h1>
      <p class="text-xs text-gray-400 mt-1">Penerbit</p>

      <nav class="mt-8 space-y-2 flex-1">
        <router-link to="/publisher" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors">
          Dashboard
        </router-link>
        <router-link to="/publisher/terbitkan" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors">
          (+) Terbitkan Sertifikat
        </router-link>
        <router-link to="/publisher/monitoring" class="block px-3 py-2 rounded-lg bg-blue-50 text-blue-700 font-medium">
          (=) Monitoring Data
        </router-link>
      </nav>

      <button @click="logout" class="block w-full text-left px-3 py-2 rounded-lg text-red-600 hover:bg-red-50 transition-colors">
        Logout
      </button>
    </div>

    <!-- Content -->
    <div class="flex-1 p-8">
      <div class="flex items-center justify-between mb-6">
        <h1 class="text-2xl font-bold text-gray-800">Monitoring Data</h1>
        <span class="text-sm text-gray-500">Universitas Maritim Raja Ali Haji</span>
      </div>

      <div class="card">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div class="relative flex-1 max-w-sm">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Cari Nama Peserta..."
              class="w-full form-input pl-10"
            />
            <svg class="w-5 h-5 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
          </div>
          <div class="flex items-center space-x-3">
            <button @click="showAuditChain" class="btn-secondary flex items-center space-x-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
              </svg>
              <span>+ Audit Rantai</span>
            </button>
            <button @click="refreshData" class="btn-secondary flex items-center space-x-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
              <span>Refresh</span>
            </button>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="text-center py-12 text-gray-400">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p class="mt-4">Memuat data sertifikat...</p>
        </div>

        <!-- Tabel GROUPED PER BATCH -->
        <div v-else>
          <!-- Jika tidak ada data -->
          <div v-if="groupedBatches.length === 0" class="text-center py-12 text-gray-400">
            <svg class="w-12 h-12 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            <p>Tidak ada data sertifikat</p>
          </div>

          <!-- Loop per Batch -->
          <div v-for="batch in groupedBatches" :key="batch.batch_id" class="mb-8">
            <!-- Header Batch -->
            <div class="flex items-center justify-between bg-blue-50 p-3 rounded-lg mb-3">
              <div>
                <h3 class="font-semibold text-blue-800">📦 Batch #{{ batch.batch_id }}</h3>
                <span class="text-sm text-gray-600">{{ batch.sertifikat.length }} sertifikat</span>
              </div>
              <span class="text-xs text-gray-500">
                {{ formatDate(batch.created_at) }}
              </span>
            </div>

            <!-- Tabel Sertifikat dalam Batch -->
            <div class="overflow-x-auto">
              <table class="w-full">
                <thead>
                  <tr class="text-left border-b border-gray-200">
                    <th class="py-2 px-3 text-xs font-semibold text-gray-500 uppercase">#</th>
                    <th class="py-2 px-3 text-xs font-semibold text-gray-500 uppercase">Nama Peserta</th>
                    <th class="py-2 px-3 text-xs font-semibold text-gray-500 uppercase">Merkle Root</th>
                    <th class="py-2 px-3 text-xs font-semibold text-gray-500 uppercase">TX Hash</th>
                    <th class="py-2 px-3 text-xs font-semibold text-gray-500 uppercase">Waktu Terbit</th>
                    <th class="py-2 px-3 text-xs font-semibold text-gray-500 uppercase text-center">Aksi</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(cert, index) in batch.sertifikat"
                    :key="cert.id"
                    class="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                  >
                    <td class="py-2 px-3 text-sm text-gray-600">{{ index + 1 }}</td>
                    <td class="py-2 px-3 text-sm font-medium text-gray-800">{{ cert.nama_peserta }}</td>
                    <td class="py-2 px-3 text-xs font-mono text-gray-500 truncate max-w-[100px]">
                      {{ cert.merkle_root ? cert.merkle_root.slice(0, 12) + '...' : '⏳ Menunggu' }}
                    </td>
                    <td class="py-2 px-3 text-xs font-mono text-gray-500 truncate max-w-[100px]">
                      {{ cert.tx_hash ? cert.tx_hash.slice(0, 12) + '...' : '⏳ Menunggu' }}
                    </td>
                    <td class="py-2 px-3 text-sm text-gray-600">{{ formatDate(cert.created_at) }}</td>
                    <td class="py-2 px-3 text-center">
                      <div class="flex items-center justify-center space-x-2">
                        <button
                          @click="viewCertificate(cert)"
                          class="text-blue-600 hover:text-blue-800 text-xs font-medium"
                        >
                          👁 Lihat
                        </button>
                        <button
                          @click="showQR(cert)"
                          class="text-green-600 hover:text-green-800 text-xs font-medium"
                        >
                          📱 QR
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL DETAIL SERTIFIKAT -->
    <div v-if="detailModal.show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-800">📄 Detail Sertifikat</h3>
          <button @click="closeDetailModal" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div class="space-y-4">
          <div class="flex items-center space-x-3 p-3 bg-green-50 rounded-lg border border-green-200">
            <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <span class="text-sm font-medium text-green-700">Sertifikat Valid - Terverifikasi di Blockchain</span>
          </div>

          <div class="bg-gray-50 rounded-lg p-4 space-y-3">
            <div class="flex justify-between py-2 border-b border-gray-200">
              <span class="text-sm text-gray-500">ID Sertifikat</span>
              <span class="text-sm font-medium text-gray-800">{{ detailData.id || '-' }}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-200">
              <span class="text-sm text-gray-500">Batch ID</span>
              <span class="text-sm font-medium text-gray-800">{{ detailData.batch_id || '-' }}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-200">
              <span class="text-sm text-gray-500">Public ID</span>
              <span class="text-xs font-mono text-gray-800 break-all">{{ detailData.public_id || '-' }}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-200">
              <span class="text-sm text-gray-500">Nama Peserta</span>
              <span class="text-sm font-medium text-gray-800">{{ detailData.nama_peserta || '-' }}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-200">
              <span class="text-sm text-gray-500">Nama Kegiatan</span>
              <span class="text-sm font-medium text-gray-800">{{ detailData.nama_kegiatan || '-' }}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-200">
              <span class="text-sm text-gray-500">Nama Lokasi</span>
              <span class="text-sm font-medium text-gray-800">{{ detailData.nama_lokasi || '-' }}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-200">
              <span class="text-sm text-gray-500">Koordinat</span>
              <span class="text-sm font-medium text-gray-800">{{ detailData.latitude || '0' }}, {{ detailData.longitude || '0' }}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-200">
              <span class="text-sm text-gray-500">Waktu Mulai</span>
              <span class="text-sm font-medium text-gray-800">{{ detailData.waktu_mulai || '-' }}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-200">
              <span class="text-sm text-gray-500">Waktu Selesai</span>
              <span class="text-sm font-medium text-gray-800">{{ detailData.waktu_selesai || '-' }}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-200">
              <span class="text-sm text-gray-500">Cert Hash</span>
              <span class="text-xs font-mono text-gray-500 break-all">{{ detailData.cert_hash || '-' }}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-200">
              <span class="text-sm text-gray-500">Merkle Root</span>
              <span class="text-xs font-mono text-gray-500 break-all">{{ detailData.merkle_root || '-' }}</span>
            </div>
            <div class="flex justify-between py-2 border-b border-gray-200">
              <span class="text-sm text-gray-500">TX Hash</span>
              <span class="text-xs font-mono text-gray-500 break-all">{{ detailData.tx_hash || '-' }}</span>
            </div>
            <div class="flex justify-between py-2">
              <span class="text-sm text-gray-500">Tanggal Terbit</span>
              <span class="text-sm font-medium text-gray-800">{{ formatDate(detailData.created_at) || '-' }}</span>
            </div>
          </div>

          <button @click="closeDetailModal" class="w-full btn-primary py-2">Tutup</button>
        </div>
      </div>
    </div>

    <!-- MODAL QR CODE -->
    <div v-if="qrModal.show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl p-6 max-w-sm w-full">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-800">📱 QR Code Sertifikat</h3>
          <button @click="closeQRModal" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div class="flex flex-col items-center">
          <p class="text-sm text-gray-500 mb-3">Scan untuk verifikasi sertifikat</p>

          <div class="bg-white p-4 rounded-lg border border-gray-200 mb-3">
            <img
              v-if="qrModal.qrData"
              :src="qrModal.qrData"
              alt="QR Code"
              class="w-48 h-48"
            />
            <div v-else class="w-48 h-48 bg-gray-100 rounded flex items-center justify-center text-gray-400">
              <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"/>
              </svg>
            </div>
          </div>

          <div class="w-full bg-gray-50 rounded-lg p-3 text-center">
            <p class="text-xs text-gray-500 truncate">ID: {{ qrModal.certId || '-' }}</p>
            <p class="text-xs text-gray-500 truncate">Nama: {{ qrModal.namaPeserta || '-' }}</p>
          </div>

          <button @click="closeQRModal" class="w-full btn-secondary py-2 mt-4">Tutup</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import api from '../services/api'
import QRCode from 'qrcode'

const router = useRouter()
const authStore = useAuthStore()

// ============================================
// STATE
// ============================================
const certificates = ref([])
const loading = ref(false)
const searchQuery = ref('')

// ============================================
// AMBIL DATA ASLI DARI BACKEND
// ============================================
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

onMounted(() => {
  fetchCertificates()
})

// ============================================
// GROUPING PER BATCH (REVISI BARU!)
// ============================================
const groupedBatches = computed(() => {
  const groups = {}
  
  // Filter dulu berdasarkan searchQuery
  let filtered = certificates.value
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = certificates.value.filter(c =>
      c.nama_peserta.toLowerCase().includes(query)
    )
  }
  
  // Kelompokkan berdasarkan batch_id
  filtered.forEach(cert => {
    const batchId = cert.batch_id || 'unknown'
    if (!groups[batchId]) {
      groups[batchId] = {
        batch_id: batchId,
        sertifikat: [],
        created_at: cert.created_at
      }
    }
    groups[batchId].sertifikat.push(cert)
  })
  
  // Urutkan dari batch terbaru (batch_id terbesar)
  return Object.values(groups).sort((a, b) => b.batch_id - a.batch_id)
})

// ============================================
// MODAL DETAIL
// ============================================
const detailModal = ref({ show: false })
const detailData = ref({})

const viewCertificate = (cert) => {
  detailData.value = cert
  detailModal.value.show = true
}

const closeDetailModal = () => {
  detailModal.value.show = false
}

// ============================================
// MODAL QR
// ============================================
const qrModal = ref({
  show: false,
  qrData: null,
  certId: null,
  namaPeserta: null
})

const showQR = async (cert) => {
  try {
    const qrDataUrl = await QRCode.toDataURL(cert.verify_url, { width: 300 })
    qrModal.value = {
      show: true,
      qrData: qrDataUrl,
      certId: cert.public_id,
      namaPeserta: cert.nama_peserta
    }
  } catch (error) {
    console.error('Gagal generate QR:', error)
  }
}

const closeQRModal = () => {
  qrModal.value.show = false
}

// ============================================
// FORMAT TANGGAL
// ============================================
const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('id-ID', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// ============================================
// FUNGSI LAINNYA
// ============================================
const showAuditChain = () => {
  alert('🔗 Fitur Audit Rantai\n\nMenampilkan seluruh riwayat transaksi blockchain untuk sertifikat terpilih.')
}

const refreshData = () => {
  fetchCertificates()
}

const logout = () => {
  authStore.logout()
  router.push('/')
}
</script>