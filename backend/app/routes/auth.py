from flask import Blueprint, request, jsonify, current_app
import jwt
import datetime
import bcrypt
import secrets 

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# === HELPER FUNCTIONS ===
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def generate_jwt(user_id: int, username: str, role: str) -> str:
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET'], algorithm='HS256')

# === ENDPOINTS ===
@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'success': False, 'message': 'Username dan password wajib diisi'}), 400

        supabase = current_app.supabase
        response = supabase.table('users').select('*').eq('username', username).execute()

        if not response.data:
            return jsonify({'success': False, 'message': 'Username atau password salah'}), 401

        user = response.data[0]
        status = user.get('status', 'active')
        is_active = user.get('is_active', True)
        
        if status == 'inactive' or status == 'revoked' or is_active == False:
            return jsonify({'success': False, 'message': '⚠️ Akun Anda telah dinonaktifkan oleh admin.'}), 403

        # VERIFIKASI BCRYPT (ANTI-CRASH)
        try:
            if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                return jsonify({'success': False, 'message': 'Username atau password salah'}), 401
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Sistem keamanan baru (Bcrypt) diterapkan. Akun lama tidak valid, silakan daftarkan ulang akun Anda.'
            }), 401

        user.pop('password', None)
        token = secrets.token_hex(32)

        return jsonify({'success': True, 'message': 'Login berhasil', 'user': user, 'token': token})

    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    nama_lengkap = data.get('nama_lengkap')
    role = data.get('role', 'penerbit')

    if not username or not password or not nama_lengkap:
        return jsonify({'error': 'Username, password, and nama_lengkap required'}), 400

    existing = current_app.supabase.table('users').select('*').eq('username', username).execute()
    if existing.data:
        return jsonify({'error': 'Username already exists'}), 400

    hashed = hash_password(password)

    user_data = {
        'username': username,
        'password': hashed,
        'nama_lengkap': nama_lengkap,
        'role': role,
        'status': 'active',
        'is_active': True
    }

    result = current_app.supabase.table('users').insert(user_data).execute()
    return jsonify({'message': 'User registered successfully', 'user': result.data[0]}), 201

@auth_bp.route('/status/<username>', methods=['GET'])
def check_status(username):
    try:
        supabase = current_app.supabase
        response = supabase.table('users').select('status,is_active').eq('username', username).execute()
        
        if not response.data:
            return jsonify({'success': False, 'message': 'User tidak ditemukan'}), 404
        
        user = response.data[0]
        is_active = user.get('is_active', True) and user.get('status') != 'revoked'
        
        return jsonify({'success': True, 'username': username, 'is_active': is_active, 'status': user.get('status', 'active')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500