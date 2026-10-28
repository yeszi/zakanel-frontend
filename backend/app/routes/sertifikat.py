from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import base64
import io
import json
import secrets

import qrcode

from app.utils.auth_helper import token_required, current_user, ROLE_ADMIN, ROLE_PENERBIT
from app.utils.audit import log_audit
from app.utils.chain import get_contract, verify_root_tx, is_penerbit_active_onchain, is_valid_address
from app.utils.merkle import (fmt_coord, compute_leaf_hash, build_merkle_tree, verify_merkle_proof,
                              encode_proof_for_db, decode_proof_from_db)

sertifikat_bp = Blueprint('sertifikat', __name__, url_prefix='/api/sertifikat')

REQUIRED_FIELDS = ['nama_peserta', 'nama_kegiatan', 'nama_lokasi', 'latitude', 'longitude',
                   'waktu_mulai', 'waktu_selesai']
MAX_BATCH = 500

LIST_FIELDS = ('id', 'public_id', 'batch_id', 'nama_peserta', 'nama_kegiatan', 'nama_lokasi', 'latitude',
               'longitude', 'waktu_mulai', 'waktu_selesai', 'keterangan', 'cert_hash', 'merkle_root',
               'tx_hash', 'verify_url', 'created_at', 'status', 'penerbit_id')


def _base_url():
    return current_app.config['VERIFICATION_BASE_URL'].rstrip('/')


def _normalize_public_id(public_id: str):
    raw = (public_id or '').replace('-', '').lower()
    if len(raw) != 32 or any(c not in '0123456789abcdef' for c in raw):
        return None, None
    return raw, f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"


# ============================================
# DAFTAR SERTIFIKAT (admin: semua, penerbit: miliknya)
# ============================================
@sertifikat_bp.route('', methods=['GET'])
@token_required(ROLE_ADMIN, ROLE_PENERBIT)
def get_all_sertifikat():
    user = current_user()
    q = current_app.supabase.table('sertifikat').select('*')
    if user['role'] == ROLE_PENERBIT:
        q = q.eq('penerbit_id', user['id'])
    res = q.order('created_at', desc=True).execute()
    return jsonify({'success': True, 'sertifikat': [{k: s.get(k) for k in LIST_FIELDS} for s in res.data]})


@sertifikat_bp.route('/draft', methods=['GET'])
@token_required(ROLE_PENERBIT)
def get_draft_sertifikat():
    res = current_app.supabase.table('sertifikat').select('*').eq('penerbit_id', current_user()['id']) \
        .eq('status', 'draft').order('created_at', desc=True).execute()
    return jsonify({'success': True, 'sertifikat': [{k: s.get(k) for k in LIST_FIELDS} for s in res.data]})


