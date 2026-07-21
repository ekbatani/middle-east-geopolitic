from mei.infrastructure.collection.rss import parse_feed

_SAMPLE_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Sample Wire</title>
    <item>
      <title>First headline</title>
      <link>https://example.com/articles/first</link>
      <guid>urn:uuid:11111111-1111-1111-1111-111111111111</guid>
      <pubDate>Mon, 20 Jul 2026 08:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Second headline</title>
      <link>https://example.com/articles/second</link>
      <guid>urn:uuid:22222222-2222-2222-2222-222222222222</guid>
      <pubDate>Mon, 20 Jul 2026 09:30:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


def test_parse_feed_extracts_items() -> None:
    items = parse_feed(_SAMPLE_FEED)

    assert len(items) == 2
    assert items[0].link == "https://example.com/articles/first"
    assert items[0].title == "First headline"
    assert items[0].external_id == "urn:uuid:11111111-1111-1111-1111-111111111111"
    assert items[0].published_at is not None
    assert items[0].published_at.year == 2026


def test_parse_feed_skips_entries_without_link() -> None:
    body = b"""<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <item><title>No link here</title></item>
    </channel></rss>
    """

    assert parse_feed(body) == []


def test_parse_feed_returns_empty_list_for_garbage_input() -> None:
    assert parse_feed(b"not a feed at all") == []
