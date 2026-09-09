<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Sidebar -->
    <div class="w-64 bg-white border-r border-gray-200 p-4 min-h-screen flex flex-col">
      <h1 class="text-lg font-bold text-blue-700">MENU</h1>
      <p class="text-xs text-gray-400 mt-1">Penerbit</p>
      <nav class="mt-8 space-y-2 flex-1">
        <router-link to="/publisher" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50">Dashboard</router-link>
        <router-link to="/publisher/terbitkan" class="block px-3 py-2 rounded-lg bg-blue-50 text-blue-700 font-medium">(+) Terbitkan Sertifikat</router-link>
        <router-link to="/publisher/monitoring" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50">(=) Monitoring Data</router-link>
      </nav>
      <button @click="logout" class="block w-full text-left px-3 py-2 rounded-lg text-red-600 hover:bg-red-50">Logout</button>
    </div>

    <!-- Content -->
    <div class="flex-1 p-8">
      <h1 class="text-2xl font-bold text-gray-800 mb-6">Terbitkan Sertifikat</h1>

      <!-- Status MetaMask -->
      <div class="mb-6 p-4 rounded-lg border" :class="isConnected ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium" :class="isConnected ? 'text-green-700' : 'text-yellow-700'">
              {{ isConnected ? '✅ Wallet Terhubung' : '⚠️ Wallet Belum Terhubung' }}
            </p>
            <p v-if="isConnected" class="text-xs text-gray-500 mt-1">{{ walletAddress }}</p>
          </div>
          <button v-if="!isConnected" @click="connectWallet" class="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 text-sm font-medium">Connect MetaMask</button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Form -->
        <div class="lg:col-span-2">
          <div class="card">
            <form @submit.prevent="addToBatch" class="space-y-5">
              <div>
                <label class="form-label">Nama Kegiatan</label>
                <input v-model="form.nama_kegiatan" type="text" class="form-input w-full" required />
              </div>
              <div>
                <label class="form-label">Nama Lokasi</label>
                <input v-model="form.nama_lokasi" type="text" class="form-input w-full" required />
              </div>
              <div>
                <label class="form-label">Koordinat GPS</label>
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="text-xs">Latitude</label>
                    <input v-model="form.latitude" type="number" step="0.0000001" class="form-input w-full" required />
                  </div>
                  <div>
                    <label class="text-xs">Longitude</label>
                    <input v-model="form.longitude" type="number" step="0.0000001" class="form-input w-full" required />
                  </div>
                </div>
                <button type="button" @click="getCurrentLocation" :disabled="loadingLocation" class="mt-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm disabled:opacity-50">
                  {{ loadingLocation ? '⏳ Mengambil lokasi...' : '📍 Ambil Lokasi GPS' }}
                </button>
              </div>
              <div>
                <label class="form-label">Waktu Mulai</label>
                <input v-model="form.waktu_mulai" type="datetime-local" class="form-input w-full" required />
              </div>
              <div>
                <label class="form-label">Waktu Selesai</label>
                <input v-model="form.waktu_selesai" type="datetime-local" class="form-input w-full" required />
              </div>
              <div>
                <label class="form-label">Nama Lengkap Peserta</label>
                <input v-model="form.nama_peserta" type="text" class="form-input w-full" required />
              </div>
              <div>
                <label class="form-label">Keterangan <span class="text-gray-400 font-normal">(opsional)</span></label>
                <textarea v-model="form.keterangan" rows="2" class="form-input w-full" placeholder="Deskripsi tambahan..."></textarea>
              </div>
              <button type="submit" :disabled="loading" class="w-full btn-primary py-2 disabled:opacity-50">+ Tambah Antrean Batch</button>
            </form>
          </div>
        </div>

        <!-- Tabel Antrean -->
        <div class="lg:col-span-1">
          <div class="card sticky top-8">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-gray-800">📋 Tabel Antrean</h3>
              <span class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">{{ batch.length }} data</span>
            </div>

            <div v-if="batch.length === 0" class="text-center py-12 text-gray-400 text-sm">Belum ada data</div>

            <div v-else class="space-y-3 max-h-[400px] overflow-y-auto">
              <div v-for="(item, index) in batch" :key="index" class="bg-gray-50 rounded-lg p-4 border">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="font-medium text-gray-800">{{ item.nama_peserta }}</p>
                    <p class="text-xs text-gray-500">{{ item.nama_kegiatan }} · {{ item.nama_lokasi }}</p>
                  </div>
                  <div class="flex space-x-2">
                    <button @click="openEditModal(index)" class="text-blue-600 hover:text-blue-800 text-sm font-medium">✏️ edit</button>
                    <button @click="removeFromBatch(index)" class="text-red-500 hover:text-red-700 text-sm font-medium">🗑 hapus</button>
                  </div>
                </div>
              </div>
            </div>

            <button @click="publishBatch" :disabled="batch.length === 0 || publishing || !isConnected" class="w-full btn-success py-3 mt-4 disabled:opacity-50 text-lg font-semibold">
              {{ publishing ? '⏳ Menerbitkan...' : 'Terbitkan Batch' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL EDIT -->
    <div v-if="editModal.show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-xl p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-800">✏️ Edit Data Sertifikat</h3>
          <button @click="closeEditModal" class="text-gray-400 hover:text-gray-600">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <form @submit.prevent="saveEdit" class="space-y-4">
          <div>
            <label class="form-label">Nama Kegiatan</label>
            <input v-model="editForm.nama_kegiatan" type="text" class="form-input w-full" required />
          </div>
          <div>
            <label class="form-label">Nama Lokasi</label>
            <input v-model="editForm.nama_lokasi" type="text" class="form-input w-full" required />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="form-label">Latitude</label>
              <input v-model="editForm.latitude" type="number" step="0.0000001" class="form-input w-full" required />
            </div>
            <div>
              <label class="form-label">Longitude</label>
              <input v-model="editForm.longitude" type="number" step="0.0000001" class="form-input w-full" required />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="form-label">Waktu Mulai</label>
              <input v-model="editForm.waktu_mulai" type="datetime-local" class="form-input w-full" required />
            </div>
            <div>
              <label class="form-label">Waktu Selesai</label>
              <input v-model="editForm.waktu_selesai" type="datetime-local" class="form-input w-full" required />
            </div>
          </div>
          <div>
            <label class="form-label">Nama Lengkap Peserta</label>
            <input v-model="editForm.nama_peserta" type="text" class="form-input w-full" required />
          </div>
          <div>
            <label class="form-label">Keterangan Tambahan</label>
            <textarea v-model="editForm.keterangan" rows="2" class="form-input w-full"></textarea>
          </div>

          <div class="flex space-x-3 pt-4">
            <button type="button" @click="closeEditModal" class="flex-1 btn-secondary py-2">Batal</button>
            <button type="submit" class="flex-1 btn-primary py-2">Simpan Perubahan</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal QR Code -->
    <div v-if="showQRModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div class="bg-white rounded-xl p-6 max-w-lg w-full">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-800">📱 QR Code</h3>
          <button @click="closeQRModal" class="text-gray-400">X</button>
        </div>
        <div v-if="selectedQR" class="text-center">
          <img :src="selectedQR.qr_code" alt="QR" class="mx-auto w-64 h-64" />
          <p class="mt-2 text-sm text-gray-600 break-all">🔗 {{ selectedQR.verify_url }}</p>
        </div>
        <button @click="closeQRModal" class="btn-secondary px-6 py-2 w-full mt-4">Tutup</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { useContract } from '../composables/useContract'
import api from '../services/api'

const router = useRouter()
const authStore = useAuthStore()
const contract = useContract()

const isConnected = contract.isConnected
const walletAddress = contract.walletAddress
const connectWallet = async () => await contract.connectWallet()

// Form utama
const form = reactive({
  nama_kegiatan: '',
  nama_lokasi: '',
  latitude: '',
  longitude: '',
  waktu_mulai: '',
  waktu_selesai: '',
  nama_peserta: '',
  keterangan: ''
})

// Modal Edit
const editModal = ref({ show: false, index: null })
const editForm = reactive({
  nama_kegiatan: '',
  nama_lokasi: '',
  latitude: '',
  longitude: '',
  waktu_mulai: '',
  waktu_selesai: '',
  nama_peserta: '',
  keterangan: ''
})

const batch = ref([])
const loading = ref(false)
const publishing = ref(false)
const loadingLocation = ref(false)

const qrCodes = ref([])
const showQRModal = ref(false)
const selectedQR = ref(null)

// LocalStorage
const saveToLocalStorage = () => {
  try { localStorage.setItem('batch_data', JSON.stringify(batch.value)) } catch(e) {}
}
const loadFromLocalStorage = () => {
  const saved = localStorage.getItem('batch_data')
  if (saved) {
    try { batch.value = JSON.parse(saved) } catch (e) {}
  }
}
watch(batch, saveToLocalStorage, { deep: true })

const getCurrentLocation = () => {
  loadingLocation.value = true
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      form.latitude = pos.coords.latitude.toFixed(7)
      form.longitude = pos.coords.longitude.toFixed(7)
      loadingLocation.value = false
    },
    (err) => {
      loadingLocation.value = false
      alert('Gagal ambil lokasi: ' + err.message)
    },
    { enableHighAccuracy: true, timeout: 10000 }
  )
}

