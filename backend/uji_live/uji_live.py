"""
PENGUJIAN TERINTEGRASI (LIVE): Supabase + Ethereum Sepolia (via Infura)
=======================================================================
Menjalankan skenario TC-01 s.d. TC-15, pengujian RBAC/JWT, validasi transaksi,
konsistensi off-chain vs on-chain, deteksi manipulasi, dan waktu respons
terhadap Supabase dan smart contract yang SEBENARNYA.

Cara pakai (dari folder backend):
    pip install -r requirements.txt -r uji_live/requirements-uji.txt
    copy uji_live\\.env.uji.example uji_live\\.env.uji      (lalu isi)
    python uji_live/uji_live.py                             (uji)
    python uji_live/uji_live.py --bersihkan                 (hapus data uji)

Hasil: uji_live/hasil_uji_live.json  -> kirim file ini (TIDAK berisi kunci/rahasia).
PRIVATE KEY HANYA DIBACA DARI .env.uji DI KOMPUTER ANDA. JANGAN DIBAGIKAN.
"""
import os, sys, json, time, math, base64, threading, statistics, logging, argparse, datetime, platform

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, BACKEND); sys.path.insert(0, HERE)
os.chdir(BACKEND)

from dotenv import load_dotenv
load_dotenv(os.path.join(BACKEND, '.env'))
load_dotenv(os.path.join(HERE, '.env.uji'), override=True)

import requests, jwt, numpy as np, cv2
from web3 import Web3
from eth_account import Account

ap = argparse.ArgumentParser()
ap.add_argument('--bersihkan', action='store_true', help='hapus akun/sertifikat/batch uji dari Supabase lalu keluar')
ap.add_argument('--tanpa-deteksi', action='store_true', help='lewati uji deteksi manipulasi 8 variabel (paling lama)')
args = ap.parse_args()

def need(k):
    v = os.getenv(k)
    if not v: sys.exit(f'[X] {k} belum diisi di .env / uji_live/.env.uji')
    return v

ADMIN_USER, ADMIN_PASS = need('UJI_ADMIN_USERNAME'), need('UJI_ADMIN_PASSWORD')
KA, K1, K2 = need('UJI_ADMIN_PRIVATE_KEY'), need('UJI_PENERBIT1_PRIVATE_KEY'), need('UJI_PENERBIT2_PRIVATE_KEY')
ADMIN, PUB1, PUB2 = (Account.from_key(k).address for k in (KA, K1, K2))
BENCH_N = int(os.getenv('UJI_BENCH_N', '20'))
WALLET_BENCH_N = int(os.getenv('UJI_WALLET_BENCH_N', '3'))
PREFIX = 'uji_'
U1N, U2N, PW = PREFIX + 'penerbit1', PREFIX + 'penerbit2', 'Penerbit#Uji2026'

from app import create_app
from app.utils.audit import verify_audit_chain, compute_entry_hash, GENESIS_HASH
from app.utils.merkle import build_merkle_tree, verify_merkle_proof, decode_proof_from_db, compute_leaf_hash
app = create_app()
sb, w3 = app.supabase, app.w3
abi = json.load(open(os.path.join(BACKEND, 'abi.json')))['abi']
K = w3.eth.contract(address=app.contract_address, abi=abi)

def log(*a): print(*a, flush=True)

# ---------------------------------------------------------------- bersihkan
def bersihkan():
    us = sb.table('users').select('id, username').like('username', PREFIX + '%').execute().data
    ids = [u['id'] for u in us]
    if ids:
        sb.table('sertifikat').delete().in_('penerbit_id', ids).execute()
        sb.table('batch_sertifikat').delete().in_('penerbit_id', ids).execute()
        sb.table('users').delete().in_('id', ids).execute()
    log(f'[i] Data uji dihapus: {len(ids)} akun uji beserta sertifikat & batch-nya (audit log tidak dapat dihapus karena append-only).')

if args.bersihkan:
    bersihkan(); sys.exit(0)

# ---------------------------------------------------------------- pra-cek
log('== PRA-CEK ==')
chain_id = w3.eth.chain_id
onchain_admin = K.functions.admin().call()
bal = {n: w3.from_wei(w3.eth.get_balance(a), 'ether') for n, a in (('admin', ADMIN), ('penerbit1', PUB1), ('penerbit2', PUB2))}
log(f'chain_id={chain_id}  kontrak={app.contract_address}  admin kontrak={onchain_admin}')
log(f'saldo Sepolia ETH: {bal}')
if chain_id != int(os.getenv('UJI_DEV_CHAIN', '11155111')): sys.exit('[X] RPC bukan Sepolia (chain id 11155111).')
if onchain_admin.lower() != ADMIN.lower(): sys.exit('[X] UJI_ADMIN_PRIVATE_KEY bukan wallet admin (pembuat) smart contract.')
if len({ADMIN, PUB1, PUB2}) < 3: sys.exit('[X] Wallet admin, penerbit1, penerbit2 harus berbeda.')
for n in ('admin', 'penerbit1'):
    if bal[n] < 0.01: sys.exit(f'[X] Saldo {n} kurang (< 0.01 SepoliaETH). Isi dari faucet dulu.')
