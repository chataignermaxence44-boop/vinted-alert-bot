import requests
import time
import os
import json
import re
from collections import deque
from statistics import mean

# ==============================
# CONFIG
# ==============================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SCAN_INTERVAL = 120
COMMAND_CHECK_INTERVAL = 5
ALERT_SCORE_THRESHOLD = 60
STATS_FILE = "stats.json"

VINTED_COMMISSION_RATE = 0.05

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
last_update_id = None
last_scan_time = 0

# ==============================
# LOAD / SAVE STATS
# ==============================

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    else:
        return {
            "total_deals": 0,
            "total_profit_net": 0,
            "total_invested": 0,
            "best_score": 0
        }

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)

stats = load_stats()

# ==============================
# TELEGRAM
# ==============================

def send_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    requests.post(url, data=data)

def send_stats():
    roi = 0
    if stats["total_invested"] > 0:
        roi = (stats["total_profit_net"] / stats["total_invested"]) * 100

    message = f"""
📊 <b>STATISTIQUES BOT</b>

🔥 Deals totaux: {stats['total_deals']}
💰 Profit net total: {round(stats['total_profit_net'],2)}€
💸 Capital investi: {round(stats['total_invested'],2)}€
📈 ROI net moyen: {round(roi,2)}%
🏆 Meilleur score: {stats['best_score']}
"""
    send_message(message)

def check_telegram_commands():
    global last_update_id
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    response = requests.get(url).json()

    if not response["ok"]:
        return

    for update in response["result"]:
        update_id = update["update_id"]

        if last_update_id and update_id <= last_update_id:
            continue

        last_update_id = update_id

        if "message" in update and "text" in update["message"]:
            if update["message"]["text"] == "/stats":
                send_stats()

# ==============================
# ANALYSE PRIX
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
# MODULE POKÉMON ULTRA
# ==============================

def analyze_pokemon_lot(title, price):

    title_lower = title.lower()

    # Détection nombre de cartes
    numbers = re.findall(r'\d+', title_lower)
    estimated_value = 0
    boost_score = 0

    if numbers:
        card_count = max([int(n) for n in numbers if int(n) <= 1000], default=0)

        if card_count >= 50:
            estimated_value = card_count * 0.5  # estimation prudente 0.5€ par carte
            boost_score += 30

    premium_keywords = [
        "psa", "gradée", "gold", "ultra",
        "secrète", "full art", "gx", "ex",
        "vmax", "vstar", "holo"
    ]

    if any(word in title_lower for word in premium_keywords):
        boost_score += 25
        estimated_value *= 1.5

    if estimated_value > 0:
        commission = estimated_value * VINTED_COMMISSION_RATE
        net_resale = estimated_value - commission
        net_profit = net_resale - price

        if net_profit > 0:
            roi = (net_profit / price) * 100
            return {
                "activated": True,
                "estimated_value": round(estimated_value,2),
                "net_profit": round(net_profit,2),
                "roi": round(roi,2),
                "boost_score": boost_score
            }

    return {"activated": False}

# ==============================
# SIMULATION FETCH
# ==============================

def fetch_items(query):

    sample_prices = [
        80, 85, 78, 82, 79,
        90, 88, 76, 84, 81,
        83, 77, 86, 87, 75,
        120, 30, 95, 92, 89,
        91, 93, 94, 96, 97
    ]

    avg_price = clean_average(sample_prices)

    return [{
        "id": f"{query}_1",
        "title": f"Lot 200 cartes Pokemon GX ultra rare",
        "price": 60,
        "avg_price": avg_price,
        "link": "https://www.vinted.fr/item/123456789"
    }]

# ==============================
# MAIN LOOP
# ==============================

def main():
    global current_index, last_scan_time

    send_message("🚀 Bot ULTRA + Module Pokémon activé")

    while True:

        check_telegram_commands()

        if time.time() - last_scan_time >= SCAN_INTERVAL:

            queries_to_scan = [
                SEARCH_QUERIES[current_index],
                SEARCH_QUERIES[(current_index + 1) % len(SEARCH_QUERIES)]
            ]

            current_index = (current_index + 2) % len(SEARCH_QUERIES)
            last_scan_time = time.time()

            for query in queries_to_scan:
                items = fetch_items(query)

                for item in items:

                    if item["id"] in seen_items:
                        continue

                    seen_items.append(item["id"])

                    # MODULE POKÉMON INDÉPENDANT
                    pokemon_analysis = analyze_pokemon_lot(item["title"], item["price"])

                    if pokemon_analysis["activated"]:

                        stats["total_deals"] += 1
                        stats["total_profit_net"] += pokemon_analysis["net_profit"]
                        stats["total_invested"] += item["price"]

                        save_stats(stats)

                        message = f"""
🃏 <b>MODULE POKÉMON ULTRA ACTIVÉ</b>

📦 {item['title']}
💰 Achat: {item['price']}€
📊 Valeur estimée: {pokemon_analysis['estimated_value']}€

💸 Profit net estimé: {pokemon_analysis['net_profit']}€
📈 ROI: {pokemon_analysis['roi']}%

🔥 Score Pokémon Boosté: +{pokemon_analysis['boost_score']}

🔗 {item['link']}
"""

                        send_message(message)

        time.sleep(COMMAND_CHECK_INTERVAL)

if __name__ == "__main__":
    main()
