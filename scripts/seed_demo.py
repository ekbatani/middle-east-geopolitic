"""Comprehensive demo data seed script for the Middle East Geopolitical Intelligence Platform.

Populates realistic, interconnected intelligence data across ALL 15 platform modules:
1. Actors, Aliases & Leadership
2. Curated Sources & Ingested Documents
3. Claims & Evidence Links
4. Geocoded Events & Impact Assessments (Map View)
5. Multilateral Actor Relationships & Trend Scores (Graph View)
6. Indicator Observations & Evaluated Risk Models (Risk Engine)
7. Geopolitical Scenarios & Probabilistic Assessments (Scenarios View)
8. Forecast Records & Calibration Metrics (Forecasts View)
9. Intelligence Reports (Daily Briefs, Country Briefs, Conflict Outlooks)
10. Active Investigations & Timeline Steps (Investigations View)
11. Real-time Monitors & Triggered Notification Alerts (Monitors View)
12. Review Queue Items (Entity Resolution & High-Impact Events)
13. Imagery Evidence with Geospatial Coordinates & Analysis JSON (Imagery View)
14. Analyst Assessments & Multi-Model Review Disagreements (Disagreements View)
15. Administrator Identity & API Key
"""

import asyncio
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mei.infrastructure.database import models as _all_models  # noqa: F401
from mei.application.services.identity import IdentityService
from mei.domain.actors.models import Actor, ActorAlias
from mei.domain.analyst_assessments.models import AnalystAssessment
from mei.domain.claims.models import Claim, ClaimEvidence
from mei.domain.documents.models import Document, DocumentChunk
from mei.domain.events.models import Event, EventActor, EventImpact, EventLocation
from mei.domain.forecasts.models import ForecastRecord
from mei.domain.imagery.models import ImageEvidence
from mei.domain.indicators.models import IndicatorObservation
from mei.domain.investigations.models import Investigation, InvestigationStep
from mei.domain.model_reviews.models import ModelReviewResult
from mei.domain.monitors.models import Monitor, Notification
from mei.domain.relationships.models import Relationship, RelationshipObservation
from mei.domain.reports.models import Report
from mei.domain.review.models import ReviewItem
from mei.domain.risks.models import RiskAssessment
from mei.domain.scenarios.models import Scenario, ScenarioAssessment
from mei.domain.sources.models import Source
from mei.infrastructure.database.session import get_session_factory
from mei.infrastructure.repositories.actors import ActorRepository
from mei.infrastructure.repositories.indicators import IndicatorRepository
from mei.infrastructure.repositories.risks import RiskRepository
from mei.shared.config import get_settings
from mei.shared.enums import (
    ActorType,
    DisagreementSubjectType,
    DocumentStatus,
    EvidenceStance,
    ForecastOutcome,
    ForecastStatus,
    LifecycleStatus,
    ModelReviewSubjectType,
    RelationshipDirectionality,
    RelationshipStatus,
    ReportStatus,
    ReportType,
    ReviewStatus,
    ReviewType,
    RoleName,
    ScenarioFamily,
    ScenarioStatus,
    Scope,
    ScopeType,
    Trend,
    VerificationStatus,
)
from mei.shared.ids import uuid7
from mei.shared.logging import configure_logging, get_logger
from mei.shared.time import utcnow
from scripts.seed import _seed_actors, _seed_risk_indicators, _seed_schedules, _seed_sources


configure_logging(json_output=False)
logger = get_logger(__name__)


async def seed_extended_actors(session: AsyncSession) -> dict[str, Actor]:
    """Ensure core and non-state actors exist and return a lookup map."""
    repo = ActorRepository(session)
    extra_actors = [
        ("Houthis (Ansar Allah)", ActorType.ARMED_GROUP, "أنصار الله"),
        ("Quds Force", ActorType.MILITARY, "نیروی قدس"),
        ("United States Central Command (CENTCOM)", ActorType.MILITARY, None),
        ("Mossad", ActorType.INTELLIGENCE_SERVICE, "המוסד"),
        ("Islamic Resistance in Iraq", ActorType.ARMED_GROUP, "المقاومة الإسلامية في العراق"),
    ]
    for name, actor_type, native in extra_actors:
        if await repo.get_by_canonical_name(name) is None:
            await repo.create(canonical_name=name, actor_type=actor_type, native_name=native)

    all_actors = await repo.list_all(limit=200)
    actor_map = {a.canonical_name: a for a in all_actors}

    # Aliases
    iran = actor_map.get("Iran")
    if iran:
        res = await session.execute(select(ActorAlias).where(ActorAlias.actor_id == iran.id))
        if not res.scalars().first():
            session.add_all([
                ActorAlias(actor_id=iran.id, alias="Islamic Republic of Iran", alias_type="official_name"),
                ActorAlias(actor_id=iran.id, alias="IRI", alias_type="acronym"),
                ActorAlias(actor_id=iran.id, alias="Tehran", alias_type="metonym"),
            ])

    israel = actor_map.get("Israel")
    if israel:
        res = await session.execute(select(ActorAlias).where(ActorAlias.actor_id == israel.id))
        if not res.scalars().first():
            session.add_all([
                ActorAlias(actor_id=israel.id, alias="State of Israel", alias_type="official_name"),
                ActorAlias(actor_id=israel.id, alias="Tel Aviv", alias_type="metonym"),
            ])

    return actor_map


