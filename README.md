# SIAsisten Lowongan Notifier 🔔

Bot otomatis yang memantau lowongan asisten dosen di [SIAsisten Fasilkom UI](https://siasisten.cs.ui.ac.id) dan mengirim notifikasi ke Discord ketika ada lowongan baru untuk semester selanjutnya.

## Cara Kerja

Bot berjalan otomatis via **GitHub Actions** setiap 5 menit:

1. Login ke SIAsisten menggunakan kredensial SSO UI
2. Scrape tabel lowongan **Semester Selanjutnya**
3. Bandingkan dengan data cache sebelumnya
4. Kirim notifikasi ke Discord jika ada lowongan baru
5. Perbarui cache di repo

## Setup

### 1. Fork repo ini

Klik tombol **Fork** di kanan atas halaman ini.

### 2. Tambahkan Secrets

Buka repo hasil fork → **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Isi |
|--------|-----|
| `SITE_USERNAME` | Username SSO UI |
| `SITE_PASSWORD` | Password SSO UI |
| `DISCORD_WEBHOOK_URL` | URL webhook Discord  |

#### Cara mendapatkan Discord Webhook URL:
1. Buka channel Discord yang diinginkan
2. **Edit Channel → Integrations → Webhooks → New Webhook**
3. Beri nama, pilih channel, klik **Copy Webhook URL**

### 3. Aktifkan GitHub Actions

Buka tab **Actions** di repo → klik **"I understand my workflows, go ahead and enable them"**

### 4. Test jalankan

Buka **Actions → SIAsisten Lowongan Checker → Run workflow → Run workflow**

Jika berhasil, output log akan menampilkan:
```
Login berhasil!
Ditemukan X baris di tabel.
Tidak ada lowongan baru.
Cache diperbarui.
```

## Struktur File

```
.
├── .github/
│   └── workflows/
│       └── checker.yml     # Jadwal & konfigurasi GitHub Actions
├── checker.py              # Script utama
├── requirements.txt        # Dependency Python
├── last_data.json          # Cache data (auto-generated)
└── README.md
```

## Contoh Notifikasi Discord

```
🔔 Lowongan Baru — Semester Selanjutnya

📚 Matkul    Pengantar Organisasi Komputer
👨‍🏫 Dosen     adhi
📋 Status    Dibuka
🪑 Kuota     4
👥 Pendaftar 9
```

## Catatan

- **Jadwal:** Setiap 5 menit. GitHub Actions bisa telat 5–15 menit di jam sibuk.
- **Cache:** File `last_data.json` di-commit otomatis ke repo setiap run untuk menyimpan state.
- **Kredensial:** Username dan password disimpan sebagai GitHub Secrets — tidak pernah terekspos di kode.
- **Semester:** Bot hanya memantau tabel **Semester Selanjutnya** (Ganjil 2026/2027).

## Teknologi

- Python 3.11
- `requests` + `BeautifulSoup4` untuk scraping
- GitHub Actions untuk penjadwalan
- Discord Webhook untuk notifikasi

## Kontribusi

Pull request dan issue sangat disambut! Beberapa ide pengembangan:
- Notifikasi perubahan status lowongan
- Filter berdasarkan mata kuliah tertentu
- Tambahan info jumlah pelamar diterima