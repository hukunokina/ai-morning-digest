import os, html, requests
import config


def render_markdown(groups, date_str):
    lines = [f"# 🤖 AI Sabah Özeti — {date_str}\n"]
    if not any(groups.values()):
        lines.append("_Bugün yeni bir şey yok._")
        return "\n".join(lines)
    for section, items in groups.items():
        if not items:
            continue
        lines.append(f"\n## {section}\n")
        for it in items:
            sc = f" · {it['score']}p" if it["score"] else ""
            tr = it["title_tr"] or it["title"]
            num = it.get("n", "")
            lines.append(f"**{num}.** {tr}{sc}")
            lines.append(f"  - {it['title']}")
            lines.append(f"  - {it['url']}")
    return "\n".join(lines)


def write_markdown(text, file_date):
    os.makedirs(config.OUT_DIR, exist_ok=True)
    path = os.path.join(config.OUT_DIR, f"{file_date}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def _tg_send(text):
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }
    if config.TELEGRAM_THREAD_ID:
        data["message_thread_id"] = config.TELEGRAM_THREAD_ID
    r = requests.post(url, data=data, timeout=20)
    if not r.ok:
        print(f"[telegram] gonderim hatasi: {r.status_code} {r.text[:200]}")
    return r.ok


def send_telegram(groups, date_str):
    if not (config.TELEGRAM_TOKEN and config.TELEGRAM_CHAT_ID):
        print("[telegram] token/chat_id yok, atlandi (sadece markdown yazildi)")
        return False
    blocks = [f"<b>🤖 AI Sabah Özeti — {date_str}</b>"]
    for section, items in groups.items():
        if not items:
            continue
        blocks.append(f"\n<b>{html.escape(section)}</b>")
        for it in items:
            tr = html.escape(it["title_tr"] or it["title"])
            sc = f" · {it['score']}p" if it["score"] else ""
            num = it.get("n", "")
            blocks.append(f'<b>{num}.</b> <a href="{html.escape(it["url"])}">{tr}</a>{sc}')
    blocks.append("\n<i>💬 Özet için numarayı yaz (örn. 5)</i>")
    text = "\n".join(blocks)
    ok, chunk = True, ""
    for line in text.split("\n"):
        if len(chunk) + len(line) + 1 > 3800:
            ok = _tg_send(chunk) and ok
            chunk = ""
        chunk += line + "\n"
    if chunk.strip():
        ok = _tg_send(chunk) and ok
    return ok
