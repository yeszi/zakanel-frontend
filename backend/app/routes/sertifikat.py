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

# ============================================
# CONTRACT ABI - KONTRAK BARU DENGAN PUBLIC_ID
# ============================================
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

# ============================================
# GET ALL SERTIFIKAT
# ============================================
@sertifikat_bp.route('/sertifikat', methods=['GET'])
def get_all_sertifikat():
    try:
        supabase = current_app.supabase
        user_id = request.headers.get('X-User-ID')
        user_role = request.headers.get('X-User-Role')
        print(f"🔍 Request dari user_id={user_id}, role={user_role}")
        if user_role == 'admin':
            response = supabase.table('sertifikat').select('*').order('created_at', desc=True).execute()
        else:
            if user_id:
                response = supabase.table('sertifikat').select('*').eq('penerbit_id', int(user_id)).order('created_at', desc=True).execute()
            else:
                return jsonify({'success': True, 'sertifikat': []})
        result = []
        for s in response.data:
            merkle_root = s.get('merkle_root')
            if not merkle_root and s.get('merkle_proof'):
                try:
                    proof_data = json.loads(s.get('merkle_proof'))
                    if proof_data and isinstance(proof_data, list) and len(proof_data) > 0:
                        merkle_root = proof_data[0].get('root') if isinstance(proof_data[0], dict) else None
                except:
                    merkle_root = None
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
                'merkle_root': merkle_root,
                'merkle_proof': json.loads(s.get('merkle_proof')) if s.get('merkle_proof') else [],
                'tx_hash': s.get('tx_hash'),
                'verify_url': s.get('verify_url'),
                'created_at': s.get('created_at')
            })
        return jsonify({'success': True, 'sertifikat': result})
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# VERIFY SERTIFIKAT - CEK KE BLOCKCHAIN + SUPABASE
# ============================================
@sertifikat_bp.route('/sertifikat/verify/<public_id>', methods=['GET'])
def verify_sertifikat(public_id):
    try:
        w3 = current_app.w3
        contract_address = current_app.contract_address
        print(f"🔍 Verifikasi public_id: {public_id}")

        contract = w3.eth.contract(address=contract_address, abi=CONTRACT_ABI)

        public_id_clean = public_id.replace('-', '')
        if len(public_id_clean) % 2 != 0:
            public_id_clean = '0' + public_id_clean
        public_id_bytes = bytes.fromhex(public_id_clean)
        if len(public_id_bytes) < 32:
            public_id_bytes = public_id_bytes.rjust(32, b'\x00')

        batch_id = contract.functions.getBatchIdByPublicId(public_id_bytes).call()
        if batch_id == 0:
            return jsonify({
                'valid': False,
                'message': 'Sertifikat tidak ditemukan di blockchain'
            }), 200

        merkle_root = contract.functions.merkleRoots(batch_id).call()
        merkle_root = '0x' + merkle_root.hex()

        supabase = current_app.supabase
        db_response = supabase.table('sertifikat').select('*').eq('public_id', public_id).execute()
        cert_data = db_response.data[0] if db_response.data else {}

        print(f"✅ Sertifikat valid! Batch ID: {batch_id}")

        return jsonify({
            'valid': True,
            'public_id': public_id,
            'batch_id': batch_id,
            'merkle_root': merkle_root,
            'nama_peserta': cert_data.get('nama_peserta', 'Tidak tersedia'),
            'nama_kegiatan': cert_data.get('nama_kegiatan', 'Tidak tersedia'),
            'nama_lokasi': cert_data.get('nama_lokasi', 'Tidak tersedia'),
            'waktu_mulai': cert_data.get('waktu_mulai'),
            'waktu_selesai': cert_data.get('waktu_selesai'),
            'created_at': cert_data.get('created_at'),
            'message': 'Sertifikat valid (diverifikasi dari blockchain)'
        })

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'valid': False, 'error': str(e)}), 200

