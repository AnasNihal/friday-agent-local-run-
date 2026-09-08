import unittest
from unittest.mock import Mock, patch

from friday.tools.browser import open_world_monitor, search_browser
from friday.tools.news import get_world_news, parse_feed


class NewsTests(unittest.TestCase):
    def test_parse_feed_returns_structured_headline(self):
        content = b"""<rss><channel><item><title>World update</title><link>https://example.com/world</link><pubDate>Tue, 08 Sep 2026 10:00:00 GMT</pubDate></item></channel></rss>"""
        result = parse_feed(content, "Example")
        self.assertEqual(result[0]["headline"], "World update")
        self.assertEqual(result[0]["source"], "Example")
        self.assertTrue(result[0]["url"].startswith("https://"))

    @patch("friday.tools.browser.webbrowser.open", return_value=True)
    def test_world_monitor_validates_and_opens_configured_url(self, open_browser):
        result = open_world_monitor()
        self.assertTrue(result["success"])
        open_browser.assert_called_once()

    @patch("friday.tools.browser.webbrowser.open", return_value=True)
    def test_search_browser_encodes_query(self, open_browser):
        result = search_browser("world map & news")
        self.assertTrue(result["success"])
        self.assertIn("world+map+%26+news", result["url"])

    @patch("friday.tools.news._fetch_feed")
    def test_news_aggregates_sources_without_network(self, fetch):
        fetch.side_effect = lambda source, url: (source, [{"headline": source, "source": source, "published": "", "url": "https://example.com"}], None)
        result = get_world_news()
        self.assertTrue(result["success"])
        self.assertEqual(len(result["headlines"]), 4)
        self.assertTrue(all(item["headline"] for item in result["headlines"]))


if __name__ == "__main__":
    unittest.main()
