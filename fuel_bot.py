import os
import requests
from bs4 import BeautifulSoup
import re
import time

# Discord webhook from environment variables
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
if not DISCORD_WEBHOOK:
    raise ValueError("DISCORD_WEBHOOK environment variable not set!")

# URLs to scrape
URLS = [
    "https://www.gmanetwork.com/news/money/",
    "https://news.abs-cbn.com/business",
    "https://business.inquirer.net/"
]

# Filter: only these fuel types trigger alerts
FUEL_FILTER = {"Diesel", "Gasoline"}  # Add "Kerosene" if needed

# Keep track of messages already sent
last_sent_messages = set()


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

        except Exception as e:
            print(f"Error fetching {url}: {e}")
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

    # Ignore if not in filter
    if fuel_type not in FUEL_FILTER:
        return None

    # Improved direction detection
    direction = None
    if any(word in text_lower for word in ["increase", "hike", "up", "rise"]):
        direction = "⬆️ Increase"
    elif any(word in text_lower for word in ["rollback", "decrease", "down", "cut"]):
        direction = "⬇️ Rollback"

    # Extract numbers (₱ values)
    matches = re.findall(r'₱?\d+(\.\d+)?', text)
    values = []

    for m in matches:
        try:
            val = float(m.replace("₱", ""))
            # Relaxed filter (was <10 before)
            if val < 20:
                values.append(val)
        except:
            continue

    if fuel_type and direction and values:
        return fuel_type, direction, min(values), max(values)

    return None


def send_to_discord(message):
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": message})
        print("Sent message to Discord.")
    except Exception as e:
        print("Error sending to Discord:", e)


def main():
    global last_sent_messages

    articles = fetch_articles()
    print(f"Fetched {len(articles)} articles")

    # ✅ STEP 5: TEST MESSAGE (REMOVE AFTER CONFIRMATION)
    send_to_discord("✅ TEST MESSAGE FROM FUEL BOT")
    print("Sent test message")

    for article in articles:
        print("Checking:", article[:100])

        result = extract_price_info(article)

        if result:
            fuel, direction, min_val, max_val = result

            message = f"""
⛽ Fuel Price Alert

Fuel: {fuel}
Direction: {direction}
Estimated Change: ₱{min_val:.2f} – ₱{max_val:.2f} per liter
"""

            print("MATCH FOUND:", message)

            if message not in last_sent_messages:
                send_to_discord(message)
                last_sent_messages.add(message)


# Continuous loop
if __name__ == "__main__":
    while True:
        main()
        # 5 minutes interval (for testing)
        time.sleep(300)
