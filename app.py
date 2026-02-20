import requests
import time
import os
import json
from collections import deque
from statistics import mean

# ==============================
# CONFIG
# ==============================

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SCAN_INTERVAL = 120
ALERT_SCORE_THRESHOLD = 60
STATS_FILE = "stats.json"

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
            "total_profit": 0,
            "total_invested": 0,
            "best_score": 0,
            "mode_deals": 0,
            "mode_profit": 0,
            "pokemon_deals": 0,
            "pokemon_profit": 0
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
        "disable_web_page_preview": False  # IMPORTANT pour afficher image preview
    }
    requests.post(url, data=data)

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
            text = update["message"]["text"]

            if text == "/stats":
                send_stats()

# ==============================
# STATS MESSAGE
# ==============================

def send_stats():
    roi = 0
    if stats["total_invested"] > 0:
        roi = (stats["total_profit"] / stats["total_invested"]) * 100

    message = f"""
📊 <b>STATISTIQUES BOT</b>

🔥 Deals totaux: {stats['total_deals']}
💰 Marge totale estimée: {round(stats['total_profit'],2)}€
💸 Capital investi théorique: {round(stats['total_invested'],2)}€
📈 ROI moyen: {round(roi,2)}%

🏆 Meilleur score: {stats['best_score']}

👟 Mode:
Deals: {stats['mode_deals']}
Profit: {round(stats['mode_profit'],2)}€

🃏 Pokémon:
Deals: {stats['pokemon_deals']}
Profit: {round(stats['pokemon_profit'],2)}€
"""
    send_message(message)

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
# CATEGORY + SCORE
# ==============================

def detect_category(title):
    title = title.lower()
    if "nike" in title or "adidas" in title:
        return "mode"
    if "pokemon" in title or "booster" in title or "etb" in title:
        return "pokemon"
    return "autre"

def calculate_score(item, discount):
    score = 0
    title = item["title"].lower()

    if discount >= 50:
        score += 50
    elif discount >= 40:
        score += 40
    elif discount >= 30:
        score += 30

    if "nike" in title or "adidas" in title:
        score += 20

    if "booster" in title or "etb" in title:
        score += 25

    if any(size in title for size in ["41", "42", "43"]):
        score += 15

    if item["price"] < 50:
        score += 10

    return score

# ==============================
# SIMULATION FETCH (À remplacer plus tard)
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

    return [
        {
            "id": f"{query}_1",
            "title": f"{query} Nike 42",
            "price": 40,
            "avg_price": avg_price,
            "link": "https://www.vinted.fr/item/123456789"
        }
    ]

# ==============================
# MAIN LOOP
# ==============================

def main():
    global current_index

    send_message("🚀 Bot PRO ULTRA activé (Preview image auto + ROI + /stats)")

    while True:

        check_telegram_commands()

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

                        category = detect_category(item["title"])
                        potential_profit = round(item["avg_price"] - item["price"], 2)

                        stats["total_deals"] += 1
                        stats["total_profit"] += potential_profit
                        stats["total_invested"] += item["price"]

                        if score > stats["best_score"]:
                            stats["best_score"] = score

                        if category == "mode":
                            stats["mode_deals"] += 1
                            stats["mode_profit"] += potential_profit
                        elif category == "pokemon":
                            stats["pokemon_deals"] += 1
                            stats["pokemon_profit"] += potential_profit

                        save_stats(stats)

                        message = f"""
🔥 <b>DEAL SCORE {score}/100</b>

📦 {item['title']}
💰 {item['price']}€
📉 Moyenne: {item['avg_price']}€
📊 -{discount}%

💸 Marge estimée: {potential_profit}€

🔗 Voir l'annonce :
{item['link']}
"""

                        send_message(message)

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