if bal['penerbit2'] < 0.003: sys.exit('[X] Saldo penerbit2 kurang (< 0.003 SepoliaETH).')
bersihkan()

# ---------------------------------------------------------------- server
API = os.getenv('UJI_API_URL', '').rstrip('/')
if not API:
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    from werkzeug.serving import make_server
    srv = make_server('127.0.0.1', 5059, app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    API = 'http://127.0.0.1:5059'
B = API
log(f'API diuji: {B}')

T_START_UTC = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
R = {'env': 'live', 'waktu_uji': datetime.datetime.now().isoformat(timespec='seconds'), 'platform': platform.platform(),
     'contract': app.contract_address, 'chain_id': chain_id, 'api': 'lokal (in-process)' if B.startswith('http://127.') else 'deploy',
     'tc': [], 'timing': {}, 'rbac': [], 'txval': [], 'misc': {}, 'tx': []}
def tc(id, fr, name, expected, actual, ok):
    R['tc'].append(dict(id=id, fr=fr, name=name, expected=expected, actual=actual, status='PASS' if ok else 'FAIL'))
    log(f'  {id} {"PASS" if ok else "FAIL"}  {actual}')
def timed(fn):
    t = time.perf_counter(); r = fn(); return r, (time.perf_counter() - t) * 1000
def stats(xs):
    xs = sorted(xs)
    if not xs: return dict(n=0, mean=0, min=0, max=0, p95=0, sd=0)
    return dict(n=len(xs), mean=round(statistics.mean(xs), 2), min=round(xs[0], 2), max=round(xs[-1], 2),
                p95=round(xs[max(0, int(len(xs) * 0.95) - 1)], 2), sd=round(statistics.pstdev(xs), 2))
H = lambda t: {'Authorization': f'Bearer {t}'}
def J(r):
    try: return r.json()
    except Exception: return {}

def send(fn, key, label):
    acct = Account.from_key(key)
    tx = fn.build_transaction({'from': acct.address, 'nonce': w3.eth.get_transaction_count(acct.address, 'pending'), 'chainId': chain_id})
    signed = acct.sign_transaction(tx)
    raw = getattr(signed, 'raw_transaction', None) or getattr(signed, 'rawTransaction')
    t0 = time.perf_counter(); h = w3.eth.send_raw_transaction(raw)
    rc = w3.eth.wait_for_transaction_receipt(h, timeout=600, poll_latency=1)
    dt = time.perf_counter() - t0
    txh = '0x' + rc['transactionHash'].hex().removeprefix('0x')
    egp = rc.get('effectiveGasPrice', 0)
    R['tx'].append(dict(label=label, tx=txh, gas=rc['gasUsed'], gwei=round(egp / 1e9, 4), eth=float(w3.from_wei(rc['gasUsed'] * egp, 'ether')),
                        konfirmasi_s=round(dt, 2), block=rc['blockNumber'], status=rc['status']))
    log(f'    tx {label}: {txh[:14]}… gas={rc["gasUsed"]} konfirmasi {dt:.1f}s')
    if rc['status'] != 1: raise RuntimeError(f'transaksi {label} gagal')
    return txh, rc['gasUsed']

def b32(pid):
    b = pid.encode()[:32]; return b + b'\0' * (32 - len(b))
def login(u, p): return requests.post(B + '/api/auth/login', json={'username': u, 'password': p}, timeout=60)
def uid_of(u): return sb.table('users').select('id').eq('username', u).execute().data[0]['id']
def cert_row(pid_hex):
    pid = f'{pid_hex[:8]}-{pid_hex[8:12]}-{pid_hex[12:16]}-{pid_hex[16:20]}-{pid_hex[20:]}'
    return sb.table('sertifikat').select('*').eq('public_id', pid).execute().data[0]
def upd_cert(row, field, value):
    sb.table('sertifikat').update({field: value}).eq('id', row['id']).execute()

# ================================================================ TC-01/02
log('== AUTENTIKASI ==')
r = login(ADMIN_USER, ADMIN_PASS)
if r.status_code != 200: sys.exit(f'[X] Login admin gagal: {r.status_code} {r.text[:200]}')
TA = r.json()['token']; pl = jwt.decode(TA, options={'verify_signature': False})
tc('TC-01', 'FR-01', 'Login berhasil (admin)', '200 OK, JWT diterbitkan, diarahkan ke /admin', f"{r.status_code}, role={pl['role']}, JWT {jwt.get_unverified_header(TA)['alg']} berlaku {(pl['exp']-pl['iat'])//60} menit", r.status_code == 200 and pl['role'] == 'admin')
R['misc']['jwt_example'] = {'header': jwt.get_unverified_header(TA), 'payload': {k: pl.get(k) for k in ('sub', 'username', 'role', 'wallet', 'iat', 'exp', 'jti')}, 'len': len(TA)}
r = login(ADMIN_USER, ADMIN_PASS + '_salah')
tc('TC-02', 'FR-01', 'Login gagal (password salah)', '401 Unauthorized, tetap di halaman login', f"{r.status_code}, {J(r).get('message') or J(r).get('error')}", r.status_code == 401)

# ================================================================ TC-03
log('== TAMBAH PENERBIT (Sepolia) ==')
gas = {}
def add_penerbit(uname, wal, nama):
    c = requests.get(B + '/api/penerbit/check', params={'username': uname, 'wallet_address': wal}, headers=H(TA))
    txh, g = send(K.functions.tambahPenerbit(wal), KA, f'tambahPenerbit {uname}')
    r = requests.post(B + '/api/penerbit', json={'username': uname, 'password': PW, 'wallet_address': wal, 'nama_lengkap': nama, 'tx_hash': txh}, headers=H(TA), timeout=120)
    return c.status_code, r, g, txh
c1, r1, gas['tambah'], tx_add1 = add_penerbit(U1N, PUB1, 'Laboratorium Komputer FTTK (uji)')
c2, r2, _, _ = add_penerbit(U2N, PUB2, 'Laboratorium Jaringan FTTK (uji)')
act1 = K.functions.isPenerbitActive(PUB1).call()
tc('TC-03', 'FR-02/FR-03', 'Admin tambah penerbit', 'Wallet aktif di smart contract, tx diverifikasi backend, data tersimpan', f"cek={c1}, tx tambahPenerbit (gas {gas['tambah']}) terverifikasi, HTTP {r1.status_code}/{r2.status_code}, isPenerbitActive={act1}", r1.status_code == 200 and r2.status_code == 200 and act1)
if r1.status_code != 200 or r2.status_code != 200: sys.exit(f'[X] Tambah penerbit gagal: {r1.text[:200]} {r2.text[:200]}')
T1, T2 = login(U1N, PW).json()['token'], login(U2N, PW).json()['token']

# ================================================================ terbitkan batch
log('== PENERBITAN BATCH (Sepolia) ==')
import dataset_loader
data, SRC = dataset_loader.load()
R['dataset'] = dict(sumber=SRC, jumlah=len(data))
from collections import OrderedDict
_g = OrderedDict()
for d in data: _g.setdefault(d['nama_kegiatan'], []).append(d)
groups = list(_g.values())
if len(groups) < 2: groups = [data[i:i + 10] for i in range(0, len(data), 10)]
batches, tprep, tconf = [], [], []
for gi, g in enumerate(groups):
    tok, key, un = (T1, K1, U1N) if gi < (len(groups) + 1) // 2 else (T2, K2, U2N)
    r, t = timed(lambda: requests.post(B + '/api/sertifikat/prepare', json={'sertifikat_list': g}, headers=H(tok), timeout=300)); tprep.append(t); j = r.json()
    if r.status_code != 200: sys.exit(f'[X] prepare gagal: {r.text[:300]}')
    txh, gu = send(K.functions.simpanRoot(j['batch_id'], j['merkle_root'], b32(j['first_public_id'])), key, f'simpanRoot batch {gi+1} ({len(g)} data)')
    r2_, t2 = timed(lambda: requests.post(B + '/api/sertifikat/konfirmasi', json={'merkle_root': j['merkle_root'], 'tx_hash': txh, 'batch_id_onchain': j['batch_id'], 'sertifikat_list': [{'public_id': d['public_id']} for d in j['data']]}, headers=H(tok), timeout=300)); tconf.append(t2)
    batches.append(dict(kegiatan=g[0]['nama_kegiatan'], n=len(g), batch_id=j['batch_id'], root=j['merkle_root'], tx=txh, gas=gu, prep_status=r.status_code, conf=J(r2_), ids=[d['public_id'].replace('-', '') for d in j['data']], user=un))
gas['simpan'] = batches[0]['gas']
R['batches'] = [{k: v for k, v in b.items() if k != 'ids'} for b in batches]
allids = [i for b in batches for i in b['ids']]
c0 = cert_row(batches[0]['ids'][0])
tc('TC-05', 'FR-04', 'Penerbit input 8 metadata', 'Hash dihitung, metadata tersimpan', f"HTTP {batches[0]['prep_status']}, {batches[0]['n']} baris tersimpan di Supabase, cert_hash={c0['cert_hash'][:16]}…", batches[0]['prep_status'] == 200 and len(c0['cert_hash']) == 64)
depth = len(json.loads(c0['merkle_proof'])) if isinstance(c0['merkle_proof'], str) else len(c0['merkle_proof'])
exp_depth = math.ceil(math.log2(batches[0]['n'])) if batches[0]['n'] > 1 else 0
tc('TC-06', 'FR-05', 'Pembentukan Merkle Tree', 'Pohon biner terbentuk', f"{batches[0]['n']} daun -> {exp_depth + 1} tingkat, proof {depth} simpul per daun", depth == exp_depth)
tc('TC-07', 'FR-05', 'Perhitungan Merkle Root', '1 nilai 256-bit (64 karakter hex)', f"{batches[0]['root'][:20]}… ({len(batches[0]['root'])-2} karakter hex)", len(batches[0]['root']) == 66)
pub = sb.table('sertifikat').select('status').in_('batch_id', [b['batch_id'] for b in batches]).execute().data
okc = all(b['conf'].get('success') for b in batches) and all(x['status'] == 'published' for x in pub)
tc('TC-08', 'FR-06/FR-07', 'Penerbit terbitkan sertifikat (simpanRoot)', 'Root tersimpan on-chain, tx divalidasi, status published', f"{len(batches)} tx sukses di Sepolia (gas {gas['simpan']}), {len(pub)} sertifikat published di Supabase", okc)

pid0 = batches[0]['ids'][0]
r = requests.get(B + f'/api/sertifikat/generate-qr/{pid0}'); img = base64.b64decode(r.json()['qr_code'].split(',')[1])
def qr_decode(im):
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) if im.ndim == 3 else im
    for sc in (1, 2, 3, 0.5):
        x = gray if sc == 1 else cv2.resize(gray, None, fx=sc, fy=sc, interpolation=cv2.INTER_NEAREST)
        for det in (cv2.QRCodeDetector(),) + ((cv2.QRCodeDetectorAruco(),) if hasattr(cv2, 'QRCodeDetectorAruco') else ()):
            try: u = det.detectAndDecode(x)[0]
            except Exception: u = ''
            if u: return u
    return ''