async def seed_documents_and_claims(
    session: AsyncSession, actor_map: dict[str, Actor]
) -> tuple[dict[str, Document], dict[str, Claim]]:
    sources_res = await session.execute(select(Source))
    sources = list(sources_res.scalars().all())
    source = sources[0] if sources else None
    if not source:
        return {}, {}

    docs_data = [
        {
            "key": "red_sea_doc",
            "url": "https://www.aljazeera.com/news/2026/8/10/red-sea-maritime-interceptions-escalate",
            "title": "Maritime Security Update: Red Sea Drone and Missile Interceptions",
            "text": "United States Central Command intercepted two anti-ship ballistic missiles and three unmanned aerial vehicles launched from Houthi-controlled territory in Yemen over the southern Red Sea. Commercial shipping continues to divert around the Cape of Good Hope, sustaining freight rate increases of 35% across major Asia-Europe trade corridors.",
        },
        {
            "key": "levant_doc",
            "url": "https://www.reuters.com/world/middle-east/israel-hezbollah-cross-border-exchanges-2026-08-12",
            "title": "Intensive Cross-Border Exchanges Reported Along the Blue Line",
            "text": "Cross-border artillery and precision rocket exchanges between the Israel Defense Forces and Hezbollah forces intensified today across southern Lebanon and northern Galilee. International diplomatic efforts led by France and the United States aim to establish a demilitarized buffer zone south of the Litani River.",
        },
        {
            "key": "diplomatic_doc",
            "url": "https://www.middleeasteye.net/news/saudi-iran-bilateral-security-consultations-riyadh",
            "title": "Saudi-Iranian High-Level Security Consultations Convene in Riyadh",
            "text": "Senior diplomatic and security delegations from the Islamic Republic of Iran and the Kingdom of Saudi Arabia held closed-door consultations in Riyadh to discuss Persian Gulf maritime safety, diplomatic de-escalation protocols, and bilateral economic channels.",
        },
    ]

    doc_map: dict[str, Document] = {}
    for d in docs_data:
        existing = await session.execute(select(Document).where(Document.canonical_url == d["url"]))
        doc = existing.scalars().first()
        if not doc:
            doc = Document(
                source_id=source.id,
                canonical_url=d["url"],
                title=d["title"],
                extracted_text=d["text"],
                translation_text=d["text"],
                status=DocumentStatus.PARSED,
                published_at=utcnow() - timedelta(days=2),
                retrieved_at=utcnow() - timedelta(days=2),
            )
            session.add(doc)
            await session.flush()
            session.add(
                DocumentChunk(
                    document_id=doc.id,
                    sequence=1,
                    text=d["text"],
                    token_count=len(d["text"].split()),
                )
            )
        doc_map[d["key"]] = doc

    # Seed Claims
    claims_data = [
        {
            "key": "claim_houthi_interception",
            "text": "US CENTCOM naval forces successfully neutralized multi-vector Houthi drone attack in southern Red Sea.",
            "type": "military_action",
            "claimant": "United States",
            "subject": "Houthis (Ansar Allah)",
            "doc": "red_sea_doc",
            "stance": EvidenceStance.SUPPORTS,
            "status": VerificationStatus.VERIFIED,
            "confidence": 0.92,
        },
        {
            "key": "claim_freight_rate_spike",
            "text": "Red Sea shipping diversions have resulted in a 35% surge in international maritime container freight rates.",
            "type": "economic_impact",
            "claimant": "United States",
            "subject": "Yemen",
            "doc": "red_sea_doc",
            "stance": EvidenceStance.SUPPORTS,
            "status": VerificationStatus.VERIFIED,
            "confidence": 0.88,
        },
        {
            "key": "claim_saudi_iran_dialogue",
            "text": "Saudi Arabia and Iran reached preliminary understanding on shared maritime de-escalation channels in the Gulf.",
            "type": "diplomatic_agreement",
            "claimant": "Saudi Arabia",
            "subject": "Iran",
            "doc": "diplomatic_doc",
            "stance": EvidenceStance.PARTIALLY_SUPPORTS,
            "status": VerificationStatus.PARTIALLY_CORROBORATED,
            "confidence": 0.78,
        },
    ]

    claim_map: dict[str, Claim] = {}
    for c in claims_data:
        existing = await session.execute(select(Claim).where(Claim.claim_text == c["text"]))
        claim = existing.scalars().first()
        if not claim:
            claimant = actor_map.get(c["claimant"])
            subject = actor_map.get(c["subject"])
            doc = doc_map.get(c["doc"])
            claim = Claim(
                claim_text=c["text"],
                normalized_claim=c["text"],
                claim_type=c["type"],
                claimant_actor_id=claimant.id if claimant else None,
                subject_actor_id=subject.id if subject else None,
                verification_status=c["status"],
                confidence=c["confidence"],
                lifecycle_status=LifecycleStatus.APPROVED,
                created_by_type="system",
                first_observed_at=utcnow() - timedelta(days=2),
                last_checked_at=utcnow(),
            )
            session.add(claim)
            await session.flush()

            if doc:
                session.add(
                    ClaimEvidence(
                        claim_id=claim.id,
                        document_id=doc.id,
                        stance=c["stance"],
                        excerpt=doc.extracted_text[:200] if doc.extracted_text else "",
                        confidence=c["confidence"],
                        directness="direct",
                    )
                )
        claim_map[c["key"]] = claim

    return doc_map, claim_map


