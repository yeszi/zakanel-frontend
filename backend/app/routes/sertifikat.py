from flask import Blueprint, request, jsonify, current_app
from flask_cors import CORS
from datetime import datetime
import json
import hashlib
import secrets
import bcrypt
import os
import qrcode
import io
import base64
from web3 import Web3  

# CONTRACT ABI
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

sertifikat_bp = Blueprint('sertifikat', __name__, url_prefix='/api')

def fmt_coord(val):
    try:
        f = float(val)
        s = f"{f:.7f}".rstrip('0').rstrip('.')
        return s
    except:
        return str(val)

# ===== GET ALL SERTIFIKAT =====
@sertifikat_bp.route('/sertifikat', methods=['GET'])
def get_all_sertifikat():
    try:
        supabase = current_app.supabase
        user_id = request.headers.get('X-User-ID')
        user_role = request.headers.get('X-User-Role')

        if user_role == 'admin':
            response = supabase.table('sertifikat').select('*').order('created_at', desc=True).execute()
        else:
            if user_id:
                response = supabase.table('sertifikat').select('*').eq('penerbit_id', int(user_id)).order('created_at', desc=True).execute()
            else:
                return jsonify({'success': True, 'sertifikat': []})

        result = []
        for s in response.data:
            result.append({
                'id': s.get('id'),
                'public_id': s.get('public_id'),
                'batch_id': s.get('batch_id'),
                'nama_peserta': s.get('nama_peserta'),
                'nama_kegiatan': s.get('nama_kegiatan'),
                'nama_lokasi': s.get('nama_lokasi'),
                'latitude': s.get('latitude'),
                'longitude': s.get('longitude'),
                'waktu_mulai': s.get('waktu_mulai'),
                'waktu_selesai': s.get('waktu_selesai'),
                'cert_hash': s.get('cert_hash'),
                'merkle_root': s.get('merkle_root'),
                'tx_hash': s.get('tx_hash'),
                'verify_url': s.get('verify_url'),
                'created_at': s.get('created_at')
            })

        return jsonify({'success': True, 'sertifikat': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================
# 🔥 VERIFY SERTIFIKAT - VERSI FINAL DENGAN ENCODING YANG BENAR
# ============================================================
@sertifikat_bp.route('/sertifikat/verify/<public_id>', methods=['GET'])
def verify_sertifikat(public_id):
    try:
        supabase = current_app.supabase
        w3 = current_app.w3
        contract_address = current_app.contract_address
        contract = w3.eth.contract(address=contract_address, abi=CONTRACT_ABI)

        raw_id = public_id.replace('-', '')
        formatted_public_id = f"{raw_id[:8]}-{raw_id[8:12]}-{raw_id[12:16]}-{raw_id[16:20]}-{raw_id[20:]}"
        
        print(f"🔍 Public ID: {public_id}")
        print(f"📝 Raw ID: {raw_id}")

        # 🔥 PERBAIKAN: Encoding yang benar (sama dengan ethers.js)
        public_id_bytes = Web3.to_bytes(text=raw_id).ljust(32, b'\x00')
        print(f"🔑 public_id_bytes (hex): {public_id_bytes.hex()}")

        onchain_batch_id = contract.functions.getBatchIdByPublicId(public_id_bytes).call()
        print(f"📊 onchain_batch_id: {onchain_batch_id}")

        if onchain_batch_id == 0:
            return jsonify({
                'valid': False,
                'message': '❌ Sertifikat tidak terdaftar di blockchain.'
            }), 200

        onchain_merkle_root_bytes = contract.functions.merkleRoots(onchain_batch_id).call()
        onchain_merkle_root = '0x' + onchain_merkle_root_bytes.hex()
        print(f"🌳 On-chain Merkle Root: {onchain_merkle_root}")

        db_response = supabase.table('sertifikat').select('*').eq('public_id', formatted_public_id).execute()
        
        if not db_response.data:
            return jsonify({
                'valid': False,
                'message': '❌ Data sertifikat tidak ditemukan di database.'
            }), 200

        data = db_response.data[0]
        db_merkle_root = data.get('merkle_root', '')
        print(f"📦 DB Merkle Root: {db_merkle_root}")

        if db_merkle_root != onchain_merkle_root:
            print(f"❌ Merkle Root MISMATCH! DB: {db_merkle_root}, Onchain: {onchain_merkle_root}")
            return jsonify({
                'valid': False,
                'message': '❌ Data sertifikat telah dimodifikasi'
            }), 200

        return jsonify({
            'valid': True,
            'public_id': formatted_public_id,
            'batch_id': onchain_batch_id,
            'merkle_root': onchain_merkle_root,
            'nama_peserta': data.get('nama_peserta', 'Tidak tersedia'),
            'nama_kegiatan': data.get('nama_kegiatan', 'Tidak tersedia'),
            'nama_lokasi': data.get('nama_lokasi', 'Tidak tersedia'),
            'waktu_mulai': data.get('waktu_mulai'),
            'waktu_selesai': data.get('waktu_selesai'),
            'created_at': data.get('created_at'),
            'message': '✅ Sertifikat valid (Data sesuai dengan blockchain)'
        })

    except Exception as e:
        print(f"❌ ERROR verify: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'valid': False, 'error': str(e)}), 200

# ===== KONFIRMASI BATCH =====
@sertifikat_bp.route('/sertifikat/konfirmasi', methods=['POST'])
def konfirmasi_batch():
    try:
        data = request.json
        supabase = current_app.supabase

        merkle_root = data.get('merkle_root')
        tx_hash = data.get('tx_hash')
        batch_id_onchain = data.get('batch_id_onchain')
        sertifikat_list = data.get('sertifikat_list', [])

        if not sertifikat_list:
            return jsonify({'success': False, 'error': 'Tidak ada sertifikat'}), 400

        try:
            supabase.table('batch_sertifikat').update({
                'merkle_root': merkle_root,
                'tx_hash': tx_hash
            }).eq('id', batch_id_onchain).execute()
        except Exception as e:
            print(f"⚠️ Gagal update batch: {e}")

        updated = []
        for cert in sertifikat_list:
            public_id = cert.get('public_id')
            if not public_id:
                continue

            update_data = {
                'merkle_root': merkle_root,
                'merkle_proof': json.dumps(cert.get('proof', [])),
                'tx_hash': tx_hash,
                'batch_id': batch_id_onchain,
                'status': 'published'
            }
            response = supabase.table('sertifikat').update(update_data).eq('public_id', public_id).execute()
            if response.data:
                updated.append(public_id)

        return jsonify({'success': True, 'message': f'{len(updated)} sertifikat dikonfirmasi di blockchain'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== KELOLA PENERBIT =====
@sertifikat_bp.route('/penerbit', methods=['GET'])
def get_penerbit():
    try:
        supabase = current_app.supabase
        response = supabase.table('users').select('*').eq('role', 'penerbit').execute()
        penerbit_list = []
        for user in response.data:
            penerbit_list.append({
                'id': user.get('id'),
                'username': user.get('username'),
                'nama_lengkap': user.get('nama_lengkap', user.get('username')),
                'wallet_address': user.get('wallet_address', ''),
                'status': user.get('status', 'active')
            })
        return jsonify({'success': True, 'penerbit': penerbit_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sertifikat_bp.route('/penerbit', methods=['POST'])
def add_penerbit():
    try:
        data = request.json
        supabase = current_app.supabase
        if not data.get('username') or not data.get('password'):
            return jsonify({'success': False, 'error': 'Username dan password wajib diisi'}), 400

        check = supabase.table('users').select('*').eq('username', data['username']).execute()
        if check.data:
            return jsonify({'success': False, 'error': 'Username sudah digunakan'}), 400

        hashed = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = {
            'username': data['username'],
            'password': hashed,
            'role': data.get('role', 'penerbit'),
            'nama_lengkap': data.get('nama_lengkap', data['username']),
            'wallet_address': data.get('wallet_address', ''),
            'status': 'active',
            'is_active': True
        }
        supabase.table('users').insert(new_user).execute()
        return jsonify({'success': True, 'message': 'Penerbit berhasil ditambahkan'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sertifikat_bp.route('/penerbit/<int:id>/revoke', methods=['POST'])
def revoke_penerbit(id):
    try:
        supabase = current_app.supabase
        check = supabase.table('users').select('*').eq('id', id).eq('role', 'penerbit').execute()
        if not check.data:
            return jsonify({'success': False, 'error': 'Penerbit tidak ditemukan'}), 404

        supabase.table('users').update({'status': 'inactive', 'is_active': False}).eq('id', id).eq('role', 'penerbit').execute()
        return jsonify({'success': True, 'message': 'Hak penerbit berhasil dicabut'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@sertifikat_bp.route('/penerbit/<int:id>/activate', methods=['POST'])
def activate_penerbit(id):
    try:
        supabase = current_app.supabase
        check = supabase.table('users').select('*').eq('id', id).eq('role', 'penerbit').execute()
        if not check.data:
            return jsonify({'success': False, 'error': 'Penerbit tidak ditemukan'}), 404

        supabase.table('users').update({'status': 'active', 'is_active': True}).eq('id', id).eq('role', 'penerbit').execute()
        return jsonify({'success': True, 'message': 'Penerbit diaktifkan kembali'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== GENERATE QR CODE =====
@sertifikat_bp.route('/sertifikat/generate-qr/<public_id>', methods=['GET'])
def generate_qr(public_id):
    try:
        base_url = os.getenv('VERIFICATION_BASE_URL', 'https://zakanel-frontend.pages.dev')
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        verify_url = f"{base_url}/verifikasi/valid?id={public_id}"

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(verify_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({'success': True, 'qr_code': f"data:image/png;base64,{img_base64}", 'verify_url': verify_url})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== PREPARE SERTIFIKAT =====
@sertifikat_bp.route('/sertifikat/prepare', methods=['POST'])
def prepare_sertifikat():
    try:
        data = request.json
        supabase = current_app.supabase

        penerbit_id = data.get('penerbit_id')
        if not penerbit_id:
            penerbit_id = request.headers.get('X-User-ID')
        if not penerbit_id:
            return jsonify({'success': False, 'error': 'penerbit_id tidak ditemukan'}), 400

        try:
            penerbit_id = int(penerbit_id)
        except ValueError:
            return jsonify({'success': False, 'error': 'penerbit_id harus berupa angka'}), 400

        cert_list = data.get('sertifikat_list', [])
        if not cert_list:
            return jsonify({'success': False, 'error': 'Tidak ada data sertifikat'}), 400

        # Hitung Merkle Root
        hashes = []
        for cert in cert_list:
            required_fields = ['nama_peserta', 'nama_kegiatan', 'nama_lokasi', 'latitude', 'longitude']
            for field in required_fields:
                if not cert.get(field):
                    return jsonify({'success': False, 'error': f'Field {field} wajib diisi'}), 400

            lat = fmt_coord(cert.get('latitude'))
            lon = fmt_coord(cert.get('longitude'))
            cert_string = f"{cert.get('nama_peserta')}{cert.get('nama_kegiatan')}{cert.get('nama_lokasi')}{lat}{lon}"
            hash_val = hashlib.sha256(cert_string.encode()).hexdigest()
            hashes.append(hash_val)

        combined = ''.join(hashes)
        merkle_root = '0x' + hashlib.sha256(combined.encode()).hexdigest()

        # Insert Batch
        batch_id = int(datetime.now().timestamp() * 1000)
        try:
            supabase.table('batch_sertifikat').insert({
                'id': batch_id,
                'merkle_root': merkle_root,
                'created_at': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            return jsonify({'success': False, 'error': f'Gagal insert batch: {str(e)}'}), 500

        # Insert Sertifikat
        base_url = os.getenv('VERIFICATION_BASE_URL', 'https://zakanel-frontend.pages.dev')
        if base_url.endswith('/'):
            base_url = base_url[:-1]

        results = []
        for cert_data in cert_list:
            public_id = secrets.token_hex(16)
            cert_string = f"{cert_data.get('nama_peserta')}{cert_data.get('nama_kegiatan')}{cert_data.get('nama_lokasi')}{datetime.now()}"
            cert_hash = hashlib.sha256(cert_string.encode()).hexdigest()

            new_cert = {
                'public_id': public_id,
                'batch_id': batch_id,
                'nama_peserta': cert_data.get('nama_peserta', ''),
                'nama_kegiatan': cert_data.get('nama_kegiatan', ''),
                'nama_lokasi': cert_data.get('nama_lokasi', ''),
                'latitude': float(cert_data.get('latitude', 0)),
                'longitude': float(cert_data.get('longitude', 0)),
                'waktu_mulai': cert_data.get('waktu_mulai', datetime.now().isoformat()),
                'waktu_selesai': cert_data.get('waktu_selesai', datetime.now().isoformat()),
                'keterangan': cert_data.get('keterangan', ''),
                'cert_hash': cert_hash,
                'merkle_root': merkle_root,
                'merkle_proof': '[]',
                'tx_hash': None,
                'verify_url': f"{base_url}/verifikasi/valid?id={public_id}",
                'penerbit_id': penerbit_id,
                'status': 'draft'
            }

            try:
                response = supabase.table('sertifikat').insert(new_cert).execute()
                if response.data:
                    results.append(response.data[0])
            except Exception as e:
                print(f"❌ Error insert sertifikat: {e}")

        if not results:
            return jsonify({'success': False, 'error': 'Gagal menyimpan semua sertifikat'}), 500

        return jsonify({
            'success': True,
            'count': len(results),
            'data': results,
            'merkle_root': merkle_root,
            'batch_id': batch_id
        })

    except Exception as e:
        print(f"❌ ERROR PREPARE: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== GET DRAFT SERTIFIKAT =====
@sertifikat_bp.route('/sertifikat/draft', methods=['GET'])
def get_draft_sertifikat():
    try:
        supabase = current_app.supabase
        user_id = request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({'success': True, 'sertifikat': []})

        response = supabase.table('sertifikat').select('*').eq('penerbit_id', int(user_id)).eq('status', 'draft').order('created_at', desc=True).execute()

        result = []
        for s in response.data:
            result.append({
                'id': s.get('id'),
                'public_id': s.get('public_id'),
                'nama_peserta': s.get('nama_peserta'),
                'nama_kegiatan': s.get('nama_kegiatan'),
                'nama_lokasi': s.get('nama_lokasi'),
                'latitude': s.get('latitude'),
                'longitude': s.get('longitude'),
                'waktu_mulai': s.get('waktu_mulai'),
                'waktu_selesai': s.get('waktu_selesai'),
                'cert_hash': s.get('cert_hash'),
                'verify_url': s.get('verify_url'),
                'created_at': s.get('created_at'),
                'status': s.get('status')
            })

        return jsonify({'success': True, 'sertifikat': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500