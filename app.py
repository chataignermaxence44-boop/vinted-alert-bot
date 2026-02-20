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

# Mémoire anti-doublon (garde 500 IDs max)
seen_items = deque(maxlen=500)

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
# ANALYSE PRIX
# ==============================

def calculate_discount(price, avg_price):
    if avg_price == 0:
        return 0
    return round(((avg_price - price) / avg_price) * 100, 2)

# ==============================
# SCORING
# ==============================

def calculate_score(item, discount):
    score = 0

    # Discount scoring
    if discount >= 40:
        score += 45
    elif discount >= 30:
        score += 30

    # Marque forte
    strong_brands = ["nike", "adidas", "tn", "air max"]
    if any(brand in item["title"].lower() for brand in strong_brands):
        score += 20

    # Pokémon keywords
    pokemon_keywords = ["booster", "scellé", "etb", "elite trainer"]
    if any(word in item["title"].lower() for word in pokemon_keywords):
        score += 25

    # Taille recherchée
    hot_sizes = ["41", "42", "43"]
    if any(size in item["title"] for size in hot_sizes):
        score += 15

    # Prix psychologique
    if item["price"] < 50:
        score += 10

    return score

# ==============================
# SIMULATION DONNÉES (TEMPORAIRE)
# ==============================

def fetch_items():
    # ⚠️ Simulation pour moteur
    return [
        {
            "id": "1",
            "title": "Nike Air Max 42 Homme",
            "price": 45,
            "avg_price": 80,
            "link": "https://vinted.fr/item/123"
        },
        {
            "id": "2",
            "title": "Booster Pokémon Scellé",
            "price": 70,
            "avg_price": 100,
            "link": "https://vinted.fr/item/456"
        }
    ]

# ==============================
# MAIN LOOP
# ==============================

def main():
    send_telegram("🤖 Bot PRO actif - Version Scoring activée")

    while True:
        items = fetch_items()

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

📦 {item['title']}
💰 {item['price']}€
📉 Moyenne: {item['avg_price']}€
📊 -{discount}%

🎯 Catégorie: Auto détectée
📈 Potentiel revente: {'Élevé' if score >= 75 else 'Moyen'}

🔗 <a href="{item['link']}">Voir sur Vinted</a>
"""
                    send_telegram(message)

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