async def seed_events(session: AsyncSession, actor_map: dict[str, Actor]) -> list[Event]:
    events_data = [
        {
            "title": "Southern Red Sea Commercial Vessel Drone Interception",
            "event_type": "maritime_attack",
            "summary": "Multiple one-way attack drones and anti-ship cruise missiles intercepted near the Bab el-Mandeb strait.",
            "severity": 8,
            "significance": "high",
            "status": VerificationStatus.VERIFIED,
            "confidence": 0.95,
            "started_at": utcnow() - timedelta(hours=14),
            "location": {"name": "Bab el-Mandeb Strait", "lat": 12.5833, "lon": 43.3333, "country": "Yemen"},
            "actors": [("Houthis (Ansar Allah)", "instigator"), ("United States", "defender")],
            "impact": {"type": "maritime_security", "mag": 8.5, "unit": "threat_index"},
        },
        {
            "title": "Damascus Logistics Hub Precision Airstrike",
            "event_type": "airstrike",
            "summary": "Targeted airstrikes struck a logistics depot adjacent to Damascus International Airport.",
            "severity": 7,
            "significance": "high",
            "status": VerificationStatus.VERIFIED,
            "confidence": 0.90,
            "started_at": utcnow() - timedelta(days=1, hours=4),
            "location": {"name": "Damascus Airport Perimeter", "lat": 33.5138, "lon": 36.2765, "country": "Syria"},
            "actors": [("Israel", "instigator"), ("Syria", "target"), ("Iran", "affected_party")],
            "impact": {"type": "infrastructure_damage", "mag": 7.0, "unit": "severity_score"},
        },
        {
            "title": "Strait of Hormuz Naval Security Escort Exercise",
            "event_type": "naval_exercise",
            "summary": "IRGC Navy conducted coordinated surface and unmanned vessel maneuvers in the Strait of Hormuz.",
            "severity": 5,
            "significance": "medium",
            "status": VerificationStatus.VERIFIED,
            "confidence": 0.85,
            "started_at": utcnow() - timedelta(days=2),
            "location": {"name": "Strait of Hormuz", "lat": 26.5667, "lon": 56.2500, "country": "Iran"},
            "actors": [("Iran", "instigator"), ("United States", "monitor")],
            "impact": {"type": "military_readiness", "mag": 5.5, "unit": "readiness_level"},
        },
        {
            "title": "Intense Artillery Duel in Southern Lebanon Border Zone",
            "event_type": "border_clash",
            "summary": "Hezbollah guided anti-tank missile fire met with IDF counter-battery artillery strikes across the Blue Line.",
            "severity": 8,
            "significance": "critical",
            "status": VerificationStatus.VERIFIED,
            "confidence": 0.94,
            "started_at": utcnow() - timedelta(hours=8),
            "location": {"name": "Marjayoun Valley", "lat": 33.3600, "lon": 35.5900, "country": "Lebanon"},
            "actors": [("Hezbollah", "instigator"), ("Israel", "target")],
            "impact": {"type": "population_displacement", "mag": 9.0, "unit": "evacuation_index"},
        },
        {
            "title": "Riyadh GCC Regional Security & Maritime Summit",
            "event_type": "diplomatic_summit",
            "summary": "High-level diplomatic delegates convened to establish joint de-escalation corridors and crisis channels.",
            "severity": 2,
            "significance": "high",
            "status": VerificationStatus.VERIFIED,
            "confidence": 0.98,
            "started_at": utcnow() - timedelta(days=3),
            "location": {"name": "Riyadh Diplomatic Quarter", "lat": 24.7136, "lon": 46.6753, "country": "Saudi Arabia"},
            "actors": [("Saudi Arabia", "host"), ("United Arab Emirates", "participant"), ("Qatar", "participant")],
            "impact": {"type": "diplomatic_progress", "mag": 7.5, "unit": "cooperation_index"},
        },
        {
            "title": "Tel Aviv Multi-Layer Air Defense Interception Incident",
            "event_type": "missile_interception",
            "summary": "Arrow-3 air defense battery successfully engaged a long-range ballistic projectile outside Israeli airspace.",
            "severity": 9,
            "significance": "critical",
            "status": VerificationStatus.VERIFIED,
            "confidence": 0.96,
            "started_at": utcnow() - timedelta(days=4),
            "location": {"name": "Gush Dan Central District", "lat": 32.0853, "lon": 34.7818, "country": "Israel"},
            "actors": [("Israel", "defender"), ("Houthis (Ansar Allah)", "instigator")],
            "impact": {"type": "air_defense_activation", "mag": 9.5, "unit": "interception_rate"},
        },
    ]

    created_events: list[Event] = []
    for e in events_data:
        existing = await session.execute(select(Event).where(Event.title == e["title"]))
        event = existing.scalars().first()
        if not event:
            event = Event(
                title=e["title"],
                event_type=e["event_type"],
                summary=e["summary"],
                severity=e["severity"],
                strategic_significance=e["significance"],
                verification_status=e["status"],
                confidence=e["confidence"],
                lifecycle_status=LifecycleStatus.APPROVED,
                started_at=e["started_at"],
            )
            session.add(event)
            await session.flush()

            loc = e["location"]
            c_actor = actor_map.get(loc["country"])
            session.add(
                EventLocation(
                    event_id=event.id,
                    name=loc["name"],
                    latitude=loc["lat"],
                    longitude=loc["lon"],
                    country_actor_id=c_actor.id if c_actor else None,
                )
            )

            for act_name, role in e["actors"]:
                act = actor_map.get(act_name)
                if act:
                    session.add(
                        EventActor(
                            event_id=event.id,
                            actor_id=act.id,
                            role=role,
                            confidence=0.9,
                        )
                    )

            imp = e["impact"]
            session.add(
                EventImpact(
                    event_id=event.id,
                    impact_type=imp["type"],
                    magnitude=imp["mag"],
                    unit=imp["unit"],
                    confidence=0.85,
                )
            )
        created_events.append(event)

    return created_events


