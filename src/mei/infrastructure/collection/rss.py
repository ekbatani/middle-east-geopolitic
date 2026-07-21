from dataclasses import dataclass
from datetime import datetime

import dateparser
import feedparser


@dataclass(frozen=True)
class FeedItem:
    link: str
    title: str | None
    external_id: str | None
    published_at: datetime | None


def parse_feed(body: bytes) -> list[FeedItem]:
    """Parse RSS/Atom bytes into feed items, per design doc section 4.5/10.1.

    `feedparser` never raises on malformed feeds (it sets `bozo` and does its
    best); a feed with no usable items just yields an empty list rather than
    failing the collection run.
    """
    parsed = feedparser.parse(body)
    items: list[FeedItem] = []

    for entry in parsed.entries:
        link = entry.get("link")
        if not link:
            continue

        published_raw = entry.get("published") or entry.get("updated")
        published_at = dateparser.parse(published_raw) if published_raw else None

        items.append(
            FeedItem(
                link=link,
                title=entry.get("title"),
                external_id=entry.get("id") or entry.get("guid") or None,
                published_at=published_at,
            )
        )

    return items


__all__ = ["FeedItem", "parse_feed"]
