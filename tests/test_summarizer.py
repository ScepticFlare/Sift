"""
tests/test_summarizer.py — Unit tests for the AI summarizer module.
"""

import json
from unittest.mock import patch, MagicMock

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


SAMPLE_ARTICLES = [
    {
        "title": "Global Climate Summit Agreement",
        "source": "BBC World",
        "link": "https://example.com/climate",
        "published": "2026-03-20T10:00:00+00:00",
        "snippet": "World leaders commit to historic climate deal...",
    },
    {
        "title": "Celebrity Outfit at Award Show",
        "source": "Entertainment Weekly",
        "link": "https://example.com/celeb",
        "published": "2026-03-20T11:00:00+00:00",
        "snippet": "A famous celebrity turned heads at the red carpet...",
    },
]

AI_RESPONSE = json.dumps([
    {
        "title": "Global Climate Summit Reaches Historic Agreement",
        "sources": ["BBC World"],
        "link": "https://example.com/climate",
        "summary": (
            "World leaders reached a landmark climate agreement. "
            "The deal commits nations to cut emissions by 50%. "
            "Developing nations will receive substantial funding. "
            "Environmental groups praised the outcome."
        ),
    }
])


class TestSummarizer:

    @patch("summarizer.config")
    @patch("summarizer.anthropic.Anthropic")
    def test_filters_and_summarizes(self, MockAnthropic, mock_config):
        """Should keep real news and filter out celebrity fluff."""
        mock_config.ANTHROPIC_API_KEY = "test-key"
        mock_config.KEEP_CATEGORIES = ["world news"]
        mock_config.REJECT_CATEGORIES = ["celebrity gossip"]

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=AI_RESPONSE)]
        mock_client = MockAnthropic.return_value
        mock_client.messages.create.return_value = mock_response

        from summarizer import summarize_articles
        results = summarize_articles(SAMPLE_ARTICLES)

        assert len(results) == 1
        assert "Climate" in results[0]["title"]
        assert len(results[0]["summary"]) > 0

    @patch("summarizer.config")
    def test_empty_input_returns_empty(self, mock_config):
        """No articles in → no summaries out."""
        from summarizer import summarize_articles
        results = summarize_articles([])
        assert results == []

    @patch("summarizer.config")
    def test_missing_api_key_returns_empty(self, mock_config):
        """Without an API key, should return empty gracefully."""
        mock_config.ANTHROPIC_API_KEY = ""

        from summarizer import summarize_articles
        results = summarize_articles(SAMPLE_ARTICLES)
        assert results == []

    @patch("summarizer.config")
    @patch("summarizer.anthropic.Anthropic")
    def test_retries_on_json_error(self, MockAnthropic, mock_config):
        """Should retry when Claude returns invalid JSON."""
        mock_config.ANTHROPIC_API_KEY = "test-key"
        mock_config.KEEP_CATEGORIES = ["world news"]
        mock_config.REJECT_CATEGORIES = ["celebrity gossip"]

        bad_response = MagicMock()
        bad_response.content = [MagicMock(text="not valid json")]

        good_response = MagicMock()
        good_response.content = [MagicMock(text=AI_RESPONSE)]

        mock_client = MockAnthropic.return_value
        mock_client.messages.create.side_effect = [bad_response, good_response]

        from summarizer import summarize_articles
        results = summarize_articles(SAMPLE_ARTICLES)

        assert len(results) == 1
        assert mock_client.messages.create.call_count == 2
