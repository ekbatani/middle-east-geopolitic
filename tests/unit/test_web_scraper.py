from unittest.mock import AsyncMock, patch

import pytest

from mei.infrastructure.collection.http_fetcher import FetchResult
from mei.infrastructure.collection.web_scraper import WebScraper


@pytest.mark.asyncio
async def test_web_scraper_single_url():
    scraper = WebScraper()
    html = """
    <html>
        <head><title>Middle East Update</title></head>
        <body>
            <nav>Menu Items</nav>
            <article>
                <h1>Major Escalation in Red Sea</h1>
                <p>Commercial shipping routes face heightened disruption near Bab el-Mandeb strait with ongoing naval tensions and verified radar detections.</p>
                <p>Naval coalition forces intercept incoming projectile over international maritime corridors.</p>
            </article>
            <footer>Copyright 2026</footer>
        </body>
    </html>
    """
    fake_result = FetchResult(
        url="https://www.aljazeera.com/news/middle-east-test",
        status_code=200,
        content_type="text/html",
        body=html.encode("utf-8"),
    )

    with patch("mei.infrastructure.collection.web_scraper.fetch_url", new_callable=AsyncMock, return_value=fake_result):
        article = await scraper.scrape_single_url("https://www.aljazeera.com/news/middle-east-test")
        assert article.title == "Middle East Update"
        assert article.status_code == 200
        assert article.extracted_text is not None
        assert "Major Escalation in Red Sea" in article.extracted_text
        assert len(article.chunks) > 0


@pytest.mark.asyncio
async def test_web_scraper_crawl_hub():
    scraper = WebScraper(max_crawl_links=5)
    hub_html = """
    <html>
        <head><title>News Hub</title></head>
        <body>
            <a href="/news/article-1">Article 1</a>
            <a href="https://www.aljazeera.com/news/article-2">Article 2</a>
            <a href="https://external.com/article-3">External</a>
        </body>
    </html>
    """
    article_html = """
    <html>
        <head><title>Article 1</title></head>
        <body>
            <article>
                <h1>Strategic Pipeline Security Update</h1>
                <p>Energy infrastructure security monitoring across the Persian Gulf remains on high alert with updated patrol routes and automated sensor triggers active across the region.</p>
            </article>
        </body>
    </html>
    """

    async def mock_fetch(url: str):
        body = article_html.encode("utf-8") if "article" in url else hub_html.encode("utf-8")
        return FetchResult(url=url, status_code=200, content_type="text/html", body=body)

    with patch("mei.infrastructure.collection.web_scraper.fetch_url", side_effect=mock_fetch):
        result = await scraper.crawl_hub("https://www.aljazeera.com/news")
        assert len(result.discovered_urls) >= 1
        assert len(result.articles) >= 1
