"""
Audit log yang tamper-evident (hash chaining).

Setiap entri menyimpan:
  prev_hash  = entry_hash dari entri sebelumnya ('0' * 64 untuk entri pertama)
  entry_hash = SHA-256(prev_hash || JSON kanonik isi entri)

Jika ada satu baris yang diubah/dihapus di database, rantai hash akan putus
dan terdeteksi oleh verify_audit_chain().
"""
import datetime
import hashlib
import json
import threading

from flask import current_app, request, g, has_request_context

GENESIS_HASH = '0' * 64
_lock = threading.Lock()  # mencegah dua entri memakai prev_hash yang sama (1 proses backend)

# Kolom yang ikut di-hash (urutan tidak berpengaruh karena sort_keys=True)
HASHED_FIELDS = ('logged_at', 'actor_id', 'actor_username', 'actor_role', 'action',
                 'target_type', 'target_id', 'detail', 'tx_hash', 'ip_address', 'status')


def canonical(entry: dict) -> str:
    data = {k: entry.get(k) for k in HASHED_FIELDS}
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False, default=str)


def compute_entry_hash(prev_hash: str, entry: dict) -> str:
    return hashlib.sha256((prev_hash + canonical(entry)).encode('utf-8')).hexdigest()


def _client_ip():
    if not has_request_context():
        return None
    # Cloudflare Tunnel meneruskan IP asli di header ini
    return (request.headers.get('CF-Connecting-IP')
            or (request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or None)
            or request.remote_addr)


def log_audit(action, status='success', target_type=None, target_id=None,
              detail=None, tx_hash=None, actor=None):
    """
    Mencatat satu aktivitas. Tidak pernah melempar exception ke pemanggil,
    supaya kegagalan logging tidak menggagalkan proses utama.
    """
    try:
        if actor is None and has_request_context():
            actor = getattr(g, 'user', None)
        entry = {
            # disimpan sebagai TEXT agar format waktunya tidak diubah PostgreSQL (hash tetap sama)
            'logged_at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='microseconds'),
            'actor_id': actor.get('id') if actor else None,
            'actor_username': actor.get('username') if actor else None,
            'actor_role': actor.get('role') if actor else 'publik',
            'action': action,
            'target_type': target_type,
            'target_id': str(target_id) if target_id is not None else None,
            # disimpan sebagai TEXT berisi JSON kanonik agar hash bisa dihitung ulang persis
            'detail': json.dumps(detail or {}, sort_keys=True, separators=(',', ':'), ensure_ascii=False, default=str),
            'tx_hash': tx_hash,
            'ip_address': _client_ip(),
            'status': status,
        }
        sb = current_app.supabase
        with _lock:
            last = sb.table('audit_logs').select('entry_hash').order('id', desc=True).limit(1).execute()
            prev_hash = last.data[0]['entry_hash'] if last.data else GENESIS_HASH
            entry['prev_hash'] = prev_hash
            entry['entry_hash'] = compute_entry_hash(prev_hash, entry)
            sb.table('audit_logs').insert(entry).execute()
        return entry['entry_hash']
    except Exception as e:  # pragma: no cover
        print(f'⚠️ Gagal mencatat audit log ({action}): {e}')
        return None


def verify_audit_chain(rows):
    """
    rows: seluruh baris audit_logs diurutkan berdasarkan id (ASC).
    Mengembalikan dict hasil pemeriksaan.
    """
    prev = GENESIS_HASH
    for i, row in enumerate(rows):
        if row.get('prev_hash') != prev:
            return {'valid': False, 'total': len(rows), 'checked': i, 'broken_at_id': row.get('id'),
                    'reason': 'prev_hash tidak cocok (ada entri yang dihapus/disisipkan)'}
        expected = compute_entry_hash(prev, row)
        if expected != row.get('entry_hash'):
            return {'valid': False, 'total': len(rows), 'checked': i, 'broken_at_id': row.get('id'),
                    'reason': 'entry_hash tidak cocok (isi entri telah diubah)'}
        prev = row['entry_hash']
    return {'valid': True, 'total': len(rows), 'checked': len(rows), 'head_hash': prev}
