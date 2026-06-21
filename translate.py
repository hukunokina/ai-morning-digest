import re, time, json, requests
import config

# --- google (deep-translator) backend icin AI jargon korumasi ---
GLOSSARY = [
    "RLHF", "QLoRA", "LoRA", "vLLM", "CUDA", "KV cache",
    "LLMs", "LLM", "RAG", "GPUs", "GPU", "CPU", "TPU", "NPU", "MoE",
    "FP8", "FP16", "BF16", "INT8", "INT4", "API", "SDK", "SOTA",
    "AGI", "ASI", "NLP", "OCR", "TTS", "ASR", "MLP", "CNN", "RNN",
    "GAN", "VAE", "SFT", "DPO", "PPO", "RL",
]
_PATTERNS = [(t, re.compile(r"(?<![A-Za-z])" + re.escape(t) + r"(?![A-Za-z])")) for t in GLOSSARY]

_GEMINI_PROMPT = (
    "Asagidaki Ingilizce AI/teknoloji haber basliklarini Turkce'ye cevir.\n"
    "KURALLAR:\n"
    "- Teknik terimleri ve kisaltmalari INGILIZCE BIRAK: LLM, RAG, GPU, CPU, vLLM, KV cache, "
    "API, SDK, MoE, LoRA, RLHF, fine-tuning, inference, embedding, transformer, benchmark ve "
    "model isimleri (GPT, Llama, Qwen, Gemini, Claude, DeepSeek, Mistral, Gemma vb.).\n"
    "- Dogal, akici, KISA Turkce kullan; haber basligi tonunu koru.\n"
    "- Reddit etiketlerini ([D], [R], [P]) oldugu gibi birak.\n"
    "- Sadece cevirileri ayni sirada bir JSON string dizisi olarak don.\n\n"
    "Basliklar:\n"
)


def _gemini(titles):
    key = config.GOOGLE_API_KEY
    if not key:
        print("[gemini] GOOGLE_API_KEY yok")
        return None
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{config.GEMINI_MODEL}:generateContent?key={key}")
    listing = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles))
    body = {
        "contents": [{"parts": [{"text": _GEMINI_PROMPT + listing}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
            "responseSchema": {"type": "ARRAY", "items": {"type": "STRING"}},
        },
    }
    try:
        r = requests.post(url, json=body, timeout=60)
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        arr = json.loads(text)
        if isinstance(arr, list) and len(arr) == len(titles):
            return [str(x) for x in arr]
        print(f"[gemini] uzunluk uyumsuz {len(arr)}!={len(titles)}")
        return None
    except Exception as e:
        print(f"[gemini] hata: {e}")
        return None


def _protect(text):
    mapping = {}
    for term, pat in _PATTERNS:
        def repl(m):
            token = f"#{len(mapping)}#"
            mapping[token] = m.group(0)
            return token
        text = pat.sub(repl, text)
    return text, mapping


def _restore(text, mapping):
    for token, term in mapping.items():
        text = text.replace(token, term)
    return text


def _google(titles):
    from deep_translator import GoogleTranslator
    tr = GoogleTranslator(source="auto", target=config.TRANSLATE_TARGET)
    out = []
    for t in titles:
        guarded, mapping = _protect(t)
        try:
            res = tr.translate(guarded[:480]) or guarded
            out.append(_restore(res, mapping))
        except Exception as e:
            print(f"[translate] hata: {e}")
            out.append(t)
        time.sleep(0.2)
    return out


def translate_items(items):
    if config.TRANSLATE_BACKEND == "none" or not items:
        for it in items:
            it["title_tr"] = it["title"]
        return items
    titles = [it["title"] for it in items]
    if config.TRANSLATE_BACKEND == "gemini":
        tr = _gemini(titles)
        if tr is None:
            print("[translate] gemini basarisiz -> google fallback")
            tr = _google(titles)
    else:
        tr = _google(titles)
    for it, t in zip(items, tr):
        it["title_tr"] = t
    return items
