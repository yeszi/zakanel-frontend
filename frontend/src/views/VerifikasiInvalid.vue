<template>
  <div class="min-h-screen bg-gradient-to-br from-red-50 to-gray-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl shadow-xl w-full max-w-lg p-8">
      
      <!-- LOADING -->
      <div v-if="loading" class="text-center py-8">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p class="text-gray-500 mt-4">Memverifikasi sertifikat...</p>
      </div>

      <!-- HASIL TIDAK VALID -->
      <div v-else>
        <div class="text-center">
          <div class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg class="w-12 h-12 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </div>

          <h1 class="text-2xl font-bold text-red-600 mb-2">❌ Sertifikat Tidak Valid</h1>
          <p class="text-gray-600 mb-2">{{ errorMessage || 'Sertifikat Gagal Terverifikasi' }}</p>
          <p class="text-sm text-gray-500 mb-6">Sertifikat ini tidak tercatat di blockchain atau telah dimodifikasi</p>
        </div>

        <!-- Detail Sertifikat (jika ada) -->
        <div v-if="certData" class="bg-gray-50 rounded-xl p-4 space-y-2">
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-sm text-gray-500">ID Sertifikat</span>
            <span class="text-sm font-medium text-gray-800">{{ certData.public_id || '-' }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="text-sm text-gray-500">Nama Peserta</span>
            <span class="text-sm font-medium text-gray-800">{{ certData.nama_peserta || '-' }}</span>
          </div>
          <div class="flex justify-between py-2">
            <span class="text-sm text-gray-500">Nama Kegiatan</span>
            <span class="text-sm font-medium text-gray-800">{{ certData.nama_kegiatan || '-' }}</span>
          </div>
        </div>

        <!-- Pesan Error -->
        <div class="bg-red-50 border border-red-200 rounded-xl p-4 text-center mt-4">
          <p class="text-sm text-red-700">
            ⚠️ Sertifikat tidak ditemukan atau belum terdaftar di blockchain.<br>
            Hubungi penerbit untuk informasi lebih lanjut.
          </p>
        </div>

        <button @click="goHome" class="w-full btn-primary py-3 mt-6">Kembali ke Beranda</button>
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
  
  console.log('🔍 Invalid Public ID:', publicId)
  
  if (publicId) {
    try {
      const response = await api.get(`/sertifikat/verify/${publicId}`)
      if (response.data) {
        certData.value = response.data
        errorMessage.value = response.data.message || 'Sertifikat tidak valid'
      }
    } catch (err) {
      console.error('❌ Error:', err)
      errorMessage.value = err.response?.data?.message || 'Sertifikat tidak ditemukan di sistem'
    }
  } else {
    errorMessage.value = 'ID Sertifikat tidak ditemukan'
  }
  
  loading.value = false
})

const goHome = () => {
  router.push('/')
}
</script>