# ============================================
# PREPARE: hashing SHA-256 + Merkle Tree, simpan draft
# ============================================
@sertifikat_bp.route('/prepare', methods=['POST'])
@token_required(ROLE_PENERBIT)
def prepare_sertifikat():
    user = current_user()
    data = request.get_json(silent=True) or {}
    cert_list = data.get('sertifikat_list') or []

    if not cert_list:
        return jsonify({'success': False, 'error': 'Tidak ada data sertifikat'}), 400
    if len(cert_list) > MAX_BATCH:
        return jsonify({'success': False, 'error': f'Maksimal {MAX_BATCH} sertifikat per batch'}), 400
    for cert in cert_list:
        for field in REQUIRED_FIELDS:
            if cert.get(field) in (None, ''):
                return jsonify({'success': False, 'error': f'Field {field} wajib diisi'}), 400

    wallet = user.get('wallet_address')
    if not is_valid_address(wallet) or not is_penerbit_active_onchain(wallet):
        log_audit('CERT_PREPARE', status='denied', target_type='wallet', target_id=wallet,
                  detail={'reason': 'wallet tidak aktif di smart contract'})
        return jsonify({'success': False, 'error': 'Wallet Anda belum/tidak aktif di smart contract.'}), 403

    public_ids = [secrets.token_hex(16) for _ in cert_list]
    leaves = [compute_leaf_hash(c['nama_peserta'], c['nama_kegiatan'], c['nama_lokasi'], c['latitude'],
                                c['longitude'], c.get('waktu_mulai', ''), c.get('waktu_selesai', ''),
                                c.get('keterangan', ''), public_ids[i]) for i, c in enumerate(cert_list)]
    root_bytes, all_proofs = build_merkle_tree(leaves)
    merkle_root = '0x' + root_bytes.hex()
    batch_id = int(datetime.now().timestamp() * 1000)

    sb = current_app.supabase
    sb.table('batch_sertifikat').insert({
        'id': batch_id, 'merkle_root': merkle_root, 'penerbit_id': user['id'], 'status': 'pending',
        'created_at': datetime.now().isoformat(),
    }).execute()

    rows = []
    for idx, c in enumerate(cert_list):
        rows.append({
            'public_id': public_ids[idx], 'batch_id': batch_id, 'leaf_index': idx,
            'nama_peserta': c['nama_peserta'], 'nama_kegiatan': c['nama_kegiatan'], 'nama_lokasi': c['nama_lokasi'],
            'latitude': fmt_coord(c['latitude']), 'longitude': fmt_coord(c['longitude']),
            'waktu_mulai': c.get('waktu_mulai', ''), 'waktu_selesai': c.get('waktu_selesai', ''),
            'keterangan': c.get('keterangan', ''), 'cert_hash': leaves[idx].hex(), 'merkle_root': merkle_root,
            'merkle_proof': encode_proof_for_db(all_proofs[idx]), 'tx_hash': None,
            'verify_url': f"{_base_url()}/verifikasi/valid?id={public_ids[idx]}",
            'penerbit_id': user['id'], 'status': 'draft',
        })
    results = []
    for r in rows:
        res = sb.table('sertifikat').insert(r).execute()
        if res.data:
            results.append(res.data[0])

    log_audit('CERT_PREPARE', target_type='batch', target_id=batch_id,
              detail={'jumlah': len(results), 'merkle_root': merkle_root})
    return jsonify({'success': True, 'count': len(results), 'data': results, 'merkle_root': merkle_root,
                    'batch_id': batch_id, 'first_public_id': results[0]['public_id'] if results else None})


# ============================================
# KONFIRMASI: validasi transaksi simpanRoot lalu publish
# ============================================
@sertifikat_bp.route('/konfirmasi', methods=['POST'])
@token_required(ROLE_PENERBIT)
def konfirmasi_batch():
    user = current_user()
    data = request.get_json(silent=True) or {}
    tx_hash = (data.get('tx_hash') or '').strip()
    merkle_root = (data.get('merkle_root') or '').strip().lower()
    batch_id = data.get('batch_id_onchain')
    if not tx_hash or not merkle_root or batch_id is None:
        return jsonify({'success': False, 'error': 'tx_hash, merkle_root, dan batch_id_onchain wajib diisi'}), 400

    sb = current_app.supabase
    batch = sb.table('batch_sertifikat').select('*').eq('id', batch_id).execute().data
    if not batch or batch[0].get('penerbit_id') != user['id']:
        log_audit('CERT_PUBLISH', status='denied', target_type='batch', target_id=batch_id, tx_hash=tx_hash,
                  detail={'reason': 'batch bukan milik penerbit ini'})
        return jsonify({'success': False, 'error': 'Batch tidak ditemukan atau bukan milik Anda.'}), 403
    if (batch[0].get('merkle_root') or '').lower() != merkle_root:
        return jsonify({'success': False, 'error': 'Merkle root tidak sesuai dengan batch yang disiapkan.'}), 400

    ok, err = verify_root_tx(tx_hash, batch_id, merkle_root, user.get('wallet_address'))
    if not ok:
        log_audit('CERT_PUBLISH', status='failed', target_type='batch', target_id=batch_id, tx_hash=tx_hash,
                  detail={'reason': err})
        return jsonify({'success': False, 'error': f'Konfirmasi ditolak: {err}'}), 400

    sb.table('batch_sertifikat').update({'tx_hash': tx_hash, 'status': 'success'}).eq('id', batch_id).execute()
    updated = sb.table('sertifikat').update({'tx_hash': tx_hash, 'status': 'published'}) \
        .eq('batch_id', batch_id).eq('penerbit_id', user['id']).execute().data
    log_audit('CERT_PUBLISH', target_type='batch', target_id=batch_id, tx_hash=tx_hash,
              detail={'jumlah': len(updated), 'merkle_root': merkle_root})
    return jsonify({'success': True, 'message': f'{len(updated)} sertifikat dikonfirmasi di blockchain'})


