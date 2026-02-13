import requests
import json
import os
import sys

# --- 設定 ---

PRODUCT_FILE = "products.json"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def load_products():
    if os.path.exists(PRODUCT_FILE):
        try:
            with open(PRODUCT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 設定ファイルの読み込みに失敗しました: {e}")
            return []
    else:
        print(f"⚠ 設定ファイル {PRODUCT_FILE} が見つかりません。")
        return []


def send_discord_notification(message):
    if not DISCORD_WEBHOOK_URL:
        print("❌ DISCORD_WEBHOOK_URL が設定されていません")
        sys.exit(1)

    data = {"content": message}

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data, timeout=10)
        if response.status_code == 204:
            print("✅ Discord通知 成功")
        else:
            print(f"❌ Discord通知 失敗: {response.status_code}")
    except Exception as e:
        print("❌ Discord送信エラー:", e)


# --- 在庫チェック ---

def check_stock(product):
    print(f"在庫確認中: {product['name']}")

    try:
        api_url = product["url"] + ".js"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }

        response = requests.get(api_url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"⚠ API取得失敗: {response.status_code}")
            return

        data = response.json()

        for variant in data.get("variants", []):
            if variant.get("available"):
                print("🟢 在庫あり")
                send_discord_notification(
                    f"🟢 在庫復活\n"
                    f"商品名: {product['name']}\n"
                    f"URL: {product['url']}"
                )
                return

        print("🔴 在庫なし")

    except Exception as e:
        print("❌ エラー:", e)


# --- 実行 ---

if __name__ == "__main__":
    print("=== GitHub Actions 在庫監視開始 ===")

    products = load_products()

    if not products:
        print("監視対象がありません")
        sys.exit(0)

    for product in products:
        check_stock(product)

    print("=== 処理終了 ===")
