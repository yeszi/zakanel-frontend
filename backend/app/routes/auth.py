from flask import Blueprint, request, jsonify, current_app
import bcrypt

from app.utils.auth_helper import generate_jwt, token_required, current_user, is_user_active, VALID_ROLES, ROLE_ADMIN
from app.utils.audit import log_audit

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Hash bcrypt "palsu" untuk menyamakan waktu respons saat username tidak ditemukan
# (mencegah penyerang menebak username dari perbedaan waktu).
_DUMMY_HASH = bcrypt.hashpw(b'dummy-password', bcrypt.gensalt(12))

PUBLIC_USER_FIELDS = ('id', 'username', 'role', 'nama_lengkap', 'wallet_address', 'status', 'is_active')


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')


def public_user(user: dict) -> dict:
    return {k: user.get(k) for k in PUBLIC_USER_FIELDS}


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username dan password wajib diisi'}), 400

    res = current_app.supabase.table('users').select('*').eq('username', username).execute()
    user = res.data[0] if res.data else None

    stored = (user or {}).get('password', '')
    try:
        ok = bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8') if user else _DUMMY_HASH)
    except ValueError:
        ok = False  # hash lama yang bukan format bcrypt

    if not user or not ok:
        log_audit('LOGIN_FAILED', status='failed', target_type='user', target_id=username,
                  detail={'reason': 'kredensial salah'})
        return jsonify({'success': False, 'message': 'Username atau password salah'}), 401

    if not is_user_active(user):
        log_audit('LOGIN_BLOCKED', status='denied', target_type='user', target_id=user['id'],
                  actor=user, detail={'reason': 'akun dinonaktifkan'})
        return jsonify({'success': False, 'message': '⚠️ Akun Anda telah dinonaktifkan oleh admin.'}), 403

    token = generate_jwt(user)
    log_audit('LOGIN_SUCCESS', target_type='user', target_id=user['id'], actor=user)
    return jsonify({'success': True, 'message': 'Login berhasil', 'user': public_user(user), 'token': token,
                    'expires_in': current_app.config['JWT_EXPIRATION_MINUTES'] * 60})


@auth_bp.route('/me', methods=['GET'])
@token_required()
def me():
    return jsonify({'success': True, 'user': public_user(current_user())})


@auth_bp.route('/logout', methods=['POST'])
@token_required()
def logout():
    log_audit('LOGOUT', target_type='user', target_id=current_user()['id'])
    return jsonify({'success': True})


@auth_bp.route('/register', methods=['POST'])
def register_admin_bootstrap():
    """
    HANYA untuk membuat akun admin PERTAMA ketika tabel users masih kosong dari admin
    dan ALLOW_BOOTSTRAP_ADMIN=1 di .env. Penerbit dibuat lewat POST /api/penerbit oleh admin.
    """
    if not current_app.config['ALLOW_BOOTSTRAP_ADMIN']:
        return jsonify({'success': False, 'error': 'Registrasi publik dinonaktifkan.'}), 403
    sb = current_app.supabase
    if sb.table('users').select('id').eq('role', ROLE_ADMIN).limit(1).execute().data:
        return jsonify({'success': False, 'error': 'Admin sudah ada. Matikan ALLOW_BOOTSTRAP_ADMIN.'}), 403

    data = request.get_json(silent=True) or {}
    username, password = (data.get('username') or '').strip(), data.get('password') or ''
    if not username or len(password) < 8:
        return jsonify({'success': False, 'error': 'Username wajib dan password minimal 8 karakter.'}), 400

    user = sb.table('users').insert({
        'username': username, 'password': hash_password(password),
        'nama_lengkap': data.get('nama_lengkap') or username, 'role': ROLE_ADMIN,
        'wallet_address': data.get('wallet_address') or None, 'status': 'active', 'is_active': True,
    }).execute().data[0]
    log_audit('ADMIN_BOOTSTRAP', target_type='user', target_id=user['id'], actor=user)
    return jsonify({'success': True, 'user': public_user(user)}), 201