# ============================================
# VERIFIKASI PUBLIK
# ============================================
@sertifikat_bp.route('/verify/<public_id>', methods=['GET'])
def verify_sertifikat(public_id):
    raw_id, formatted = _normalize_public_id(public_id)

    def result(valid, message, extra=None, log_detail=None):
        log_audit('CERT_VERIFY', status='success' if valid else 'failed', target_type='sertifikat',
                  target_id=formatted or public_id[:64], detail={'valid': valid, **(log_detail or {})})
        return jsonify({'valid': valid, 'message': message, **(extra or {})}), 200

    if not raw_id:
        return result(False, '❌ Format ID sertifikat tidak valid.', log_detail={'reason': 'format_id'})

    rows = current_app.supabase.table('sertifikat').select('*').eq('public_id', formatted).execute().data
    if not rows:
        return result(False, '❌ Sertifikat tidak ditemukan di database.', log_detail={'reason': 'not_found'})
    data = rows[0]
    if data.get('status') != 'published' or not data.get('batch_id'):
        return result(False, '❌ Sertifikat belum diterbitkan ke blockchain.', log_detail={'reason': 'not_published'})

    try:
        _, contract = get_contract()
        onchain_root = contract.functions.getRoot(int(data['batch_id'])).call()
    except Exception as e:
        print(f'❌ getRoot gagal: {e}')
        return jsonify({'valid': False, 'message': '❌ Gagal menghubungi blockchain, coba lagi.'}), 503
    if onchain_root == b'\x00' * 32:
        return result(False, '❌ Batch belum terdaftar di blockchain.', log_detail={'reason': 'no_root'})

    leaf = compute_leaf_hash(data.get('nama_peserta'), data.get('nama_kegiatan'), data.get('nama_lokasi'),
                             data.get('latitude'), data.get('longitude'), data.get('waktu_mulai', ''),
                             data.get('waktu_selesai', ''), data.get('keterangan', ''), raw_id)
    if not verify_merkle_proof(leaf, decode_proof_from_db(data.get('merkle_proof', '[]')), onchain_root):
        return result(False, '❌ Data sertifikat telah dimodifikasi (proof invalid).',
                      log_detail={'reason': 'proof_invalid', 'batch_id': data['batch_id']})

    return result(True, '✅ Sertifikat valid (root & proof sesuai dengan blockchain)', extra={
        'public_id': formatted, 'batch_id': data['batch_id'], 'merkle_root': '0x' + onchain_root.hex(),
        'tx_hash': data.get('tx_hash'), 'nama_peserta': data.get('nama_peserta'),
        'nama_kegiatan': data.get('nama_kegiatan'), 'nama_lokasi': data.get('nama_lokasi'),
        'waktu_mulai': data.get('waktu_mulai'), 'waktu_selesai': data.get('waktu_selesai'),
        'created_at': data.get('created_at'),
    }, log_detail={'batch_id': data['batch_id']})


