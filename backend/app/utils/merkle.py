import hashlib
import json
import unicodedata
from datetime import datetime, timezone, timedelta
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Serialisasi kanonik input leaf hash (revisi F01 Pak Hendra)
#   - objek JSON dengan urutan kunci TETAP (bukan string gabungan tanpa pemisah)
#   - teks dinormalisasi Unicode NFC, di-encode UTF-8
#   - koordinat ditulis dengan format desimal tetap (maks. 7 digit, nol di belakang dibuang)
#   - waktu ditulis ISO 8601 dengan zona waktu eksplisit (+07:00 bila data tanpa zona)
#   - JSON tanpa spasi tambahan
# Aturan ini WAJIB dipakai sama persis saat prepare (penerbitan), verify, dan batch-audit.
# ---------------------------------------------------------------------------
HASH_VERSION = 2
FIELD_ORDER = ('nama_peserta', 'nama_kegiatan', 'nama_lokasi', 'latitude', 'longitude',
               'waktu_mulai', 'waktu_selesai', 'keterangan', 'public_id')
WIB = timezone(timedelta(hours=7))


def fmt_coord(val):
    try:
        f = float(val)
        s = f"{f:.7f}".rstrip('0').rstrip('.')
        return s if s not in ('', '-0') else '0'
    except (TypeError, ValueError):
        return '' if val is None else str(val)


def _text(val):
    return unicodedata.normalize('NFC', '' if val is None else str(val))


def _time(val):
    if val is None or val == '':
        return ''
    s = str(val).replace('Z', '+00:00')
    try:
        d = datetime.fromisoformat(s)
    except ValueError:
        return _text(val)          # format tidak dikenal: dipakai apa adanya
    if d.tzinfo is None:
        d = d.replace(tzinfo=WIB)
    d = d.astimezone(WIB)          # waktu yang sama selalu ditulis dalam zona +07:00
    return d.isoformat(timespec='minutes' if d.second == 0 and d.microsecond == 0 else 'seconds')


def canonical_payload(nama_peserta, nama_kegiatan, nama_lokasi, lat, lon,
                      waktu_mulai='', waktu_selesai='', keterangan='', public_id='') -> str:
    data = {
        'nama_peserta': _text(nama_peserta),
        'nama_kegiatan': _text(nama_kegiatan),
        'nama_lokasi': _text(nama_lokasi),
        'latitude': fmt_coord(lat),
        'longitude': fmt_coord(lon),
        'waktu_mulai': _time(waktu_mulai),
        'waktu_selesai': _time(waktu_selesai),
        'keterangan': _text(keterangan),
        'public_id': _text(public_id).replace('-', ''),
    }
    ordered = {k: data[k] for k in FIELD_ORDER}   # urutan tetap, tidak bergantung dict
    return json.dumps(ordered, ensure_ascii=False, separators=(',', ':'))


def compute_leaf_hash(nama_peserta, nama_kegiatan, nama_lokasi, lat, lon,
                      waktu_mulai='', waktu_selesai='', keterangan='', public_id='') -> bytes:
    payload = canonical_payload(nama_peserta, nama_kegiatan, nama_lokasi, lat, lon,
                                waktu_mulai, waktu_selesai, keterangan, public_id)
    return hashlib.sha256(payload.encode('utf-8')).digest()


def compute_leaf_hash_v1(nama_peserta, nama_kegiatan, nama_lokasi, lat, lon,
                         waktu_mulai='', waktu_selesai='', keterangan='', public_id='') -> bytes:
    """Versi LAMA (penggabungan tanpa pemisah). Hanya untuk memverifikasi batch lama / pembanding uji."""
    lat_str = lat if isinstance(lat, str) else fmt_coord(lat)
    lon_str = lon if isinstance(lon, str) else fmt_coord(lon)
    parts = [nama_peserta, nama_kegiatan, nama_lokasi, lat_str, lon_str,
             '' if waktu_mulai is None else waktu_mulai, '' if waktu_selesai is None else waktu_selesai,
             '' if keterangan is None else keterangan, '' if public_id is None else public_id]
    return hashlib.sha256(''.join(str(p) for p in parts).encode('utf-8')).digest()


def build_merkle_tree(leaves: List[bytes]) -> Tuple[bytes, List[List[Tuple[bytes, str]]]]:
    if not leaves:
        return b'', []

    current_level = leaves[:]
    tree = [current_level]

    while len(tree[-1]) > 1:
        level = tree[-1]
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            next_level.append(hashlib.sha256(left + right).digest())
        tree.append(next_level)

    root = tree[-1][0]

    proofs = []
    for leaf_index in range(len(leaves)):
        proof = []
        idx = leaf_index
        for level_idx in range(len(tree) - 1):
            level = tree[level_idx]
            if idx % 2 == 0:
                sibling = level[idx + 1] if idx + 1 < len(level) else level[idx]
                side = 'right'
            else:
                sibling = level[idx - 1]
                side = 'left'
            proof.append((sibling, side))
            idx = idx // 2
        proofs.append(proof)

    return root, proofs


def verify_merkle_proof(leaf_hash: bytes, proof: List[Tuple[bytes, str]], root: bytes) -> bool:
    current = leaf_hash
    for sibling, side in proof:
        if side == 'left':
            current = hashlib.sha256(sibling + current).digest()
        else:
            current = hashlib.sha256(current + sibling).digest()
    return current == root


def encode_proof_for_db(proof: List[Tuple[bytes, str]]) -> str:
    return json.dumps([[sibling.hex(), side] for sibling, side in proof])


def decode_proof_from_db(proof_json: str) -> List[Tuple[bytes, str]]:
    if not proof_json or proof_json == '[]':
        return []
    try:
        data = json.loads(proof_json)
        return [(bytes.fromhex(item[0]), item[1]) for item in data]
    except (ValueError, TypeError, IndexError):
        return []
