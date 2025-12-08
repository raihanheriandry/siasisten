import requests
from bs4 import BeautifulSoup
import json
import os

LOGIN_URL = "https://siasisten.cs.ui.ac.id/login/"
LOWONGAN_URL = "https://siasisten.cs.ui.ac.id/lowongan/listLowongan/"

USERNAME = os.getenv("SIASISTEN_USER")
PASSWORD = os.getenv("SIASISTEN_PASS")
WEBHOOK = os.getenv("DISCORD_WEBHOOK")

def send_discord(msg):
    requests.post(WEBHOOK, json={"content": msg})

def login():
    session = requests.Session()
    # ambil csrf token
    r = session.get(LOGIN_URL)
    soup = BeautifulSoup(r.text, "html.parser")
    csrf = soup.find("input", {"name": "csrfmiddlewaretoken"})["value"]

    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "csrfmiddlewaretoken": csrf
    }

    session.post(LOGIN_URL, data=payload, headers={"Referer": LOGIN_URL})
    return session

def fetch_lowongan(session):
    r = session.get(LOWONGAN_URL)
    soup = BeautifulSoup(r.text, "html.parser")

    rows = soup.find_all("tr")[1:]  # skip header

    lowongan = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue

        a_tag = row.find("a")
        if not a_tag:
            continue  # baris tanpa link (misal lowongan tutup)

        link = a_tag["href"]

        # Ambil ID terakhir dari URL lengkap /lowongan/daftarLowongan/2398/
        id_lowongan = link.strip("/").split("/")[-1]

        nama = cols[1].get_text(" ", strip=True)
        dosen = cols[2].get_text(strip=True)
        status = cols[3].get_text(strip=True)

        lowongan.append({
            "id": id_lowongan,
            "nama": nama,
            "dosen": dosen,
            "status": status,
            "url": "https://siasisten.cs.ui.ac.id" + link
        })

    return lowongan

def load_last():
    if os.path.exists("last.json"):
        with open("last.json", "r") as f:
            return json.load(f)
    return []

def save_last(data):
    with open("last.json", "w") as f:
        json.dump(data, f)

def main():
    session = login()
    data = fetch_lowongan(session)
    last = load_last()

    last_ids = {item["id"] for item in last}
    new_lowongan = [l for l in data if l["id"] not in last_ids]

    for low in new_lowongan:
        msg = (
            f"📢 **Lowongan Baru Dibuka!**\n"
            f"**{low['nama']}**\n"
            f"Dosen: {low['dosen']}\n"
            f"Status: {low['status']}\n"
            f"Link: {low['url']}"
        )
        send_discord(msg)

    save_last(data)


if __name__ == "__main__":
    main()
