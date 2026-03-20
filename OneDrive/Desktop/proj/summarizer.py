import json
import logging
import re
import time

import config

logger = logging.getLogger(__name__)

# keywords for offline filtering
KEEP_WORDS = {
    "war", "conflict", "military", "troops", "missile", "attack", "strike",
    "election", "vote", "president", "minister", "government", "parliament",
    "economy", "gdp", "inflation", "interest rate", "federal reserve", "trade",
    "climate", "earthquake", "hurricane", "flood", "wildfire", "disaster",
    "court", "supreme court", "verdict", "arrested", "charged", "sentenced",
    "summit", "treaty", "nato", "united nations", "sanctions", "diplomat",
    "health", "vaccine", "pandemic", "outbreak", "who",
    "sport", "football", "cricket", "tennis", "championship", "world cup",
    "olympics", "medal", "league", "match", "scored", "final",
    "killed", "dead", "shooting", "bomb", "hostage", "crisis",
    "space", "nasa", "rocket", "satellite", "discovery",
    "market", "stock", "billion", "trillion", "recession",
    "police", "protest", "rally", "riot",
    "tech", "ai", "breakthrough", "cybersecurity", "hack",
}

REJECT_WORDS = {
    "celebrity", "kardashian", "red carpet", "award show", "gossip",
    "recipe", "cooking", "restaurant review", "food hack",
    "fashion", "beauty", "skincare", "makeup",
    "horoscope", "zodiac", "astrology",
    "clickbait", "you won't believe", "top 10", "listicle",
    "tiktok", "viral video", "influencer", "instagram",
    "reality tv", "bachelor", "love island",
}

# prompt for AI-based filtering (gemini/claude)
SYSTEM_PROMPT = """You are a senior news editor for a daily briefing aimed at busy people 
who want REAL, substantive news — not fluff.

YOUR JOB:
1. Read the list of articles provided. Each has a numeric ID.
2. REJECT anything that is NOT substantive news. Reject:
   {reject_list}
3. KEEP only articles that fall into these categories:
   {keep_list}
4. For each article you KEEP, write a 4-sentence summary that tells the 
   reader exactly what happened, why it matters, and what might happen next.
   Write in a clear, neutral, professional tone.
5. If two or more articles cover the same event, merge them into ONE entry.
   List ALL their IDs in the "article_ids" field.
6. Pick the TOP 5-8 most important stories from this batch.

Respond ONLY with a JSON array, no other text:
[
  {{
    "article_ids": [1, 5],
    "title": "Clear headline",
    "summary": "Your 4-sentence summary."
  }}
]

Rules:
- "article_ids" must contain the numeric IDs of the original articles used.
- Do NOT invent URLs or links. Only return article_ids, title, and summary.
- If NONE of the articles are worth keeping, return: []
- Always respond with valid JSON.
"""


def _build_system_prompt():
    keep = ", ".join(config.KEEP_CATEGORIES)
    reject = ", ".join(config.REJECT_CATEGORIES)
    return SYSTEM_PROMPT.format(keep_list=keep, reject_list=reject)


def _chunk_list(lst, size=10):
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def _extract_json(text):
    text = text.strip()
    if "```" in text:
        match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def _resolve_links(summaries, id_map):
    resolved = []
    for s in summaries:
        ids = s.get("article_ids", [])
        if not ids:
            continue
        sources, link = [], ""
        for aid in ids:
            art = id_map.get(aid)
            if art:
                if art["source"] not in sources:
                    sources.append(art["source"])
                if not link:
                    link = art["link"]
        if not link:
            continue
        resolved.append({
            "title": s.get("title", "Untitled"),
            "sources": sources,
            "link": link,
            "summary": s.get("summary", ""),
        })
    return resolved


# offline filtering (no api calls)

def _score_article(article):
    text = (article.get("title", "") + " " + article.get("snippet", "")).lower()
    for kw in REJECT_WORDS:
        if kw in text:
            return -1
    score = 0
    for kw in KEEP_WORDS:
        if kw in text:
            score += 1
    return score


def _clean_snippet(snippet, max_sentences=4):
    snippet = re.sub(r"<[^>]+>", " ", snippet)
    snippet = re.sub(r"\s+", " ", snippet).strip()
    sentences = re.split(r"(?<=[.!?])\s+", snippet)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    return " ".join(sentences[:max_sentences])


