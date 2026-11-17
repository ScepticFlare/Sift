import argparse
import logging
import sys
import time
from datetime import datetime

import schedule
import config
from fetcher import fetch_articles
from summarizer import summarize_articles
from emailer import send_digest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sift")


def run_digest():
    logger.info("=" * 50)
    logger.info("Starting SIFT digest run")
    logger.info("=" * 50)

    # fetch
    logger.info("Fetching articles from RSS feeds...")
    articles = fetch_articles(hours_back=24)
    if not articles:
        logger.warning("No articles fetched, aborting.")
        return

    logger.info(f"Got {len(articles)} raw articles")

    # filter + summarize
    logger.info("Filtering and summarizing...")
    summaries = summarize_articles(articles)
    if not summaries:
        logger.warning("No worthy articles after filtering.")
        return

    logger.info(f"Kept {len(summaries)} articles out of {len(articles)}")

    # send email
    logger.info("Sending digest email...")
    success = send_digest(summaries)

    if success:
        logger.info("Digest delivered!")
    else:
        logger.error("Digest delivery failed.")

    logger.info("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="SIFT — Signal from the noise")
    parser.add_argument("--now", action="store_true", help="Run once immediately")
    parser.add_argument("--schedule", action="store_true", help="Run on a daily schedule")

    args = parser.parse_args()

    if not args.now and not args.schedule:
        args.schedule = True

    # quick config check
    warnings = []
    if config.AI_BACKEND != "offline" and not config.GEMINI_API_KEY and not config.ANTHROPIC_API_KEY:
        warnings.append("No AI API key set (will use offline mode)")
    if not config.SMTP_USER or not config.SMTP_PASSWORD:
        warnings.append("SMTP credentials not set")
    if not config.SUBSCRIBERS:
        warnings.append("No subscribers configured")

    for w in warnings:
        logger.warning(f"  {w}")

    if args.now:
        logger.info("Mode: one-shot (--now)")
        run_digest()
        return

    logger.info(f"Mode: scheduled — digest at {config.DIGEST_HOUR} daily")
    logger.info("Press Ctrl+C to stop.\n")

    schedule.every().day.at(config.DIGEST_HOUR).do(run_digest)

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        logger.info("\nStopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
