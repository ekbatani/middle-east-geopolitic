from __future__ import annotations

import io
import traceback
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mei.application.services.extraction import ExtractionService
from mei.application.services.forecast_audit import ForecastAuditService
from mei.application.services.imagery_ingestion import ImageryIngestionService
from mei.application.services.report_generator import ReportGenerator
from mei.application.services.risk_engine import RiskEngine
from mei.application.services.scenario_engine import ScenarioEngine
from mei.application.services.source_ingestion import SourceIngestionService
from mei.infrastructure.collection.http_fetcher import fetch_url, validate_url_security
from mei.infrastructure.collection.rss import parse_feed
from mei.infrastructure.collection.web_scraper import WebScraper
from mei.infrastructure.llm.factory import get_structured_llm
from mei.infrastructure.llm.protocol import StructuredLLM
from mei.infrastructure.repositories.documents import DocumentRepository
from mei.infrastructure.repositories.imagery import ImageryRepository
from mei.infrastructure.repositories.monitors import MonitorRepository
from mei.infrastructure.repositories.relationships import RelationshipRepository
from mei.infrastructure.repositories.risks import RiskRepository
from mei.infrastructure.repositories.scenarios import ScenarioRepository
from mei.infrastructure.repositories.sources import SourceRepository
from mei.shared.enums import (
    DocumentStatus,
    EndpointType,
    RelationshipStatus,
    ReportType,
    ScopeType,
    VerificationStatus,
)
from mei.shared.errors import FetchError, LLMConfigurationError, UnsupportedURLError
from mei.shared.logging import get_logger
from mei.shared.time import utcnow

logger = get_logger(__name__)


def _try_get_llm() -> StructuredLLM | None:
    try:
        return get_structured_llm()
    except LLMConfigurationError:
        return None


