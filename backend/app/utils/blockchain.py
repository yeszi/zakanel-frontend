from web3 import Web3
import json
import os

# ABI minimal untuk fungsi yang kita pakai
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "_batchId", "type": "uint256"},
            {"internalType": "bytes32", "name": "_merkleRoot", "type": "bytes32"}
        ],
        "name": "simpanRoot",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "_wallet", "type": "address"}],
        "name": "isPenerbitActive",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def simpan_root_ke_blockchain(w3: Web3, contract_address: str, private_key: str, batch_id: int, merkle_root_hex: str):
    """
    Mengirim transaksi simpanRoot(batchId, merkleRoot) ke Smart Contract.
    merkle_root_hex: string hash SHA-256 (64 karakter hex, tanpa 0x)
    """
    contract = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=CONTRACT_ABI)

    account = w3.eth.account.from_key(private_key)
    wallet_address = account.address

    # Konversi merkle root (hex string) ke bytes32
    merkle_root_bytes32 = bytes.fromhex(merkle_root_hex)

    nonce = w3.eth.get_transaction_count(wallet_address)

    txn = contract.functions.simpanRoot(batch_id, merkle_root_bytes32).build_transaction({
        'chainId': w3.eth.chain_id,
        'gas': 200000,
        'gasPrice': w3.eth.gas_price,
        'nonce': nonce,
    })

    signed_txn = w3.eth.account.sign_transaction(txn, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return tx_hash.hex(), tx_receipt.status