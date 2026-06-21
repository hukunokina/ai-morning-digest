import time, json, html, requests
import config, summarizer

API = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}"


def load_index():
    try:
        return json.load(open(config.INDEX_FILE)).get("items", {})
    except Exception:
        return {}


def send(chat_id, thread_id, text, reply_to=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML",
            "disable_web_page_preview": "true"}
    if thread_id:
        data["message_thread_id"] = thread_id
    if reply_to:
        data["reply_to_message_id"] = reply_to
    try:
        requests.post(f"{API}/sendMessage", data=data, timeout=30)
    except Exception as e:
        print(f"[bot] send hata: {e}")


def parse_num(text):
    t = (text or "").strip().lower()
    for p in ("/ozet", "/summary", "/o"):
        if t.startswith(p):
            t = t[len(p):].strip().lstrip("@").split()[-1] if t[len(p):].strip() else ""
            break
    return int(t) if t.isdigit() else None


def handle(msg):
    chat = msg.get("chat", {})
    if str(chat.get("id")) != str(config.TELEGRAM_CHAT_ID):
        return
    num = parse_num(msg.get("text", ""))
    if num is None:
        return
    thread = msg.get("message_thread_id") or config.TELEGRAM_THREAD_ID
    reply_to = msg.get("message_id")
    item = load_index().get(str(num))
    if not item:
        send(chat["id"], thread, f"⚠️ {num} numarali baslik bulunamadi (yeni digest gelince numaralar sifirlanir).", reply_to)
        return
    send(chat["id"], thread, f"⏳ <b>{num}.</b> ozetleniyor…", reply_to)
    summary = summarizer.summarize(item["url"])
    head = f"📄 <b>{num}. {html.escape(item['title'])}</b>\n{html.escape(item['url'])}\n\n"
    send(chat["id"], thread, head + summary, reply_to)


def main():
    # baslangicta backlog'u atla (yeniden baslayinca eski mesajlari ozetleme)
    offset = None
    try:
        r = requests.get(f"{API}/getUpdates", params={"timeout": 0}, timeout=20).json()
        ups = r.get("result", [])
        if ups:
            offset = ups[-1]["update_id"] + 1
    except Exception as e:
        print(f"[bot] drain hata: {e}")
    print("[bot] basladi, dinleniyor")
    while True:
        try:
            r = requests.get(f"{API}/getUpdates",
                             params={"timeout": 30, "offset": offset}, timeout=40).json()
            for u in r.get("result", []):
                offset = u["update_id"] + 1
                msg = u.get("message")
                if msg:
                    handle(msg)
        except Exception as e:
            print(f"[bot] loop hata: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