# ============================================
# QR CODE (publik)
# ============================================
@sertifikat_bp.route('/generate-qr/<public_id>', methods=['GET'])
def generate_qr(public_id):
    raw_id, _ = _normalize_public_id(public_id)
    if not raw_id:
        return jsonify({'success': False, 'error': 'Format ID tidak valid'}), 400
    verify_url = f"{_base_url()}/verifikasi/valid?id={raw_id}"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(verify_url)
    qr.make(fit=True)
    buf = io.BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buf, format="PNG")
    return jsonify({'success': True, 'qr_code': 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode(),
                    'verify_url': verify_url})


# ============================================
# PEMELIHARAAN (admin): hitung ulang proof satu batch
# ============================================
@sertifikat_bp.route('/fix-proof/<int:batch_id>', methods=['POST'])
@token_required(ROLE_ADMIN)
def fix_proof(batch_id):
    sb = current_app.supabase
    certs = sb.table('sertifikat').select('*').eq('batch_id', batch_id).order('leaf_index').execute().data
    if not certs:
        return jsonify({'success': False, 'error': 'Tidak ada sertifikat dalam batch'}), 404
    leaves = [compute_leaf_hash(c['nama_peserta'], c['nama_kegiatan'], c['nama_lokasi'], c['latitude'],
                                c['longitude'], c.get('waktu_mulai', ''), c.get('waktu_selesai', ''),
                                c.get('keterangan', ''), c['public_id'].replace('-', '')) for c in certs]
    root_bytes, proofs = build_merkle_tree(leaves)
    for i, c in enumerate(certs):
        sb.table('sertifikat').update({'merkle_proof': encode_proof_for_db(proofs[i]),
                                       'cert_hash': leaves[i].hex()}).eq('id', c['id']).execute()
    log_audit('PROOF_REBUILD', target_type='batch', target_id=batch_id,
              detail={'jumlah': len(certs), 'root_hasil': '0x' + root_bytes.hex()})
    return jsonify({'success': True, 'merkle_root': '0x' + root_bytes.hex(), 'jumlah': len(certs)})


# ============================================
# UNDUH SERTIFIKAT (PDF + QR Code)
# ============================================
@sertifikat_bp.route('/<public_id>/pdf', methods=['GET'])
@token_required(ROLE_ADMIN, ROLE_PENERBIT)
def download_pdf(public_id):
    from flask import send_file
    import os
    from app.utils.pdf_cert import build_certificate_pdf

    user = current_user()
    raw_id, formatted = _normalize_public_id(public_id)
    if not raw_id:
        return jsonify({'success': False, 'error': 'Format ID tidak valid'}), 400
    rows = current_app.supabase.table('sertifikat').select('*').eq('public_id', formatted).execute().data
    if not rows:
        return jsonify({'success': False, 'error': 'Sertifikat tidak ditemukan'}), 404
    cert = rows[0]
    if user['role'] == ROLE_PENERBIT and cert.get('penerbit_id') != user['id']:
        log_audit('CERT_DOWNLOAD', status='denied', target_type='sertifikat', target_id=formatted,
                  detail={'reason': 'bukan pemilik sertifikat'})
        return jsonify({'success': False, 'error': 'Sertifikat bukan milik Anda.'}), 403
    if cert.get('status') != 'published':
        return jsonify({'success': False, 'error': 'Sertifikat belum diterbitkan ke blockchain.'}), 409

    penerbit = current_app.supabase.table('users').select('nama_lengkap, username') \
        .eq('id', cert.get('penerbit_id')).execute().data
    penerbit_nama = (penerbit[0].get('nama_lengkap') or penerbit[0].get('username')) if penerbit else '-'
    logo = os.getenv('LOGO_PATH', os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'logo.png'))
    pdf = build_certificate_pdf(
        cert, f"{_base_url()}/verifikasi/valid?id={raw_id}",
        institusi=os.getenv('NAMA_INSTITUSI', 'Fakultas Teknik dan Teknologi Kemaritiman - UMRAH'),
        penerbit_nama=penerbit_nama, logo_path=logo)
    log_audit('CERT_DOWNLOAD', target_type='sertifikat', target_id=formatted,
              detail={'nama_peserta': cert.get('nama_peserta')})
    safe = ''.join(ch if ch.isalnum() else '_' for ch in cert.get('nama_peserta', 'sertifikat'))[:40]
    return send_file(io.BytesIO(pdf), mimetype='application/pdf', as_attachment=True,
                     download_name=f'Sertifikat_{safe}_{raw_id[:8]}.pdf')


