import random
random.seed(2026)
KEG = [
 ("Praktikum Basis Data", "Laboratorium Komputer 1 FTTK", 0.8568120, 104.4932210),
 ("Praktikum Jaringan Komputer", "Laboratorium Jaringan FTTK", 0.8571450, 104.4935870),
 ("Praktikum Pemrograman Web", "Laboratorium Komputer 2 FTTK", 0.8569930, 104.4929640),
 ("Praktikum Sistem Operasi", "Laboratorium Komputer 1 FTTK", 0.8568120, 104.4932210),
 ("Praktikum Algoritma dan Struktur Data", "Laboratorium Komputer 3 FTTK", 0.8573260, 104.4938120),
]
DEPAN = ["Andi","Budi","Citra","Dewi","Eka","Fajar","Gita","Hendra","Indah","Joko","Kartika","Lestari","Maria","Nanda","Oki","Putri","Rizky","Sinta","Teguh","Wulan","Yogi","Zahra","Bayu","Nur","Rahmat"]
BELAKANG = ["Saputra","Lestari","Pratama","Simanjuntak","Siregar","Hasibuan","Nasution","Wijaya","Ramadhan","Permata","Sitompul","Harahap","Kurniawan","Putra","Situmorang"]
def build():
    data = []
    used = set()
    for k,(keg,lok,lat,lon) in enumerate(KEG):
        for i in range(10):
            while True:
                n = f"{random.choice(DEPAN)} {random.choice(BELAKANG)}"
                if n not in used: used.add(n); break
            data.append({
              "nama_peserta": n, "nama_kegiatan": keg, "nama_lokasi": lok,
              "latitude": round(lat + random.uniform(-0.00005,0.00005),7),
              "longitude": round(lon + random.uniform(-0.00005,0.00005),7),
              "waktu_mulai": f"2026-0{3+k}-02T08:00", "waktu_selesai": f"2026-0{3+k}-30T16:00",
              "keterangan": f"Asisten Praktikum Semester Genap 2025/2026 - Kelompok {i%3+1}"})
    return data
