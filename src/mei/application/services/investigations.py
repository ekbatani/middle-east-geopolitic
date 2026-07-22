from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.claims.models import Claim
from mei.domain.documents.models import Document
from mei.domain.events.models import Event
from mei.domain.investigations.models import Investigation
from mei.infrastructure.repositories.claims import ClaimRepository
from mei.infrastructure.repositories.investigations import InvestigationRepository
from mei.shared.enums import EvidenceStance
from mei.shared.logging import get_logger
from mei.shared.time import utcnow

logger = get_logger(__name__)

# Common English function words excluded when turning an investigation
# question into search keywords, so a question like "Did State A violate
# State B's airspace?" searches on "State", "violate", "airspace" rather
# than matching everything via stopwords.
_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "of", "to", "in", "on",
    "for", "and", "or", "did", "does", "do", "will", "has", "have", "had",
    "what", "how", "why", "who", "when", "where", "which", "with", "that",
    "this", "be", "been", "being", "at", "by", "from", "as", "it", "its",
}


def extract_keywords(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9']+", text)
    seen: list[str] = []
    for token in tokens:
        if len(token) > 2 and token.lower() not in _STOPWORDS and token not in seen:
            seen.append(token)
    return seen


def score_narrative_comparison(
    *,
    claim_count: int,
    supporting_evidence_count: int,
    contradicting_evidence_count: int,
    claim_confidences: list[float],
) -> dict[str, object]:
    """Turn raw evidence-stance tallies into a comparison summary.

    Kept as a pure function (no DB/session access) so the scoring rules can
    be unit tested directly, matching the pattern used by
    `scenario_engine.normalize_probability_range`.
    """
    total_evidence = supporting_evidence_count + contradicting_evidence_count
    divergence_score = (
        round(contradicting_evidence_count / total_evidence, 2) if total_evidence else 0.0
    )
    confidence = (
        round(sum(claim_confidences) / len(claim_confidences), 2)
        if claim_confidences
        else (0.3 if claim_count else 0.0)
    )

    if not claim_count:
        summary = "No claims matching this question were found in the intelligence database."
    elif contradicting_evidence_count:
        summary = (
            f"Found {claim_count} claim(s); {contradicting_evidence_count} piece(s) of evidence "
            "contradict other evidence attached to the same claims, indicating disputed narratives."
        )
    else:
        summary = f"Found {claim_count} claim(s); no contradicting evidence was recorded."

    return {
        "comparison_summary": summary,
        "divergence_score": divergence_score,
        "confidence": confidence,
        "supporting_evidence_count": supporting_evidence_count,
        "contradicting_evidence_count": contradicting_evidence_count,
    }


class InvestigationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = InvestigationRepository(session)

    async def launch_investigation(
        self,
        *,
        title: str,
        question: str,
        requested_by: str,
        priority: str = "medium",
        assigned_to: str | None = None,
    ) -> Investigation:
        investigation = await self._repo.create(
            title=title,
            question=question,
            requested_by=requested_by,
            priority=priority,
            assigned_to=assigned_to,
        )

        await self._repo.create_step(
            investigation_id=investigation.id,
            step_type="source_search",
            sequence=1,
            input_json={"query": question},
        )
        await self._repo.create_step(
            investigation_id=investigation.id,
            step_type="claim_extraction",
            sequence=2,
            input_json={},
        )
        await self._repo.create_step(
            investigation_id=investigation.id,
            step_type="narrative_comparison",
            sequence=3,
            input_json={},
        )

        # Trigger celery task asynchronously
        from apps.worker.tasks.investigate import run_investigation
        run_investigation.delay(str(investigation.id))

        return investigation

    async def execute_investigation(self, investigation_id: UUID) -> Investigation:
        investigation = await self._repo.get(investigation_id)
        if not investigation:
            raise ValueError(f"Investigation {investigation_id} not found")

        logger.info("investigation.execute.start", investigation_id=str(investigation_id))
        investigation.status = "running"
        investigation.started_at = utcnow()
        await self._session.flush()

        steps = await self._repo.get_steps(investigation_id)

        try:
            documents, events = await self._search_sources(investigation.question)
            claims = await self._search_claims(investigation.question, events)
            comparison = await self._compare_narratives(claims)

            for step in steps:
                step.status = "running"
                step.started_at = utcnow()
                await self._session.flush()

                if step.step_type == "source_search":
                    step.output_json = {
                        "documents_found": [
                            {"id": str(d.id), "title": d.title} for d in documents
                        ],
                        "events_found": [
                            {"id": str(e.id), "title": e.title} for e in events
                        ],
                    }
                elif step.step_type == "claim_extraction":
                    step.output_json = {
                        "claims_extracted": [
                            {
                                "id": str(c.id),
                                "claim": c.claim_text,
                                "claimant_actor_id": str(c.claimant_actor_id) if c.claimant_actor_id else None,
                                "subject_actor_id": str(c.subject_actor_id) if c.subject_actor_id else None,
                                "verification_status": str(c.verification_status),
                                "confidence": c.confidence,
                            }
                            for c in claims
                        ]
                    }
                elif step.step_type == "narrative_comparison":
                    step.output_json = comparison
                else:
                    step.output_json = {"result": "no handler defined for this step type"}

                step.status = "completed"
                step.completed_at = utcnow()
                await self._session.flush()

            # Successfully completed all steps
            investigation.status = "completed"
            investigation.completed_at = utcnow()
            investigation.result_summary = self._summarize(
                investigation.question, documents, events, claims, comparison
            )
            investigation.confidence = comparison["confidence"]  # type: ignore[assignment]

            from mei.domain.reports.models import Report
            from mei.shared.enums import ReportStatus, ReportType

            report = Report(
                report_type=ReportType.CONFLICT_BRIEF,
                title=f"Investigation Brief: {investigation.title}",
                content_markdown=self._render_report(investigation, documents, events, claims, comparison),
                status=ReportStatus.GENERATED,
            )
            self._session.add(report)
            await self._session.flush()
            investigation.report_id = report.id

            logger.info("investigation.execute.success", investigation_id=str(investigation_id))

        except Exception as exc:
            logger.exception("investigation.execute.failed", investigation_id=str(investigation_id), error=str(exc))
            investigation.status = "failed"
            investigation.completed_at = utcnow()
            investigation.result_summary = f"Execution failed due to: {exc}"

            # Fail any running/pending steps
            for step in steps:
                if step.status in ("pending", "running"):
                    step.status = "failed"
                    step.completed_at = utcnow()
                    step.error_message = str(exc)

        await self._session.flush()
        return investigation

    async def _search_sources(self, question: str) -> tuple[list[Document], list[Event]]:
        keywords = extract_keywords(question)
        if not keywords:
            return [], []

        doc_conditions = [Document.title.ilike(f"%{kw}%") for kw in keywords] + [
            Document.extracted_text.ilike(f"%{kw}%") for kw in keywords
        ]
        doc_stmt = select(Document).where(or_(*doc_conditions)).limit(20)
        doc_result = await self._session.execute(doc_stmt)
        documents = list(doc_result.scalars())

        event_conditions = [Event.title.ilike(f"%{kw}%") for kw in keywords] + [
            Event.summary.ilike(f"%{kw}%") for kw in keywords
        ]
        event_stmt = select(Event).where(or_(*event_conditions)).limit(20)
        event_result = await self._session.execute(event_stmt)
        events = list(event_result.scalars())

        return documents, events

    async def _search_claims(self, question: str, events: list[Event]) -> list[Claim]:
        keywords = extract_keywords(question)
        event_ids = [event.id for event in events]

        conditions = [Claim.claim_text.ilike(f"%{kw}%") for kw in keywords]
        if event_ids:
            conditions.append(Claim.event_id.in_(event_ids))
        if not conditions:
            return []

        stmt = select(Claim).where(or_(*conditions)).limit(30)
        result = await self._session.execute(stmt)
        return list(result.scalars())

    async def _compare_narratives(self, claims: list[Claim]) -> dict[str, object]:
        claim_repo = ClaimRepository(self._session)
        supports = 0
        contradicts = 0
        confidences: list[float] = []

        for claim in claims:
            if claim.confidence is not None:
                confidences.append(claim.confidence)
            evidence = await claim_repo.list_evidence(claim.id)
            for item in evidence:
                if item.stance == EvidenceStance.CONTRADICTS:
                    contradicts += 1
                elif item.stance == EvidenceStance.SUPPORTS:
                    supports += 1

        return score_narrative_comparison(
            claim_count=len(claims),
            supporting_evidence_count=supports,
            contradicting_evidence_count=contradicts,
            claim_confidences=confidences,
        )

    def _summarize(
        self,
        question: str,
        documents: list[Document],
        events: list[Event],
        claims: list[Claim],
        comparison: dict[str, object],
    ) -> str:
        if not documents and not events and not claims:
            return (
                f"Investigation on: '{question}' completed. No matching documents, events, "
                "or claims were found in the intelligence database; further collection may be required."
            )
        return (
            f"Investigation on: '{question}' completed. Found {len(documents)} document(s), "
            f"{len(events)} event(s), and {len(claims)} claim(s). {comparison['comparison_summary']}"
        )

    def _render_report(
        self,
        investigation: Investigation,
        documents: list[Document],
        events: list[Event],
        claims: list[Claim],
        comparison: dict[str, object],
    ) -> str:
        lines = [
            f"# Investigation: {investigation.title}",
            "",
            f"**Question:** {investigation.question}",
            "",
            f"**Result Summary:** {investigation.result_summary}",
            "",
            "## Matched Events",
            *([f"- {e.title} (`{e.id}`)" for e in events] or ["- None found."]),
            "",
            "## Matched Documents",
            *([f"- {d.title or d.canonical_url} (`{d.id}`)" for d in documents] or ["- None found."]),
            "",
            "## Claims",
            *(
                [f"- {c.claim_text} (`{c.id}`, confidence: {c.confidence})" for c in claims]
                or ["- None found."]
            ),
            "",
            "## Narrative Comparison",
            f"- {comparison['comparison_summary']}",
        ]
        return "\n".join(lines)


__all__ = ["InvestigationService"]