dec = qr_decode(cv2.imdecode(np.frombuffer(img, np.uint8), cv2.IMREAD_COLOR))
tc('TC-09', 'FR-08', 'Generate QR Code', 'QR dapat dipindai dan mengarah ke URL verifikasi', f"Hasil decode: {dec}", dec.endswith(pid0))
r = requests.get(B + f'/api/sertifikat/verify/{pid0}').json()
tc('TC-10', 'FR-09', 'Verifikasi sertifikat valid', 'Menampilkan “Sertifikat Valid”', f"valid={r['valid']}; {r['message']}", r['valid'] is True)
row = cert_row(pid0); upd_cert(row, 'nama_peserta', row['nama_peserta'] + 'x')
try: ra = requests.get(B + f'/api/sertifikat/verify/{pid0}').json()
finally: upd_cert(row, 'nama_peserta', row['nama_peserta'])
rb = requests.get(B + '/api/sertifikat/verify/' + 'ab' * 16).json()
tc('TC-11', 'FR-09', 'Verifikasi sertifikat tidak valid', 'Menampilkan “Sertifikat Tidak Valid”', f"Data diubah di Supabase: valid={ra['valid']} ({ra['message']}); ID palsu: valid={rb['valid']}", ra['valid'] is False and rb['valid'] is False)

