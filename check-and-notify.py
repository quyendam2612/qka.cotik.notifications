import requests
import os
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
# load_dotenv()

# Config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
COTIK_AL_TOKEN = os.getenv("COTIK_AL_TOKEN")

def send_order_item_to_telegram(order):
    shop_name = order.get("shops", {}).get("name", "N/A")
    order_id = order.get("apiOrderId", "Unknown")

    for item in order.get("line_items", []):
        name = item.get("product_name", "Unnamed product")
        quantity = 1  # Update if quantity field exists
        image_url = item.get("sku_image")

        caption = (
            f"🛍️ Shop: {shop_name}\n"
            f"📦 Order ID: {order_id}\n\n"
            f"{quantity} × {name}"
        )

        if image_url:
            send_photo_with_caption(image_url, caption)
        else:
            send_text_message(caption)


def send_photo_with_caption(photo_url, caption):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        requests.post(
            telegram_url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "photo": photo_url},
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        print("[Telegram Photo Error]", e)


def send_text_message(text):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(
            telegram_url,
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        print("[Telegram Text Error]", e)

# Request
# url = "https://cotik.app/api/order/list?page=1&sizeperpage=10&filter3=AWAITING_COLLECTION"
url = "https://cotik.app/api/order/list?page=1&sizeperpage=10&filter3=ON_HOLD"
headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9,vi;q=0.8",
    "al-token": COTIK_AL_TOKEN,
    "dnt": "1",
    # "if-none-match": 'W/"42-qdxW7m95G9yw+i8jPi0zKzQrrZw"',
    "priority": "u=1, i",
    "referer": "https://cotik.app/admin/orders?tab=orders_on_hold",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "macOS",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    orders = data.get("data", {}).get("listorders", [])
    now = int(time.time())  # current time in seconds
    # ten_minutes_ago = now - 100000  # 10 minutes ago
    ten_minutes_ago = now - 600  # 10 minutes ago

    recent_orders = [
        o for o in orders
        if o.get("create_time", 0) >= ten_minutes_ago
    ]

    if recent_orders:
        order_count = len(recent_orders)
        messages = []

        for order in recent_orders:
            send_order_item_to_telegram(order)
            time.sleep(10)  # delay between messages to avoid spam/rate limit

except Exception as e:
    print(f"[ERROR] {e}")