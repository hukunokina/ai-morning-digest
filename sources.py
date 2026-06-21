import time, hashlib, requests, feedparser
import config

UA = {"User-Agent": config.USER_AGENT}


def _item(source, title, url, score=0, published=None):
    return {
        "source": source,
        "title": title.strip(),
        "title_tr": "",
        "url": url,
        "score": score,
        "published": published or "",
        "id": hashlib.sha1(url.encode()).hexdigest()[:16],
    }


import re
_AI_WORD = re.compile(r"(?<![A-Za-z])(AI|ML|AGI)(?![A-Za-z])")


def _matches(text):
    t = text.lower()
    return any(k.lower() in t for k in config.KEYWORDS)


def _hn_relevant(title):
    return _matches(title) or bool(_AI_WORD.search(title))


def fetch_hackernews():
    # front_page = su an one cikan (guncel + populer) hikayeler, tek istek.
    try:
        r = requests.get(
            "https://hn.algolia.com/api/v1/search",
            params={"tags": "front_page", "hitsPerPage": 50},
            headers=UA, timeout=15,
        )
        items = {}
        for h in r.json().get("hits", []):
            title = h.get("title") or ""
            if not title or (h.get("points") or 0) < config.HN_MIN_POINTS:
                continue
            if not _hn_relevant(title):
                continue
            url = h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}"
            it = _item("Hacker News", title, url, h.get("points", 0), h.get("created_at", ""))
            items[it["id"]] = it
        return sorted(items.values(), key=lambda x: -x["score"])[:config.HN_CAP]
    except Exception as e:
        print(f"[hn] hata: {e}")
        return []


def fetch_reddit():
    # JSON 403 -> RSS feed'i residential proxy ile cek (feed zaten top/day sirali).
    if not config.RESIDENTIAL_PROXY:
        print("[reddit] RESIDENTIAL_PROXY yok, atlandi")
        return []
    P = {"http": config.RESIDENTIAL_PROXY, "https": config.RESIDENTIAL_PROXY}
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
    items = []
    for sub in config.REDDIT_SUBS:
        try:
            r = requests.get(f"https://www.reddit.com/r/{sub}/top/.rss",
                             params={"t": "day"}, headers=h, proxies=P, timeout=30)
            if r.status_code != 200:
                print(f"[reddit:{sub}] status {r.status_code}")
                continue
            feed = feedparser.parse(r.content)
            for e in feed.entries[:config.REDDIT_PER_SUB]:
                items.append(_item(f"Reddit r/{sub}", e.title.strip(), e.link, 0,
                                   getattr(e, "published", "")))
        except Exception as ex:
            print(f"[reddit:{sub}] hata: {ex}")
    return items


def fetch_lobsters():
    try:
        r = requests.get("https://lobste.rs/t/ai.json", headers=UA, timeout=15)
        items = [
            _item("Lobsters", p.get("title", ""), p.get("url") or p.get("comments_url", ""),
                  p.get("score", 0), p.get("created_at", ""))
            for p in r.json()
        ]
        items = [i for i in items if i["title"] and i["url"]]
        items.sort(key=lambda x: -x["score"])
        return items[:config.LOBSTERS_CAP]
    except Exception as e:
        print(f"[lobsters] hata: {e}")
        return []


def fetch_arxiv():
    try:
        q = "+OR+".join(f"cat:{c}" for c in config.ARXIV_CATS)
        url = (f"https://export.arxiv.org/api/query?search_query={q}"
               f"&sortBy=submittedDate&sortOrder=descending&max_results=40")
        feed = feedparser.parse(url, agent=config.USER_AGENT)
        matched, allrecent = [], []
        for e in feed.entries:
            title = e.title.replace("\n", " ").strip()
            it = _item("arXiv", title, e.link, 0, getattr(e, "published", ""))
            allrecent.append(it)
            if _matches(title + " " + getattr(e, "summary", "")):
                matched.append(it)
        items = matched if len(matched) >= 3 else allrecent
        return items[:config.ARXIV_CAP]
    except Exception as e:
        print(f"[arxiv] hata: {e}")
        return []


def fetch_hf_papers():
    try:
        r = requests.get("https://huggingface.co/api/daily_papers", headers=UA, timeout=15)
        items = []
        for p in r.json():
            paper = p.get("paper", {}) or {}
            title = paper.get("title") or p.get("title", "")
            pid = paper.get("id") or ""
            if not title:
                continue
            url = f"https://huggingface.co/papers/{pid}" if pid else "https://huggingface.co/papers"
            score = paper.get("upvotes", p.get("upvotes", 0)) or 0
            items.append(_item("HF Papers", title, url, score, p.get("publishedAt", "")))
        items.sort(key=lambda x: -x["score"])
        return items[:config.HF_CAP]
    except Exception as e:
        print(f"[hf] hata: {e}")
        return []


def fetch_rss():
    items = []
    cutoff = time.time() - config.RSS_DAYS * 86400
    for name, url in config.RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url, agent=config.USER_AGENT)
            cnt = 0
            for e in feed.entries:
                pub = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
                if pub and time.mktime(pub) < cutoff:
                    continue
                items.append(_item(f"📰 {name}", e.title.strip(), e.link, 0, getattr(e, "published", "")))
                cnt += 1
                if cnt >= config.RSS_PER_FEED:
                    break
        except Exception as ex:
            print(f"[rss:{name}] hata: {ex}")
    return items


def fetch_all():
    res = []
    if config.SOURCES.get("hackernews"):
        res += fetch_hackernews()
    if config.SOURCES.get("reddit"):
        res += fetch_reddit()
    if config.SOURCES.get("lobsters"):
        res += fetch_lobsters()
    if config.SOURCES.get("arxiv"):
        res += fetch_arxiv()
    if config.SOURCES.get("hf_papers"):
        res += fetch_hf_papers()
    if config.SOURCES.get("rss"):
        res += fetch_rss()
    return res
