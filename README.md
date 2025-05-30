# Complexity Bot

**Complexity Bot** adalah bot pintar yang dirancang menggunakan strategi **Greedy Algorithm** dalam permainan **Etimo Board Game**. Bot ini berfokus pada efisiensi, pemilihan lokal optimal, dan pengambilan keputusan cepat — semua prinsip inti dari algoritma greedy.

## Fitur & Algoritma Bot

| Fitur                        | Penjelasan                                                                              |
| ---------------------------- | --------------------------------------------------------------------------------------- |
| **Greedy Diamond Targeting** | Memilih diamond terbaik berdasarkan nilai dan jarak (`score = points / (distance + 1)`) |
| **Smart Claiming**           | Menghindari diamond yang lebih dekat ke bot lain agar sebagai strategi kompetitif       |
| **Return to Base**           | Ketika inventori penuh, langsung kembali ke base                                        |
| **Avoid Teleport**           | Hindari semua posisi teleport untuk mencegah perpindahan tidak terkontrol               |
| **Safe Random Move**         | Jika tidak ada langkah optimal, lakukan gerakan acak yang aman                          |

## Struktur File

- `main.py` – Script utama untuk menjalankan bot.
- `bots/greedy_bot.py` – Berisi logika pengambilan keputusan dan strategi pergerakan.
- `utils/` – Folder yang menyimpan komponen dan utilitas tambahan seperti model dan API.

## Strategi Algoritma

### 1. Pulang Jika Inventori Penuh

Jika jumlah diamond di inventori mencapai batas maksimum, bot akan segera kembali ke base untuk menyimpan poin.

### 2. Mencari Diamond Terbaik

Bot mengevaluasi semua diamond yang tersedia, mempertimbangkan:

- Poin diamond (`points`)
- Jarak dari posisi bot (menggunakan Manhattan Distance)
- Apakah ada bot lain yang lebih dekat

### 3. Hindari Teleport

Setiap posisi teleport dihindari agar tidak membuat bot berpindah lokasi secara tidak terduga.

### 4. Fallback: Langkah Acak

Jika tidak ada langkah optimal, bot akan memilih langkah acak.

## Cara Menjalankan Bot

### 1. Instalasi Dependencies

Sebelum menjalankan bot, pastikan kamu sudah menginstall dependensi yang dibutuhkan.

```bash
pip install -r requirements.txt
```

### 1. Jalankan dari Terminal

Jalankan dengan nilai default (tidak pakai argumen):

```bash
python main.py
```

Jalankan dengan parameter langsung:

```bash
python main.py \
  --logic Random \
  --email=test1@email.com \
  --name=stima \
  --password=123456 \
  --team=etimo
```

### 2. Menjalankan Banyak Bot dengan Script

Jika ingin menjalankan beberapa bot sekaligus, gunakan skrip shell atau batch yang sudah disediakan.

Untuk Linux/macOS: `run-bots.sh`

```bash
chmod +x run-bots.sh
./scripts/run-bots.sh
```

Untuk Windows: `run-bots.bat`

```bash
scripts/run-bots.bat
```

## Tim

Bot ini dikembangkan sebagai bagian dari tugas mata kuliah Strategi Algoritma - Institut Teknologi Sumatera.

Anggota Tim:

1. Nashrullah Fathul Qoriib - 122140162
