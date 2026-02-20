import requests
import time
import os

TELEGRAM_TOKEN = os.environ.get("8319634501:AAFTESryARlhFX_iawzNA_DceyzYTI1P1rU")
CHAT_ID = os.environ.get("7543386790")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
    }
    requests.post(url, data=data)

while True:
    send_telegram("🚀 Bot en ligne et actif 24/7 !")
    time.sleep(300)
