import requests
import time
import os

print("🚀 Lancement du script...")

# ==============================
# VARIABLES ENVIRONNEMENT
# ==============================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not TELEGRAM_TOKEN or not CHAT_ID or not RAPIDAPI_KEY:
    print("❌ Variables manquantes")
    exit()

print("✅ Variables OK")

# ==============================
# CONFIG RAPIDAPI
# ==============================

RAPIDAPI_HOST = "vinted3.p.rapidapi.com"
BASE_URL = "https://vinted3.p.rapidapi.com/getSearch"

SEARCHES = [
    "nike homme",
    "adidas homme",
    "booster pokemon scellé",
    "etb pokemon",
    "lot carte pokemon",
    "lots de carte pokemon"
]

seen_ids = set()

# ==============================
# TELEGRAM
# ==============================

def send_telegram_photo(title, price, url, image_url):

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "🟢 Voir l'annonce",
                    "url": url
                },
                {
                    "text": "🔴 Supprimer",
                    "callback_data": "delete"
                }
            ]
        ]
    }

    caption = f"""
🔥 {title}
💰 {price}€
"""

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"

    data = {
        "chat_id": CHAT_ID,
        "photo": image_url,
        "caption": caption,
        "reply_markup": str(keyboard).replace("'", '"')
    }

    r = requests.post(telegram_url, data=data)
    print("Telegram status:", r.status_code)

# ==============================
# RAPIDAPI SEARCH
# ==============================

def search_vinted(keyword):

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    params = {
        "country": "fr",
        "page": "1",
        "keyword": keyword,
        "order": "newest_first"
    }

    response = requests.get(BASE_URL, headers=headers, params=params)

    print("STATUS CODE:", response.status_code)

    if response.status_code != 200:
        print("Erreur API:", response.text)
        return []

    data = response.json()

    # ⚠️ Structure à adapter selon réponse réelle
    if "items" not in data:
        print("Structure JSON inconnue:", data)
        return []

    return data["items"]

# ==============================
# BOUCLE PRINCIPALE
# ==============================

while True:

    print("🔎 Scan en cours...")

    for keyword in SEARCHES:

        print("Recherche:", keyword)

        items = search_vinted(keyword)

        for item in items[:5]:  # top 5 annonces

            item_id = item.get("id")

            if item_id in seen_ids:
                continue

            seen_ids.add(item_id)

            title = item.get("title")
            price = item.get("price", {}).get("amount", 0)
            url = item.get("url")
            image = item.get("photos", [{}])[0].get("url")

            if title and image and url:
                send_telegram_photo(title, price, url, image)

    time.sleep(60)
