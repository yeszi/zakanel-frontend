"""Cari sertifikat yang datanya tidak cocok lagi dengan cert_hash, lalu tebak nilai aslinya.
Jalankan DI DALAM container backend:
    python /app/cek_perbaiki.py            -> hanya mengecek (tidak mengubah apa pun)
    python /app/cek_perbaiki.py --perbaiki -> mengembalikan nilai yang ditemukan ke basis data

cert_hash disimpan saat penerbitan, jadi nilai asli dapat ditemukan dengan mencoba
kebalikan dari perubahan yang biasa dilakukan saat pengujian:
  - teks/waktu: karakter terakhir diganti (uji_manipulasi) atau ditambah 1 karakter (uji TC-15)
  - koordinat: ditambah/dikurangi 0,0000001 s.d. 0,0000003
"""
import sys, string
sys.path.insert(0, '/app')
from app import create_app
from app.utils.merkle import compute_leaf_hash

PERBAIKI = '--perbaiki' in sys.argv
app = create_app(); sb = app.supabase
FIELDS = ['nama_peserta', 'nama_kegiatan', 'nama_lokasi', 'latitude', 'longitude',
          'waktu_mulai', 'waktu_selesai', 'keterangan']
CH = string.ascii_letters + string.digits + ' .,-_()/:+'

def leaf(r):
    return compute_leaf_hash(r['nama_peserta'], r['nama_kegiatan'], r['nama_lokasi'], r['latitude'], r['longitude'],
                             r['waktu_mulai'], r['waktu_selesai'], r['keterangan'], r['public_id'].replace('-', '')).hex()

def kandidat(f, v):
    if v is None: return
    if f in ('latitude', 'longitude'):
        for d in (1, -1, 2, -2, 3, -3):
            yield round(float(v) + d * 0.0000001, 7)
        return
    v = str(v)
    if len(v) > 1: yield v[:-1]                      # karakter tambahan di akhir (mis. "Utomo1")
    for c in CH: yield v[:-1] + c                     # karakter terakhir diganti

rows = sb.table('sertifikat').select('*').order('leaf_index').execute().data
bid = max(r['batch_id'] for r in rows if r.get('batch_id') is not None)
rows = [r for r in rows if r.get('batch_id') == bid]
rusak = [r for r in rows if leaf(r) != (r.get('cert_hash') or '').lower().replace('0x', '')]
print(f'Batch {bid}: {len(rows)} sertifikat, tidak cocok dengan cert_hash: {len(rusak)}')

for r in rusak:
    print(f"\n- {r['public_id']} | {r['nama_peserta']} | {r['nama_kegiatan']}")
    target = (r.get('cert_hash') or '').lower().replace('0x', '')
    ketemu = None
    for f in FIELDS:
        for c in kandidat(f, r[f]):
            r2 = dict(r); r2[f] = c
            if leaf(r2) == target:
                ketemu = (f, r[f], c); break
        if ketemu: break
    if not ketemu:
        print('  Nilai asli tidak ditemukan otomatis. Bandingkan dengan file CSV cadangan sebelum migrasi/penerbitan.')
        continue
    f, sekarang, asli = ketemu
    print(f'  Kolom {f}: sekarang {sekarang!r} -> asli {asli!r}')
    if PERBAIKI:
        sb.table('sertifikat').update({f: asli}).eq('public_id', r['public_id']).execute()
        print('  Sudah dikembalikan ke nilai asli.')

if rusak and not PERBAIKI:
    print('\nJalankan lagi dengan --perbaiki untuk mengembalikan nilai yang ditemukan.')
