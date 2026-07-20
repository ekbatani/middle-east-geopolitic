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
from mei.shared.config import get_settings
from mei.shared.enums import ActorType, RoleName, Scope
from mei.shared.logging import configure_logging, get_logger

configure_logging(json_output=False)
logger = get_logger(__name__)

ADMIN_EMAIL = "admin@mei.local"
ACTORS_SEED_PATH = Path(__file__).resolve().parent.parent / "configs" / "actors.seed.yml"

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


async def main_async() -> None:
    settings = get_settings()
    session_factory = get_session_factory()

    async with session_factory() as session:
        await _seed_actors(session)

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
