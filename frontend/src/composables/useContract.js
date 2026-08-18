// src/composables/useContract.js
import { ref } from 'vue'
import { ethers } from 'ethers'

const CONTRACT_ADDRESS = import.meta.env.VITE_CONTRACT_ADDRESS || '0xB6ef2Cb1b0740d5082786B5d37196c1609714B78'
const RPC_URL = import.meta.env.VITE_RPC_URL || 'https://ethereum-sepolia-rpc.publicnode.com'

const CONTRACT_ABI = [
  {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
  {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"wallet","type":"address"}],"name":"PenerbitDicabut","type":"event"},
  {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"wallet","type":"address"}],"name":"PenerbitDitambahkan","type":"event"},
  {"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"batchId","type":"uint256"},{"indexed":false,"internalType":"bytes32","name":"merkleRoot","type":"bytes32"}],"name":"RootDisimpan","type":"event"},
  {"anonymous":false,"inputs":[{"indexed":true,"internalType":"bytes32","name":"publicId","type":"bytes32"},{"indexed":false,"internalType":"uint256","name":"batchId","type":"uint256"}],"name":"PublicIdTerdaftar","type":"event"},
  {"inputs":[],"name":"admin","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"_wallet","type":"address"}],"name":"cabutPenerbit","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"internalType":"bytes32","name":"_publicId","type":"bytes32"}],"name":"getBatchIdByPublicId","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"_batchId","type":"uint256"}],"name":"getRoot","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"_wallet","type":"address"}],"name":"isPenerbitActive","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"merkleRoots","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"penerbitAktif","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"publicIdToBatchId","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"_batchId","type":"uint256"},{"internalType":"bytes32","name":"_merkleRoot","type":"bytes32"}],"name":"simpanRoot","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"internalType":"uint256","name":"_batchId","type":"uint256"},{"internalType":"bytes32","name":"_merkleRoot","type":"bytes32"},{"internalType":"bytes32","name":"_publicId","type":"bytes32"}],"name":"simpanRoot","outputs":[],"stateMutability":"nonpayable","type":"function"},
  
  // 👇 REVISI: Penambahan ABI untuk tambahPenerbit dan verifyCertificate 👇
  {"inputs":[{"internalType":"address","name":"_wallet","type":"address"}],"name":"tambahPenerbit","outputs":[],"stateMutability":"nonpayable","type":"function"},
  {"inputs":[{"internalType":"bytes32","name":"_publicId","type":"bytes32"},{"internalType":"bytes32","name":"_merkleRoot","type":"bytes32"}],"name":"verifyCertificate","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"}
]

export function useContract() {
  const isConnected = ref(false)
  const walletAddress = ref('')
  const error = ref('')
  const loading = ref(false)
  const txHash = ref('')

  const connectWallet = async () => {
    if (!window.ethereum) {
      error.value = 'MetaMask tidak terdeteksi!'
      return false
    }
    try {
      const provider = new ethers.BrowserProvider(window.ethereum)
      const signer = await provider.getSigner()
      walletAddress.value = await signer.getAddress()
      isConnected.value = true
      error.value = ''
      return true
    } catch (err) {
      error.value = err.message
      return false
    }
  }

  const tambahPenerbit = async (wallet) => {
    loading.value = true
    error.value = ''
    txHash.value = ''
    try {
      if (!window.ethereum) {
        error.value = 'MetaMask tidak terdeteksi!'
        loading.value = false
        return false
      }
      const provider = new ethers.BrowserProvider(window.ethereum)
      const signer = await provider.getSigner()
      const contract = new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, signer)
      const checksumWallet = ethers.getAddress(wallet)
      const tx = await contract.tambahPenerbit(checksumWallet)
      const receipt = await tx.wait()
      txHash.value = tx.hash
      loading.value = false
      return receipt.status === 1
    } catch (err) {
      error.value = err.message || 'Gagal tambah penerbit'
      loading.value = false
      return false
    }
  }

  const cabutPenerbit = async (wallet) => {
    loading.value = true
    error.value = ''
    txHash.value = ''
    try {
      if (!window.ethereum) {
        error.value = 'MetaMask tidak terdeteksi!'
        loading.value = false
        return false
      }
      const provider = new ethers.BrowserProvider(window.ethereum)
      const signer = await provider.getSigner()
      const contract = new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, signer)
      const checksumWallet = ethers.getAddress(wallet)
      const tx = await contract.cabutPenerbit(checksumWallet)
      const receipt = await tx.wait()
      txHash.value = tx.hash
      loading.value = false
      return receipt.status === 1
    } catch (err) {
      error.value = err.message || 'Gagal cabut penerbit'
      loading.value = false
      return false
    }
  }

  const cekStatusPenerbit = async (wallet) => {
    try {
      const provider = new ethers.BrowserProvider(window.ethereum)
      const contract = new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, provider)
      const isActive = await contract.isPenerbitActive(wallet)
      return isActive
    } catch (err) {
      return false
    }
  }

  // 🔥🔥🔥 FUNGSI SIMPAN ROOT YANG DIPERBAIKI DENGAN LOG LENGKAP 🔥🔥🔥
  const simpanRoot = async (batchId, merkleRoot, publicId) => {
    loading.value = true
    error.value = ''
    txHash.value = ''

    try {
      if (!window.ethereum) {
        error.value = 'MetaMask tidak terdeteksi!'
        loading.value = false
        return false
      }

      console.log('🔄 Memulai transaksi simpanRoot...')
      console.log('📝 batchId:', batchId)
      console.log('📝 merkleRoot:', merkleRoot)
      console.log('📝 publicId (raw):', publicId)

      const provider = new ethers.BrowserProvider(window.ethereum)
      const signer = await provider.getSigner()
      const contract = new ethers.Contract(CONTRACT_ADDRESS, CONTRACT_ABI, signer)

      // 🔥 Konversi publicId ke bytes32
      let cleanPublicId = publicId
      if (cleanPublicId.includes('-')) {
        cleanPublicId = cleanPublicId.replace(/-/g, '')
      }
      // Pastikan panjang hex string genap
      if (cleanPublicId.length % 2 !== 0) {
        cleanPublicId = '0' + cleanPublicId
      }
      const publicIdBytes = ethers.getBytes('0x' + cleanPublicId)
      const publicIdBytes32 = ethers.zeroPadValue(publicIdBytes, 32)

      console.log('🆔 Public ID (hex):', cleanPublicId)
      console.log('🆔 Public ID (bytes32):', publicIdBytes32)

      // Panggil fungsi kontrak dengan overload yang benar
      const tx = await contract['simpanRoot(uint256,bytes32,bytes32)'](
        batchId,
        merkleRoot,
        publicIdBytes32
      )

      console.log('⏳ Menunggu konfirmasi transaksi...')
      const receipt = await tx.wait()

      txHash.value = tx.hash
      loading.value = false
      console.log(`✅ Root disimpan! TX: ${tx.hash}`)
      return receipt.status === 1

    } catch (err) {
      console.error('❌ Error simpan root:', err)
      if (err.code === 'ACTION_REJECTED' || err.code === 4001) {
        error.value = 'Transaksi dibatalkan di MetaMask'
      } else if (err.message?.includes('insufficient funds')) {
        error.value = 'Saldo ETH tidak cukup untuk gas fee!'
      } else {
        error.value = err.message || 'Gagal simpan root'
      }
      loading.value = false
      return false
    }
  }

  return {
    isConnected,
    walletAddress,
    error,
    loading,
    txHash,
    connectWallet,
    tambahPenerbit,
    cabutPenerbit,
    cekStatusPenerbit,
    simpanRoot
  }
}