async def seed_relationships(session: AsyncSession, actor_map: dict[str, Actor]) -> None:
    rel_data = [
        ("Iran", "Israel", "hostility", 15, 88, 92, Trend.RISING, "Direct asymmetric and missile exchanges; high escalatory posture."),
        ("Iran", "Hezbollah", "military_alliance", 95, 10, 85, Trend.STABLE, "Deep strategic, ideological, and missile weapon supply alliance."),
        ("Iran", "Houthis (Ansar Allah)", "military_cooperation", 90, 15, 80, Trend.RISING, "Advanced anti-ship missile technology transfer and coordinated regional deterrence."),
        ("Israel", "United States", "strategic_alliance", 98, 5, 20, Trend.STABLE, "Ironclad defense treaty, intelligence sharing, and integrated air defense deployment."),
        ("Saudi Arabia", "Iran", "diplomatic_detente", 60, 45, 40, Trend.FALLING, "Beijing-brokered bilateral agreement maintaining diplomatic channels despite proxy frictions."),
        ("Israel", "Hezbollah", "active_conflict", 5, 95, 95, Trend.RISING, "High-intensity cross-border kinetic conflict along the Litani buffer corridor."),
        ("United States", "Houthis (Ansar Allah)", "active_conflict", 10, 90, 85, Trend.RISING, "Operation Prosperity Guardian maritime interdictions and precision strike campaigns."),
        ("Saudi Arabia", "United Arab Emirates", "strategic_partnership", 85, 20, 25, Trend.STABLE, "GCC economic coordination with localized competition in Red Sea and Yemen policy."),
    ]

    for src_name, tgt_name, r_type, dip_score, ten_score, esc_score, trend, explanation in rel_data:
        src = actor_map.get(src_name)
        tgt = actor_map.get(tgt_name)
        if not src or not tgt:
            continue

        existing = await session.execute(
            select(Relationship).where(
                Relationship.source_actor_id == src.id,
                Relationship.target_actor_id == tgt.id,
            )
        )
        rel = existing.scalars().first()
        if not rel:
            rel = Relationship(
                source_actor_id=src.id,
                target_actor_id=tgt.id,
                relationship_type=r_type,
                directionality=RelationshipDirectionality.SYMMETRIC,
                status=RelationshipStatus.ACTIVE,
                valid_from=date(2023, 1, 1),
            )
            session.add(rel)
            await session.flush()

            session.add(
                RelationshipObservation(
                    relationship_id=rel.id,
                    observed_at=utcnow(),
                    diplomatic_score=dip_score,
                    military_tension_score=ten_score,
                    escalation_risk_score=esc_score,
                    proxy_competition_score=80 if ten_score > 70 else 30,
                    strategic_trust_score=dip_score,
                    trend=trend,
                    confidence=0.90,
                    explanation=explanation,
                    approved_at=utcnow(),
                    approved_by="Lead Regional Analyst",
                )
            )


async def seed_indicators_and_risks(session: AsyncSession, actor_map: dict[str, Actor]) -> None:
    ind_repo = IndicatorRepository(session)
    risk_repo = RiskRepository(session)

    all_defs = await ind_repo.list_definitions()
    ind_map = {d.code: d for d in all_defs}

    # Observations for Iran, Israel, Yemen, Lebanon
    countries = ["Iran", "Israel", "Yemen", "Lebanon", "Saudi Arabia"]
    for c_name in countries:
        act = actor_map.get(c_name)
        if not act:
            continue

        sample_readings = [
            ("direct_cross_border_attacks", 6.0, 0.60),
            ("missile_drone_launch_frequency", 28.0, 0.56),
            ("official_escalation_rhetoric", 8.0, 0.80),
            ("maritime_attack_frequency", 12.0, 0.60),
            ("shipping_diversion", 70.0, 0.70),
            ("internal_protest_intensity", 4.0, 0.40),
            ("humanitarian_access_deterioration", 7.5, 0.75),
        ]

        for code, raw_val, norm_val in sample_readings:
            ind_def = ind_map.get(code)
            if not ind_def:
                continue

            existing = await session.execute(
                select(IndicatorObservation).where(
                    IndicatorObservation.indicator_id == ind_def.id,
                    IndicatorObservation.scope_id == act.id,
                )
            )
            if not existing.scalars().first():
                session.add(
                    IndicatorObservation(
                        indicator_id=ind_def.id,
                        scope_type=ScopeType.COUNTRY,
                        scope_id=act.id,
                        observed_at=utcnow() - timedelta(hours=4),
                        raw_value=raw_val,
                        normalized_value=norm_val,
                        confidence=0.92,
                        source_method="osint_automated_feed",
                    )
                )

    # Risk Assessments
    risk_defs = await risk_repo.list_definitions()
    for rdef in risk_defs:
        for c_name in ["Iran", "Israel", "Lebanon", "Saudi Arabia"]:
            act = actor_map.get(c_name)
            if not act:
                continue

            existing = await session.execute(
                select(RiskAssessment).where(
                    RiskAssessment.risk_definition_id == rdef.id,
                    RiskAssessment.scope_id == act.id,
                )
            )
            if not existing.scalars().first():
                score = 78 if c_name in ("Israel", "Lebanon") else (72 if c_name == "Iran" else 45)
                session.add(
                    RiskAssessment(
                        risk_definition_id=rdef.id,
                        scope_type=ScopeType.COUNTRY,
                        scope_id=act.id,
                        assessed_at=utcnow() - timedelta(hours=2),
                        base_score=score,
                        llm_adjustment=3,
                        final_score=min(100, score + 3),
                        previous_score=score - 5,
                        trend=Trend.RISING if score > 50 else Trend.STABLE,
                        confidence=0.88,
                        explanation=f"Risk posture in {c_name} influenced by kinetic activity, cross-theater weapon flows, and alert levels.",
                        contributions_json=[
                            {"indicator": "direct_cross_border_attacks", "weight": 0.25, "impact": "+15"},
                            {"indicator": "missile_drone_launch_frequency", "weight": 0.20, "impact": "+12"},
                            {"indicator": "official_escalation_rhetoric", "weight": 0.15, "impact": "+8"},
                        ],
                        approved_by="System Automator",
                        approved_at=utcnow(),
                    )
                )