# ================================================================ validasi transaksi (sebelum pencabutan)
log('== VALIDASI TRANSAKSI ==')
uid1, uid2 = uid_of(U1N), uid_of(U2N)
j3 = requests.post(B + '/api/sertifikat/prepare', json={'sertifikat_list': data[:2]}, headers=H(T1)).json()
j4 = requests.post(B + '/api/sertifikat/prepare', json={'sertifikat_list': data[:2]}, headers=H(T1)).json()
tx4, _ = send(K.functions.simpanRoot(j4['batch_id'], j4['merkle_root'], b'\0' * 32), K2, 'simpanRoot batch penerbit1 oleh wallet penerbit2 (uji)')
OUTW = Account.create().address
tv = [
 ('Tambah penerbit dengan tx_hash palsu', lambda: requests.post(B + '/api/penerbit', json={'username': PREFIX + 'p9', 'password': PW, 'wallet_address': OUTW, 'tx_hash': '0x' + 'ab' * 32}, headers=H(TA))),
 ('Tambah penerbit memakai tx milik wallet lain', lambda: requests.post(B + '/api/penerbit', json={'username': PREFIX + 'p9', 'password': PW, 'wallet_address': OUTW, 'tx_hash': tx_add1}, headers=H(TA))),
 ('Cabut penerbit tanpa tx cabutPenerbit', lambda: requests.post(B + f'/api/penerbit/{uid1}/revoke', json={'tx_hash': batches[0]['tx']}, headers=H(TA))),
 ('Konfirmasi dengan tx_hash palsu', lambda: requests.post(B + '/api/sertifikat/konfirmasi', json={'merkle_root': j3['merkle_root'], 'tx_hash': '0x' + 'ab' * 32, 'batch_id_onchain': j3['batch_id']}, headers=H(T1))),
 ('Konfirmasi dengan tx milik batch lain', lambda: requests.post(B + '/api/sertifikat/konfirmasi', json={'merkle_root': j3['merkle_root'], 'tx_hash': batches[0]['tx'], 'batch_id_onchain': j3['batch_id']}, headers=H(T1))),
 ('Username/wallet duplikat (cek sebelum bayar gas)', lambda: requests.get(B + '/api/penerbit/check', params={'username': U1N, 'wallet_address': PUB1}, headers=H(TA))),
 ('Konfirmasi tx simpanRoot yang dikirim wallet lain', lambda: requests.post(B + '/api/sertifikat/konfirmasi', json={'merkle_root': j4['merkle_root'], 'tx_hash': tx4, 'batch_id_onchain': j4['batch_id']}, headers=H(T1))),
]
for sk, fn in tv:
    r = fn(); R['txval'].append(dict(skenario=sk, status=r.status_code, msg=(J(r).get('error') or '')[:110])); log(f'  {r.status_code} {sk}')
