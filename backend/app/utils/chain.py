"""
Helper interaksi dengan smart contract SertifikatVerifikasi.
Backend TIDAK memegang private key: semua transaksi ditandatangani di MetaMask,
backend hanya MEMBACA blockchain untuk memvalidasi transaksi tersebut.
"""
from flask import current_app
from web3 import Web3
from web3.logs import DISCARD

CONTRACT_ABI = [
  {"inputs": [], "stateMutability": "nonpayable", "type": "constructor"},
  {"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "wallet", "type": "address"}], "name": "PenerbitDicabut", "type": "event"},
  {"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "wallet", "type": "address"}], "name": "PenerbitDitambahkan", "type": "event"},
  {"anonymous": False, "inputs": [{"indexed": True, "internalType": "uint256", "name": "batchId", "type": "uint256"}, {"indexed": False, "internalType": "bytes32", "name": "merkleRoot", "type": "bytes32"}], "name": "RootDisimpan", "type": "event"},
  {"anonymous": False, "inputs": [{"indexed": True, "internalType": "bytes32", "name": "publicId", "type": "bytes32"}, {"indexed": False, "internalType": "uint256", "name": "batchId", "type": "uint256"}], "name": "PublicIdTerdaftar", "type": "event"},
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


def get_contract():
    w3 = current_app.w3
    return w3, w3.eth.contract(address=current_app.contract_address, abi=CONTRACT_ABI)


def is_valid_address(addr) -> bool:
    return isinstance(addr, str) and Web3.is_address(addr)


def same_address(a, b) -> bool:
    return bool(a) and bool(b) and a.lower() == b.lower()


def is_penerbit_active_onchain(wallet) -> bool:
    _, contract = get_contract()
    return contract.functions.isPenerbitActive(Web3.to_checksum_address(wallet)).call()


def _get_receipt(tx_hash):
    w3, contract = get_contract()
    if not isinstance(tx_hash, str) or not tx_hash.startswith('0x') or len(tx_hash) != 66:
        return None, None, 'Format tx_hash tidak valid.'
    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
    except Exception:
        return None, None, 'Transaksi tidak ditemukan di jaringan (tx_hash tidak valid atau belum ter-mining).'
    if receipt is None:
        return None, None, 'Transaksi belum ter-mining.'
    if receipt.status != 1:
        return None, None, 'Transaksi gagal (revert) di blockchain.'
    if receipt.to is None or not same_address(receipt.to, current_app.contract_address):
        return None, None, 'Transaksi tidak ditujukan ke smart contract yang benar.'
    return receipt, contract, None


def verify_root_tx(tx_hash, expected_batch_id, expected_merkle_root, expected_sender):
    """Validasi transaksi simpanRoot: sukses, ke kontrak yang benar, dikirim oleh wallet penerbit, event cocok."""
    receipt, contract, err = _get_receipt(tx_hash)
    if err:
        return False, err
    if not same_address(receipt['from'], expected_sender):
        return False, 'Transaksi tidak dikirim oleh wallet penerbit yang sedang login.'
    events = contract.events.RootDisimpan().process_receipt(receipt, errors=DISCARD)
    if not events:
        return False, 'Transaksi tidak mengandung event RootDisimpan.'
    for ev in events:
        root_hex = '0x' + ev['args']['merkleRoot'].hex().removeprefix('0x')
        if int(ev['args']['batchId']) == int(expected_batch_id) and root_hex.lower() == expected_merkle_root.lower():
            return True, None
    return False, 'batch_id/merkle_root pada event on-chain tidak cocok dengan data yang dikirim.'


def verify_penerbit_tx(tx_hash, event_name, expected_wallet):
    """
    Validasi transaksi tambahPenerbit / cabutPenerbit:
    - dikirim oleh admin kontrak (fungsi admin() di smart contract)
    - mengandung event PenerbitDitambahkan / PenerbitDicabut untuk wallet yang dimaksud
    """
    receipt, contract, err = _get_receipt(tx_hash)
    if err:
        return False, err
    onchain_admin = contract.functions.admin().call()
    if not same_address(receipt['from'], onchain_admin):
        return False, 'Transaksi tidak dikirim oleh wallet admin smart contract.'
    events = getattr(contract.events, event_name)().process_receipt(receipt, errors=DISCARD)
    for ev in events:
        if same_address(ev['args']['wallet'], expected_wallet):
            return True, None
    return False, f'Transaksi tidak mengandung event {event_name} untuk wallet {expected_wallet}.'
