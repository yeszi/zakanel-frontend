from functools import wraps
from flask import request, jsonify, current_app
import jwt

def token_required(allowed_roles=None):
    """
    Decorator untuk melindungi endpoint dengan JWT.
    allowed_roles: list role yang diizinkan, misal ['penerbit'] atau ['admin', 'penerbit']
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            auth_header = request.headers.get('Authorization')

            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

            if not token:
                return jsonify({'error': 'Token tidak ditemukan'}), 401

            try:
                payload = jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token sudah kadaluarsa'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Token tidak valid'}), 401

            if allowed_roles and payload.get('role') not in allowed_roles:
                return jsonify({'error': 'Akses ditolak untuk role ini'}), 403

            request.user = payload  # simpan payload user untuk dipakai di route
            return f(*args, **kwargs)
        return decorated
    return decorator