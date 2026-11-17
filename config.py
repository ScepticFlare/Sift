import os
from dotenv import load_dotenv

load_dotenv()

# ai backend: "offline", "gemini", or "claude"
AI_BACKEND = os.getenv("AI_BACKEND", "offline")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# smtp
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")

def _load_subscribers():
    try:
        from subscribers import get_subscribers
        subs = get_subscribers()
        if subs:
            return subs
    except Exception:
        pass
    return [s.strip() for s in os.getenv("SUBSCRIBERS", "").split(",") if s.strip()]

SUBSCRIBERS = _load_subscribers()

DIGEST_HOUR = os.getenv("DIGEST_HOUR", "07:00")

# rss feeds
RSS_FEEDS = [
    {"name": "BBC World",       "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"name": "Reuters World",   "url": "https://www.reutersagency.com/feed/?taxonomy=best-sectors&post_type=best"},
    {"name": "Al Jazeera",      "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"name": "AP News",         "url": "https://rsshub.app/apnews/topics/apf-topnews"},

    {"name": "BBC Politics",    "url": "https://feeds.bbci.co.uk/news/politics/rss.xml"},
    {"name": "Politico",        "url": "https://rss.politico.com/politics-news.xml"},

    {"name": "BBC Business",    "url": "https://feeds.bbci.co.uk/news/business/rss.xml"},
    {"name": "CNBC Top News",   "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"},

    {"name": "BBC Science",     "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"},

    {"name": "BBC Sport",       "url": "https://feeds.bbci.co.uk/sport/rss.xml"},
    {"name": "ESPN Headlines",  "url": "https://www.espn.com/espn/rss/news"},
]

KEEP_CATEGORIES = [
    "world news", "international affairs", "politics", "elections",
    "government", "diplomacy", "military / defense", "conflicts / war",
    "economy", "business", "markets", "finance",
    "science breakthroughs", "climate / environment",
    "sports", "health / public health", "disasters / emergencies",
    "law / justice", "infrastructure",
]

REJECT_CATEGORIES = [
    "celebrity gossip", "entertainment", "reality TV",
    "food / recipes", "lifestyle", "fashion", "beauty",
    "clickbait", "listicles", "opinion pieces without news value",
    "product reviews", "sponsored content", "horoscopes",
    "social media drama", "viral videos",
]
