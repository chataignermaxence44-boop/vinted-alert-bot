import requests
import time
import os
from statistics import mean
from collections import deque

# ==============================
# CONFIG
# ==============================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SCAN_INTERVAL = 120  # 2 minutes
ALERT_SCORE_THRESHOLD = 60

SEARCH_QUERIES = [
    "nike homme",
    "adidas homme",
    "chaussure nike",
    "chaussure adidas",
    "booster pokemon scellé",
    "etb pokemon",
    "lot carte pokemon",
    "lots de carte pokemon"
]

current_index = 0
seen_items = deque(maxlen=1000)

# ==============================
# TELEGRAM
# ==============================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

# ==============================
# ANALYSE
# ==============================

def calculate_discount(price, avg_price):
    if avg_price == 0:
        return 0
    return round(((avg_price - price) / avg_price) * 100, 2)

def calculate_score(item, discount):
    score = 0
    title = item["title"].lower()

    # Discount
    if discount >= 40:
        score += 45
    elif discount >= 30:
        score += 30

    # Marques fortes
    if "nike" in title or "adidas" in title:
        score += 20

    # Pokémon premium
    pokemon_bonus = [
        "booster", "scellé", "etb",
        "ultra", "secrète", "gold",
        "full art", "psa", "gradée",
        "gx", "ex", "vmax", "vstar"
    ]

    if any(word in title for word in pokemon_bonus):
        score += 25

    # Taille recherchée
    if any(size in title for size in ["41", "42", "43"]):
        score += 15

    # Prix attractif
    if item["price"] < 50:
        score += 10

    return score

# ==============================
# SIMULATION FETCH (À REMPLACER PLUS TARD)
# ==============================

def fetch_items(query):
    # Simulation temporaire pour structure
    return [
        {
            "id": f"{query}_1",
            "title": f"{query} Nike 42",
            "price": 40,
            "avg_price": 80,
            "link": "https://vinted.fr/item/demo"
        }
    ]

# ==============================
# MAIN LOOP
# ==============================

def main():
    global current_index
    send_telegram("🤖 Bot PRO multi-recherches activé")

    while True:
        queries_to_scan = [
            SEARCH_QUERIES[current_index],
            SEARCH_QUERIES[(current_index + 1) % len(SEARCH_QUERIES)]
        ]

        current_index = (current_index + 2) % len(SEARCH_QUERIES)

        for query in queries_to_scan:
            items = fetch_items(query)

            for item in items:
                if item["id"] in seen_items:
                    continue

                seen_items.append(item["id"])

                discount = calculate_discount(item["price"], item["avg_price"])

                if discount >= 30:
                    score = calculate_score(item, discount)

                    if score >= ALERT_SCORE_THRESHOLD:
                        message = f"""
🔥 <b>DEAL SCORE {score}/100</b>

🔎 Recherche: {query}

📦 {item['title']}
💰 {item['price']}€
📉 Moyenne: {item['avg_price']}€
📊 -{discount}%

🔗 <a href="{item['link']}">Voir l'annonce</a>
"""
                        send_telegram(message)

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