# ============================================
# AUDIT KONSISTENSI BATCH (off-chain vs on-chain)
# ============================================
@sertifikat_bp.route('/batch-audit', methods=['GET'])
@token_required(ROLE_ADMIN, ROLE_PENERBIT)
def batch_audit():
    """
    Untuk setiap batch milik penerbit (admin: semua batch):
      - rekonstruksi Merkle Root dari cert_hash di basis data (urut leaf_index)
      - bandingkan dengan Merkle Root yang tersimpan di smart contract (getRoot)
      - hitung ulang leaf hash dari metadata & telusuri Merkle Proof tiap sertifikat
    """
    user = current_user()
    sb = current_app.supabase
    q = sb.table('sertifikat').select('*').eq('status', 'published')
    if user['role'] == ROLE_PENERBIT:
        q = q.eq('penerbit_id', user['id'])
    certs = q.execute().data
    _, contract = get_contract()

    groups = {}
    for c in certs:
        groups.setdefault(c['batch_id'], []).append(c)

    hasil = []
    for batch_id, items in sorted(groups.items(), key=lambda kv: kv[0], reverse=True):
        items.sort(key=lambda c: c.get('leaf_index') or 0)
        root_rekon, _ = build_merkle_tree([bytes.fromhex(c['cert_hash']) for c in items])
        try:
            root_onchain = contract.functions.getRoot(int(batch_id)).call()
        except Exception:
            root_onchain = None
        valid = 0
        rusak = []
        for c in items:
            leaf = compute_leaf_hash(c['nama_peserta'], c['nama_kegiatan'], c['nama_lokasi'], c['latitude'],
                                     c['longitude'], c.get('waktu_mulai', ''), c.get('waktu_selesai', ''),
                                     c.get('keterangan', ''), c['public_id'].replace('-', ''))
            ok = root_onchain is not None and verify_merkle_proof(leaf, decode_proof_from_db(c.get('merkle_proof')), root_onchain)
            if ok:
                valid += 1
            else:
                rusak.append({'public_id': c['public_id'], 'nama_peserta': c['nama_peserta']})
        hasil.append({
            'batch_id': batch_id,
            'nama_kegiatan': items[0].get('nama_kegiatan'),
            'jumlah': len(items),
            'tx_hash': items[0].get('tx_hash'),
            'root_onchain': ('0x' + root_onchain.hex()) if root_onchain else None,
            'root_rekonstruksi': '0x' + root_rekon.hex(),
            'root_cocok': root_onchain is not None and root_rekon == root_onchain,
            'sertifikat_valid': valid,
            'sertifikat_rusak': rusak,
        })

    total = sum(h['jumlah'] for h in hasil)
    total_valid = sum(h['sertifikat_valid'] for h in hasil)
    log_audit('BATCH_AUDIT', status='success' if total == total_valid else 'failed', target_type='batch',
              target_id='semua' if user['role'] == ROLE_ADMIN else f"penerbit:{user['id']}",
              detail={'batch': len(hasil), 'sertifikat': total, 'valid': total_valid})
    return jsonify({'success': True, 'total_batch': len(hasil), 'total_sertifikat': total,
                    'total_valid': total_valid, 'batches': hasil})
