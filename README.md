# 🤖 AI Morning Digest

A self-hosted, ~zero-cost alternative to paid AI newsletters. It pulls the day's
most important AI news from several sources, translates the headlines with an LLM
(keeping technical jargon intact), and pushes a clean **morning digest to Telegram** —
automatically, every day.

Then it gets interactive: every headline is numbered, and **you reply with a number to
get an on-demand summary** of that article, fetched and summarized by the bot.

> Built because a popular AI newsletter wanted ~$350/year for what is, underneath,
> a handful of free public feeds + an LLM. This is that, but yours.

---

## ✨ Features

- **6 sources, deduplicated** — Hacker News (front page, AI-filtered), Reddit
  (r/LocalLLaMA, r/MachineLearning), Lobsters, arXiv (cs.AI / cs.CL / cs.LG),
  Hugging Face daily papers, and official lab blogs (OpenAI, Google AI, DeepMind,
  Hugging Face, BAIR, Together, Stability).
- **LLM translation** to Turkish via **Gemini** by default, with technical terms left
  in English (LLM, GPU, vLLM, RAG, inference… stay untranslated). Free Google-Translate
  fallback included — no API key required to get started.
- **No repeats** — a seen-state file means each morning only shows what's actually new.
- **Telegram delivery** to a group topic or DM, plus a dated Markdown archive in `out/`.
- **On-demand summaries** — send a headline's number to the bot; it fetches the article
  (via Gemini's URL-context, with a residential-proxy fallback for blocked sites) and
  replies with a punchy summary that highlights what's interesting and skips the filler.
- **Runs anywhere** — small Python + cron + an optional long-polling bot service.
  No GPU. Pennies per month at most.

## 📰 Sources

| Source | What it provides | How |
|--------|------------------|-----|
| Hacker News | Current front-page AI stories | Algolia API |
| Reddit | r/LocalLLaMA + r/MachineLearning top/day | RSS via residential proxy* |
| Lobsters | AI-tagged community posts | JSON API |
| arXiv | New cs.AI / cs.CL / cs.LG papers | Atom API |
| Hugging Face | Daily papers (by upvotes) | API |
| Lab blogs | OpenAI / Google AI / DeepMind / HF / BAIR / Together / Stability | RSS |

\* Reddit blocks datacenter IPs even for RSS, so Reddit is the only source that needs a
proxy. Leave `RESIDENTIAL_PROXY` empty to simply skip Reddit.

## 🔧 How it works

```
cron (daily)                                  systemd (always-on)
   │                                                │
   ▼                                                ▼
 digest.py                                        bot.py
   │  fetch 6 sources → dedupe (state.json)          │  long-poll Telegram
   │  translate titles (Gemini, jargon-safe)         │  user sends a number
   │  number items → write index.json                │  look up index.json
   │  render → out/YYYY-MM-DD.md                      │  summarize URL (Gemini)
   ▼  push to Telegram                                ▼  reply with summary
```

## 🚀 Setup

```bash
git clone https://github.com/hukunokina/ai-morning-digest.git
cd ai-morning-digest
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

cp secrets.env.example secrets.env   # then edit it (see below)
```

**Minimum to run** (writes a Markdown digest to `out/`, no keys needed):
set `TRANSLATE_BACKEND=google` in `secrets.env` and run `./run.sh`.

**Recommended** (better Turkish + Telegram + summaries):

1. **Gemini key** — get one free at <https://aistudio.google.com/apikey>, set
   `GOOGLE_API_KEY` and `TRANSLATE_BACKEND=gemini`.
2. **Telegram** — message [@BotFather](https://t.me/BotFather) → `/newbot` → copy the
   token into `TELEGRAM_TOKEN`. Send your bot a message, then run
   `python get_chat_id.py` to get `TELEGRAM_CHAT_ID`. (For a forum topic, also set
   `TELEGRAM_THREAD_ID`.)
3. **Reddit** (optional) — set `RESIDENTIAL_PROXY=http://user:pass@host:port`. Skip to
   drop Reddit.

### Schedule the daily digest (cron)

```cron
# 07:30 in your timezone — adjust the hour to your UTC offset
30 4 * * * /path/to/ai-morning-digest/run.sh
```

### Run the on-demand summarize bot

Copy `deploy/ai-digest-bot.service.example` to
`/etc/systemd/system/ai-digest-bot.service`, fix the paths, then:

```bash
systemctl daemon-reload && systemctl enable --now ai-digest-bot
```

> The bot reads plain numbers in the chat. Telegram bots can't see plain group messages
> unless you disable **Group Privacy** in BotFather (`/setprivacy` → Disable) and re-add
> the bot. Otherwise use the command form: `/o 12`.

## ⚙️ Configuration

Everything lives in [`config.py`](config.py):

- `KEYWORDS` — topics used to filter HN / arXiv.
- `SOURCES` — toggle each source on/off.
- `GEMINI_MODEL` — translation/summarization model.
- limits (`HN_CAP`, `ARXIV_CAP`, `RSS_FEEDS`, …).

Output language defaults to Turkish (`TRANSLATE_TARGET` + the Gemini prompts in
[`translate.py`](translate.py) / [`summarizer.py`](summarizer.py)); adapt those prompts
for another language.

## 📄 License

MIT — see [LICENSE](LICENSE).