for jj in (j3, j4):  # hapus draft uji
    sb.table('sertifikat').delete().eq('batch_id', jj['batch_id']).execute(); sb.table('batch_sertifikat').delete().eq('id', jj['batch_id']).execute()

# ================================================================ TC-04
log('== CABUT PENERBIT (Sepolia) ==')
txc, gas['cabut'] = send(K.functions.cabutPenerbit(PUB2), KA, 'cabutPenerbit penerbit2')
r = requests.post(B + f'/api/penerbit/{uid2}/revoke', json={'tx_hash': txc}, headers=H(TA), timeout=120)
rl = login(U2N, PW); rt = requests.get(B + '/api/sertifikat', headers=H(T2))
try: K.functions.simpanRoot(99, b'\x11' * 32, b'\0' * 32).call({'from': PUB2}); rev = 'tidak revert'
except Exception as e: rev = str(e)
tc('TC-04', 'FR-02/FR-03', 'Admin cabut hak penerbit', 'Status dicabut, penerbit tidak dapat login/menerbitkan', f"HTTP {r.status_code}; login={rl.status_code}; token lama={rt.status_code}; isPenerbitActive={K.functions.isPenerbitActive(PUB2).call()}; simpanRoot revert", r.status_code == 200 and rl.status_code == 403 and rt.status_code == 403 and 'Bukan penerbit aktif' in rev)
R['misc']['revert_revoked'] = rev[:160]

# ================================================================ RBAC
log('== RBAC & JWT ==')
now = int(time.time())
forged = jwt.encode({'sub': '1', 'username': ADMIN_USER, 'role': 'admin', 'iat': now, 'exp': now + 600}, 'secret-salah-' * 4, algorithm='HS256')
expired = jwt.encode({'sub': str(pl['sub']), 'username': ADMIN_USER, 'role': 'admin', 'iat': now - 7200, 'exp': now - 3600}, os.getenv('JWT_SECRET'), algorithm='HS256')
none_tok = 'eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxIiwicm9sZSI6ImFkbWluIiwiZXhwIjo5OTk5OTk5OTk5fQ.'
cases = [
 ('POST /api/penerbit', 'Tanpa token', lambda: requests.post(B + '/api/penerbit', json={'username': 'a', 'password': '12345678'})),
 ('POST /api/penerbit', 'Header X-User-Role: admin dipalsukan', lambda: requests.post(B + '/api/penerbit', json={'username': 'a', 'password': '12345678'}, headers={'X-User-Role': 'admin', 'X-User-ID': '1'})),
 ('POST /api/penerbit', 'Token peran penerbit', lambda: requests.post(B + '/api/penerbit', json={'username': 'a', 'password': '12345678'}, headers=H(T1))),
 ('POST /api/penerbit/{id}/revoke', 'Token peran penerbit', lambda: requests.post(B + f'/api/penerbit/{uid1}/revoke', json={}, headers=H(T1))),
 ('POST /api/penerbit/{id}/activate', 'Tanpa token', lambda: requests.post(B + f'/api/penerbit/{uid2}/activate', json={})),
 ('POST /api/sertifikat/prepare', 'Tanpa token', lambda: requests.post(B + '/api/sertifikat/prepare', json={'sertifikat_list': data[:1]})),
 ('POST /api/sertifikat/prepare', 'Token peran admin', lambda: requests.post(B + '/api/sertifikat/prepare', json={'sertifikat_list': data[:1]}, headers=H(TA))),
 ('POST /api/sertifikat/fix-proof/{batch}', 'Token peran penerbit', lambda: requests.post(B + f"/api/sertifikat/fix-proof/{batches[0]['batch_id']}", headers=H(T1))),
 ('GET /api/audit', 'Token peran penerbit', lambda: requests.get(B + '/api/audit', headers=H(T1))),
 ('GET /api/penerbit', 'Token ditandatangani secret lain', lambda: requests.get(B + '/api/penerbit', headers=H(forged))),
 ('GET /api/penerbit', 'Token kedaluwarsa', lambda: requests.get(B + '/api/penerbit', headers=H(expired))),
 ('GET /api/penerbit', 'Token alg=none', lambda: requests.get(B + '/api/penerbit', headers=H(none_tok))),
 ('GET /api/sertifikat', 'Token lama penerbit yang dicabut', lambda: requests.get(B + '/api/sertifikat', headers=H(T2))),
 ('POST /api/auth/login', 'Login penerbit yang dicabut', lambda: login(U2N, PW)),
 ('POST /api/sertifikat/konfirmasi', 'Konfirmasi batch milik penerbit lain', lambda: requests.post(B + '/api/sertifikat/konfirmasi', json={'merkle_root': batches[-1]['root'], 'tx_hash': batches[-1]['tx'], 'batch_id_onchain': batches[-1]['batch_id']}, headers=H(T1))),
 ('POST /api/auth/register', 'Registrasi publik setelah admin ada', lambda: requests.post(B + '/api/auth/register', json={'username': 'x', 'password': '12345678'})),
]
for ep, sk, fn in cases:
    r = fn(); R['rbac'].append(dict(endpoint=ep, skenario=sk, status=r.status_code, msg=((J(r).get('error') or J(r).get('message') or ''))[:80]))