def _summarize_offline(articles):
    logger.info("Using offline mode (keyword filtering)")
    scored = []
    for art in articles:
        score = _score_article(art)
        if score > 0:
            scored.append((score, art))

    scored.sort(key=lambda x: x[0], reverse=True)

    seen_titles = set()
    results = []
    for score, art in scored[:15]:
        title_key = re.sub(r"[^a-z0-9]", "", art["title"].lower())[:40]
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)

        summary = _clean_snippet(art.get("snippet", ""))
        if not summary:
            summary = art["title"]

        results.append({
            "title": art["title"],
            "sources": [art["source"]],
            "link": art["link"],
            "summary": summary,
        })
        if len(results) >= 10:
            break

    logger.info(f"Offline filter: {len(results)} kept from {len(articles)} total")
    return results


# ai backends

def _call_gemini(system_prompt, user_msg):
    from google import genai
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    model_name = getattr(config, "GEMINI_MODEL", "gemini-2.0-flash")
    response = client.models.generate_content(
        model=model_name,
        contents=f"{system_prompt}\n\n{user_msg}",
    )
    return response.text


def _call_claude(system_prompt, user_msg):
    import anthropic
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    model = getattr(config, "CLAUDE_MODEL", "claude-sonnet-4-20250514")
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
    )
    return response.content[0].text


def _get_backend():
    backend = getattr(config, "AI_BACKEND", "offline").lower()
    if backend == "offline":
        return "offline", None
    if backend == "gemini":
        if not getattr(config, "GEMINI_API_KEY", ""):
            logger.warning("GEMINI_API_KEY not set, falling back to offline")
            return "offline", None
        return "gemini", _call_gemini
    if backend == "claude":
        if not getattr(config, "ANTHROPIC_API_KEY", ""):
            logger.warning("ANTHROPIC_API_KEY not set, falling back to offline")
            return "offline", None
        return "claude", _call_claude
    logger.warning(f"Unknown AI_BACKEND '{backend}', using offline")
    return "offline", None


def summarize_articles(articles, max_retries=3):
    if not articles:
        logger.info("No articles to summarize.")
        return []

    backend_name, call_ai = _get_backend()

    if backend_name == "offline" or call_ai is None:
        return _summarize_offline(articles)

    # ai mode
    system_prompt = _build_system_prompt()
    all_summaries = []
    global_id = 1
    id_map = {}

    chunks = list(_chunk_list(articles, size=10))
    logger.info(f"Processing {len(articles)} articles in {len(chunks)} chunks via {backend_name}")

    for chunk_idx, chunk in enumerate(chunks):
        articles_text = ""
        for art in chunk:
            id_map[global_id] = art
            articles_text += (
                f"---\nID: {global_id}\n"
                f"Title: {art['title']}\n"
                f"Source: {art['source']}\n"
                f"Published: {art['published']}\n"
                f"Snippet: {art['snippet'][:300]}\n"
            )
            global_id += 1

        user_msg = f"Here are {len(chunk)} articles. Filter and summarize the important ones.\n\n{articles_text}"

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Chunk {chunk_idx + 1}/{len(chunks)} (attempt {attempt})")
                raw = call_ai(system_prompt, user_msg)
                summaries = _extract_json(raw)
                if summaries is None:
                    raise json.JSONDecodeError("Could not extract JSON", raw[:200], 0)
                if not isinstance(summaries, list):
                    raise json.JSONDecodeError("Not a list", str(summaries)[:100], 0)
                resolved = _resolve_links(summaries, id_map)
                all_summaries.extend(resolved)
                logger.info(f"Chunk {chunk_idx + 1}: {len(resolved)} articles kept")
                break
            except json.JSONDecodeError as exc:
                logger.warning(f"JSON error attempt {attempt}: {exc}")
                if attempt == max_retries:
                    logger.error("Skipping chunk.")
            except Exception as exc:
                err = str(exc).lower()
                if any(w in err for w in ("credit", "purchase", "quota", "429")):
                    logger.warning("API limit hit, falling back to offline")
                    return _summarize_offline(articles)
                logger.error(f"AI error: {exc}")
                if attempt == max_retries:
                    logger.error("Skipping chunk.")
                time.sleep(1)

        if chunk_idx < len(chunks) - 1:
            time.sleep(0.5)

    if not all_summaries:
        logger.warning("AI returned nothing, falling back to offline")
        return _summarize_offline(articles)

    logger.info(f"Total summaries: {len(all_summaries)}")
    return all_summaries