async def seed_scenarios(session: AsyncSession, actor_map: dict[str, Actor]) -> None:
    scenarios_data = [
        {
            "name": "Direct Israel-Iran High-Intensity Ballistic Exchange",
            "family": ScenarioFamily.REGIONAL_ESCALATION,
            "scope": "Iran",
            "horizon": "30-90 Days",
            "prob_low": 0.65,
            "prob_high": 0.80,
            "confidence": 0.85,
            "desc": "Unconstrained multi-wave ballistic missile and hypersonic strikes targeting critical defense and energy infrastructure.",
            "triggers": ["Assassination of senior leadership", "Preemptive strike on nuclear enrichment facility"],
            "indicators": ["Air defense dispersal", "Underground silo hatch openings", "NOTAM airspace shutdowns"],
            "assumptions": ["Deterrence threshold broken", "Diplomatic off-ramps exhausted"],
        },
        {
            "name": "Sustained Attrition along the Litani Buffer Zone",
            "family": ScenarioFamily.MANAGED_CONFRONTATION,
            "scope": "Lebanon",
            "horizon": "1-6 Months",
            "prob_low": 0.70,
            "prob_high": 0.85,
            "confidence": 0.90,
            "desc": "High-volume tactical artillery and UAV exchanges without full-scale armored ground invasion of Beirut.",
            "triggers": ["Failure of UNIFIL diplomatic negotiations", "Increased cross-border anti-tank guided missile fire"],
            "indicators": ["Civilian evacuation radius expansion", "IDF reserve brigade mobilization"],
            "assumptions": ["Both sides prefer managed friction over total war"],
        },
        {
            "name": "Omani-Mediated Red Sea Maritime Navigation Protocol",
            "family": ScenarioFamily.CONTROLLED_DEESCALATION,
            "scope": "Yemen",
            "horizon": "3-6 Months",
            "prob_low": 0.25,
            "prob_high": 0.40,
            "confidence": 0.75,
            "desc": "Conditional commercial safe-transit agreements in exchange for humanitarian port access in Hodeidah.",
            "triggers": ["Bilateral Muscat talks", "Easing of commercial cargo insurance surcharges"],
            "indicators": ["Decline in missile launches against commercial hulls", "Resumption of Bab el-Mandeb transits"],
            "assumptions": ["Regional intermediaries successfully de-link maritime campaign from other theaters"],
        },
        {
            "name": "Multi-Front Regional War with Chokepoint Interdiction",
            "family": ScenarioFamily.SYSTEMIC_REGIONAL_WAR,
            "scope": "Iran",
            "horizon": "6-12 Months",
            "prob_low": 0.15,
            "prob_high": 0.30,
            "confidence": 0.70,
            "desc": "Simultaneous closure of Strait of Hormuz and Bab el-Mandeb accompanied by regional energy facility destruction.",
            "triggers": ["Direct state declaration of war", "Mine-laying in Persian Gulf sea lanes"],
            "indicators": ["Mining vessel deployments", "Global oil price spikes above $140/bbl"],
            "assumptions": ["Asymmetric denial strategy fully activated"],
        },
    ]

    for s in scenarios_data:
        act = actor_map.get(s["scope"])
        existing = await session.execute(select(Scenario).where(Scenario.name == s["name"]))
        scen = existing.scalars().first()
        if not scen:
            scen = Scenario(
                name=s["name"],
                scope_type=ScopeType.COUNTRY,
                scope_id=act.id if act else None,
                scenario_family=s["family"],
                time_horizon=s["horizon"],
                status=ScenarioStatus.ACTIVE,
                description=s["desc"],
            )
            session.add(scen)
            await session.flush()

            session.add(
                ScenarioAssessment(
                    scenario_id=scen.id,
                    assessed_at=utcnow() - timedelta(hours=6),
                    probability_low=s["prob_low"],
                    probability_high=s["prob_high"],
                    confidence=s["confidence"],
                    assumptions_json=s["assumptions"],
                    trigger_events_json=s["triggers"],
                    leading_indicators_json=s["indicators"],
                    expected_actor_behavior=s["desc"],
                    military_consequences="High alert and reserve mobilization across northern and southern commands.",
                    economic_consequences="Insurance surcharges on maritime freight and regional crude transport.",
                    humanitarian_consequences="Displacement in border buffer areas.",
                    invalidation_criteria_json=["Comprehensive verified ceasefire accord"],
                    explanation_of_change="Upward probability adjustment based on cross-border kinetic cadence.",
                    approved_by="Lead Geopolitical Modeler",
                    approved_at=utcnow(),
                )
            )


async def seed_forecasts(session: AsyncSession) -> None:
    forecasts_data = [
        {
            "question": "Will commercial container traffic through the Bab el-Mandeb Strait remain below 50% of 2023 baseline levels through Q4 2026?",
            "prob": 0.82,
            "conf": 0.88,
            "status": ForecastStatus.OPEN,
            "res_date": date(2026, 12, 31),
            "assumptions": ["Houthi targeting capabilities remain intact", "Insurance premiums stay prohibitive"],
        },
        {
            "question": "Will direct military exchanges occur between Israel and Iran within the next 60 days?",
            "prob": 0.74,
            "conf": 0.80,
            "status": ForecastStatus.OPEN,
            "res_date": date(2026, 10, 15),
            "assumptions": ["Retaliatory deterrence cycle accelerates", "Diplomatic mediation remains stalled"],
        },
        {
            "question": "Did Saudi Arabia and Iran conduct formal bilateral maritime security talks in Riyadh before August 2026?",
            "prob": 0.65,
            "conf": 0.90,
            "status": ForecastStatus.RESOLVED,
            "outcome": ForecastOutcome.YES,
            "brier": 0.1225,
            "res_date": date(2026, 8, 1),
            "note": "Resolved YES following official Saudi-Iranian security summit on August 10, 2026.",
            "assumptions": ["Bilateral diplomatic channels remained open"],
        },
        {
            "question": "Will the IAEA officially verify uranium enrichment to 90% purity at any declared Iranian nuclear installation?",
            "prob": 0.30,
            "conf": 0.75,
            "status": ForecastStatus.RESOLVED,
            "outcome": ForecastOutcome.NO,
            "brier": 0.09,
            "res_date": date(2026, 8, 1),
            "note": "Resolved NO based on latest quarterly IAEA Safeguards Report indicating stockpiles maintained at 60%.",
            "assumptions": ["Safeguards inspections ongoing"],
        },
    ]

    for f in forecasts_data:
        existing = await session.execute(select(ForecastRecord).where(ForecastRecord.question == f["question"]))
        if not existing.scalars().first():
            session.add(
                ForecastRecord(
                    question=f["question"],
                    issued_at=utcnow() - timedelta(days=30),
                    resolution_date=f["res_date"],
                    probability=f["prob"],
                    confidence=f["conf"],
                    assumptions_json=f["assumptions"],
                    status=f["status"],
                    outcome=f.get("outcome"),
                    resolved_at=utcnow() - timedelta(days=3) if f["status"] == ForecastStatus.RESOLVED else None,
                    brier_score=f.get("brier"),
                    evaluation_note=f.get("note"),
                )
            )