log(f"  {sum(1 for x in R['rbac'] if x['status'] >= 400)}/{len(R['rbac'])} ditolak")
sc_rev = {}
for nm, fn, frm in (('tambah_by_nonadmin', K.functions.tambahPenerbit(PUB2), PUB1), ('cabut_by_nonadmin', K.functions.cabutPenerbit(PUB1), PUB1),
                    ('simpan_by_outsider', K.functions.simpanRoot(98, b'\x22' * 32, b'\0' * 32), OUTW), ('simpan_by_revoked', K.functions.simpanRoot(97, b'\x33' * 32, b'\0' * 32), PUB2)):
    try: fn.call({'from': frm}); sc_rev[nm] = 'TIDAK revert'
    except Exception as e: sc_rev[nm] = str(e)[:120]
R['misc']['contract_rbac'] = sc_rev

# ================================================================ konsistensi & verifikasi
log('== KONSISTENSI OFF-CHAIN vs ON-CHAIN ==')
cons = pv = 0; all_rows = {}
for b in batches:
    rows = sorted(sb.table('sertifikat').select('*').eq('batch_id', b['batch_id']).execute().data, key=lambda x: x['leaf_index'])
    rd, _ = build_merkle_tree([bytes.fromhex(x['cert_hash']) for x in rows]); oc = K.functions.getRoot(int(b['batch_id'])).call()
    for x in rows:
        all_rows[x['public_id'].replace('-', '')] = x
        cons += rd == oc
        lf = compute_leaf_hash(x['nama_peserta'], x['nama_kegiatan'], x['nama_lokasi'], x['latitude'], x['longitude'], x['waktu_mulai'], x['waktu_selesai'], x['keterangan'], x['public_id'].replace('-', ''))
        pv += verify_merkle_proof(lf, decode_proof_from_db(x['merkle_proof']), oc)
R['misc']['konsistensi'] = dict(match=cons, total=len(allids), proof_valid=pv)
tver = []; nv = 0
for pid in allids:
    r, t = timed(lambda: requests.get(B + f'/api/sertifikat/verify/{pid}')); tver.append(t); nv += r.json()['valid'] is True
R['misc']['verify_all'] = dict(valid=nv, total=len(allids))
log(f'  root cocok {cons}/{len(allids)}, proof valid {pv}, verify valid {nv}')

# ================================================================ deteksi manipulasi
FIELDS = ['nama_kegiatan', 'nama_lokasi', 'latitude', 'longitude', 'waktu_mulai', 'waktu_selesai', 'keterangan', 'nama_peserta']
def mutate(f, v):
    if f in ('latitude', 'longitude'): return round(float(v) + 0.0000001, 7)
    v = str(v)
    if f in ('waktu_mulai', 'waktu_selesai'): return v[:-1] + ('1' if v[-1] != '1' else '2')
    return v[:-1] + ('a' if v[-1] != 'a' else 'b')
if not args.tanpa_deteksi:
    log(f'== DETEKSI MANIPULASI ({8 * len(allids)} skenario, mengubah lalu memulihkan data di Supabase) ==')
    det = {f: 0 for f in FIELDS}
    for k, pid in enumerate(allids):
        row = all_rows[pid]
        for f in FIELDS:
            o = row[f]; upd_cert(row, f, mutate(f, o))
            try:
                if requests.get(B + f'/api/sertifikat/verify/{pid}').json()['valid'] is False: det[f] += 1
            finally:
                upd_cert(row, f, o)
        if (k + 1) % 10 == 0: log(f'  {k + 1}/{len(allids)} sertifikat')
    R['misc']['deteksi'] = det
    after = sum(requests.get(B + f'/api/sertifikat/verify/{p}').json()['valid'] is True for p in allids)
    R['misc']['setelah_pemulihan_valid'] = after
    log(f'  terdeteksi {sum(det.values())}/{8 * len(allids)}; setelah pemulihan valid {after}/{len(allids)}')

# ================================================================ TC-12 / TC-13
log('== AUDIT LOG ==')
logs = requests.get(B + '/api/audit', params={'limit': 1000}, headers=H(TA)).json()['logs']
t_start = T_START_UTC
acts = {}
for l in logs:
    if l['logged_at'] < t_start[:19]: continue
    acts.setdefault(l['action'], {}).setdefault(l['status'], 0); acts[l['action']][l['status']] += 1
