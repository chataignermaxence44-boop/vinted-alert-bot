import requests
import time
import os
import json

print("🚀 BOT RAPIDAPI LANCÉ")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

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

CHECK_INTERVAL = 60
seen_ids = set()

# ================= TELEGRAM =================

def send_telegram_photo(title, price, url, image_url):

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "🟢 Voir l'annonce",
                    "url": url
                }
            ]
        ]
    }

    caption = f"""
🔥 {title}
💰 {price}€
"""

    payload = {
        "chat_id": CHAT_ID,
        "photo": image_url,
        "caption": caption,
        "reply_markup": json.dumps(keyboard)
    }

    r = requests.post(telegram_url, data=payload)
    print("Telegram:", r.status_code, flush=True)

# ================= RAPIDAPI =================

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

    print("STATUS:", response.status_code, flush=True)

    if response.status_code != 200:
        print("Erreur API:", response.text, flush=True)
        return []

    data = response.json()

    if "products" not in data:
        print("Structure inconnue:", data, flush=True)
        return []

    return data["products"]

# ================= MAIN =================

while True:

    print("🔎 Scan...", flush=True)

    for keyword in SEARCHES:

        print("Recherche:", keyword, flush=True)

        products = search_vinted(keyword)

        for product in products[:10]:

            product_id = product.get("id")

            if product_id in seen_ids:
                continue

            seen_ids.add(product_id)

            title = product.get("title", "Annonce")
            price = product.get("price", {}).get("amount", 0)
            url = product.get("url", "")

            images = product.get("images", [])
            image_url = images[0]["url"] if images else "https://via.placeholder.com/300"

            if url and image_url:
                send_telegram_photo(title, price, url, image_url)

    time.sleep(CHECK_INTERVAL)
