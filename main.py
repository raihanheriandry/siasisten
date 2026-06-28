import os
import json
import hashlib
import requests
from bs4 import BeautifulSoup

# ── Config ──────────────────────────────────────────────
LOGIN_URL    = "https://siasisten.cs.ui.ac.id/login/"
LOWONGAN_URL = "https://siasisten.cs.ui.ac.id/lowongan/listLowongan/"
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]
CACHE_FILE   = "last_data.json"

# ── Login ────────────────────────────────────────────────
session = requests.Session()

# Ambil CSRF token dulu (Django butuh ini)
r = session.get(LOGIN_URL)
soup = BeautifulSoup(r.text, "html.parser")
csrf_token = soup.find("input", {"name": "csrfmiddlewaretoken"})["value"]

login_payload = {
    "csrfmiddlewaretoken": csrf_token,
    "username": os.environ["SITE_USERNAME"],
    "password": os.environ["SITE_PASSWORD"],
}

r = session.post(LOGIN_URL, data=login_payload, headers={"Referer": LOGIN_URL})
r.raise_for_status()

# Validasi login berhasil
if "login" in r.url.lower() or "Login" in r.text[:500]:
    raise Exception("Login gagal! Cek username/password.")

print("Login berhasil.")

# ── Scrape tabel Semester Selanjutnya ───────────────────
r = session.get(LOWONGAN_URL)
r.raise_for_status()
soup = BeautifulSoup(r.text, "html.parser")

# Cari section "Semester Selanjutnya"
section = soup.find("div", {"data-testid": "section-semester-selanjutnya"})
if not section:
    raise Exception("Section semester selanjutnya tidak ditemukan.")

rows = []
for tr in section.select("table tbody tr"):
    cols = [td.get_text(strip=True) for td in tr.find_all("td")]
    if len(cols) >= 5:
        row = {
            "no":              cols[0],
            "mata_kuliah":     cols[1],
            "dosen":           cols[2],
            "status_lowongan": cols[3],
            "jumlah_lowongan": cols[4],
        }
        rows.append(row)

print(f"Ditemukan {len(rows)} baris di tabel.")

# ── Load cache ───────────────────────────────────────────
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE) as f:
        cached = json.load(f)
    old_hashes = set(cached.get("hashes", []))
    old_rows   = {r["mata_kuliah"]: r for r in cached.get("rows", [])}
else:
    old_hashes = set()
    old_rows   = {}

# ── Deteksi baris baru ───────────────────────────────────
def row_hash(row):
    key = row["mata_kuliah"] + row["dosen"] + row["status_lowongan"]
    return hashlib.md5(key.encode()).hexdigest()

new_rows = [r for r in rows if row_hash(r) not in old_hashes]

# ── Kirim ke Discord ─────────────────────────────────────
if new_rows:
    for row in new_rows:
        status_color = 0x57F287 if row["status_lowongan"] == "Dibuka" else 0xED4245
        payload = {
            "embeds": [{
                "title": "🔔 Lowongan Baru — Semester Selanjutnya",
                "color": status_color,
                "fields": [
                    {"name": "📚 Mata Kuliah", "value": row["mata_kuliah"], "inline": False},
                    {"name": "👨‍🏫 Dosen",       "value": row["dosen"],        "inline": True},
                    {"name": "📋 Status",       "value": row["status_lowongan"], "inline": True},
                    {"name": "🪑 Kuota",        "value": row["jumlah_lowongan"], "inline": True},
                ],
                "footer": {"text": "SIAsisten • Ganjil 2026/2027"},
                "url": LOWONGAN_URL,
            }]
        }
        resp = requests.post(DISCORD_WEBHOOK, json=payload)
        print(f"Notifikasi dikirim: {row['mata_kuliah']} (status {resp.status_code})")
    print(f"Total {len(new_rows)} lowongan baru dikirim ke Discord.")
else:
    print("Tidak ada lowongan baru.")

# ── Update cache ─────────────────────────────────────────
all_hashes = [row_hash(r) for r in rows]
with open(CACHE_FILE, "w") as f:
    json.dump({"hashes": all_hashes, "rows": rows}, f, ensure_ascii=False, indent=2)

print("Cache diperbarui.")