R['misc']['audit_actions'] = acts
need_a = ['LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGIN_BLOCKED', 'ACCESS_DENIED', 'PENERBIT_ADD', 'PENERBIT_REVOKE', 'CERT_PREPARE', 'CERT_PUBLISH', 'CERT_VERIFY']
tx_logged = sum(1 for l in logs if l.get('tx_hash') and l['logged_at'] >= t_start[:19])
tc('TC-12', 'FR-10', 'Pencatatan audit log', 'Setiap aktivitas penting tercatat beserta aktor, waktu, status, dan tx_hash', f"{len([a for a in need_a if a in acts])}/{len(need_a)} jenis aktivitas utama tercatat di Supabase; {tx_logged} entri memuat tx_hash", all(a in acts for a in need_a))
v0, tv0 = timed(lambda: requests.get(B + '/api/audit/verify', headers=H(TA), timeout=300).json())
victim = sb.table('audit_logs').select('id').order('id', desc=True).limit(1).execute().data[0]['id']
def coba(fn):
    try: fn(); return 'DITERIMA (tidak ditolak!)'
    except Exception as e: return 'ditolak: ' + str(e)[:140]
up = coba(lambda: sb.table('audit_logs').update({'detail': '{}'}).eq('id', victim).execute())
de = coba(lambda: sb.table('audit_logs').delete().eq('id', victim).execute())
v2 = requests.get(B + '/api/audit/verify', headers=H(TA), timeout=300).json()
R['misc']['audit_live'] = dict(chain_valid=v0['valid'], total=v0['total'], verify_ms=round(tv0, 2), update=up, delete=de, valid_after=v2['valid'], broken_at=v0.get('broken_at_id'), reason=v0.get('reason'))
ok13 = v0['valid'] and up.startswith('ditolak') and de.startswith('ditolak') and v2['valid']
tc('TC-13', 'FR-10', 'Perlindungan dan integritas audit log', 'UPDATE/DELETE pada audit_logs ditolak; verifikasi rantai valid', f"rantai {v0['total']} entri valid={v0['valid']}; UPDATE {up.split(':')[0]}; DELETE {de.split(':')[0]}", ok13)

# ================================================================ TC-14 PDF
log('== PDF ==')
rp, _ = timed(lambda: requests.get(B + f'/api/sertifikat/{pid0}/pdf', headers=H(T1), timeout=120))
open(os.path.join(HERE, 'contoh_sertifikat_live.pdf'), 'wb').write(rp.content)
rp2 = requests.get(B + f'/api/sertifikat/{batches[-1]["ids"][0]}/pdf', headers=H(T1))
rp3 = requests.get(B + f'/api/sertifikat/{pid0}/pdf')
qurl = ''
try:
    import fitz
    pg = fitz.open(stream=rp.content, filetype='pdf')[0].get_pixmap(dpi=150)
    im = np.frombuffer(pg.samples, np.uint8).reshape(pg.height, pg.width, pg.n)
    qurl = qr_decode(cv2.cvtColor(im, cv2.COLOR_RGB2BGR) if pg.n == 3 else im[:, :, :3].copy())
except Exception as e:
    log('  (decode QR PDF dilewati: ' + str(e)[:80] + ')')
ok14 = rp.status_code == 200 and rp.content[:5] == b'%PDF-' and (qurl.endswith(pid0)) and rp2.status_code == 403 and rp3.status_code == 401
tc('TC-14', 'FR-08', 'Unduh sertifikat PDF', 'PDF berisi QR Code ke URL verifikasi; hanya pemilik/admin yang dapat mengunduh', f"HTTP {rp.status_code}, {len(rp.content)} byte, QR {'terbaca' if qurl.endswith(pid0) else 'TIDAK terbaca'}; penerbit lain={rp2.status_code}; tanpa token={rp3.status_code}", ok14)
R['misc']['pdf'] = dict(bytes=len(rp.content), qr_ok=qurl.endswith(pid0), other=rp2.status_code, notoken=rp3.status_code)

# ================================================================ TC-15
log('== AUDIT RANTAI ==')
a1 = requests.get(B + '/api/sertifikat/batch-audit', headers=H(T1), timeout=300).json()
rowx = sorted(sb.table('sertifikat').select('*').eq('batch_id', batches[0]['batch_id']).execute().data, key=lambda x: x['leaf_index'])[min(2, batches[0]['n'] - 1)]
upd_cert(rowx, 'nama_lokasi', rowx['nama_lokasi'] + ' B')
try: a2 = requests.get(B + '/api/sertifikat/batch-audit', headers=H(T1), timeout=300).json()
finally: upd_cert(rowx, 'nama_lokasi', rowx['nama_lokasi'])
aA = requests.get(B + '/api/sertifikat/batch-audit', headers=H(TA), timeout=300).json()
ok15 = a1['total_valid'] == a1['total_sertifikat'] and all(b_['root_cocok'] for b_ in a1['batches']) and a2['total_valid'] == a2['total_sertifikat'] - 1 and aA['total_sertifikat'] >= len(allids)
tc('TC-15', 'FR-10', 'Audit rantai batch', 'Root rekonstruksi = root on-chain; sertifikat yang diubah ditandai', f"{U1N}: {a1['total_batch']} batch, {a1['total_valid']}/{a1['total_sertifikat']} valid; setelah 1 data diubah: {a2['total_valid']}/{a2['total_sertifikat']}; admin melihat {aA['total_sertifikat']} sertifikat", ok15)
R['misc']['batch_audit'] = dict(before=[a1['total_valid'], a1['total_sertifikat'], a1['total_batch']], after=[a2['total_valid'], a2['total_sertifikat']], admin=aA['total_sertifikat'])
R['tc'].sort(key=lambda x: int(x['id'][3:]))

