"""Uji tambahan revisi Pak Hendra (F01 dan F08). TIDAK mengubah data apa pun.
Jalankan di dalam container backend:  python /app/uji_tambahan.py
Butuh env JWT_SECRET yang sama dengan backend."""
import os, sys, json, datetime, secrets, urllib.request, urllib.error
sys.path.insert(0, '/app')
import jwt
from app import create_app
from app.utils.merkle import compute_leaf_hash, compute_leaf_hash_v1

BASE = 'http://localhost:5000'
app = create_app(); sb = app.supabase
SECRET = os.getenv('JWT_SECRET')

print('=== F01: pasangan input ambigu ===')
A = ('Windy', 'Teknik Kendali', 'Lab A', '1.5', '104.417', '2026-05-22T10:00', '2026-05-22T11:40', '2201010047', 'abc')
B = ('Windy', 'Teknik Kendali', 'Lab A1', '.5', '104.417', '2026-05-22T10:00', '2026-05-22T11:40', '2201010047', 'abc')
print('Versi lama (tanpa pemisah): hash sama =', compute_leaf_hash_v1(*A) == compute_leaf_hash_v1(*B))
print('Versi baru (JSON kanonik) : hash sama =', compute_leaf_hash(*A) == compute_leaf_hash(*B))

def call(path, token=None, headers=None):
    req = urllib.request.Request(BASE + path, headers=headers or {})
    if token: req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'{}')

def token_for(user, minutes):
    now = datetime.datetime.now(datetime.timezone.utc)
    return jwt.encode({'sub': str(user['id']), 'username': user['username'], 'role': user['role'],
                       'wallet': (user.get('wallet_address') or '').lower(), 'iat': now - datetime.timedelta(hours=2),
                       'exp': now + datetime.timedelta(minutes=minutes), 'jti': secrets.token_hex(8)},
                      SECRET, algorithm='HS256')

admin = sb.table('users').select('*').eq('role', 'admin').limit(1).execute().data[0]
penerbit = sb.table('users').select('*').eq('role', 'penerbit').eq('is_active', True).limit(1).execute().data[0]

print('\n=== F08: skenario keamanan yang sebelumnya tidak diulang ===')
print('Skenario | Status HTTP | Pesan | Hasil')
s, b = call('/api/penerbit', token_for(admin, -5))
print(f'Token admin kedaluwarsa -> GET /api/penerbit | {s} | {b.get("error")} | {"PASS" if s == 401 else "GAGAL"}')
s, b = call('/api/penerbit', token_for(penerbit, 30), {'X-User-Role': 'admin'})
print(f'Token penerbit + header X-User-Role: admin -> GET /api/penerbit | {s} | {b.get("error")} | {"PASS" if s == 403 else "GAGAL"}')
s, b = call('/api/audit', token_for(penerbit, 30), {'X-User-Role': 'admin'})
print(f'Token penerbit + header X-User-Role: admin -> GET /api/audit | {s} | {b.get("error")} | {"PASS" if s == 403 else "GAGAL"}')
