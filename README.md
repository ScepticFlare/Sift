# SIFT — Signal from the Noise

An automated Python bot that pulls articles from trusted news sources, filters out fluff using AI (or keyword scoring), writes concise summaries, and emails a clean daily digest to subscribers. No human curation needed.

![SIFT Preview](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square) ![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

## What It Does

1. **Fetches** articles from 11 RSS feeds (BBC, Reuters, Al Jazeera, AP, ESPN, CNBC, Politico)
2. **Filters** out celebrity gossip, clickbait, food/lifestyle fluff using AI or keyword scoring
3. **Summarizes** each worthy article in 4 sentences — built for people in a hurry
4. **Emails** a polished dark-themed HTML digest to subscribers on a daily schedule

## Quick Start

```bash
# Clone and install
git clone https://github.com/ScepticFlare/sift.git
cd sift
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your email credentials (see below)

# Run once
python main.py --now

# Run daily at scheduled time
python main.py --schedule
```

## Configuration

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Description |
|---|---|---|
| `AI_BACKEND` | ✅ | `offline` (no API), `gemini` (free), or `claude` (paid) |
| `GEMINI_API_KEY` | Only if gemini | Free at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `ANTHROPIC_API_KEY` | Only if claude | From [console.anthropic.com](https://console.anthropic.com) |
| `SMTP_USER` | ✅ | Your Gmail address |
| `SMTP_PASSWORD` | ✅ | Gmail [App Password](https://myaccount.google.com/apppasswords) (enable 2FA first) |
| `SENDER_EMAIL` | ✅ | Same as SMTP_USER |
| `SUBSCRIBERS` | ✅ | Comma-separated recipient emails |
| `DIGEST_HOUR` | ✅ | Time to send (24h format, default: `07:00`) |

## AI Backends

| Backend | Cost | Quality | Setup |
|---|---|---|---|
| `offline` | Free | Good — keyword filtering | No API key needed |
| `gemini` | Free | Great — AI summaries | Get key from Google AI Studio |
| `claude` | ~$0.02/day | Best — Claude AI summaries | Requires Anthropic billing |

## Managing Subscribers

```bash
python subscribers.py add friend@gmail.com
python subscribers.py remove friend@gmail.com
python subscribers.py list
python subscribers.py count
```

## Project Structure

```
├── main.py              # Orchestrator + scheduler (CLI)
├── fetcher.py           # RSS feed puller (11 sources)
├── summarizer.py        # AI/offline filter + summaries
├── emailer.py           # SMTP email sender
├── subscribers.py       # Subscriber manager (CLI)
├── config.py            # Settings loader
├── templates/
│   └── digest.html      # Dark-themed HTML email (Jinja2)
├── tests/
│   ├── test_fetcher.py
│   └── test_summarizer.py
├── .env.example         # Config template
├── requirements.txt
└── .gitignore
```

## News Sources

| Category | Feeds |
|---|---|
| World | BBC World, Reuters, Al Jazeera, AP News |
| Politics | BBC Politics, Politico |
| Business | BBC Business, CNBC |
| Science | BBC Science & Environment |
| Sports | BBC Sport, ESPN |

## Tech Stack

- **Python 3.8+**
- **Feedparser** — RSS parsing
- **Google Gemini / Anthropic Claude** — AI summarization
- **Jinja2** — HTML email templating
- **smtplib** — Email delivery
- **schedule** — Daily scheduling

## License

MIT
