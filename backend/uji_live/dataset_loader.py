"""Muat dataset pengguna (CSV/XLSX) bila tersedia; jika tidak, pakai data sintetis."""
import os, csv
import dataset
COLS = ['nama_peserta', 'nama_kegiatan', 'nama_lokasi', 'latitude', 'longitude', 'waktu_mulai', 'waktu_selesai', 'keterangan']
def load(path=None):
    path = path or os.getenv('DATASET_PATH')
    if not path or not os.path.exists(path):
        return dataset.build(), 'sintetis'
    rows = []
    if path.lower().endswith(('.xlsx', '.xls')):
        import openpyxl
        ws = openpyxl.load_workbook(path, data_only=True).active
        it = ws.iter_rows(values_only=True); hdr = [str(h).strip().lower() for h in next(it)]
        for r in it:
            if any(v not in (None, '') for v in r): rows.append(dict(zip(hdr, r)))
    else:
        with open(path, newline='', encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        d = {c: ('' if r.get(c) is None else str(r.get(c)).strip()) for c in COLS}
        d['latitude'] = float(str(d['latitude']).replace(',', '.')); d['longitude'] = float(str(d['longitude']).replace(',', '.'))
        out.append(d)
    return out, os.path.basename(path)
