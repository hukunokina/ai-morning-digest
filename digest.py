import json, os, datetime
import config, sources, translate, deliver

SECTION_ORDER = ["Hacker News", "Reddit r/LocalLLaMA", "Reddit r/MachineLearning",
                 "Lobsters", "arXiv", "HF Papers"]


def load_state():
    if os.path.exists(config.STATE_FILE):
        try:
            return set(json.load(open(config.STATE_FILE)))
        except Exception:
            return set()
    return set()


def save_state(seen):
    json.dump(list(seen)[-3000:], open(config.STATE_FILE, "w"))


def group_items(items):
    groups = {}
    for it in items:
        groups.setdefault(it["source"], []).append(it)
    ordered = {}
    for s in SECTION_ORDER:
        if s in groups:
            ordered[s] = groups.pop(s)
    for s in sorted(groups):  # RSS (📰 ...) en sona
        ordered[s] = groups[s]
    return ordered


def main():
    seen = load_state()
    items = sources.fetch_all()
    fresh = [it for it in items if it["id"] not in seen]
    print(f"{len(items)} cekildi, {len(fresh)} yeni")

    fresh = translate.translate_items(fresh)
    groups = group_items(fresh)

    # global numaralandirma (gosterim sirasiyla) + bot icin index.json
    n = 0
    index = {}
    for section, its in groups.items():
        for it in its:
            n += 1
            it["n"] = n
            index[str(n)] = {"url": it["url"], "title": it["title_tr"] or it["title"], "source": section}

    now = datetime.datetime.now()
    if fresh:
        json.dump({"date": now.strftime("%Y-%m-%d"), "items": index},
                  open(config.INDEX_FILE, "w"), ensure_ascii=False)
    md = deliver.render_markdown(groups, now.strftime("%d.%m.%Y"))
    path = deliver.write_markdown(md, now.strftime("%Y-%m-%d"))
    print(f"markdown: {path}")

    if fresh:
        deliver.send_telegram(groups, now.strftime("%d.%m.%Y"))
    else:
        print("yeni icerik yok, telegram atlandi")

    for it in fresh:
        seen.add(it["id"])
    save_state(seen)
    print("bitti")


if __name__ == "__main__":
    main()
