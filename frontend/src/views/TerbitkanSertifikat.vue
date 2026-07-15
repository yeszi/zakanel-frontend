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
        <router-link to="/publisher/terbitkan" class="block px-3 py-2 rounded-lg bg-blue-50 text-blue-700 font-medium">
          (+) Terbitkan Sertifikat
        </router-link>
        <router-link to="/publisher/monitoring" class="block px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors">
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
        <h1 class="text-2xl font-bold text-gray-800">Terbitkan Sertifikat</h1>
        <span class="text-sm text-gray-500">Universitas Maritim Raja Ali Haji</span>
      </div>

      <!-- Wallet MetaMask -->
      <div class="mb-6 p-4 rounded-lg border" :class="isConnected ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium" :class="isConnected ? 'text-green-700' : 'text-yellow-700'">
              {{ isConnected ? '✅ Wallet Terhubung' : '⚠️ Wallet Belum Terhubung' }}
            </p>
            <p v-if="isConnected" class="text-xs text-gray-500 mt-1">{{ walletAddress }}</p>
          </div>
          <button
            v-if="!isConnected"
            @click="connectWallet"
            class="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 text-sm font-medium"
          >
            Connect MetaMask
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Form -->
        <div class="lg:col-span-2">
          <div class="card">
            <form @submit.prevent="addToBatch" class="space-y-5">
              <div>
                <label class="form-label">Nama Kegiatan</label>
                <input v-model="form.nama_kegiatan" type="text" class="form-input w-full" placeholder="Contoh: Praktikum Algoritma" required />
              </div>

              <div>
                <label class="form-label">Nama Lokasi</label>
                <input v-model="form.nama_lokasi" type="text" class="form-input w-full" placeholder="Contoh: Lab Algoritma FTTK" required />
              </div>

              <div>
                <label class="form-label">Koordinat GPS</label>
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="text-xs text-gray-500">Latitude</label>
                    <input v-model="form.latitude" type="number" step="0.0000001" class="form-input w-full" placeholder="0.0000000" required />
                  </div>
                  <div>
                    <label class="text-xs text-gray-500">Longitude</label>
                    <input v-model="form.longitude" type="number" step="0.0000001" class="form-input w-full" placeholder="0.0000000" required />
                  </div>
                </div>
                
                <button 
                  type="button" 
                  @click="getCurrentLocation" 
                  :disabled="loadingLocation"
                  class="mt-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium disabled:opacity-50"
                >
                  {{ loadingLocation ? '⏳ Mengambil lokasi...' : '📍 Ambil Lokasi GPS' }}
                </button>
                
                <div v-if="locationStatus" class="mt-2 text-xs" :class="locationStatus.type === 'success' ? 'text-green-600' : 'text-red-600'">
                  {{ locationStatus.message }}
                </div>
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
                <input v-model="form.nama_peserta" type="text" class="form-input w-full" placeholder="Nama lengkap peserta" required />
              </div>

              <div>
                <label class="form-label">Keterangan Tambahan</label>
                <textarea v-model="form.keterangan" rows="3" class="form-input w-full" placeholder="Keterangan tambahan (opsional)"></textarea>
              </div>

              <button type="submit" :disabled="loading" class="w-full btn-primary py-2 disabled:opacity-50">
                {{ loading ? 'Memproses...' : '+ Tambah Antrean Batch' }}
              </button>
            </form>
          </div>
        </div>

        <!-- Batch Queue -->
        <div class="lg:col-span-1">
          <div class="card sticky top-8">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-gray-800">📋 Tabel Antrean Sementara</h3>
              <span class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">{{ batch.length }} data</span>
            </div>

            <div v-if="batch.length === 0" class="text-center py-12 text-gray-400 text-sm">
              <svg class="w-12 h-12 mx-auto text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
              </svg>
              <p>Belum ada data dalam antrean</p>
              <p class="text-xs mt-1">Isi form di samping untuk menambahkan</p>
            </div>

            <div v-else class="space-y-3 max-h-[400px] overflow-y-auto pr-1">
              <div v-for="(item, index) in batch" :key="index" class="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center space-x-2">
                    <span class="w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-xs font-bold">
                      {{ index + 1 }}
                    </span>
                    <p class="font-medium text-gray-800">{{ item.nama_peserta || 'Belum diisi' }}</p>
                  </div>
                  <div class="flex items-center space-x-2">
                    <span class="badge-warning text-xs">menunggu</span>
                    <span v-if="isItemComplete(item)" class="text-green-500 text-xs">✅</span>
                    <span v-else class="text-red-500 text-xs">⚠️</span>
                  </div>
                </div>

                <div class="text-xs text-gray-500 space-y-1 ml-8">
                  <div><span class="font-medium">Kegiatan:</span> {{ item.nama_kegiatan || '-' }}</div>
                  <div><span class="font-medium">Lokasi:</span> {{ item.nama_lokasi || '-' }}</div>
                  <div><span class="font-medium">Koordinat:</span> {{ item.latitude || '0' }}, {{ item.longitude || '0' }}</div>
                </div>

                <div class="flex items-center justify-end space-x-3 mt-3 pt-3 border-t border-gray-200">
                  <button @click="editBatch(index)" class="text-blue-600 hover:text-blue-800 text-sm font-medium">✏️ edit</button>
                  <button @click="removeFromBatch(index)" class="text-red-500 hover:text-red-700 text-sm font-medium">🗑 hapus</button>
                </div>
              </div>
            </div>

            <div v-if="batch.length > 0" class="mt-3 p-2 rounded-lg text-sm"
                 :class="isBatchComplete ? 'bg-green-100 border border-green-300 text-green-700' : 'bg-yellow-100 border border-yellow-300 text-yellow-700'">
              <div class="flex items-center justify-between">
                <span>
                  {{ isBatchComplete ? '✅ Semua data lengkap!' : '⚠️ ' + incompleteCount + ' data belum lengkap' }}
                </span>
                <span class="text-xs font-medium">{{ batch.length }} sertifikat</span>
              </div>
            </div>

            <button 
              @click="publishBatch" 
              :disabled="batch.length === 0 || publishing || !isConnected || !isBatchComplete" 
              class="w-full btn-success py-3 mt-4 disabled:opacity-50 disabled:cursor-not-allowed text-lg font-semibold"
            >
              {{ publishing ? '⏳ Menerbitkan...' : 'Terbitkan Batch' }}
            </button>

            <div v-if="publishResult" class="mt-3 p-3 rounded-lg" 
                 :class="publishResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'">
              <p class="text-sm" :class="publishResult.success ? 'text-green-700' : 'text-red-700'">
                {{ publishResult.message }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Modal Edit -->
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

      <!-- ============================================ -->
      <!-- 🟢 MODAL QR CODE (TAMBAHAN BARU)              -->
      <!-- ============================================ -->
      <div v-if="showQRModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
        <div class="bg-white rounded-xl p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold text-gray-800">📱 QR Code Sertifikat</h3>
            <button @click="closeQRModal" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <div v-if="selectedQR" class="text-center">
            <img :src="selectedQR.qr_code" alt="QR Code Sertifikat" class="mx-auto w-64 h-64" />
            <p class="mt-2 text-sm text-gray-600 break-all">🔗 {{ selectedQR.verify_url }}</p>
            <p class="text-xs text-gray-400 mt-1">Scan QR Code untuk verifikasi sertifikat</p>
            
            <!-- Jika ada banyak QR, tampilkan daftar -->
            <div v-if="qrCodes.length > 1" class="mt-4 flex flex-wrap gap-2 justify-center">
              <button 
                v-for="(qr, idx) in qrCodes" 
                :key="idx"
                @click="selectedQR = qr"
                class="px-3 py-1 text-xs rounded-full border"
                :class="selectedQR === qr ? 'bg-blue-600 text-white border-blue-600' : 'bg-gray-100 border-gray-300'"
              >
                Sertifikat {{ idx + 1 }}
              </button>
            </div>
          </div>

          <div class="flex justify-end mt-4">
            <button @click="closeQRModal" class="btn-secondary px-6 py-2">Tutup</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { useContract } from '../composables/useContract'
import api from '../services/api'

const router = useRouter()
const authStore = useAuthStore()
const contract = useContract()

// MetaMask
const isConnected = contract.isConnected
const walletAddress = contract.walletAddress

const connectWallet = async () => {
  await contract.connectWallet()
}

// Form
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

const batch = ref([])
const loading = ref(false)
const publishing = ref(false)
const loadingLocation = ref(false)
const locationStatus = ref(null)
const publishResult = ref(null)

// 🔥 QR Code state (TAMBAHAN BARU)
const qrCodes = ref([])              // Array untuk menyimpan QR Code
const showQRModal = ref(false)       // Control modal QR
const selectedQR = ref(null)         // QR yang sedang dilihat

// Computed
const isBatchComplete = computed(() => {
  if (batch.value.length === 0) return false
  return batch.value.every(item => 
    item.nama_peserta && item.nama_kegiatan && item.nama_lokasi && 
    item.latitude && item.longitude && item.waktu_mulai && item.waktu_selesai
  )
})

const incompleteCount = computed(() => {
  return batch.value.filter(item => 
    !item.nama_peserta || !item.nama_kegiatan || !item.nama_lokasi || 
    !item.latitude || !item.longitude || !item.waktu_mulai || !item.waktu_selesai
  ).length
})

const isItemComplete = (item) => {
  return item.nama_peserta && item.nama_kegiatan && item.nama_lokasi && 
         item.latitude && item.longitude && item.waktu_mulai && item.waktu_selesai
}

// LocalStorage
const saveToLocalStorage = () => {
  try {
    localStorage.setItem('batch_data', JSON.stringify(batch.value))
    console.log('💾 Data disimpan ke localStorage:', batch.value.length, 'data')
  } catch (e) {
    console.error('Gagal simpan ke localStorage:', e)
  }
}

const loadFromLocalStorage = () => {
  try {
    const saved = localStorage.getItem('batch_data')
    if (saved) {
      const parsed = JSON.parse(saved)
      if (Array.isArray(parsed) && parsed.length > 0) {
        batch.value = parsed
        console.log('📥 Data dimuat dari localStorage:', parsed.length, 'data')
      }
    }
  } catch (e) {
    console.error('Gagal load dari localStorage:', e)
  }
}

watch(batch, () => {
  saveToLocalStorage()
}, { deep: true })

// Edit Modal
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

// ============================================
// AMBIL LOKASI GPS
// ============================================
const getCurrentLocation = () => {
  if (!navigator.geolocation) {
    locationStatus.value = { type: 'error', message: '❌ Browser tidak mendukung geolokasi' }
    return
  }
  
  loadingLocation.value = true
  locationStatus.value = { type: 'loading', message: '⏳ Mengambil lokasi...' }
  
  navigator.geolocation.getCurrentPosition(
    (position) => {
      form.latitude = position.coords.latitude.toFixed(7)
      form.longitude = position.coords.longitude.toFixed(7)
      loadingLocation.value = false
      locationStatus.value = { type: 'success', message: '✅ Lokasi berhasil diambil' }
      setTimeout(() => { locationStatus.value = null }, 3000)
    },
    (error) => {
      loadingLocation.value = false
      locationStatus.value = { type: 'error', message: '❌ Gagal mengambil lokasi: ' + error.message }
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
  )
}

// ============================================
// FUNGSI BATCH
// ============================================
const addToBatch = () => {
  console.log('📝 Menambahkan ke batch...', form)

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

  const newData = { ...form }
  batch.value.push(newData)
  
  form.nama_kegiatan = ''
  form.nama_lokasi = ''
  form.latitude = ''
  form.longitude = ''
  form.waktu_mulai = ''
  form.waktu_selesai = ''
  form.nama_peserta = ''
  form.keterangan = ''
  locationStatus.value = null

  alert(`✅ "${newData.nama_peserta}" berhasil ditambahkan ke antrean! (${batch.value.length} data)`)
}

const removeFromBatch = (index) => {
  if (confirm(`Hapus data "${batch.value[index].nama_peserta}" dari antrean?`)) {
    batch.value.splice(index, 1)
  }
}

// ============================================
// FUNGSI EDIT
// ============================================
const editBatch = (index) => {
  const item = batch.value[index]
  editModal.value.show = true
  editModal.value.index = index
  Object.keys(editForm).forEach(key => {
    editForm[key] = item[key] || ''
  })
}

const saveEdit = () => {
  const index = editModal.value.index
  batch.value[index] = { ...editForm }
  closeEditModal()
}

const closeEditModal = () => {
  editModal.value.show = false
  editModal.value.index = null
}

// ============================================
// 🔥 GENERATE QR CODE (FUNGSI BARU)
// ============================================
const generateQRForSertifikat = async (publicId, index) => {
  try {
    const response = await fetch(`/api/sertifikat/generate-qr/${publicId}`)
    const data = await response.json()
    
    if (data.success) {
      qrCodes.value[index] = {
        public_id: publicId,
        qr_code: data.qr_code,
        verify_url: data.verify_url
      }
    } else {
      console.error('Gagal generate QR:', data.error)
    }
  } catch (error) {
    console.error('Error fetch QR:', error)
  }
}

const closeQRModal = () => {
  showQRModal.value = false
  selectedQR.value = null
}

// ============================================
// TERBITKAN BATCH (REVISI: TAMBAHKAN GENERATE QR)
// ============================================
const publishBatch = async () => {
  if (batch.value.length === 0) {
    alert('❌ Antrean kosong!')
    return
  }

  // CEK KELENGKAPAN DATA
  const incompleteData = batch.value.filter(item => 
    !item.nama_peserta || !item.nama_kegiatan || !item.nama_lokasi || 
    !item.latitude || !item.longitude || !item.waktu_mulai || !item.waktu_selesai
  )

  if (incompleteData.length > 0) {
    alert(`⚠️ Ada ${incompleteData.length} data yang belum lengkap!`)
    return
  }

  // CEK METAMASK
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
  publishResult.value = null

  try {
    const user = authStore.user
    const penerbitId = user?.id || 3

    console.log('📤 ====== MENERBITKAN BATCH ======')
    console.log('📤 Data batch:', batch.value)
    console.log('📤 Penerbit ID:', penerbitId)

    // STEP 1: Kirim ke backend untuk prepare
    const prepareResponse = await api.post('/sertifikat/prepare', {
      sertifikat_list: batch.value,
      penerbit_id: penerbitId
    })

    console.log('✅ Prepare response:', prepareResponse.data)

    // STEP 2: Ambil data hasil prepare
    const allData = prepareResponse.data.data || []
    const merkleRoot = prepareResponse.data.merkle_root

    if (!merkleRoot) {
      throw new Error('Merkle Root tidak ditemukan dari backend!')
    }

    // STEP 3: Buat batchId
    const batchIdOnchain = Date.now()

    console.log('🌳 Merkle Root dari backend:', merkleRoot)

    // STEP 4: Ambil public_id dari data pertama
    const publicId = allData.length > 0 ? allData[0].public_id : null
    if (!publicId) {
      throw new Error('Public ID tidak ditemukan dari backend!')
    }

    console.log('🆔 Public ID (UUID):', publicId)

    // STEP 5: Simpan ke Blockchain via MetaMask
    publishResult.value = {
      success: true,
      message: '⏳ Menunggu konfirmasi transaksi di MetaMask...'
    }

    const txSuccess = await contract.simpanRoot(batchIdOnchain, merkleRoot, publicId)
    
    if (!txSuccess) {
      throw new Error('Gagal simpan root di blockchain: ' + contract.error.value)
    }

    // STEP 6: Konfirmasi ke backend (update status jadi published)
    const confirmResponse = await api.post('/sertifikat/konfirmasi', {
      merkle_root: merkleRoot,
      tx_hash: contract.txHash.value,
      batch_id_onchain: batchIdOnchain,
      sertifikat_list: allData.map(item => ({
        public_id: item.public_id,
        proof: []
      }))
    })

    console.log('✅ Confirm response:', confirmResponse.data)

    publishResult.value = {
      success: true,
      message: `✅ ${allData.length} sertifikat berhasil diterbitkan!\n🔗 TX: ${contract.txHash.value.slice(0, 10)}...`
    }

    // ============================================
    // GENERATE QR CODE UNTUK SETIAP SERTIFIKAT
    // ============================================
    qrCodes.value = [] // Reset
    for (let i = 0; i < allData.length; i++) {
      const item = allData[i]
      if (item.public_id) {
        await generateQRForSertifikat(item.public_id, i)
      }
    }
    // Tampilkan modal QR setelah semua selesai
    if (qrCodes.value.length > 0) {
      selectedQR.value = qrCodes.value[0]
      showQRModal.value = true
    }

    // KOSONGKAN ANTREAN DAN LOCALSTORAGE
    batch.value = []
    localStorage.removeItem('batch_data')

  } catch (error) {
    console.error('❌ ====== ERROR ======')
    console.error('❌ Error:', error)
    
    let errorMessage = error.message || 'Terjadi kesalahan'
    if (error.response?.data?.error) {
      errorMessage = error.response.data.error
    } else if (error.code === 'ACTION_REJECTED' || error.code === 4001) {
      errorMessage = 'Transaksi dibatalkan di MetaMask'
    } else if (error.message?.includes('insufficient funds')) {
      errorMessage = 'Saldo ETH tidak cukup untuk gas fee!'
    }
    
    publishResult.value = {
      success: false,
      message: '❌ Gagal: ' + errorMessage
    }
  }

  publishing.value = false
}

// ============================================
// LOGOUT
// ============================================
const logout = () => {
  authStore.logout()
  router.push('/')
}

// ============================================
// MOUNTED - LOAD DARI LOCALSTORAGE
// ============================================
onMounted(() => {
  loadFromLocalStorage()
})
</script>