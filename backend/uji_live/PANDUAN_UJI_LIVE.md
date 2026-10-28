# Panduan Pengujian Live (Supabase + Ethereum Sepolia via Infura)

Script `uji_live.py` menjalankan **semua skenario pengujian Bab IV** (TC-01 s.d. TC-15, RBAC/JWT,
validasi transaksi, konsistensi off-chain vs on-chain, deteksi manipulasi 8 variabel, audit log,
PDF, Audit Rantai, waktu respons, dan biaya gas) terhadap **Supabase dan smart contract Sepolia
yang sebenarnya**. Hasilnya dipakai untuk mengganti angka uji lokal di laporan.

Perkiraan waktu: 20–40 menit. Perkiraan biaya: ± 11 transaksi, < 0,005 SepoliaETH (gratis dari faucet).

## 1. Persiapan (sekali saja)

1. **Supabase sudah memakai skema versi baru.** Jika belum, jalankan `backend/sql/001_rbac_jwt_audit.sql`
   di Supabase › SQL Editor.
2. **`backend/.env` sudah lengkap**: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `SEPOLIA_RPC_URL` (Infura),
   `CONTRACT_ADDRESS`, `JWT_SECRET`, `VERIFICATION_BASE_URL`.
3. **Siapkan 3 wallet di MetaMask (jaringan Sepolia):**
   - Wallet **admin** = wallet yang dulu men-deploy kontrak `0xE04d…4c8a`.
   - Buat **2 akun baru** (Add account) untuk penerbit uji. Jangan pakai wallet pribadi yang berisi aset.
   - Isi SepoliaETH dari faucet (misalnya Google Cloud Web3 Faucet atau faucet Infura/Alchemy):
     admin ≥ 0,01; penerbit 1 ≥ 0,01; penerbit 2 ≥ 0,003.
4. Salin `uji_live/.env.uji.example` menjadi `uji_live/.env.uji`, lalu isi username/password admin aplikasi
   dan **private key** ketiga wallet (MetaMask › titik tiga › Account details › Show private key).
   File ini hanya dibaca di laptop Anda dan sudah masuk `.gitignore`. **Jangan kirim ke siapa pun.**
5. Jika ingin memakai data penelitian Anda, isi `DATASET_PATH` di `.env.uji` (CSV/XLSX dengan kolom
   `nama_peserta, nama_kegiatan, nama_lokasi, latitude, longitude, waktu_mulai, waktu_selesai, keterangan`).

## 2. Jalankan (PowerShell, dari folder `backend`)

```powershell
cd backend
python -m venv venv            # jika belum ada
venv\Scripts\activate
pip install -r requirements.txt -r uji_live\requirements-uji.txt
python uji_live\uji_live.py
```

Script akan menghentikan diri dengan pesan `[X] …` bila ada yang belum siap (RPC bukan Sepolia,
private key admin bukan pembuat kontrak, saldo kurang, login admin gagal).
Jika ingin lebih cepat, tambahkan `--tanpa-deteksi` (melewati 400 skenario deteksi manipulasi).

## 3. Hasil

- `uji_live\hasil_uji_live.json` → **kirim file ini ke Claude** (tidak berisi kunci/rahasia;
  hanya status, waktu, hash transaksi, dan alamat wallet publik).
- `uji_live\contoh_sertifikat_live.pdf` → contoh sertifikat untuk lampiran (opsional dikirim).
- Semua transaksi dapat dicek di `https://sepolia.etherscan.io/address/<CONTRACT_ADDRESS>`.

Data uji (akun `uji_penerbit1`, `uji_penerbit2`, `uji_bench*` dan sertifikatnya) dibiarkan agar bisa
di-screenshot dari aplikasi. Setelah selesai, hapus dengan:

```powershell
python uji_live\uji_live.py --bersihkan
```

Audit log tidak ikut terhapus karena tabelnya memang append-only (itu salah satu yang diuji).

## 4. Catatan

- Backend dijalankan sementara di laptop (port 5059) tetapi **terhubung ke Supabase dan Sepolia asli**.
  Untuk menguji backend yang sudah di-deploy (Cloudflare Tunnel), isi `UJI_API_URL`.
- Uji manipulasi mengubah satu nilai lalu langsung mengembalikannya (dalam `try/finally`).
- Jika script terhenti di tengah, jalankan `--bersihkan` lalu ulangi.

## 5. Pengujian API dengan Postman (Bab III E.6.4)

1. Buka Postman › Import › pilih `uji_live/Zakanel_Pengujian_API.postman_collection.json`.
2. Klik koleksi › tab **Variables**, isi `base_url` (misalnya `http://127.0.0.1:5000` atau URL backend
   Cloudflare Tunnel), `admin_user`, `admin_pass`. `penerbit_user`/`penerbit_pass` sudah terisi akun uji
   dari `uji_live.py` (jalankan `uji_live.py` dulu, sebelum `--bersihkan`).
3. Klik **Run collection** › Run. Ada 22 request dan 49 assertion PASS/FAIL.
4. **Screenshot halaman hasil Runner** (ringkasan PASS/FAIL dan waktu respons) dan kirim ke Claude
   untuk dimasukkan ke Bab IV bagian C.3. Bisa juga Export Results (JSON) dan kirim file-nya.
