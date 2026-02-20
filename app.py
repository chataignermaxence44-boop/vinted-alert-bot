import requests
import time
import os
import json
import re
from collections import deque
from statistics import mean

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

SCAN_INTERVAL = 120
COMMAND_CHECK_INTERVAL = 5
STATS_FILE = "stats.json"

VINTED_COMMISSION_RATE = 0.05

PRIORITY_ROI_THRESHOLD = 80
PRIORITY_PROFIT_THRESHOLD = 50

SEARCH_QUERIES = []  # Tu gardes tes 40 recherches côté Vinted

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
            "best_roi": 0
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

🔥 Deals: {stats['total_deals']}
💰 Profit net total: {round(stats['total_profit_net'],2)}€
💸 Capital investi: {round(stats['total_invested'],2)}€
📈 ROI moyen: {round(roi,2)}%
🏆 Meilleur ROI: {round(stats['best_roi'],2)}%
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
# ANALYSE MODE
# ==============================

def analyze_item(title, price, estimated_value):

    commission = estimated_value * VINTED_COMMISSION_RATE
    net_resale = estimated_value - commission
    net_profit = net_resale - price

    if net_profit <= 0:
        return None

    roi = (net_profit / price) * 100

    return {
        "net_profit": round(net_profit,2),
        "roi": round(roi,2)
    }

# ==============================
# SIMULATION (À remplacer si besoin)
# ==============================

def simulate_item():

    title = "Lot 200 cartes Pokemon GX ultra rare"
    price = 60
    estimated_value = 160

    return title, price, estimated_value, "https://www.vinted.fr/item/123456789"

# ==============================
# MAIN LOOP
# ==============================

def main():

    send_message("🚀 Bot FUSION MAX + PRIORITÉ activé")

    while True:

        check_telegram_commands()

        title, price, estimated_value, link = simulate_item()

        result = analyze_item(title, price, estimated_value)

        if result:

            net_profit = result["net_profit"]
            roi = result["roi"]

            stats["total_deals"] += 1
            stats["total_profit_net"] += net_profit
            stats["total_invested"] += price

            if roi > stats["best_roi"]:
                stats["best_roi"] = roi

            save_stats(stats)

            # PRIORITÉ CHECK
            if roi >= PRIORITY_ROI_THRESHOLD or net_profit >= PRIORITY_PROFIT_THRESHOLD:

                message = f"""
🚨 <b>DEAL PRIORITÉ - SNIPER IMMÉDIAT</b>

📦 {title}
💰 Achat: {price}€
📊 Valeur estimée: {estimated_value}€

💸 Profit net: {net_profit}€
📈 ROI: {roi}%

⚡ ACTION RAPIDE RECOMMANDÉE

🔗 {link}
"""

            else:

                message = f"""
🔥 DEAL RENTABLE

📦 {title}
💰 Achat: {price}€
💸 Profit net: {net_profit}€
📈 ROI: {roi}%

🔗 {link}
"""

            send_message(message)

        time.sleep(120)

if __name__ == "__main__":
    main()