async def seed_reports(session: AsyncSession, actor_map: dict[str, Actor]) -> None:
    iran = actor_map.get("Iran")
    reports_data = [
        {
            "type": ReportType.DAILY_BRIEF,
            "title": "Daily Strategic Intelligence Briefing: Levant Cross-Border Intensity & Red Sea Chokepoints",
            "content": """# Executive Daily Intelligence Briefing

**Classification:** RESTRICTED // REL TO PLATFORM ANALYSTS
**Date:** 14 August 2026

## 1. Key Judgment Highlights
- **Red Sea Operational Dynamics:** Houthi maritime interdiction operations continue to impose high diversion rates on container logistics transiting Bab el-Mandeb.
- **Northern Arena Posture:** Cross-border artillery and precision ATGM strikes in the Marjayoun sector indicate high friction with elevated risks of accidental escalation.
- **Persian Gulf Channel:** Saudi-Iranian bilateral dialogues in Riyadh provide a partial diplomatic stabilizing counter-weight to northern kinetic escalation.

## 2. Risk Indicators & Anomaly Detection
- Cross-border kinetic events: **+22%** week-over-week.
- Freight rate surcharges: **+35%** across primary trade corridors.
- Air defense readiness levels across central theater: **CRITICAL**.

## 3. Recommended Watchpoints
1. Potential retaliatory missile volleys targeting critical military installations.
2. Escalation of electronic warfare and GPS spoofing around civil maritime lanes in the Gulf of Oman.
""",
        },
        {
            "type": ReportType.COUNTRY_BRIEF,
            "title": "Comprehensive Country Threat & Defense Assessment: Islamic Republic of Iran",
            "content": """# Country Strategic Assessment: Iran

## Executive Summary
Iran maintains a forward-defense posture leveraging decentralized regional alliances ('Axis of Resistance') combined with a diversified ballistic and cruise missile arsenal.

## Key Capabilities
- **Missile Arsenal:** Emad, Kheibar Shekan, and Fattah series with ranges exceeding 1,800 km.
- **Asymmetric Naval Assets:** Fast Attack Craft, sea-mine deployment capacity, and loitering munitions based out of Bandar Abbas and Jask.
- **Strategic Nuclear Posture:** Documented enrichment capability maintained at 60% with rapid breakout hedging.
""",
        },
    ]

    for r in reports_data:
        existing = await session.execute(select(Report).where(Report.title == r["title"]))
        if not existing.scalars().first():
            session.add(
                Report(
                    report_type=r["type"],
                    title=r["title"],
                    scope_type=ScopeType.COUNTRY,
                    scope_id=iran.id if iran else None,
                    content_markdown=r["content"],
                    status=ReportStatus.PUBLISHED,
                    approved_by="Chief Intelligence Officer",
                    approved_at=utcnow() - timedelta(hours=6),
                    published_at=utcnow() - timedelta(hours=5),
                )
            )


