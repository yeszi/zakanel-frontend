"""
Manajemen penerbit (khusus Admin).

Alur agar database (off-chain) dan smart contract (on-chain) selalu sinkron:
  1. Frontend memanggil GET /api/penerbit/check  -> memastikan username & wallet belum dipakai
  2. Admin menandatangani tambahPenerbit / cabutPenerbit di MetaMask
  3. Frontend mengirim tx_hash ke backend; backend MEMVERIFIKASI transaksi di blockchain
     sebelum mengubah database dan mencatat audit log.
"""
from flask import Blueprint, request, jsonify, current_app
from web3 import Web3

from app.routes.auth import hash_password
from app.utils.auth_helper import token_required, current_user, ROLE_ADMIN, ROLE_PENERBIT
from app.utils.audit import log_audit
from app.utils.chain import verify_penerbit_tx, is_valid_address

penerbit_bp = Blueprint('penerbit', __name__, url_prefix='/api/penerbit')


def _fmt(u):
    return {'id': u.get('id'), 'username': u.get('username'),
            'nama_lengkap': u.get('nama_lengkap') or u.get('username'),
            'wallet_address': u.get('wallet_address') or '', 'status': u.get('status', 'active'),
            'is_active': u.get('is_active', True)}


def _find_penerbit(pid):
    res = current_app.supabase.table('users').select('*').eq('id', pid).eq('role', ROLE_PENERBIT).execute()
    return res.data[0] if res.data else None


def _check_availability(username, wallet):
    sb = current_app.supabase
    if username and sb.table('users').select('id').eq('username', username).execute().data:
        return 'Username sudah digunakan.'
    if wallet:
        if not is_valid_address(wallet):
            return 'Alamat wallet tidak valid.'
        for u in sb.table('users').select('wallet_address').execute().data:
            if (u.get('wallet_address') or '').lower() == wallet.lower():
                return 'Wallet sudah terdaftar untuk akun lain.'
    return None


@penerbit_bp.route('', methods=['GET'])
@token_required(ROLE_ADMIN)
def list_penerbit():
    res = current_app.supabase.table('users').select('*').eq('role', ROLE_PENERBIT).order('id').execute()
    return jsonify({'success': True, 'penerbit': [_fmt(u) for u in res.data]})


@penerbit_bp.route('/check', methods=['GET'])
@token_required(ROLE_ADMIN)
def check_penerbit():
    err = _check_availability(request.args.get('username', '').strip(), request.args.get('wallet_address', '').strip())
    return jsonify({'success': err is None, 'error': err}), (200 if err is None else 409)


@penerbit_bp.route('', methods=['POST'])
@token_required(ROLE_ADMIN)
def add_penerbit():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    wallet = (data.get('wallet_address') or '').strip()
    tx_hash = (data.get('tx_hash') or '').strip()

    if not username or len(password) < 8:
        return jsonify({'success': False, 'error': 'Username wajib dan password minimal 8 karakter.'}), 400
    if not is_valid_address(wallet):
        return jsonify({'success': False, 'error': 'Alamat wallet penerbit tidak valid.'}), 400
    err = _check_availability(username, wallet)
    if err:
        return jsonify({'success': False, 'error': err}), 409

    ok, err = verify_penerbit_tx(tx_hash, 'PenerbitDitambahkan', wallet)
    if not ok:
        log_audit('PENERBIT_ADD', status='failed', target_type='wallet', target_id=wallet,
                  tx_hash=tx_hash or None, detail={'username': username, 'reason': err})
        return jsonify({'success': False, 'error': f'Transaksi on-chain tidak valid: {err}'}), 400

    user = current_app.supabase.table('users').insert({
        'username': username, 'password': hash_password(password), 'role': ROLE_PENERBIT,
        'nama_lengkap': data.get('nama_lengkap') or username,
        'wallet_address': Web3.to_checksum_address(wallet), 'status': 'active', 'is_active': True,
    }).execute().data[0]
    log_audit('PENERBIT_ADD', target_type='user', target_id=user['id'], tx_hash=tx_hash,
              detail={'username': username, 'wallet': user['wallet_address']})
    return jsonify({'success': True, 'message': 'Penerbit berhasil ditambahkan', 'penerbit': _fmt(user)})


def _change_status(pid, new_active: bool):
    action = 'PENERBIT_ACTIVATE' if new_active else 'PENERBIT_REVOKE'
    event = 'PenerbitDitambahkan' if new_active else 'PenerbitDicabut'
    tx_hash = ((request.get_json(silent=True) or {}).get('tx_hash') or '').strip()

    user = _find_penerbit(pid)
    if not user:
        return jsonify({'success': False, 'error': 'Penerbit tidak ditemukan'}), 404
    ok, err = verify_penerbit_tx(tx_hash, event, user.get('wallet_address'))
    if not ok:
        log_audit(action, status='failed', target_type='user', target_id=pid, tx_hash=tx_hash or None,
                  detail={'reason': err})
        return jsonify({'success': False, 'error': f'Transaksi on-chain tidak valid: {err}'}), 400

    current_app.supabase.table('users').update({
        'status': 'active' if new_active else 'inactive', 'is_active': new_active
    }).eq('id', pid).eq('role', ROLE_PENERBIT).execute()
    log_audit(action, target_type='user', target_id=pid, tx_hash=tx_hash,
              detail={'username': user['username'], 'wallet': user.get('wallet_address')})
    return jsonify({'success': True, 'message': 'Penerbit diaktifkan kembali' if new_active else 'Hak penerbit berhasil dicabut'})


@penerbit_bp.route('/<int:pid>/revoke', methods=['POST'])
@token_required(ROLE_ADMIN)
def revoke_penerbit(pid):
    return _change_status(pid, False)


@penerbit_bp.route('/<int:pid>/activate', methods=['POST'])
@token_required(ROLE_ADMIN)
def activate_penerbit(pid):
    return _change_status(pid, True)
