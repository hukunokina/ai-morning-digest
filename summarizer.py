import re, time, requests
import config

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"}

_SUM_RULES = (
    "Bu özeti biri 'içeriğe tıklamalı mıyım' diye karar vermek için okuyacak; amacın merak uyandırmak.\n"
    "- En ÇARPICI, şaşırtıcı veya önemli noktayı en başa al ve onu biraz AÇ/detaylandır.\n"
    "- Rutin, dolgu, sıkıcı kısımları ATLA; her cümle bir değer katsın.\n"
    "- Doğrudan öze gir; 'Bu makale...', 'Bu paylaşım...' gibi giriş cümlesi YAPMA.\n"
    "- Vurucu, net, akıcı Türkçe — zeki bir arkadaşın anlattığı gibi, kuru haber dili değil.\n"
    "- Teknik terim/kısaltma/model isimlerini İngilizce bırak (LLM, GPU, vLLM, KV cache, RAG, fine-tuning...).\n"
    "- Atıf/kaynak işareti KOYMA ([1.1], [2] gibi).\n"
    "- 3-5 cümle. Sadece özeti yaz."
)


def _clean(t):
    t = re.sub(r"\s*\[\d+(?:\.\d+)*\]", "", t)          # [1.1] gibi atiflari sil
    return re.sub(r"[ \t]{2,}", " ", t).strip()


def _api():
    return (f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{config.GEMINI_MODEL}:generateContent?key={config.GOOGLE_API_KEY}")


def _post(body, retries=3):
    # 429/transient hatalarda backoff ile tekrar dene
    for i in range(retries):
        try:
            r = requests.post(_api(), json=body, timeout=90)
            if r.status_code == 200:
                j = r.json()
                if "candidates" in j:
                    return j
            elif r.status_code not in (429, 500, 503):
                print(f"[sum] api {r.status_code}: {r.text[:150]}")
                return None
        except Exception as e:
            print(f"[sum] post hata: {e}")
        time.sleep(3 * (i + 1))
    return None


def _extract(j):
    parts = j["candidates"][0].get("content", {}).get("parts", [])
    texts = [p["text"] for p in parts if p.get("text") and not p.get("thought")]
    return _clean("\n".join(texts))


def _gemini_url(url):
    prompt = f"Bu URLdeki yaziyi Turkce ozetle. {_SUM_RULES}\nURL: {url}"
    j = _post({"contents": [{"parts": [{"text": prompt}]}], "tools": [{"url_context": {}}]})
    if not j:
        return "", False
    meta = j["candidates"][0].get("urlContextMetadata") or j["candidates"][0].get("url_context_metadata") or {}
    ok = any("SUCCESS" in str(m.get("urlRetrievalStatus", "")) for m in meta.get("urlMetadata", []))
    return _extract(j), ok


def _gemini_text(content):
    prompt = f"Asagidaki metni Turkce ozetle. {_SUM_RULES}\n\nMETIN:\n{content[:14000]}"
    j = _post({"contents": [{"parts": [{"text": prompt}]}]})
    return _extract(j) if j else ""


def _proxy_html(url):
    P = None
    if config.RESIDENTIAL_PROXY:
        P = {"http": config.RESIDENTIAL_PROXY, "https": config.RESIDENTIAL_PROXY}
    return requests.get(url, headers=UA, proxies=P, timeout=30).text


def _normalize(url):
    # arxiv /pdf/ cok yavas; abstract sayfasi hizli ve ozet icin yeterli
    m = re.match(r"https?://arxiv\.org/pdf/([\w.]+?)(?:v\d+)?(?:\.pdf)?/?$", url)
    if m:
        return f"https://arxiv.org/abs/{m.group(1)}"
    return url


def summarize(url):
    url = _normalize(url)
    try:
        txt, ok = _gemini_url(url)
        if ok and txt:
            return txt
    except Exception as e:
        print(f"[sum] url_context hata: {e}")
    # Fallback: residential proxy ile cek, HTMLyi Gemini'ye ver (Reddit vb. bloklu siteler)
    try:
        html = _proxy_html(url)
        if html:
            out = _gemini_text(html)
            if out:
                return out
    except Exception as e:
        print(f"[sum] proxy fallback hata: {e}")
    return "⚠️ Ozet cikarilamadi (icerik cekilemedi)."
