import os
import json
import hashlib
import requests
from bs4 import BeautifulSoup

# ── Config ──────────────────────────────────────────────
LOGIN_URL    = "https://siasisten.cs.ui.ac.id/login.data"
LOWONGAN_URL = "https://siasisten.cs.ui.ac.id/lowongan/listLowongan/"
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]
CACHE_FILE   = "last_data.json"

# ── Login ────────────────────────────────────────────────
def login():
    session = requests.Session()

    # Step 1: GET dulu untuk dapat csrftoken cookie
    session.get("https://siasisten.cs.ui.ac.id/login")
    csrf = session.cookies.get("csrftoken")
    print("CSRF token:", csrf)

    # Step 2: POST login dengan content-type yang benar
    r = session.post(
        LOGIN_URL,
        data=f"username={os.environ['SITE_USERNAME']}&password={os.environ['SITE_PASSWORD']}",
        headers={
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "X-CSRFToken": csrf,
            "Referer": "https://siasisten.cs.ui.ac.id/login",
            "Origin": "https://siasisten.cs.ui.ac.id",
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Mobile Safari/537.36",
        }
    )
    print("Status login:", r.status_code)
    print("Response login:", r.text[:300])
    print("Cookies setelah login:", dict(session.cookies))

    if r.status_code not in (200, 202):
        raise Exception(f"Login gagal! Status: {r.status_code}")

    # Validasi: pastikan accessToken ada di cookie
    if not session.cookies.get("accessToken"):
        raise Exception("Login gagal! accessToken tidak ditemukan di cookie.")

    print("Login berhasil!")
    return session

# ── Hash ─────────────────────────────────────────────────
def row_hash(row):
    key = row["mata_kuliah"] + row["dosen"] + row["status_lowongan"]
    return hashlib.md5(key.encode()).hexdigest()

# ── Discord ──────────────────────────────────────────────
def scrape(session):
    r = session.get(LOWONGAN_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    section = soup.find("div", {"data-testid": "section-semester-selanjutnya"})
    if not section:
        raise Exception("Section semester selanjutnya tidak ditemukan.")

    rows = []
    for tr in section.select("table tbody tr"):
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cols) >= 8:
            # Ambil nama matkul saja (sebelum kode, pisah di baris pertama span)
            td_matkul = tr.select("td")[1]
            nama_matkul = td_matkul.select_one("span.font-semibold").get_text(strip=True)

            rows.append({
                "mata_kuliah":     nama_matkul,
                "dosen":           cols[3],
                "status_lowongan": cols[4],
                "jumlah_lowongan": cols[5],  # kuota
                "jumlah_pelamar":  cols[6],  # pendaftar
            })

    print(f"Ditemukan {len(rows)} baris di tabel.")
    return rows


def notify(row):
    status_color = 0x57F287 if row["status_lowongan"] == "Dibuka" else 0xED4245
    payload = {
        "embeds": [{
            "title": "🔔 Lowongan Baru — Semester Selanjutnya",
            "color": status_color,
            "fields": [
                {"name": "📚 Matkul",     "value": row["mata_kuliah"],     "inline": True},
                {"name": "👨‍🏫 Dosen",      "value": row["dosen"],           "inline": True},
                {"name": "📋 Status",      "value": row["status_lowongan"], "inline": True},
                {"name": "🪑 Kuota",       "value": row["jumlah_lowongan"], "inline": True},
                {"name": "👥 Pendaftar",   "value": row["jumlah_pelamar"],  "inline": True},
            ],
            "footer": {"text": "Daftar Gas"},
            "url": LOWONGAN_URL,
        }]
    }
    r = requests.post(DISCORD_WEBHOOK, json=payload)
    print(f"Notifikasi dikirim: {row['mata_kuliah']} (status {r.status_code})")

# ── Main ─────────────────────────────────────────────────
session = login()
rows = scrape(session)

# Load cache
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE) as f:
        cached = json.load(f)
    old_hashes = set(cached.get("hashes", []))
else:
    old_hashes = set()

# Deteksi & kirim notifikasi
new_rows = [r for r in rows if row_hash(r) not in old_hashes]
if new_rows:
    for row in new_rows:
        notify(row)
    print(f"Total {len(new_rows)} lowongan baru dikirim ke Discord.")
else:
    print("Tidak ada lowongan baru.")

# Update cache
with open(CACHE_FILE, "w") as f:
    json.dump({
        "hashes": [row_hash(r) for r in rows],
        "rows": rows
    }, f, ensure_ascii=False, indent=2)

print("Cache diperbarui.")