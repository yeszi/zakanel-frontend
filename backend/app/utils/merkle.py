import hashlib
import json
from typing import List, Tuple

def fmt_coord(val):
    try:
        f = float(val)
        s = f"{f:.7f}".rstrip('0').rstrip('.')
        return s if s != '' else '0'
    except:
        return str(val)

def compute_leaf_hash(nama_peserta, nama_kegiatan, nama_lokasi, lat, lon):
    lat_str = lat if isinstance(lat, str) else fmt_coord(lat)
    lon_str = lon if isinstance(lon, str) else fmt_coord(lon)
    data = f"{nama_peserta}{nama_kegiatan}{nama_lokasi}{lat_str}{lon_str}"
    return hashlib.sha256(data.encode('utf-8')).digest()

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
            right = level[i+1] if i+1 < len(level) else level[i]
            combined = left + right
            next_level.append(hashlib.sha256(combined).digest())
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
    except:
        return []