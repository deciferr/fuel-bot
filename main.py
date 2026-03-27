import os
import time
import requests

# Get webhook from Railway environment variable
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

if not WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK environment variable not set!")

def send_heartbeat():
    try:
        requests.post(WEBHOOK_URL, json={"content": "🚀 Bot is alive!"})
        print("Heartbeat sent.")
    except Exception as e:
        print("Error sending heartbeat:", e)

def main():
    while True:
        print("Bot running...")
        send_heartbeat()
        time.sleep(60)  # Wait 60 seconds before next heartbeat

if __name__ == "__main__":
    main()
