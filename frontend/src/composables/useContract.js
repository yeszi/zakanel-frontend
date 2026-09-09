import { ref } from 'vue'
import Web3 from 'web3'

const CONTRACT_ABI = [
  {"inputs": [], "stateMutability": "nonpayable", "type": "constructor"},
  {"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "wallet", "type": "address"}], "name": "PenerbitDicabut", "type": "event"},
  {"anonymous": false, "inputs": [{"indexed": true, "internalType": "address", "name": "wallet", "type": "address"}], "name": "PenerbitDitambahkan", "type": "event"},
  {"anonymous": false, "inputs": [{"indexed": true, "internalType": "uint256", "name": "batchId", "type": "uint256"}, {"indexed": false, "internalType": "bytes32", "name": "merkleRoot", "type": "bytes32"}], "name": "RootDisimpan", "type": "event"},
  {"anonymous": false, "inputs": [{"indexed": true, "internalType": "bytes32", "name": "publicId", "type": "bytes32"}, {"indexed": false, "internalType": "uint256", "name": "batchId", "type": "uint256"}], "name": "PublicIdTerdaftar", "type": "event"},
  {"inputs": [], "name": "admin", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
  {"inputs": [{"internalType": "address", "name": "_wallet", "type": "address"}], "name": "cabutPenerbit", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
  {"inputs": [{"internalType": "bytes32", "name": "_publicId", "type": "bytes32"}], "name": "getBatchIdByPublicId", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
  {"inputs": [{"internalType": "uint256", "name": "_batchId", "type": "uint256"}], "name": "getRoot", "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}], "stateMutability": "view", "type": "function"},
  {"inputs": [{"internalType": "address", "name": "_wallet", "type": "address"}], "name": "isPenerbitActive", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
  {"inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "name": "merkleRoots", "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}], "stateMutability": "view", "type": "function"},
  {"inputs": [{"internalType": "address", "name": "", "type": "address"}], "name": "penerbitAktif", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
  {"inputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}], "name": "publicIdToBatchId", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
  {"inputs": [{"internalType": "uint256", "name": "_batchId", "type": "uint256"}, {"internalType": "bytes32", "name": "_merkleRoot", "type": "bytes32"}, {"internalType": "bytes32", "name": "_publicId", "type": "bytes32"}], "name": "simpanRoot", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
  {"inputs": [{"internalType": "address", "name": "_wallet", "type": "address"}], "name": "tambahPenerbit", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
]

export function useContract() {
  const web3 = ref(null)
  const contract = ref(null)
  const walletAddress = ref('')
  const isConnected = ref(false)
  const txHash = ref('')
  const error = ref('')

  const connectWallet = async () => {
    if (!window.ethereum) {
      error.value = 'MetaMask tidak terdeteksi!'
      return false
    }
    try {
      await window.ethereum.request({ method: 'eth_requestAccounts' })
      web3.value = new Web3(window.ethereum)
      const accounts = await web3.value.eth.getAccounts()
      walletAddress.value = accounts[0]
      isConnected.value = true

      const contractAddress = import.meta.env.VITE_CONTRACT_ADDRESS
      contract.value = new web3.value.eth.Contract(CONTRACT_ABI, contractAddress)
      return true
    } catch (err) {
      error.value = err.message
      return false
    }
  }

  const tambahPenerbit = async (wallet) => {
    try {
      const tx = await contract.value.methods.tambahPenerbit(wallet).send({
        from: walletAddress.value
      })
      txHash.value = tx.transactionHash
      return true
    } catch (err) {
      error.value = err.message
      return false
    }
  }

  const cabutPenerbit = async (wallet) => {
    try {
      const tx = await contract.value.methods.cabutPenerbit(wallet).send({
        from: walletAddress.value
      })
      txHash.value = tx.transactionHash
      return true
    } catch (err) {
      error.value = err.message
      return false
    }
  }

  const simpanRoot = async (batchId, merkleRoot, publicId) => {
    try {
      // 🔥 Konversi publicId ke bytes32 tanpa Buffer
      const encoder = new TextEncoder()
      const bytes = encoder.encode(publicId)
      const padded = new Uint8Array(32)
      padded.set(bytes.slice(0, 32))

      // Ubah Uint8Array ke hex string (manual)
      let hex = ''
      for (const byte of padded) {
        hex += byte.toString(16).padStart(2, '0')
      }
      const publicIdBytes = '0x' + hex

      console.log('📤 simpanRoot params:', {
        batchId,
        merkleRoot,
        publicId,
        publicIdBytes
      })

      const tx = await contract.value.methods.simpanRoot(batchId, merkleRoot, publicIdBytes).send({
        from: walletAddress.value
      })
      txHash.value = tx.transactionHash
      return true
    } catch (err) {
      error.value = err.message
      console.error('❌ simpanRoot error:', err)
      return false
    }
  }

  const cekStatusPenerbit = async (wallet) => {
    try {
      return await contract.value.methods.isPenerbitActive(wallet).call()
    } catch (err) {
      return false
    }
  }

  return {
    connectWallet,
    tambahPenerbit,
    cabutPenerbit,
    simpanRoot,
    cekStatusPenerbit,
    walletAddress,
    isConnected,
    txHash,
    error
  }
}