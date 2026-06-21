import os

# ============ KONULAR ============
# HN / arXiv / Lobsters basliklarini bu kelimelere gore filtreler.
# Kurulum sonrasi buraya ekle/cikar.
KEYWORDS = [
    "LLM", "language model", "agent", "vLLM", "inference",
    "quantization", "fine-tun", "RAG", "diffusion", "transformer",
    "open source", "open-source", "reasoning", "multimodal",
    "GPU", "CUDA", "embedding", "context window", "MoE", "fine-tuning",
    "llama", "qwen", "mistral", "claude", "gpt", "gemini",
]

# ============ KAYNAK AC/KAPA ============
SOURCES = {
    "hackernews": True,
    "reddit": True,
    "lobsters": True,
    "arxiv": True,
    "hf_papers": True,
    "rss": True,
}

# Reddit JSON 403 veriyor (OAuth gerekiyor); RSS feed'i residential proxy ile cekiyoruz.
REDDIT_SUBS = ["LocalLLaMA", "MachineLearning"]
REDDIT_PER_SUB = 4
# Residential proxy (sadece Reddit icin - residential trafik metered). secrets.env'den:
RESIDENTIAL_PROXY = os.environ.get("RESIDENTIAL_PROXY", "")

# ============ LIMITLER ============
HN_MIN_POINTS = 30
HN_PER_KEYWORD = 12
HN_CAP = 8
LOBSTERS_CAP = 5
ARXIV_CAP = 6
HF_CAP = 6
RSS_DAYS = 3
RSS_PER_FEED = 2

ARXIV_CATS = ["cs.AI", "cs.CL", "cs.LG"]

RSS_FEEDS = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss/",
    "DeepMind": "https://deepmind.google/blog/rss.xml",
    "HuggingFace": "https://huggingface.co/blog/feed.xml",
    "BAIR": "https://bair.berkeley.edu/blog/feed.xml",
    "Together": "https://www.together.ai/blog/rss.xml",
    "Stability": "https://stability.ai/news?format=rss",
}

# ============ CEVIRI ============
# gemini (onerilen) | google (bedava NMT) | none
TRANSLATE_BACKEND = os.environ.get("TRANSLATE_BACKEND", "gemini")
TRANSLATE_TARGET = "tr"
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GEMINI_MODEL = "gemini-3.5-flash"

# ============ TELEGRAM (secrets.env'den) ============
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_THREAD_ID = os.environ.get("TELEGRAM_THREAD_ID", "")  # forum konu (topic) id

USER_AGENT = "Mozilla/5.0 (compatible; ai-morning-digest/1.0; personal)"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "state.json")
OUT_DIR = os.path.join(BASE_DIR, "out")
INDEX_FILE = os.path.join(BASE_DIR, "index.json")  # numara -> {url,title} (bot ozet icin)
