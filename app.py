import requests
import time
import os
from collections import deque
from statistics import mean, median

# ==============================
# CONFIG
# ==============================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SCAN_INTERVAL = 120
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
# ANALYSE PRIX PRO
# ==============================

def clean_average(prices):
    if len(prices) < 5:
        return mean(prices)

    prices_sorted = sorted(prices)
    cut = int(len(prices_sorted) * 0.2)

    cleaned = prices_sorted[cut:-cut] if cut > 0 else prices_sorted
    return round(mean(cleaned), 2)

def calculate_discount(price, avg_price):
    if avg_price == 0:
        return 0
    return round(((avg_price - price) / avg_price) * 100, 2)

# ==============================
# SCORING AVANCÉ
# ==============================

def calculate_score(item, discount):
    score = 0
    title = item["title"].lower()

    # Discount
    if discount >= 50:
        score += 50
    elif discount >= 40:
        score += 40
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
# SIMULATION (structure prête pour 25 annonces)
# ==============================

def fetch_items(query):
    # Simulation de 25 prix pour calcul propre
    sample_prices = [
        80, 85, 78, 82, 79,
        90, 88, 76, 84, 81,
        83, 77, 86, 87, 75,
        120, 30, 95, 92, 89,
        91, 93, 94, 96, 97
    ]

    avg_price = clean_average(sample_prices)

    return [
        {
            "id": f"{query}_1",
            "title": f"{query} Nike 42",
            "price": 40,
            "avg_price": avg_price,
            "link": "https://vinted.fr/item/demo"
        }
    ]

# ==============================
# MAIN LOOP
# ==============================

def main():
    global current_index
    send_telegram("🚀 Bot PRO++ analyse avancée activée")

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
📉 Moyenne nettoyée: {item['avg_price']}€
📊 -{discount}%

🔗 <a href="{item['link']}">Voir l'annonce</a>
"""
                        send_telegram(message)

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
