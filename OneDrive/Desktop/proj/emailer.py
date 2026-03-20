import logging
import smtplib
import os
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader
import config

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def _render_digest(articles):
    env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR))
    template = env.get_template("digest.html")
    today = datetime.now().strftime("%A, %B %d, %Y")
    return template.render(date=today, articles=articles)


def send_digest(articles):
    if not articles:
        logger.warning("No articles to send.")
        return False

    if not config.SUBSCRIBERS:
        logger.error("No subscribers configured.")
        return False

    if not config.SMTP_USER or not config.SMTP_PASSWORD:
        logger.error("SMTP credentials not set.")
        return False

    html_body = _render_digest(articles)
    today = datetime.now().strftime("%B %d, %Y")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"SIFT — {today}"
    msg["From"] = config.SENDER_EMAIL
    msg["To"] = ", ".join(config.SUBSCRIBERS)

    # plain text fallback
    plain = "SIFT — Signal from the noise\n" + "=" * 40 + "\n\n"
    for i, art in enumerate(articles, 1):
        sources = ", ".join(art.get("sources", []))
        plain += f"{i}. {art['title']} [{sources}]\n"
        plain += f"   {art['summary']}\n"
        plain += f"   Read more: {art['link']}\n\n"

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        logger.info(f"Connecting to {config.SMTP_HOST}:{config.SMTP_PORT}")
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(config.SENDER_EMAIL, config.SUBSCRIBERS, msg.as_string())
        logger.info(f"Digest sent to {len(config.SUBSCRIBERS)} subscriber(s)")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP auth failed — check credentials. For Gmail use an App Password.")
        return False
    except Exception as exc:
        logger.error(f"Failed to send email: {exc}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample = [
        {
            "title": "Global Climate Summit Reaches Historic Agreement",
            "sources": ["BBC World", "Reuters"],
            "link": "https://example.com/climate",
            "summary": (
                "World leaders reached a landmark climate agreement today. "
                "The deal commits nations to cut emissions by 50% by 2035. "
                "Developing nations will receive $100B in annual funding. "
                "Environmental groups called it a significant step forward."
            ),
        },
        {
            "title": "Champions League Quarter-Finals Draw Revealed",
            "sources": ["BBC Sport", "ESPN"],
            "link": "https://example.com/ucl",
            "summary": (
                "The UEFA Champions League quarter-final draw produced exciting matchups. "
                "Real Madrid will face Manchester City in a repeat of last year's semifinal. "
                "Barcelona drew Bayern Munich in what promises to be a classic tie. "
                "Matches are scheduled for April 8-9 and April 15-16."
            ),
        },
    ]
    html = _render_digest(sample)
    preview_path = os.path.join(_TEMPLATE_DIR, "preview.html")
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Preview saved to {preview_path}")