// BUKA MODAL EDIT
const openEditModal = (index) => {
  const item = batch.value[index]
  editForm.nama_kegiatan = item.nama_kegiatan || ''
  editForm.nama_lokasi = item.nama_lokasi || ''
  editForm.latitude = item.latitude || ''
  editForm.longitude = item.longitude || ''
  editForm.waktu_mulai = item.waktu_mulai || ''
  editForm.waktu_selesai = item.waktu_selesai || ''
  editForm.nama_peserta = item.nama_peserta || ''
  editForm.keterangan = item.keterangan || ''
  editModal.value.show = true
  editModal.value.index = index
}

// SIMPAN EDIT
const saveEdit = () => {
  const index = editModal.value.index
  batch.value[index] = { ...editForm }
  closeEditModal()
}

// TUTUP MODAL
const closeEditModal = () => {
  editModal.value.show = false
  editModal.value.index = null
}

// TAMBAH KE BATCH
const addToBatch = () => {
  if (!form.nama_peserta) { alert('❌ Nama peserta wajib diisi!'); return }
  if (!form.nama_kegiatan) { alert('❌ Nama kegiatan wajib diisi!'); return }
  if (!form.nama_lokasi) { alert('❌ Nama lokasi wajib diisi!'); return }
  if (!form.latitude) { alert('❌ Latitude wajib diisi!'); return }
  if (!form.longitude) { alert('❌ Longitude wajib diisi!'); return }
  if (!form.waktu_mulai) { alert('❌ Waktu mulai wajib diisi!'); return }
  if (!form.waktu_selesai) { alert('❌ Waktu selesai wajib diisi!'); return }

  const isDuplicate = batch.value.some(item => item.nama_peserta === form.nama_peserta)
  if (isDuplicate) {
    alert(`⚠️ Data untuk "${form.nama_peserta}" sudah ada di antrean!`)
    return
  }

  batch.value.push({
    ...form,
    latitude: parseFloat(form.latitude),
    longitude: parseFloat(form.longitude)
  })

  form.nama_kegiatan = ''
  form.nama_lokasi = ''
  form.latitude = ''
  form.longitude = ''
  form.waktu_mulai = ''
  form.waktu_selesai = ''
  form.nama_peserta = ''
  form.keterangan = ''
}

