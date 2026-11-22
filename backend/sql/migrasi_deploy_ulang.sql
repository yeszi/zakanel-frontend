-- Jalankan di Supabase SQL Editor SETELAH kontrak baru ter-deploy dan SEBELUM menerbitkan batch baru.
-- Tujuan: data lama (hash versi lama + kontrak lama) tidak tercampur dengan pengujian baru.

-- 0) CADANGKAN dulu: Table Editor -> sertifikat / batch_sertifikat -> Export to CSV.

-- 1) Arsipkan sertifikat & batch lama (tidak dihapus, hanya diberi status arsip).
--    Jika muncul error constraint pada kolom status, hapus saja datanya setelah dicadangkan:
--    delete from sertifikat; delete from batch_sertifikat;
update sertifikat       set status = 'arsip_v1' where status in ('published', 'draft');
update batch_sertifikat set status = 'arsip_v1' where status in ('success', 'pending');

-- 2) Penerbit belum terdaftar di kontrak baru. Tandai nonaktif agar tombol
--    "Aktifkan Kembali" muncul di menu Data Penerbit, lalu aktifkan lewat MetaMask
--    (transaksi tambahPenerbit ke kontrak BARU).
update users set status = 'inactive', is_active = false where role = 'penerbit';

-- Catatan: tabel audit_logs TIDAK disentuh (append-only). Semua aktivitas lama tetap tercatat.
