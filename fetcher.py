import re
import time
import logging
from datetime import datetime, timedelta, timezone

import feedparser
import config

logger = logging.getLogger(__name__)


def _parse_published(entry):
    for attr in ("published_parsed", "updated_parsed"):
        tp = getattr(entry, attr, None)
        if tp:
            try:
                return datetime(*tp[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return None


def _snippet(entry, max_len=500):
    for field in ("summary", "description", "content"):
        val = getattr(entry, field, None)
        if not val:
            continue
        text = val[0].get("value", "") if isinstance(val, list) else str(val)
        text = re.sub(r"<[^>]+>", " ", text).strip()
        if text:
            return text[:max_len]
    return ""


def fetch_articles(hours_back=24):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    seen_urls = set()
    articles = []

    for feed_cfg in config.RSS_FEEDS:
        name = feed_cfg["name"]
        url = feed_cfg["url"]
        logger.info(f"Fetching feed: {name}")

        try:
            parsed = feedparser.parse(url)
        except Exception as exc:
            logger.warning(f"Failed to fetch {name}: {exc}")
            continue

        if parsed.bozo and not parsed.entries:
            logger.warning(f"Feed {name} returned no entries (bozo={parsed.bozo})")
            continue

        for entry in parsed.entries:
            link = getattr(entry, "link", "")
            if not link or link in seen_urls:
                continue

            pub_date = _parse_published(entry)
            if pub_date and pub_date < cutoff:
                continue

            title = getattr(entry, "title", "").strip()
            if not title:
                continue

            seen_urls.add(link)
            articles.append({
                "title": title,
                "link": link,
                "source": name,
                "published": pub_date.isoformat() if pub_date else "unknown",
                "snippet": _snippet(entry),
            })

    logger.info(f"Fetched {len(articles)} articles from {len(config.RSS_FEEDS)} feeds")
    return articles


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    arts = fetch_articles()
    for a in arts[:5]:
        print(f"[{a['source']}] {a['title']}")
        print(f"  {a['link']}")
        print()
