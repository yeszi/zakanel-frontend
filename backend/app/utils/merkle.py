import hashlib
import json

def hash_data(data: dict) -> str:
    """
    Menghasilkan SHA-256 hash dari data sertifikat (metadata).
    Data di-serialize ke JSON dengan urutan key yang konsisten (sort_keys=True)
    supaya hash selalu sama untuk data yang identik.
    """
    json_string = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_string.encode('utf-8')).hexdigest()


def build_merkle_tree(hashes: list) -> dict:
    """
    Membangun Merkle Tree dari daftar hash (leaf nodes).
    Mengembalikan Merkle Root dan seluruh level tree (untuk keperluan Merkle Proof).
    """
    if not hashes:
        raise ValueError("Daftar hash tidak boleh kosong")

    tree_levels = [hashes]  # level 0 = leaf nodes
    current_level = hashes

    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            # Kalau jumlah ganjil, node terakhir dipasangkan dengan dirinya sendiri
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            combined = left + right
            parent_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
            next_level.append(parent_hash)
        tree_levels.append(next_level)
        current_level = next_level

    merkle_root = current_level[0]

    return {
        "root": merkle_root,
        "levels": tree_levels
    }


def get_merkle_proof(tree_levels: list, leaf_index: int) -> list:
    """
    Mengambil Merkle Proof (daftar hash pendamping) untuk satu leaf tertentu,
    berdasarkan indeksnya di level paling bawah (leaf).
    """
    proof = []
    index = leaf_index

    for level in tree_levels[:-1]:  # jangan proses level terakhir (root)
        is_right_node = index % 2 == 1
        pair_index = index - 1 if is_right_node else index + 1

        if pair_index < len(level):
            proof.append({
                "hash": level[pair_index],
                "position": "left" if is_right_node else "right"
            })
        index = index // 2

    return proof


def verify_merkle_proof(leaf_hash: str, proof: list, root: str) -> bool:
    """
    Memverifikasi apakah sebuah leaf_hash + proof menghasilkan root yang sama
    dengan Merkle Root yang tersimpan (misalnya di Smart Contract).
    """
    computed_hash = leaf_hash

    for item in proof:
        if item["position"] == "left":
            combined = item["hash"] + computed_hash
        else:
            combined = computed_hash + item["hash"]
        computed_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()

    return computed_hash == root