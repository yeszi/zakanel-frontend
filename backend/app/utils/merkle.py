import hashlib
import json
from typing import List, Tuple

def fmt_coord(val):
    try:
        f = float(val)
        s = f"{f:.7f}".rstrip('0').rstrip('.')
        return s
    except:
        return str(val)

def compute_leaf_hash(nama_peserta, nama_kegiatan, nama_lokasi, lat, lon):
    lat_str = fmt_coord(lat)
    lon_str = fmt_coord(lon)
    data = f"{nama_peserta}{nama_kegiatan}{nama_lokasi}{lat_str}{lon_str}"
    return hashlib.sha256(data.encode('utf-8')).digest()

def build_merkle_tree(leaves: List[bytes]) -> Tuple[bytes, List[List[Tuple[bytes, str]]]]:
    if not leaves:
        return b'', []

    # Copy leaves agar tidak merubah original
    current_level = leaves[:]
    
    # Duplikasi leaf terakhir jika jumlah ganjil
    if len(current_level) % 2 == 1:
        current_level = current_level + [current_level[-1]]
    
    tree = [current_level]
    
    while len(tree[-1]) > 1:
        current_level = tree[-1]
        next_level = []
        
        # Pastikan genap di setiap level
        if len(current_level) % 2 == 1:
            current_level = current_level + [current_level[-1]]
        
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i+1]
            combined = left + right
            next_level.append(hashlib.sha256(combined).digest())
        
        tree.append(next_level)
    
    root = tree[-1][0]
    
    # Buat proof untuk setiap leaf ORIGINAL (sebelum duplikasi)
    proofs = []
    for leaf_index in range(len(leaves)):
        proof = []
        idx = leaf_index
        
        for level_idx in range(len(tree) - 1):
            level = tree[level_idx]
            
            if idx % 2 == 0:
                # Anak kiri -> sibling di kanan
                if idx + 1 < len(level):
                    sibling = level[idx + 1]
                    side = 'right'
                else:
                    sibling = level[idx]
                    side = 'right'
            else:
                # Anak kanan -> sibling di kiri
                sibling = level[idx - 1]
                side = 'left'
            
            proof.append((sibling, side))
            idx = idx // 2
        
        proofs.append(proof)
    
    return root, proofs

def verify_merkle_proof(leaf_hash: bytes, proof: List[Tuple[bytes, str]], root: bytes) -> bool:
    if not proof:
        return leaf_hash == root
    
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