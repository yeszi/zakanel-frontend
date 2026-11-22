"""Uji manipulasi audit log pada SALINAN di memori (tidak menulis apa pun ke database).
Jalankan di dalam container backend:  python /app/uji_audit.py"""
import sys, copy, collections
sys.path.insert(0, '/app')
from app import create_app
from app.utils.audit import verify_audit_chain, compute_entry_hash

app = create_app(); sb = app.supabase
COLUMNS = ('id, logged_at, actor_id, actor_username, actor_role, action, target_type, target_id, '
           'detail, tx_hash, ip_address, status, prev_hash, entry_hash')
rows, start = [], 0
while True:
    ch = sb.table('audit_logs').select(COLUMNS).order('id').range(start, start + 999).execute().data
    rows.extend(ch)
    if len(ch) < 1000: break
    start += 1000

print(f'Total entri audit log: {len(rows)} (ID {rows[0]["id"]} s/d {rows[-1]["id"]})')
base = verify_audit_chain(rows)
print('Rantai asli:', 'VALID' if base['valid'] else 'RUSAK', {k: base.get(k) for k in ('checked', 'head_hash', 'broken_at_id', 'reason')})

cnt = collections.Counter((r['action'], r['status']) for r in rows)
print('\n=== REKAP AKTIVITAS (action | status | jumlah) ===')
for (a, s), n in sorted(cnt.items()): print(f'{a} | {s} | {n}')

# entri target: di tengah rantai, punya entri sesudahnya
k = len(rows) // 2
tid = rows[k]['id']
print(f'\nEntri target manipulasi: ID {tid} (urutan {k + 1} dari {len(rows)})')

def hasil(nama, data):
    r = verify_audit_chain(data)
    print(f'{nama} | ID {tid} | {"Rusak" if not r["valid"] else "VALID (tidak terdeteksi!)"} | terdeteksi pada ID {r.get("broken_at_id")} | {r.get("reason")}')

print('\n=== HASIL MANIPULASI ===')
print('Skenario | Entri dimanipulasi | Hasil | Terdeteksi pada | Penyebab')
d = copy.deepcopy(rows); d[k]['detail'] = {'dimanipulasi': True}; hasil('Ubah isi kolom detail', d)
d = copy.deepcopy(rows); d[k]['actor_username'] = 'penyerang'; hasil('Ubah aktor (actor_username)', d)
d = copy.deepcopy(rows); del d[k]; hasil('Hapus satu entri', d)
d = copy.deepcopy(rows); d[k]['detail'] = {'dimanipulasi': True}
d[k]['entry_hash'] = compute_entry_hash(d[k]['prev_hash'], d[k]); hasil('Ubah isi lalu hitung ulang entry_hash', d)
# --- Revisi F03: skenario 5, penulisan ulang SELURUH rantai (pihak dengan hak superuser) ---
d = copy.deepcopy(rows); d[k]['detail'] = {'dimanipulasi': True}
prev = d[k]['prev_hash']
for row in d[k:]:
    row['prev_hash'] = prev
    row['entry_hash'] = compute_entry_hash(prev, row)
    prev = row['entry_hash']
hasil('Ubah isi lalu tulis ulang seluruh rantai', d)   # diharapkan: VALID (tidak terdeteksi) -> batas threat model

# Dengan jangkar: hash kepala asli dicatat lebih dulu di tempat yang tidak dikuasai admin DB
# (mis. smart contract atau dokumen bertanda tangan). Rantai hasil penulisan ulang dibandingkan
# dengan jangkar tersebut.
r = verify_audit_chain(d)
anchor_head = base['head_hash']
print(f'Dibandingkan dengan jangkar hash kepala | '
      f'{"Rusak (terdeteksi oleh jangkar)" if r.get("head_hash") != anchor_head else "tidak terdeteksi"} | '
      f'head baru {str(r.get("head_hash"))[:12]}… vs jangkar {anchor_head[:12]}…')