async def seed_investigations_and_monitors(
    session: AsyncSession, admin_user_id: UUID
) -> None:
    # Investigations
    invs = [
        {
            "title": "Investigation into Long-Range UAV Component Transshipment Routes across Eastern Syria",
            "question": "What are the primary logistics corridors utilized for unmanned aerial system component transfers into the Levant theater?",
            "status": "running",
            "priority": "high",
            "confidence": 0.85,
            "summary": "Identified multiple overland waypoints connecting Al-Bukamal crossing with secondary assembly facilities in Homs governorate.",
            "steps": [
                ("flight_radar_correlation", "Completed OSINT tracking of transport flights from Mehrabad to Damascus."),
                ("satellite_imagery_inspection", "Analyzed commercial imagery over Al-Bukamal border crossing."),
                ("actor_network_mapping", "Correlated key logistics unit leadership with known transport networks."),
            ],
        },
        {
            "title": "Persian Gulf Ghost Tanker STS Transfers & Sanctions Evasion",
            "question": "Which maritime anchorages are currently utilized for dark fleet ship-to-ship oil transfers off Khor Fakkan?",
            "status": "completed",
            "priority": "medium",
            "confidence": 0.92,
            "summary": "Verified 4 primary STS transfer coordinates active during night hours with AIS transponders deactivated.",
            "steps": [
                ("ais_anomaly_detection", "Detected 14 vessel transponder blackout events in Fujairah outer anchorage."),
                ("optical_satellite_verification", "Obtained high-resolution optical imagery confirming side-by-side mooring."),
            ],
        },
    ]

    for inv_data in invs:
        existing = await session.execute(select(Investigation).where(Investigation.title == inv_data["title"]))
        if not existing.scalars().first():
            inv = Investigation(
                title=inv_data["title"],
                question=inv_data["question"],
                status=inv_data["status"],
                priority=inv_data["priority"],
                requested_by="Principal Analyst",
                assigned_to="Strategic Recon Team",
                started_at=utcnow() - timedelta(days=5),
                completed_at=utcnow() - timedelta(days=1) if inv_data["status"] == "completed" else None,
                result_summary=inv_data["summary"],
                confidence=inv_data["confidence"],
            )
            session.add(inv)
            await session.flush()

            for seq, (stype, desc) in enumerate(inv_data["steps"], 1):
                session.add(
                    InvestigationStep(
                        investigation_id=inv.id,
                        step_type=stype,
                        sequence=seq,
                        status="completed",
                        output_json={"details": desc},
                        started_at=utcnow() - timedelta(days=4),
                        completed_at=utcnow() - timedelta(days=2),
                    )
                )

    # Monitors & Notifications
    monitors_data = [
        {
            "name": "Red Sea High-Severity Kinetic Incident Alert",
            "type": "event_threshold",
            "channel": "telegram",
            "condition": {"min_severity": 7, "region": "Red Sea", "event_types": ["maritime_attack", "missile_launch"]},
            "notifications": [
                ("critical", "CRITICAL ALERT: Multi-Vector Drone Swarm Intercepted Near Bab el-Mandeb", "CENTCOM naval escort ships engaged multiple airborne targets."),
                ("warning", "WARNING: Merchant Vessel Reports Suspected Fast-Boat Harassment", "Vessel 45nm southwest of Mokha reported two approaching skiffs."),
            ],
        },
        {
            "name": "Levant Air Defense & Airspace Closure Monitor",
            "type": "indicator_spike",
            "channel": "slack",
            "condition": {"indicator": "evacuation_airspace_closure", "threshold": True},
            "notifications": [
                ("warning", "ALERT: Temporary NOTAM Airspace Restriction Issued for Eastern Mediterranean Corridor", "Civil aviation authorities rerouting commercial flights away from northern flight paths."),
            ],
        },
    ]

    for m_data in monitors_data:
        existing = await session.execute(select(Monitor).where(Monitor.name == m_data["name"]))
        if not existing.scalars().first():
            mon = Monitor(
                name=m_data["name"],
                user_id=admin_user_id,
                monitor_type=m_data["type"],
                condition_json=m_data["condition"],
                delivery_channel=m_data["channel"],
                enabled=True,
                last_evaluated_at=utcnow() - timedelta(minutes=15),
                last_triggered_at=utcnow() - timedelta(hours=2),
            )
            session.add(mon)
            await session.flush()

            for sev, title, body in m_data["notifications"]:
                session.add(
                    Notification(
                        monitor_id=mon.id,
                        severity=sev,
                        title=title,
                        body=body,
                        delivery_channel=m_data["channel"],
                        status="sent",
                        sent_at=utcnow() - timedelta(hours=2),
                    )
                )


async def seed_review_queue_and_imagery(
    session: AsyncSession,
    doc_map: dict[str, Document],
    claim_map: dict[str, Claim] | None = None,
    actor_map: dict[str, Actor] | None = None,
) -> None:
    # Review Queue Items
    existing_reviews = await session.execute(select(ReviewItem).limit(1))
    if not existing_reviews.scalars().first():
        doc = list(doc_map.values())[0] if doc_map else None
        target_claim = list(claim_map.values())[0] if claim_map else None
        iraq_actor = actor_map.get("Islamic Resistance in Iraq") if actor_map else None

        review_items_data = [
            {
                "type": ReviewType.HIGH_IMPACT_EVENT,
                "subject": {
                    "event_title": "Unconfirmed Long-Range Cruise Missile Impact near Military Radar Site",
                    "source": "OSINT Telegram Feed",
                },
                "candidates": [
                    {"label": "Direct Kinetic Strike on Active Radar Array", "confidence": 0.65},
                    {"label": "Air Defense Interception Debris Field", "confidence": 0.72},
                ],
            },
            {
                "type": ReviewType.ENTITY_RESOLUTION,
                "subject": {
                    "candidate_name": "Kata'ib Sayyid al-Shuhada",
                    "link_kind": "subject",
                    "target_type": "claim",
                    "target_id": str(target_claim.id) if target_claim else None,
                    "document_id": str(doc.id) if doc else None,
                    "context": "Statement claiming responsibility for border drone launch",
                },
                "candidates": [
                    {
                        "actor_id": str(iraq_actor.id) if iraq_actor else None,
                        "canonical_name": "Islamic Resistance in Iraq",
                        "score": 88.0,
                    },
                ],
            },
        ]

        for r in review_items_data:
            session.add(
                ReviewItem(
                    review_type=r["type"],
                    status=ReviewStatus.PENDING,
                    subject_json=r["subject"],
                    candidates_json=r["candidates"],
                )
            )

    # Imagery Evidence
    doc = list(doc_map.values())[0] if doc_map else None
    imagery_data = [
        {
            "key": "imagery/hodeidah_port_pier_recon_20260812.jpg",
            "caption": "Port of Hodeidah Berth 4: Optical satellite reconnaissance of maritime unloading operations.",
            "lat": 14.7978,
            "lon": 42.9545,
            "status": VerificationStatus.VERIFIED,
            "confidence": 0.94,
            "analysis": {
                "detected_objects": ["Fast Patrol Craft", "Container Crane Array", "Fuel Storage Bunkers"],
                "vision_model": "gemini-1.5-pro-vision",
                "summary": "No missile canister launchers detected in commercial container zone; active fuel bunkering observed.",
            },
        },
        {
            "key": "imagery/bandar_abbas_naval_base_20260810.jpg",
            "caption": "Bandar Abbas IRIN Naval Base: Surface combatant readiness and frigate mooring positions.",
            "lat": 27.1492,
            "lon": 56.2064,
            "status": VerificationStatus.VERIFIED,
            "confidence": 0.91,
            "analysis": {
                "detected_objects": ["Moudge-class Frigate", "Tareq-class Submarine", "Fast Attack Catamaran"],
                "vision_model": "gemini-1.5-pro-vision",
                "summary": "Two combat frigates deployed outside harbor basin; submarine berthed at primary maintenance drydock.",
            },
        },
    ]

    for img in imagery_data:
        existing = await session.execute(select(ImageEvidence).where(ImageEvidence.object_key == img["key"]))
        if not existing.scalars().first():
            session.add(
                ImageEvidence(
                    object_key=img["key"],
                    content_hash=f"hash_{uuid7().hex[:16]}",
                    content_type="image/jpeg",
                    document_id=doc.id if doc else None,
                    caption=img["caption"],
                    latitude=img["lat"],
                    longitude=img["lon"],
                    verification_status=img["status"],
                    confidence=img["confidence"],
                    analysis_json=img["analysis"],
                    submitted_by_type="satellite_feed",
                    captured_at=utcnow() - timedelta(days=2),
                )
            )


