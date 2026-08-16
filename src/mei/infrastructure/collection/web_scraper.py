from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from mei.infrastructure.collection.http_fetcher import fetch_url, validate_url_security
from mei.infrastructure.collection.parser import chunk_text, extract_text
from mei.shared.errors import FetchError, UnsupportedURLError
from mei.shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ScrapedArticle:
    url: str
    title: str | None
    extracted_text: str | None
    chunks: list[str]
    detected_language: str | None
    status_code: int


@dataclass
class ScrapeHubResult:
    hub_url: str
    discovered_urls: list[str]
    articles: list[ScrapedArticle]


class WebScraper:
    """Intelligent web crawler and article extractor."""

    def __init__(self, *, max_crawl_links: int = 15) -> None:
        self.max_crawl_links = max_crawl_links

    async def scrape_single_url(self, url: str) -> ScrapedArticle:
        """Fetch, sanitize, and extract text from a single webpage."""
        validate_url_security(url)
        fetch_res = await fetch_url(url)

        # Extract main text
        text = extract_text(fetch_res.body, url=url)

        # Extract title from HTML
        title: str | None = None
        try:
            soup = BeautifulSoup(fetch_res.body, "html.parser")
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            elif soup.find("h1"):
                h1 = soup.find("h1")
                if h1:
                    title = h1.get_text().strip()
        except Exception:
            title = None

        chunks = chunk_text(text or "") if text else []

        # Detect language
        detected_lang: str | None = None
        if text:
            try:
                from langdetect import detect

                detected_lang = detect(text[:1000])
            except Exception:
                detected_lang = "en"

        return ScrapedArticle(
            url=url,
            title=title,
            extracted_text=text,
            chunks=chunks,
            detected_language=detected_lang,
            status_code=fetch_res.status_code,
        )

    async def crawl_hub(self, hub_url: str, *, link_patterns: list[str] | None = None) -> ScrapeHubResult:
        """Crawl an intelligence hub or news index page to discover and scrape recent articles."""
        validate_url_security(hub_url)
        fetch_res = await fetch_url(hub_url)

        parsed_hub = urlparse(hub_url)
        hub_domain = parsed_hub.netloc

        soup = BeautifulSoup(fetch_res.body, "html.parser")
        links: set[str] = set()

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if not href or href.startswith(("#", "javascript:")):
                continue

            full_url = urljoin(hub_url, href)
            parsed_target = urlparse(full_url)

            # Ensure same domain or allowed path
            if parsed_target.netloc == hub_domain and parsed_target.scheme in ("http", "https"):
                # Avoid non-article media files
                if re.search(r"\.(pdf|jpg|png|gif|zip|exe|mp4|mp3|svg)$", parsed_target.path, re.IGNORECASE):
                    continue

                if link_patterns:
                    if any(re.search(pat, full_url, re.IGNORECASE) for pat in link_patterns):
                        links.add(full_url)
                else:
                    # Generic heuristic for article URLs (has depth >= 2 or date/slug)
                    path_parts = [p for p in parsed_target.path.split("/") if p]
                    if len(path_parts) >= 2 or re.search(r"/(news|article|world|middle-east|report)/\w+", parsed_target.path):
                        links.add(full_url)

            if len(links) >= self.max_crawl_links:
                break

        discovered_urls = list(links)[: self.max_crawl_links]
        articles: list[ScrapedArticle] = []

        for target_url in discovered_urls:
            try:
                article = await self.scrape_single_url(target_url)
                if article.extracted_text and len(article.extracted_text) > 100:
                    articles.append(article)
            except (FetchError, UnsupportedURLError, Exception) as exc:
                logger.warning("scraper.crawl_target_failed", target_url=target_url, error=str(exc))

        return ScrapeHubResult(
            hub_url=hub_url,
            discovered_urls=discovered_urls,
            articles=articles,
        )


__all__ = ["ScrapeHubResult", "ScrapedArticle", "WebScraper"]
