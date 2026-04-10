import os
import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime

# ---------------------------
# CONFIG
# ---------------------------
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
if not DISCORD_WEBHOOK:
    raise ValueError("DISCORD_WEBHOOK environment variable not set!")

DATA_FILE = "data.json"

NEWS_URLS = [
    "https://www.gmanetwork.com/news/money/",
    "https://news.abs-cbn.com/business",
    "https://business.inquirer.net/"
]

last_sent_messages = set()


# ---------------------------
# DATA STORAGE
# ---------------------------
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


# ---------------------------
# REAL MARKET DATA
# ---------------------------
def get_brent_price():
    try:
        url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=BZ=F"
        res = requests.get(url, timeout=10)
        data = res.json()

        price = data["quoteResponse"]["result"][0]["regularMarketPrice"]
        return float(price)

    except Exception as e:
        print("Brent error:", e)
        return None


def get_usd_php():
    try:
        url = "https://api.exchangerate.host/latest?base=USD&symbols=PHP"
        res = requests.get(url, timeout=10)
        return float(res.json()["rates"]["PHP"])

    except Exception as e:
        print("FX error:", e)
        return None


# ---------------------------
# STORE DAILY DATA
# ---------------------------
def add_today_data(brent, fx):
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")

    # prevent duplicates
    for d in data:
        if d["date"] == today:
            return

    data.append({
        "date": today,
        "brent": brent,
        "fx": fx
    })

    save_data(data)


# ---------------------------
# WEEKLY AVERAGE CALCULATION
# ---------------------------
def compute_weekly_averages():
    data = load_data()

    if len(data) < 14:
        return None

    last_week = data[-7:]
    prev_week = data[-14:-7]

    def avg(arr, key):
        return sum(d[key] for d in arr) / len(arr)

    return {
        "brent_last": avg(last_week, "brent"),
        "brent_prev": avg(prev_week, "brent"),
        "fx_last": avg(last_week, "fx"),
        "fx_prev": avg(prev_week, "fx")
    }


# ---------------------------
# SIGNAL ENGINE (MOPS STYLE)
# ---------------------------
def generate_signal(avg):
    score = 0

    if avg["brent_last"] > avg["brent_prev"]:
        score += 1
        brent_trend = "⬆️"
    else:
        score -= 1
        brent_trend = "⬇️"

    if avg["fx_last"] > avg["fx_prev"]:
        score += 1
        fx_trend = "⬆️"
    else:
        score -= 1
        fx_trend = "⬇️"

    if score == 2:
        bias = "⛽ Strong Increase"
        confidence = "HIGH"
    elif score == 1:
        bias = "⛽ Mild Increase"
        confidence = "MEDIUM"
    elif score == 0:
        bias = "⛽ Neutral"
        confidence = "LOW"
    elif score == -1:
        bias = "⛽ Mild Rollback"
        confidence = "MEDIUM"
    else:
        bias = "⛽ Strong Rollback"
        confidence = "HIGH"

    return brent_trend, fx_trend, bias, confidence


# ---------------------------
# DISCORD SENDER
# ---------------------------
def send_to_discord(message):
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": message})
        print("Sent to Discord")
    except Exception as e:
        print("Discord error:", e)


# ---------------------------
# MAIN BOT LOGIC
# ---------------------------
def main():
    brent = get_brent_price()
    fx = get_usd_php()

    print(f"Brent: {brent} | FX: {fx}")

    if not brent or not fx:
        return

    # store daily snapshot
    add_today_data(brent, fx)

    # compute weekly averages
    avg = compute_weekly_averages()

    if not avg:
        print("Not enough data yet for weekly average.")
        return

    brent_trend, fx_trend, bias, confidence = generate_signal(avg)

    message = f"""
📊 Weekly Fuel Price Signal

Brent Avg: {avg['brent_prev']:.2f} → {avg['brent_last']:.2f} {brent_trend}
FX Avg: {avg['fx_prev']:.2f} → {avg['fx_last']:.2f} {fx_trend}

Bias: {bias}
Confidence: {confidence}
"""

    if message not in last_sent_messages:
        send_to_discord(message)
        last_sent_messages.add(message)


# ---------------------------
# RUN LOOP
# ---------------------------
if __name__ == "__main__":
    while True:
        main()
        time.sleep(3600)  # hourly update