const removeFromBatch = (idx) => {
  if (confirm(`Hapus data "${batch.value[idx].nama_peserta}" dari antrean?`)) {
    batch.value.splice(idx, 1)
  }
}

const generateQRForSertifikat = async (publicId, index) => {
  try {
    const response = await api.get(`/sertifikat/generate-qr/${publicId}`)
    if (response.data.success) {
      qrCodes.value[index] = {
        public_id: publicId,
        qr_code: response.data.qr_code,
        verify_url: response.data.verify_url
      }
    }
  } catch (error) {
    console.error('Error QR:', error)
  }
}

const closeQRModal = () => {
  showQRModal.value = false
  selectedQR.value = null
}

const publishBatch = async () => {
  if (batch.value.length === 0) {
    alert('❌ Antrean kosong!')
    return
  }

  if (!isConnected.value) {
    alert('⚠️ Silakan connect MetaMask terlebih dahulu!')
    return
  }

  if (!authStore.user || authStore.user.role !== 'penerbit') {
    alert('❌ Anda bukan penerbit!')
    return
  }

  if (!confirm(`📤 Terbitkan ${batch.value.length} sertifikat?\n\n⚠️ Transaksi ini akan membutuhkan GAS FEE di MetaMask!`)) {
    return
  }

  publishing.value = true

  try {
    const penerbitId = authStore.user?.id
    if (!penerbitId) throw new Error('ID penerbit tidak ditemukan!')

    const prepareRes = await api.post('/sertifikat/prepare', {
      sertifikat_list: batch.value,
      penerbit_id: penerbitId
    })

    if (!prepareRes.data.success) {
      throw new Error(prepareRes.data.error || 'Gagal prepare sertifikat')
    }

    const allData = prepareRes.data.data || []
    const merkleRoot = prepareRes.data.merkle_root
    const batchIdOnchain = prepareRes.data.batch_id || Date.now()

    if (!merkleRoot || allData.length === 0) {
      throw new Error('Merkle Root atau data sertifikat kosong!')
    }

    const publicId = prepareRes.data.first_public_id
    if (!publicId) {
      throw new Error('Public ID tidak ditemukan dari response prepare')
    }
    console.log('🔑 Public ID yang akan didaftarkan di blockchain:', publicId)

    const txSuccess = await contract.simpanRoot(batchIdOnchain, merkleRoot, publicId)
    if (!txSuccess) {
      throw new Error('Gagal simpan root di blockchain: ' + contract.error.value)
    }

    await api.post('/sertifikat/konfirmasi', {
      merkle_root: merkleRoot,
      tx_hash: contract.txHash.value,
      batch_id_onchain: batchIdOnchain,
      sertifikat_list: allData.map(i => ({ public_id: i.public_id, proof: [] }))
    })

    qrCodes.value = []
    for (let i = 0; i < allData.length; i++) {
      await generateQRForSertifikat(allData[i].public_id, i)
    }

    if (qrCodes.value.length > 0) {
      selectedQR.value = qrCodes.value[0]
      showQRModal.value = true
    }

    batch.value = []
    localStorage.removeItem('batch_data')

    alert(`✅ ${allData.length} sertifikat berhasil diterbitkan!\n🔗 TX: ${contract.txHash.value.slice(0, 10)}...`)

  } catch (error) {
    console.error('❌ Error:', error)
    let errorMessage = error.message || 'Terjadi kesalahan'
    if (error.response?.data?.error) errorMessage = error.response.data.error
    else if (error.code === 'ACTION_REJECTED' || error.code === 4001) errorMessage = 'Transaksi dibatalkan di MetaMask'
    else if (error.message?.includes('insufficient funds')) errorMessage = 'Saldo ETH tidak cukup untuk gas fee!'
    alert('❌ Gagal: ' + errorMessage)
  }

  publishing.value = false
}

const logout = () => {
  authStore.logout()
  router.push('/')
}

onMounted(loadFromLocalStorage)
</script>