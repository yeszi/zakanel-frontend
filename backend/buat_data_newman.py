"""Buat file data CSV untuk koleksi Newman "Pengujian Per Sertifikat" dari batch terbaru.
Jalankan dari folder proyek (Windows CMD/PowerShell):
    docker compose exec -T backend python /app/buat_data_newman.py > data_sertifikat.csv
Nama kolom default "public_id". Jika CSV lama memakai nama kolom lain (mis. "id"):
    docker compose exec -T backend python /app/buat_data_newman.py id > data_sertifikat.csv
"""
import sys, io, contextlib
sys.path.insert(0, '/app')
with contextlib.redirect_stdout(io.StringIO()):      # sembunyikan log "CORS origins..." agar CSV bersih
    from app import create_app
    app = create_app()
kolom = sys.argv[1] if len(sys.argv) > 1 else 'public_id'
rows = app.supabase.table('sertifikat').select('public_id,batch_id,leaf_index').order('leaf_index').execute().data
bid = max(r['batch_id'] for r in rows if r.get('batch_id') is not None)
print(kolom)
for r in rows:
    if r.get('batch_id') == bid:
        print(r['public_id'])