# ============================================
# KONFIRMASI BATCH
# ============================================
@sertifikat_bp.route('/sertifikat/konfirmasi', methods=['POST'])
def konfirmasi_batch():
    try:
        data = request.json
        supabase = current_app.supabase
        print("=" * 50)
        print("📝 KONFIRMASI BATCH:", data)
        print("=" * 50)
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
            print(f"✅ Batch {batch_id_onchain} diupdate")
        except Exception as e:
            print(f"⚠️ Gagal update batch: {e}")
        updated = []
        for cert in sertifikat_list:
            public_id = cert.get('public_id')
            if not public_id:
                print(f"⚠️ Skip: tidak ada public_id untuk {cert}")
                continue
            print(f"📝 Update sertifikat: {public_id}")
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
                print(f"✅ {public_id} berhasil diupdate")
            else:
                print(f"❌ Gagal update {public_id}")
        return jsonify({
            'success': True,
            'message': f'{len(updated)} sertifikat dikonfirmasi di blockchain',
            'count': len(updated)
        })
    except Exception as e:
        print(f"❌ ERROR KONFIRMASI: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# KELOLA PENERBIT
# ============================================
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
        response = supabase.table('users').insert(new_user).execute()
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

# ============================================
# GENERATE QR CODE (DENGAN DEBUG PRINT)
# ============================================
@sertifikat_bp.route('/sertifikat/generate-qr/<public_id>', methods=['GET'])
def generate_qr(public_id):
    """Generate QR Code dengan link publik dari environment variable"""
    try:
        # Ambil base URL dari environment variable
        base_url = os.getenv('VERIFICATION_BASE_URL', 'http://localhost:3000')
        # Bersihkan trailing slash jika ada
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        verify_url = f"{base_url}/verifikasi/valid?id={public_id}"

        # DEBUG: cetak ke terminal agar terlihat
        print("=" * 50)
        print(f"🔍 DEBUG generate_qr:")
        print(f"   base_url   = {base_url}")
        print(f"   public_id  = {public_id}")
        print(f"   verify_url = {verify_url}")
        print("=" * 50)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(verify_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({
            'success': True,
            'qr_code': f"data:image/png;base64,{img_base64}",
            'verify_url': verify_url
        })
    except Exception as e:
        print(f"❌ Error generate QR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# PREPARE SERTIFIKAT (REVISI: PAKAI .env UNTUK URL)
# ============================================
@sertifikat_bp.route('/sertifikat/prepare', methods=['POST'])
def prepare_sertifikat():
    try:
        data = request.json
        supabase = current_app.supabase
        print("=" * 50)
        print("📝 REQUEST DATA:", data)
        print("=" * 50)
        penerbit_id = data.get('penerbit_id')
        if not penerbit_id:
            penerbit_id = request.headers.get('X-User-ID', 3)
        cert_list = data.get('sertifikat_list', [])
        if not cert_list:
            return jsonify({'success': False, 'error': 'Tidak ada data sertifikat'}), 400
        import hashlib
        import time
        hashes = []
        for cert in cert_list:
            cert_string = f"{cert.get('nama_peserta')}{cert.get('nama_kegiatan')}{cert.get('nama_lokasi')}{cert.get('latitude')}{cert.get('longitude')}"
            hash_val = hashlib.sha256(cert_string.encode()).hexdigest()
            hashes.append(hash_val)
            print(f"📝 Hash untuk {cert.get('nama_peserta')}: {hash_val}")
        combined = ''.join(hashes)
        merkle_root = hashlib.sha256(combined.encode()).hexdigest()
        merkle_root = '0x' + merkle_root
        print(f"🌳 Merkle Root: {merkle_root}")
        batch_id = int(time.time() * 1000)
        try:
            supabase.table('batch_sertifikat').insert({
                'id': batch_id,
                'merkle_root': merkle_root,
                'created_at': datetime.now().isoformat()
            }).execute()
            print(f"✅ Batch {batch_id} dibuat")
        except Exception as e:
            print(f"⚠️ Gagal insert batch: {e}")
        # ✅ Ambil base URL dari .env untuk QR Code
        base_url = os.getenv('VERIFICATION_BASE_URL', 'http://localhost:3000')
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        print(f"🔍 DEBUG prepare: VERIFICATION_BASE_URL = {base_url}")
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
                'penerbit_id': int(penerbit_id),
                'status': 'draft'
            }
            response = supabase.table('sertifikat').insert(new_cert).execute()
            if response.data:
                results.append(response.data[0])
                print(f"✅ {new_cert['nama_peserta']} disimpan dengan public_id: {public_id}")
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

# ============================================
# GET DRAFT SERTIFIKAT
# ============================================
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