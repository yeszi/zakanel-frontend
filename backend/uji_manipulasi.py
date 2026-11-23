"""Uji deteksi manipulasi data sertifikat (8 variabel x semua sertifikat dalam batch terbaru).
Dijalankan DI DALAM container backend:  python /app/uji_manipulasi.py
Alur per skenario: ubah 1 nilai di Supabase -> panggil /verify -> pulihkan nilai asli.
Cadangan data asli disimpan lebih dulu ke /tmp/cadangan_sertifikat.json."""
import json, time, sys, statistics, urllib.request
sys.path.insert(0, '/app')
from app import create_app
from app.utils.merkle import compute_leaf_hash

app = create_app(); sb = app.supabase
BASE = 'http://localhost:5000'
FIELDS = ['nama_kegiatan', 'nama_lokasi', 'latitude', 'longitude', 'waktu_mulai', 'waktu_selesai', 'keterangan', 'nama_peserta']

rows = sb.table('sertifikat').select('*').order('leaf_index').execute().data
bid = max(r['batch_id'] for r in rows if r.get('batch_id') is not None)
rows = [r for r in rows if r.get('batch_id') == bid]
json.dump(rows, open('/tmp/cadangan_sertifikat.json', 'w'), default=str)
print(f'Batch {bid}: {len(rows)} sertifikat. Cadangan: /tmp/cadangan_sertifikat.json', flush=True)

def verify(pid):
    # dicoba ulang bila RPC/Infura sedang lambat (503/timeout), agar skrip tidak berhenti di tengah
    for coba in range(5):
        try:
            with urllib.request.urlopen(f'{BASE}/api/sertifikat/verify/{pid}', timeout=120) as r:
                return json.load(r)['valid']
        except Exception as e:
            print(f'    verify {pid[:8]} gagal ({e}); coba lagi {coba + 1}/5', flush=True)
            time.sleep(3 * (coba + 1))
    raise RuntimeError('verify gagal 5 kali berturut-turut')

def mutate(f, v):
    if f in ('latitude', 'longitude'): return round(float(v) + 0.0000001, 7)
    v = str(v)
    if f in ('waktu_mulai', 'waktu_selesai'): return v[:-1] + ('1' if v[-1] != '1' else '2')
    return v[:-1] + ('a' if v[-1] != 'a' else 'b')

def leaf(r):
    return compute_leaf_hash(r['nama_peserta'], r['nama_kegiatan'], r['nama_lokasi'], r['latitude'], r['longitude'],
                             r['waktu_mulai'], r['waktu_selesai'], r['keterangan'], r['public_id'].replace('-', ''))

def bits(a, b): return bin(int.from_bytes(a, 'big') ^ int.from_bytes(b, 'big')).count('1')

det = {f: 0 for f in FIELDS}; bt = {f: [] for f in FIELDS}; lat = []
awal = sum(verify(r['public_id']) is True for r in rows)
print(f'Sebelum uji: valid {awal}/{len(rows)}', flush=True)
if awal != len(rows):
    print('BERHENTI: ada sertifikat yang sudah tidak valid sebelum uji. Jalankan dulu: python /app/cek_perbaiki.py')
    sys.exit(1)
for k, r in enumerate(rows):
    for f in FIELDS:
        o = r[f]; m = mutate(f, o)
        r2 = dict(r); r2[f] = m
        bt[f].append(bits(leaf(r), leaf(r2)))
        sb.table('sertifikat').update({f: m}).eq('public_id', r['public_id']).execute()
        try:
            t = time.time(); v = verify(r['public_id']); lat.append((time.time() - t) * 1000)
            if v is False: det[f] += 1
        finally:
            sb.table('sertifikat').update({f: o}).eq('public_id', r['public_id']).execute()
    if (k + 1) % 5 == 0: print(f'  {k + 1}/{len(rows)} sertifikat', flush=True)

akhir = sum(verify(r['public_id']) is True for r in rows)
n = len(rows); allb = [x for f in FIELDS for x in bt[f]]
print('\n=== HASIL ===')
print('Variabel | Terdeteksi | % | Rata2 bit berubah | Min-Maks')
for f in FIELDS:
    print(f'{f} | {det[f]}/{n} | {100*det[f]/n:.0f}% | {statistics.mean(bt[f]):.2f} | {min(bt[f])}-{max(bt[f])}')
print(f'TOTAL | {sum(det.values())}/{8*n} | {100*sum(det.values())/(8*n):.0f}% | {statistics.mean(allb):.2f} ({100*statistics.mean(allb)/256:.2f}%) | {min(allb)}-{max(allb)}')
print(f'Latensi verify saat dimanipulasi: rata2 {statistics.mean(lat):.0f} ms (n={len(lat)})')
print(f'Setelah pemulihan: valid {akhir}/{n}')