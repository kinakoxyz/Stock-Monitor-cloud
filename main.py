import requests
import json
import os

PRODUCT_FILE = "products.json"
STATUS_FILE = "stock_status.json"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
GITHUB_EVENT_NAME = os.getenv("GITHUB_EVENT_NAME")
SHOULD_SEND_SUMMARY = GITHUB_EVENT_NAME in ["schedule", "workflow_dispatch"] or GITHUB_EVENT_NAME is None

def send_discord(message):
    if not DISCORD_WEBHOOK_URL:
        print("Webhook未設定")
        return

    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=10)
    except Exception as e:
        print("Discord送信失敗:", e)

def load_products():
    with open(PRODUCT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_status(status):
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)

def check_stock(product, previous_status):
    product_id = product["id"]

    try:
        api_url = product["url"] + ".js"
        response = requests.get(api_url, timeout=10)

        if response.status_code != 200:
            raise Exception(f"API取得失敗: {response.status_code}")

        data = response.json()
        current_stock = any(v.get("available") for v in data.get("variants", []))
        previous_stock = previous_status.get(product_id)

        # --- 状態変化チェック ---
        if previous_stock is not None:
            if not previous_stock and current_stock:
                send_discord(
                    f"🟢 在庫復活！\n"
                    f"商品名: {product['name']}\n"
                    f"URL: {product['url']}"
                )

            elif previous_stock and not current_stock:
                send_discord(
                    f"🔴 売り切れ！\n"
                    f"商品名: {product['name']}\n"
                    f"URL: {product['url']}"
                )

        return current_stock

    except Exception as e:
        send_discord(
            f"❌ エラー発生\n"
            f"商品名: {product['name']}\n"
            f"内容: {str(e)}"
        )
        return previous_status.get(product_id, False)

if __name__ == "__main__":
    print("=== 状態変化監視モード ===")

    products = load_products()
    previous_status = load_status()
    new_status = {}

    # --- 商品チェック ---
    for product in products:
        new_status[product["id"]] = check_stock(product, previous_status)

    # --- 状態保存 ---
    save_status(new_status)

    # --- サマリー通知 ---
    if SHOULD_SEND_SUMMARY:
        summary_lines = []
        for product in products:
            status = new_status.get(product["id"])
            icon = "🟢" if status else "🔴"
            summary_lines.append(f"{icon} {product['name']}\n{product['url']}")

        summary_message = "📊 本日の在庫状況\n\n" + "\n".join(summary_lines)
        send_discord(summary_message)

    print("=== 処理終了 ===")
