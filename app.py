import requests
import time
import json
import os

# ==============================
# VARIABLES ENV (Render)
# ==============================

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
RAPIDAPI_HOST = "vinted3.p.rapidapi.com"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SEARCH_QUERY = "nike homme"
CHECK_INTERVAL = 60

SEEN_FILE = "seen_ids.json"

# ==============================
# UTIL
# ==============================

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def calculate_score(price):
    try:
        price = float(price)
    except:
        price = 0

    if price <= 5:
        return 95
    elif price <= 10:
        return 90
    elif price <= 20:
        return 80
    elif price <= 40:
        return 70
    return 50

# ==============================
# TELEGRAM
# ==============================

def send_telegram_with_buttons(image_url, caption, url):

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🟢 Voir l'annonce", "url": url}
            ],
            [
                {"text": "🔴 Supprimer", "callback_data": "delete"}
            ]
        ]
    }

    payload = {
        "chat_id": CHAT_ID,
        "photo": image_url,
        "caption": caption,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(keyboard)
    }

    r = requests.post(telegram_url, data=payload)
    print("Telegram send status:", r.status_code, flush=True)

def delete_message(message_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteMessage"
    payload = {
        "chat_id": CHAT_ID,
        "message_id": message_id
    }
    requests.post(url, data=payload)

def check_callbacks():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    response = requests.get(url).json()

    for update in response.get("result", []):
        if "callback_query" in update:
            message_id = update["callback_query"]["message"]["message_id"]
            delete_message(message_id)

# ==============================
# RAPIDAPI FETCH
# ==============================

def fetch_vinted():

    url = "https://vinted3.p.rapidapi.com/search"

    querystring = {
        "query": SEARCH_QUERY,
        "country": "fr",
        "page": "1"
    }

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }

    response = requests.get(url, headers=headers, params=querystring)

    print("STATUS CODE:", response.status_code, flush=True)

    try:
        data = response.json()
        print("JSON reçu:", data, flush=True)
        return data
    except:
        print("Erreur parsing JSON", flush=True)
        return None

# ==============================
# MAIN
# ==============================

def main():

    print("🚀 Lancement du script...", flush=True)

    seen_ids = load_seen()

    print("🚀 Bot DEBUG démarré", flush=True)

    # TEST TELEGRAM
    send_telegram_with_buttons(
        "https://via.placeholder.com/300",
        "✅ TEST TELEGRAM OK",
        "https://google.com"
    )

    while True:
        try:

            check_callbacks()

            data = fetch_vinted()

            if not data:
                print("Aucune donnée reçue.", flush=True)
                time.sleep(CHECK_INTERVAL)
                continue

            # Adapter selon structure JSON
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict) and "items" in data:
                items = data["items"]
            else:
                print("Structure JSON inconnue", flush=True)
                time.sleep(CHECK_INTERVAL)
                continue

            for item in items[:10]:

                product_id = item.get("productId")

                if not product_id:
                    continue

                if product_id in seen_ids:
                    continue

                seen_ids.add(product_id)
                save_seen(seen_ids)

                title = item.get("title", "Annonce")
                price = item.get("price", {}).get("amount", {}).get("amount", 0)
                url = item.get("url", "")
                image = item.get("image", "")

                score = calculate_score(price)

                message = f"""
🔥 <b>DEAL SCORE {score}/100</b>

📦 <b>{title}</b>
💰 {price} €
"""

                send_telegram_with_buttons(image, message, url)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("ERREUR:", e, flush=True)
            time.sleep(30)

if __name__ == "__main__":
    main()