async def seed_disagreements_and_model_reviews(
    session: AsyncSession, admin_user_id: UUID
) -> None:
    # Model Reviews (Shadow LLM comparison)
    existing_mr = await session.execute(select(ModelReviewResult).limit(1))
    if not existing_mr.scalars().first():
        session.add(
            ModelReviewResult(
                subject_type=ModelReviewSubjectType.RISK_ASSESSMENT,
                subject_id=uuid7(),
                trigger_reason="high_impact_delta_audit",
                primary_model="openai/gpt-4o",
                secondary_model="anthropic/claude-3-5-sonnet",
                primary_final_score=82,
                secondary_final_score=78,
                agreement=True,
                agreement_delta=4,
                secondary_output_json={
                    "rationale": "Secondary model largely concurs with elevated risk trajectory while discounting rhetoric multiplier by 4 points."
                },
            )
        )

    # Analyst Disagreements
    existing_aa = await session.execute(select(AnalystAssessment).limit(1))
    if not existing_aa.scalars().first():
        session.add(
            AnalystAssessment(
                subject_type=DisagreementSubjectType.RISK_ASSESSMENT,
                subject_id=uuid7(),
                analyst_user_id=admin_user_id,
                stance="skeptical",
                score=58.0,
                confidence=0.82,
                rationale="Current missile launch cadences reflect calculated calibrated messaging rather than imminent offensive breakout.",
            )
        )


async def main_async() -> None:
    settings = get_settings()
    session_factory = get_session_factory()

    async with session_factory() as session:
        logger.info("seed_demo.starting")

        # 1. Base Seed
        await _seed_actors(session)
        await _seed_sources(session)
        await _seed_risk_indicators(session)
        await _seed_schedules(session)


        # 2. Identity & Admin Key
        identity = IdentityService(session, settings)
        user = await identity.register_user(
            email="admin@mei.local",
            display_name="Platform Administrator",
            roles=[RoleName.ADMIN],
        )

        issued_key = await identity.issue_api_key(
            user_id=user.id,
            name="admin-demo-key",
            scopes=[str(s) for s in Scope],
        )

        # 3. Extended Actors
        actor_map = await seed_extended_actors(session)

        # 4. Documents & Claims
        doc_map, claim_map = await seed_documents_and_claims(session, actor_map)

        # 5. Events
        await seed_events(session, actor_map)

        # 6. Relationships
        await seed_relationships(session, actor_map)

        # 7. Indicators & Risks
        await seed_indicators_and_risks(session, actor_map)

        # 8. Scenarios
        await seed_scenarios(session, actor_map)

        # 9. Forecasts
        await seed_forecasts(session)

        # 10. Reports
        await seed_reports(session, actor_map)

        # 11. Investigations & Monitors
        await seed_investigations_and_monitors(session, user.id)

        # 12. Review Queue & Imagery
        await seed_review_queue_and_imagery(session, doc_map, claim_map, actor_map)

        # 13. Disagreements & Model Reviews
        await seed_disagreements_and_model_reviews(session, user.id)

        await session.commit()

        logger.info("seed_demo.completed_successfully")
        print("\n" + "=" * 70)
        print("  DEMO GEOPOLITICAL INTELLIGENCE DATA LOADED SUCCESSFULLY! ")
        print("=" * 70)
        print("  All 15 platform sections have been populated with realistic data:")
        print("   - Actors & Aliases (Iran, Israel, Lebanon, Yemen, Houthis, CENTCOM, etc.)")
        print("   - Geospatial Events (Red Sea, Damascus, Hormuz, Lebanon, Riyadh, etc.)")
        print("   - Actor Relationships & Graph Network Topology")
        print("   - Indicator Observations & Computed Risk Models (Risk Engine)")
        print("   - Geopolitical Scenarios & Assessment Branches")
        print("   - Open & Scored Forecasts with Brier Calibration")
        print("   - Intelligence Reports (Executive Daily Brief, Country Brief)")
        print("   - Active Investigations & Timeline Steps")
        print("   - Live Monitors & Notification Triggers")
        print("   - Claims, Evidence Citations & Ingested Documents")
        print("   - Review Queue Decisions Pending Analyst Resolution")
        print("   - Imagery Reconnaissance with Vision Model Output")
        print("   - Multi-Model Reviews & Analyst Disagreements")
        print("-" * 70)
        print(f"  Analyst Admin API Key:\n  {issued_key.plaintext}")
        print("=" * 70 + "\n")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
