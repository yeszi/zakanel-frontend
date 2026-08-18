<template>
  <div class="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg p-8">
      
      <!-- LOADING -->
      <div v-if="loading" class="text-center py-8">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p class="text-gray-500 mt-4">Memverifikasi sertifikat...</p>
      </div>

      <!-- HASIL VERIFIKASI VALID -->
      <div v-else-if="certData && certData.valid === true">
        <div class="text-center">
          <div class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-12 h-12 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-green-600 mb-2">✅ Sertifikat Valid</h1>
          <p class="text-gray-600 mb-2">Sertifikat Terverifikasi di Blockchain</p>
          <p class="text-sm text-gray-500 mb-6">Sertifikat ini sah dan tercatat di blockchain</p>
        </div>

        <!-- DATA SERTIFIKAT -->
        <div class="bg-gray-50 rounded-xl p-4 space-y-3">
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-sm text-gray-500">Nama Peserta</span>
            <span class="text-sm font-medium text-gray-800">{{ certData.nama_peserta || '-' }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-sm text-gray-500">Nama Kegiatan</span>
            <span class="text-sm font-medium text-gray-800">{{ certData.nama_kegiatan || '-' }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-sm text-gray-500">Lokasi</span>
            <span class="text-sm font-medium text-gray-800">{{ certData.nama_lokasi || '-' }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-sm text-gray-500">Waktu Mulai</span>
            <span class="text-sm font-medium text-gray-800">{{ formatDate(certData.waktu_mulai) || '-' }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-sm text-gray-500">Waktu Selesai</span>
            <span class="text-sm font-medium text-gray-800">{{ formatDate(certData.waktu_selesai) || '-' }}</span>
          </div>
          <div class="flex justify-between py-2">
            <span class="text-sm text-gray-500">Tanggal Terbit</span>
            <span class="text-sm font-medium text-gray-800">{{ formatDate(certData.created_at) || '-' }}</span>
          </div>
        </div>

        <div class="mt-4 p-3 bg-green-50 rounded-lg border border-green-200 text-center">
          <p class="text-sm text-green-700 font-medium">✅ Sertifikat ini telah diverifikasi dan tercatat di blockchain</p>
        </div>

        <button @click="goHome" class="w-full btn-primary py-3 mt-6">Kembali ke Beranda</button>
      </div>

      <!-- TIDAK VALID -->
      <div v-else-if="certData && certData.valid === false">
        <div class="text-center">
          <div class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-12 h-12 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-red-600 mb-2">❌ Sertifikat Tidak Valid</h1>
          <p class="text-gray-600">{{ certData.message || 'Sertifikat tidak ditemukan' }}</p>
          <button @click="goHome" class="w-full btn-primary py-3 mt-6">Kembali</button>
        </div>
      </div>

      <!-- ERROR -->
      <div v-else>
        <div class="text-center">
          <div class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-12 h-12 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </div>
          <h1 class="text-2xl font-bold text-red-600 mb-2">❌ Error</h1>
          <p class="text-gray-600">{{ errorMessage || 'Terjadi kesalahan' }}</p>
          <button @click="goHome" class="w-full btn-primary py-3 mt-6">Kembali</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../services/api'

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const certData = ref(null)
const errorMessage = ref('')

onMounted(async () => {
  const publicId = route.query.id
  
  console.log('🔍 Public ID:', publicId)
  
  if (!publicId) {
    errorMessage.value = 'ID Sertifikat tidak ditemukan'
    loading.value = false
    return
  }

  try {
    const response = await api.get(`/sertifikat/verify/${publicId}`)
    console.log('✅ Response:', response.data)
    certData.value = response.data
  } catch (err) {
    console.error('❌ Error:', err)
    errorMessage.value = err.response?.data?.message || 'Gagal memverifikasi'
  } finally {
    loading.value = false
  }
})

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

const goHome = () => {
  router.push('/')
}
</script>