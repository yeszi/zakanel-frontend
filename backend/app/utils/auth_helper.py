"""
Autentikasi JWT + Role-Based Access Control (RBAC).

- Token dibuat saat login dan ditandatangani server dengan JWT_SECRET (HS256).
- Peran (role) dan ID pengguna DIAMBIL DARI TOKEN, bukan dari header yang dikirim klien,
  sehingga tidak bisa dipalsukan.
- Setiap request juga mengecek status akun di database, sehingga penerbit yang dicabut
  langsung kehilangan akses walaupun tokennya belum kedaluwarsa.
"""
import datetime
import secrets
from functools import wraps

import jwt
from flask import request, jsonify, current_app, g

ROLE_ADMIN = 'admin'
ROLE_PENERBIT = 'penerbit'
VALID_ROLES = {ROLE_ADMIN, ROLE_PENERBIT}


def generate_jwt(user: dict) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        'sub': str(user['id']),          # PyJWT >= 2.10 mewajibkan sub bertipe string
        'username': user['username'],
        'role': user['role'],
        'wallet': (user.get('wallet_address') or '').lower(),
        'iat': now,
        'exp': now + datetime.timedelta(minutes=current_app.config['JWT_EXPIRATION_MINUTES']),
        'jti': secrets.token_hex(8),
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET'], algorithm=current_app.config['JWT_ALGORITHM'])


def decode_jwt(token: str) -> dict:
    return jwt.decode(token, current_app.config['JWT_SECRET'],
                      algorithms=[current_app.config['JWT_ALGORITHM']],
                      options={'require': ['exp', 'iat', 'sub']})


def is_user_active(user: dict) -> bool:
    return user.get('is_active', True) is not False and user.get('status', 'active') not in ('inactive', 'revoked')


def _deny(status, message, reason):
    from app.utils.audit import log_audit
    log_audit('ACCESS_DENIED', status='denied', target_type='endpoint',
              target_id=f'{request.method} {request.path}', detail={'reason': reason})
    return jsonify({'success': False, 'error': message}), status


def token_required(*allowed_roles):
    """
    Pemakaian:
        @token_required()                      -> semua user yang login
        @token_required('admin')               -> hanya admin
        @token_required('admin', 'penerbit')   -> admin atau penerbit
    Setelah lolos, data user tersedia di flask.g.user
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return _deny(401, 'Token tidak ditemukan. Silakan login.', 'no_token')
            token = auth_header.split(' ', 1)[1].strip()

            try:
                payload = decode_jwt(token)
            except jwt.ExpiredSignatureError:
                return _deny(401, 'Sesi berakhir, silakan login kembali.', 'token_expired')
            except jwt.InvalidTokenError:
                return _deny(401, 'Token tidak valid.', 'token_invalid')

            # Ambil data user terbaru dari DB (agar pencabutan hak langsung berlaku)
            res = current_app.supabase.table('users').select(
                'id, username, role, wallet_address, nama_lengkap, status, is_active'
            ).eq('id', int(payload['sub'])).execute()
            if not res.data:
                return _deny(401, 'Akun tidak ditemukan.', 'user_not_found')
            user = res.data[0]
            g.user = user  # supaya ACCESS_DENIED di bawah tercatat dengan nama user

            if not is_user_active(user):
                return _deny(403, 'Akun Anda telah dinonaktifkan oleh admin.', 'user_inactive')
            if user['role'] != payload.get('role'):
                return _deny(401, 'Peran akun berubah, silakan login kembali.', 'role_changed')
            if allowed_roles and user['role'] not in allowed_roles:
                return _deny(403, 'Akses ditolak untuk peran ini.', f"role_{user['role']}_not_allowed")

            return f(*args, **kwargs)
        return wrapper
    return decorator


def current_user():
    return getattr(g, 'user', None)