# ================================================================ waktu respons
log('== WAKTU RESPONS ==')
def bench(name, fn, n=BENCH_N):
    xs = []
    for _ in range(n): _, t = timed(fn); xs.append(t)
    R['timing'][name] = stats(xs); log(f"  {name}: {R['timing'][name]['mean']} ms")
bench('POST /api/auth/login (200)', lambda: login(ADMIN_USER, ADMIN_PASS))
bench('POST /api/auth/login (401)', lambda: login(ADMIN_USER, 'salah-salah'))
bench('GET /api/auth/me', lambda: requests.get(B + '/api/auth/me', headers=H(TA)))
bench('GET /api/penerbit', lambda: requests.get(B + '/api/penerbit', headers=H(TA)))
addt, revt = [], []
for i in range(WALLET_BENCH_N):
    a = Account.create().address; un = f'{PREFIX}bench{i}'
    txh, _ = send(K.functions.tambahPenerbit(a), KA, f'tambahPenerbit bench{i}')
    r, t = timed(lambda: requests.post(B + '/api/penerbit', json={'username': un, 'password': PW, 'wallet_address': a, 'tx_hash': txh}, headers=H(TA), timeout=120)); addt.append(t)
    bid = r.json()['penerbit']['id']
    txc_, _ = send(K.functions.cabutPenerbit(a), KA, f'cabutPenerbit bench{i}')
    r, t = timed(lambda: requests.post(B + f'/api/penerbit/{bid}/revoke', json={'tx_hash': txc_}, headers=H(TA), timeout=120)); revt.append(t)
R['timing']['POST /api/penerbit (+verifikasi tx)'] = stats(addt)
R['timing']['POST /api/penerbit/{id}/revoke (+verifikasi tx)'] = stats(revt)
bench('GET /api/sertifikat', lambda: requests.get(B + '/api/sertifikat', headers=H(T1)))
R['timing']['POST /api/sertifikat/prepare (10 data)'] = stats(tprep)
R['timing']['POST /api/sertifikat/konfirmasi'] = stats(tconf)
R['timing']['GET /api/sertifikat/verify/{id}'] = stats(tver)
bench('GET /api/sertifikat/generate-qr/{id}', lambda: requests.get(B + f'/api/sertifikat/generate-qr/{pid0}'))
bench('GET /api/sertifikat/{id}/pdf', lambda: requests.get(B + f'/api/sertifikat/{pid0}/pdf', headers=H(T1)))
bench('GET /api/sertifikat/batch-audit', lambda: requests.get(B + '/api/sertifikat/batch-audit', headers=H(T1)), n=max(5, BENCH_N // 4))
bench('GET /api/audit (100 entri)', lambda: requests.get(B + '/api/audit', params={'limit': 100}, headers=H(TA)))
lat = []; qr_ok = 0
for pid in allids:
    q = requests.get(B + f'/api/sertifikat/generate-qr/{pid}').json()['qr_code']; t0 = time.perf_counter()
    url = qr_decode(cv2.imdecode(np.frombuffer(base64.b64decode(q.split(',')[1]), np.uint8), cv2.IMREAD_COLOR))
    if 'id=' not in url: continue
    qr_ok += requests.get(B + '/api/sertifikat/verify/' + url.split('id=')[1]).json()['valid'] is True; lat.append((time.perf_counter() - t0) * 1000)
R['misc']['qr_decode'] = dict(ok=len(lat), valid=qr_ok, total=len(allids))
R['timing']['Latensi QR (decode + verifikasi)'] = stats(lat)
_, tv = timed(lambda: requests.get(B + '/api/audit/verify', headers=H(TA), timeout=300))
R['misc']['audit_verify_full'] = dict(entries=v2['total'], ms=round(tv, 2))
R['misc']['gas'] = gas
R['misc']['good_id'] = pid0
R['misc']['explorer'] = f'https://sepolia.etherscan.io/address/{app.contract_address}'

out = os.path.join(HERE, 'hasil_uji_live.json')
json.dump(R, open(out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False, default=str)
lulus = sum(t['status'] == 'PASS' for t in R['tc'])
log('\n=========================================================')
log(f'SELESAI: {lulus}/{len(R["tc"])} skenario PASS | {len(R["tx"])} transaksi Sepolia | total biaya {sum(x["eth"] for x in R["tx"]):.6f} SepoliaETH')
log(f'Hasil: {out}')
log('Kirim file hasil_uji_live.json (dan contoh_sertifikat_live.pdf) ke Claude. JANGAN kirim .env / .env.uji.')
log('Data uji tetap ada di Supabase agar bisa di-screenshot; hapus dengan:  python uji_live/uji_live.py --bersihkan')
