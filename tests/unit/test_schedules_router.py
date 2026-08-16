from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from apps.api.main import app
from fastapi.testclient import TestClient

from mei.infrastructure.auth.dependencies import get_current_principal
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.collection.http_fetcher import FetchResult
from mei.shared.enums import Scope


@pytest.fixture
def client():
    def _override_principal():
        return Principal(
            user_id=uuid4(),
            scopes=frozenset([
                Scope.INTELLIGENCE_READ,
                Scope.SOURCES_SUBMIT,
                Scope.ADMIN_CONFIGURATION,
            ]),
        )

    app.dependency_overrides[get_current_principal] = _override_principal
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_test_scrape_endpoint(client):
    fake_html = """<html><head><title>OSINT Report</title></head><body><article><p>Incident occurred in Bab el-Mandeb strait with ongoing maritime corridor patrol and naval tracking operations.</p></article></body></html>"""
    fake_result = FetchResult(
        url="https://www.aljazeera.com/news/middleeast/test",
        status_code=200,
        content_type="text/html",
        body=fake_html.encode("utf-8"),
    )

    with patch(
        "mei.infrastructure.collection.web_scraper.fetch_url",
        new_callable=AsyncMock,
        return_value=fake_result,
    ):
        resp = client.post(
            "/api/v1/schedules/test-scrape",
            json={"url": "https://www.aljazeera.com/news/middleeast/test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["url"] == "https://www.aljazeera.com/news/middleeast/test"
        assert data["title"] == "OSINT Report"
        assert "Incident occurred in Bab el-Mandeb" in data["extracted_text"]
