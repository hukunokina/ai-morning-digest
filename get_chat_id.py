import os, requests

token = os.environ.get("TELEGRAM_TOKEN", "")
if not token:
    raise SystemExit("Once secrets.env'e TELEGRAM_TOKEN koy ve botuna bir mesaj at.")

r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=20).json()
seen = set()
for u in r.get("result", []):
    msg = u.get("message") or u.get("channel_post") or {}
    chat = msg.get("chat", {})
    if chat.get("id") and chat["id"] not in seen:
        seen.add(chat["id"])
        print(f"chat_id={chat['id']}  ({chat.get('type')}, {chat.get('first_name') or chat.get('title','')})")
if not seen:
    print("Hic mesaj yok. Botuna Telegram'dan bir mesaj at, sonra tekrar calistir.")
