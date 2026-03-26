import requests
from bs4 import BeautifulSoup
import re
import time

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1486616926783279134/r-LXJqQA2KCf37CkPrUaNTLEkyMPLGPBVPciBPUyVSERICd757SH1pgSaTxw8VLdHIUv"

URLS = [
    "https://www.gmanetwork.com/news/money/",
    "https://news.abs-cbn.com/business",
    "https://business.inquirer.net/"
]

last_sent = ""

def fetch_articles():
    articles = []

    for url in URLS:
        try:
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            for a in soup.find_all("a"):
                text = a.get_text().strip()
                if len(text) > 30:
                    articles.append(text)
        except:
            continue

    return articles


def extract_price_info(text):
    text_lower = text.lower()

    fuel_type = None
    if "diesel" in text_lower:
        fuel_type = "Diesel"
    elif "gasoline" in text_lower or "gas" in text_lower:
        fuel_type = "Gasoline"
    elif "kerosene" in text_lower:
        fuel_type = "Kerosene"

    direction = None
    if "increase" in text_lower or "hike" in text_lower:
        direction = "⬆️ Increase"
    elif "rollback" in text_lower or "decrease" in text_lower:
        direction = "⬇️ Rollback"

    matches = re.findall(r'₱?\d+(\.\d+)?', text)

    values = []
    for m in matches:
        try:
            val = float(m.replace("₱", ""))
            if val < 10:
                values.append(val)
        except:
            continue

    if fuel_type and direction and values:
        return fuel_type, direction, min(values), max(values)

    return None


def send_to_discord(message):
    requests.post(DISCORD_WEBHOOK, json={"content": message})


def main():
    global last_sent

    articles = fetch_articles()

    for article in articles:
        result = extract_price_info(article)

        if result:
            fuel, direction, min_val, max_val = result

            message = f"""
⛽ Fuel Price Alert

Fuel: {fuel}
Direction: {direction}
Estimated Change: ₱{min_val:.2f} – ₱{max_val:.2f} per liter
"""

            if message != last_sent:
                send_to_discord(message)
                last_sent = message
                break


while True:
    main()
    time.sleep(21600)
