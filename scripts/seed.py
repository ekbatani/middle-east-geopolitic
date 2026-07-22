"""Idempotent seed-data loader.

Loads the core actor set from `configs/actors.seed.yml` (skipping actors
that already exist by canonical name) and provisions the local-development
identity: an admin user plus one API key per Hermes credential tier
described in section 23.7 of the implementation design. Re-running is safe
for actors; API keys are minted fresh each run since they're secrets that
should only ever be printed once.
"""

import asyncio
from pathlib import Path

import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from mei.application.services.identity import IdentityService
from mei.infrastructure.database.session import get_session_factory
from mei.infrastructure.repositories.actors import ActorRepository
from mei.infrastructure.repositories.indicators import IndicatorRepository
from mei.infrastructure.repositories.risks import RiskRepository
from mei.infrastructure.repositories.sources import SourceRepository
from mei.shared.config import get_settings
from mei.shared.enums import (
    ActorType,
    EndpointType,
    IndicatorDirection,
    IndicatorNormalizationMethod,
    RoleName,
    Scope,
    SourceType,
)
from mei.shared.logging import configure_logging, get_logger

configure_logging(json_output=False)
logger = get_logger(__name__)

ADMIN_EMAIL = "admin@mei.local"
CONFIGS_DIR = Path(__file__).resolve().parent.parent / "configs"
ACTORS_SEED_PATH = CONFIGS_DIR / "actors.seed.yml"
SOURCE_POLICY_PATH = CONFIGS_DIR / "source-policy.yml"
RISK_INDICATORS_PATH = CONFIGS_DIR / "risk-indicators.yml"

API_KEY_SCOPES: dict[str, list[Scope]] = {
    "admin": list(Scope),
    "hermes-read": [Scope.INTELLIGENCE_READ, Scope.INVESTIGATIONS_READ],
    "hermes-analyst": [
        Scope.INTELLIGENCE_READ,
        Scope.SOURCES_SUBMIT,
        Scope.CLAIMS_CREATE,
        Scope.EVENTS_CREATE,
        Scope.INVESTIGATIONS_CREATE,
        Scope.INVESTIGATIONS_READ,
        Scope.MONITORS_MANAGE,
    ],
    "hermes-approver": [
        Scope.INTELLIGENCE_READ,
        Scope.EVENTS_APPROVE,
        Scope.CLAIMS_ASSESS,
        Scope.REPORTS_APPROVE,
    ],
}


async def _seed_actors(session: AsyncSession) -> None:
    repo = ActorRepository(session)
    raw = yaml.safe_load(ACTORS_SEED_PATH.read_text(encoding="utf-8"))

    created = 0
    for entry in raw.get("actors", []):
        canonical_name = entry["canonical_name"]
        if await repo.get_by_canonical_name(canonical_name) is not None:
            continue
        await repo.create(
            canonical_name=canonical_name,
            actor_type=ActorType(entry["actor_type"]),
            native_name=entry.get("native_name"),
        )
        created += 1

    logger.info("seed.actors_loaded", created=created, total=len(raw.get("actors", [])))


async def _seed_sources(session: AsyncSession) -> None:
    repo = SourceRepository(session)
    raw = yaml.safe_load(SOURCE_POLICY_PATH.read_text(encoding="utf-8"))

    created = 0
    for entry in raw.get("sources", []):
        base_url = entry["base_url"]
        if await repo.get_by_base_url(base_url) is not None:
            continue

        source = await repo.create(
            name=entry["name"],
            source_type=SourceType(entry["source_type"]),
            base_url=base_url,
            default_language=entry.get("default_language"),
        )
        for endpoint in entry.get("endpoints", []):
            await repo.create_endpoint(
                source_id=source.id,
                endpoint_type=EndpointType.RSS,
                url=endpoint["url"],
                schedule=endpoint.get("schedule"),
            )
        created += 1

    logger.info("seed.sources_loaded", created=created, total=len(raw.get("sources", [])))


async def _seed_risk_indicators(session: AsyncSession) -> None:
    indicators_repo = IndicatorRepository(session)
    risks_repo = RiskRepository(session)
    raw = yaml.safe_load(RISK_INDICATORS_PATH.read_text(encoding="utf-8"))

    indicators_created = 0
    for entry in raw.get("indicators", []):
        code = entry["code"]
        if await indicators_repo.get_definition_by_code(code) is not None:
            continue
        await indicators_repo.create_definition(
            code=code,
            name=entry["name"],
            category=entry["category"],
            value_type=entry["value_type"],
            normalization_method=IndicatorNormalizationMethod(entry["normalization_method"]),
            lower_bound=entry.get("lower_bound"),
            upper_bound=entry.get("upper_bound"),
            staleness_hours=entry.get("staleness_hours"),
        )
        indicators_created += 1

    definitions_created = 0
    for entry in raw.get("risk_definitions", []):
        code = entry["code"]
        definition = await risks_repo.get_definition_by_code(code)
        if definition is None:
            definition = await risks_repo.create_definition(
                code=code,
                name=entry["name"],
                description=entry.get("description"),
                scope_types=list(entry["scope_types"]),
            )
            definitions_created += 1

        for weight_entry in entry.get("weights", []):
            indicator = await indicators_repo.get_definition_by_code(weight_entry["indicator_code"])
            if indicator is None:
                continue
            await risks_repo.set_weight(
                risk_definition_id=definition.id,
                indicator_definition_id=indicator.id,
                weight=weight_entry["weight"],
                direction=IndicatorDirection(weight_entry.get("direction", "positive")),
            )

    logger.info(
        "seed.risk_indicators_loaded",
        indicators_created=indicators_created,
        risk_definitions_created=definitions_created,
    )


async def main_async() -> None:
    settings = get_settings()
    session_factory = get_session_factory()

    async with session_factory() as session:
        await _seed_actors(session)
        await _seed_sources(session)
        await _seed_risk_indicators(session)

        identity = IdentityService(session, settings)
        user = await identity.register_user(
            email=ADMIN_EMAIL, display_name="Platform Administrator", roles=[RoleName.ADMIN]
        )

        for key_name, scopes in API_KEY_SCOPES.items():
            issued = await identity.issue_api_key(
                user_id=user.id, name=key_name, scopes=[str(scope) for scope in scopes]
            )
            logger.info("seed.api_key_issued", name=key_name, plaintext=issued.plaintext)

        await session.commit()


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
