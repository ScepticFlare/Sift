"""
tests/test_fetcher.py — Unit tests for the RSS fetcher module.
"""

import time
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

# We need to mock config before importing fetcher
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class FakeEntry:
    """Mimics a feedparser entry."""
    def __init__(self, title, link, summary="", published_parsed=None):
        self.title = title
        self.link = link
        self.summary = summary
        self.published_parsed = published_parsed
        self.updated_parsed = None
        self.content = None
        self.description = summary


def _now_struct():
    """Return time.struct_time for 'now' in UTC."""
    now = datetime.now(timezone.utc)
    return now.timetuple()


def _old_struct():
    """Return time.struct_time for 48 hours ago."""
    from datetime import timedelta
    old = datetime.now(timezone.utc) - timedelta(hours=48)
    return old.timetuple()


class TestFetcher:

    @patch("fetcher.feedparser.parse")
    def test_fetches_and_deduplicates(self, mock_parse):
        """Articles with the same URL should be deduplicated."""
        mock_parse.return_value = MagicMock(
            bozo=False,
            entries=[
                FakeEntry("Article A", "https://example.com/a", "Snippet A", _now_struct()),
                FakeEntry("Article A Dup", "https://example.com/a", "Snippet A2", _now_struct()),
                FakeEntry("Article B", "https://example.com/b", "Snippet B", _now_struct()),
            ],
        )

        from fetcher import fetch_articles
        articles = fetch_articles(hours_back=24)

        # Should have 2, not 3
        urls = [a["link"] for a in articles]
        assert len(set(urls)) == len(urls), "Duplicates were not removed"

    @patch("fetcher.feedparser.parse")
    def test_filters_old_articles(self, mock_parse):
        """Articles older than hours_back should be excluded."""
        mock_parse.return_value = MagicMock(
            bozo=False,
            entries=[
                FakeEntry("Fresh", "https://example.com/fresh", "new", _now_struct()),
                FakeEntry("Old", "https://example.com/old", "old", _old_struct()),
            ],
        )

        from fetcher import fetch_articles
        articles = fetch_articles(hours_back=24)

        titles = [a["title"] for a in articles]
        assert "Fresh" in titles
        assert "Old" not in titles

    @patch("fetcher.feedparser.parse")
    def test_extracts_required_fields(self, mock_parse):
        """Each article dict should have the required keys."""
        mock_parse.return_value = MagicMock(
            bozo=False,
            entries=[
                FakeEntry("Test Article", "https://example.com/test", "A snippet", _now_struct()),
            ],
        )

        from fetcher import fetch_articles
        articles = fetch_articles(hours_back=24)

        assert len(articles) >= 1
        art = articles[0]
        for key in ("title", "link", "source", "published", "snippet"):
            assert key in art, f"Missing key: {key}"

    @patch("fetcher.feedparser.parse")
    def test_handles_feed_errors_gracefully(self, mock_parse):
        """If a feed fails to parse, it should be skipped without crashing."""
        mock_parse.side_effect = Exception("Network error")

        from fetcher import fetch_articles
        articles = fetch_articles(hours_back=24)

        assert articles == []
