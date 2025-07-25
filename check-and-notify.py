import requests
import os
import time
from datetime import datetime, timedelta, timezone
# from dotenv import load_dotenv
# load_dotenv()

# Config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
COTIK_AL_TOKEN = os.getenv("COTIK_AL_TOKEN")

# Define GMT+7 timezone
gmt_plus_7 = timezone(timedelta(hours=7))

# Get current time in GMT+7
now_vn = datetime.now(gmt_plus_7).strftime("%Y-%m-%d %H:%M:%S")

NOTIFIED_FILE = "notified_orders.txt"

def load_notified_ids():
    if not os.path.exists(NOTIFIED_FILE):
        return set()
    with open(NOTIFIED_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}
        
def save_notified_ids(order_ids):
    with open(NOTIFIED_FILE, "a", encoding="utf-8") as f:
        for oid in order_ids:
            f.write(f"{oid}\n")

def send_order_item_to_telegram(order):
    shop_name = order.get("shops", {}).get("name", "N/A")
    order_id = order.get("apiOrderId", "Unknown")

    for item in order.get("line_items", []):
        name = item.get("product_name", "Unnamed product")
        sku_name = item.get("sku_name", "")
        quantity = 1  # Adjust if quantity field exists
        image_url = item.get("sku_image")

        # Limit product name to 40 characters
        if len(name) > 60:
            name = name[:37] + "..."

        create_ts = order.get("create_time")
        if create_ts:
            create_dt = datetime.fromtimestamp(create_ts, tz=gmt_plus_7)
            created_str = create_dt.strftime("🕒 Placed: %Y-%m-%d %H:%M:%S")
        else:
            created_str = "🕒 Placed: Unknown"
        
        caption = (
            # f"🛍️ Shop: {shop_code}\n"
            f"💥 Order ID: {order_id} - {shop_name}\n\n"
            f"{created_str}\n\n"
            f"- {quantity} × {name}"
        )

        if sku_name:
            caption += f"\n  ({sku_name})"

        if image_url:
            send_photo_with_caption(image_url, caption)
        else:
            send_text_message(caption)
        
        time.sleep(10)  # delay between messages to avoid spam/rate limit


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

notified_ids = load_notified_ids()
print("[DEBUG] Notified order IDs loaded:", notified_ids)
newly_notified = []

# Request
url = "https://cotik.app/api/order/list?page=1&sizeperpage=50&filter3=AWAITING_SHIPMENT"
url2 = "https://cotik.app/api/order/list?page=1&sizeperpage=50&filter3=ON_HOLD"
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
    response = requests.get(url, headers=headers, timeout=10)

    # Always log the raw response text
    print(f"=== Script Run Time (GMT+7) ===")
    print(now_vn)
    print("=== AWAITING_SHIPMENT RAW RESPONSE TEXT ===")
    print(response.text)
    
    response.raise_for_status()
    data = response.json()

    orders = data.get("data", {}).get("listorders", [])
    recent_orders = list(orders)

    if recent_orders:
        for order in recent_orders:
            order_id = order.get("apiOrderId")
            if not order_id or order_id in notified_ids:
                continue

            send_order_item_to_telegram(order)
            newly_notified.append(order_id)

except Exception as e:
    print(f"[ERROR] {e}")

try:
    response = requests.get(url2, headers=headers, timeout=10)

    # Always log the raw response text
    print(f"=== Script Run Time (GMT+7) ===")
    print(now_vn)
    print("=== ON_HOLD RAW RESPONSE TEXT ===")
    print(response.text)

    response.raise_for_status()
    data = response.json()

    orders = data.get("data", {}).get("listorders", [])
    recent_orders = list(orders)

    if recent_orders:
        for order in recent_orders:
            order_id = order.get("apiOrderId")
            if not order_id or order_id in notified_ids:
                continue

            send_order_item_to_telegram(order)
            newly_notified.append(order_id)

except Exception as e:
    print(f"[ERROR] {e}")

if newly_notified:
    save_notified_ids(newly_notified)