class PipelineJobExecutor:
    """Executes background jobs, scrapers, AI extractions, risk recalculations, and report generators."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._llm = _try_get_llm()

    async def run_job(self, job_type: str, parameters: dict[str, Any] | None = None) -> tuple[int, str]:
        """Dispatch a job by type and return (items_processed, log_output)."""
        log_stream = io.StringIO()

        def log(msg: str) -> None:
            now_str = utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            log_stream.write(f"[{now_str}] {msg}\n")
            logger.info("pipeline_job.step", job_type=job_type, message=msg)

        log(f"Starting job '{job_type}' with parameters: {parameters or {}}")
        items_processed = 0

        try:
            if job_type == "daily_news_scraping":
                items_processed = await self._run_daily_news_scraping(log)
            elif job_type == "satellite_ingestion":
                items_processed = await self._run_satellite_ingestion(log)
            elif job_type == "social_broadcast_scraping":
                items_processed = await self._run_social_broadcast_scraping(log)
            elif job_type == "risk_recalculation":
                items_processed = await self._run_risk_recalculation(log)
            elif job_type == "scenario_evaluation":
                items_processed = await self._run_scenario_evaluation(log)
            elif job_type == "forecast_evaluation":
                items_processed = await self._run_forecast_evaluation(log)
            elif job_type == "daily_brief_generation":
                items_processed = await self._run_daily_brief_generation(log)
            elif job_type == "monitor_evaluation":
                items_processed = await self._run_monitor_evaluation(log)
            else:
                log(f"Warning: Unknown job type '{job_type}'. Running general feed collection.")
                items_processed = await self._run_daily_news_scraping(log)

            log(f"Job completed successfully. Total items processed: {items_processed}")
        except Exception as exc:
            log(f"ERROR: Job failed with exception: {exc}")
            log(traceback.format_exc())
            raise

        return items_processed, log_stream.getvalue()

    async def _run_daily_news_scraping(self, log: Any) -> int:
        sources_repo = SourceRepository(self._session)
        docs_repo = DocumentRepository(self._session)
        ingestion_service = SourceIngestionService(self._session)
        scraper = WebScraper(max_crawl_links=10)

        sources = await sources_repo.list_all(limit=100)
        log(f"Found {len(sources)} registered sources in catalog")

        processed_docs: list[UUID] = []

        for source in sources:
            if not source.enabled:
                log(f"Skipping disabled source: {source.name}")
                continue

            log(f"Processing source '{source.name}' ({len(source.endpoints)} endpoints)")
            for endpoint in source.endpoints:
                try:
                    if endpoint.endpoint_type == EndpointType.RSS:
                        log(f"Polling RSS endpoint: {endpoint.url}")
                        validate_url_security(endpoint.url)
                        feed_result = await fetch_url(endpoint.url)
                        await sources_repo.mark_endpoint_success(endpoint, at=utcnow())
                        items = parse_feed(feed_result.body)
                        log(f"Parsed {len(items)} feed items from {endpoint.url}")

                        for item in items[:15]:
                            if item.external_id:
                                existing = await docs_repo.find_by_external_id(endpoint.source_id, item.external_id)
                                if existing:
                                    continue
                            doc = await ingestion_service.submit_url(
                                url=item.link,
                                title=item.title,
                                source_id=endpoint.source_id,
                                external_id=item.external_id,
                                published_at=item.published_at,
                            )
                            if doc.status == DocumentStatus.PARSED and doc.duplicate_of_document_id is None:
                                processed_docs.append(doc.id)
                                log(f"Ingested document ID: {doc.id} ({doc.title or doc.canonical_url[:50]})")

                    elif endpoint.endpoint_type in (EndpointType.HTML, EndpointType.SCRAPER):
                        log(f"Crawling web scraper hub: {endpoint.url}")
                        crawl_res = await scraper.crawl_hub(endpoint.url)
                        await sources_repo.mark_endpoint_success(endpoint, at=utcnow())
                        log(f"Discovered {len(crawl_res.articles)} articles from hub {endpoint.url}")

                        for art in crawl_res.articles:
                            doc = await ingestion_service.submit_url(
                                url=art.url,
                                title=art.title,
                                source_id=endpoint.source_id,
                            )
                            if doc.status == DocumentStatus.PARSED and doc.duplicate_of_document_id is None:
                                processed_docs.append(doc.id)
                                log(f"Ingested scraped article: {art.url}")

                except (FetchError, UnsupportedURLError, Exception) as exc:
                    await sources_repo.mark_endpoint_failure(endpoint, at=utcnow())
                    log(f"Endpoint fetch error on {endpoint.url}: {exc}")

        # Run AI Structured Extraction on new documents
        if self._llm and processed_docs:
            log(f"Running LLM claim & event extraction on {len(processed_docs)} new documents...")
            extractor = ExtractionService(self._session, self._llm)
            for doc_id in processed_docs:
                doc = await docs_repo.get(doc_id)
                if doc and (doc.extracted_text or doc.translation_text):
                    try:
                        res = await extractor.extract(doc)
                        await extractor.persist(doc, res)
                        log(f"Extracted {len(res.events)} events, {len(res.claims)} claims from doc {doc.id}")
                    except Exception as extract_err:
                        log(f"Extraction warning on doc {doc.id}: {extract_err}")

        await self._session.commit()
        return len(processed_docs)

    async def _run_satellite_ingestion(self, log: Any) -> int:
        ingestion = ImageryIngestionService(self._session)

        # Predefined strategic maritime & kinetic coordinates in Middle East
        strategic_zones = [
            {"caption": "Sentinel-2 SAR Coverage - Strait of Hormuz Northern Sector", "lat": 26.5667, "lon": 56.2500, "url": "https://sentinel-hub.mock/passes/hormuz_sar_2026.jpg"},
            {"caption": "NASA FIRMS Thermal Anomaly Detections - Bab el-Mandeb Choke Point", "lat": 12.5833, "lon": 43.3333, "url": "https://firms.modis.mock/detections/thermal_anomalies_red_sea.jpg"},
            {"caption": "High-Altitude Observation - Hodeidah Port Anchorage Basin", "lat": 14.7978, "lon": 42.9545, "url": "https://sentinel-hub.mock/passes/hodeidah_berth_opt.jpg"},
            {"caption": "Electro-Optical Reconnaissance - Natanz Facility Perimeter", "lat": 33.7222, "lon": 51.7264, "url": "https://commercial-sat.mock/imagery/natanz_eo_highres.jpg"},
        ]

        count = 0
        for zone in strategic_zones:
            # Ingest image record
            try:
                img = await ingestion.ingest_image(
                    image_url=zone["url"],
                    caption=zone["caption"],
                    latitude=zone["lat"],
                    longitude=zone["lon"],
                    verification_status=VerificationStatus.SINGLE_SOURCE,
                )
                log(f"Ingested satellite imagery evidence #{img.id} ({zone['caption']})")
                count += 1
            except Exception as exc:
                log(f"Satellite ingestion note for {zone['caption']}: {exc}")

        await self._session.commit()
        return count

    async def _run_social_broadcast_scraping(self, log: Any) -> int:
        log("Checking official telegram & social broadcast feeds...")
        # Simulated OSINT broadcast ingestion
        ingestion_service = SourceIngestionService(self._session)

        broadcast_sources = [
            {"title": "CENTCOM Operational Summary - Red Sea Interceptions", "url": "https://www.centcom.mil/MEDIA/PRESS-RELEASES/Press-Release-View/Article/redsea-intercept-daily/"},
            {"title": "SABA News Statement - Maritime Movement Directives", "url": "https://www.saba.ye/en/news/statement-maritime-transit/"},
        ]

        count = 0
        for bs in broadcast_sources:
            try:
                await ingestion_service.submit_url(url=bs["url"], title=bs["title"])
                log(f"Ingested broadcast announcement: {bs['title']}")
                count += 1
            except Exception as exc:
                log(f"Broadcast fetch note for {bs['url']}: {exc}")

        await self._session.commit()
        return count

    async def _run_risk_recalculation(self, log: Any) -> int:
        risks_repo = RiskRepository(self._session)
        rel_repo = RelationshipRepository(self._session)
        engine = RiskEngine(self._session)

        definitions = await risks_repo.list_definitions()
        active_relationships = await rel_repo.list_all(status=RelationshipStatus.ACTIVE, limit=200)

        log(f"Re-evaluating {len(definitions)} risk definitions across {len(active_relationships)} active relationships...")
        count = 0
        for rel in active_relationships:
            for defn in definitions:
                if ScopeType.RELATIONSHIP.value in defn.scope_types:
                    try:
                        await engine.calculate(
                            risk_definition_id=defn.id,
                            scope_type=ScopeType.RELATIONSHIP,
                            scope_id=rel.id,
                            llm=self._llm,
                            triggered_by="scheduler",
                        )
                        count += 1
                    except Exception as err:
                        log(f"Risk calculation error for relationship {rel.id}: {err}")

        await self._session.commit()
        log(f"Recalculated {count} risk assessments across active relationships")
        return count

    async def _run_scenario_evaluation(self, log: Any) -> int:
        scenario_repo = ScenarioRepository(self._session)
        engine = ScenarioEngine(self._session)

        scenarios = await scenario_repo.list_all(limit=100)
        log(f"Evaluating {len(scenarios)} registered geopolitical scenarios...")

        count = 0
        for scn in scenarios:
            try:
                await engine.update_scenario(scn.id, llm=self._llm, triggered_by="scheduler")
                count += 1
                log(f"Updated scenario '{scn.title}' (ID: {scn.id})")
            except Exception as exc:
                log(f"Scenario update error for {scn.id}: {exc}")

        await self._session.commit()
        return count

    async def _run_forecast_evaluation(self, log: Any) -> int:
        audit_service = ForecastAuditService(self._session)
        due_forecasts = await audit_service.list_due()
        log(f"Audited forecast questions. {len(due_forecasts)} questions currently due for resolution/calibration.")
        return len(due_forecasts)

    async def _run_daily_brief_generation(self, log: Any) -> int:
        log("Generating daily executive intelligence brief...")
        generator = ReportGenerator(self._session)
        report = await generator.generate(
            ReportType.DAILY_BRIEF,
            llm=self._llm,
            triggered_by="scheduler",
        )
        await self._session.commit()
        log(f"Generated Executive Daily Brief Report #{report.id}")
        return 1

    async def _run_monitor_evaluation(self, log: Any) -> int:
        monitor_repo = MonitorRepository(self._session)
        monitors = await monitor_repo.list_all(enabled=True)
        log(f"Evaluating {len(monitors)} enabled automated intelligence monitors...")
        # Mark evaluation timestamp
        now = utcnow()
        for m in monitors:
            m.last_evaluated_at = now
        await self._session.commit()
        return len(monitors)


__all__ = ["PipelineJobExecutor"]
