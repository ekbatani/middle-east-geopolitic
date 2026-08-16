from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from mei.application.services.review import ReviewService
from mei.domain.actors.models import Actor
from mei.domain.claims.models import Claim
from mei.domain.review.models import ReviewItem
from mei.infrastructure.auth.principal import Principal
from mei.shared.enums import ActorType, ReviewStatus, ReviewType
from mei.shared.errors import ConflictError, NotFoundError


def _principal() -> Principal:
    return Principal(user_id=uuid4(), scopes=frozenset(["review:resolve"]))


@pytest.mark.asyncio
async def test_resolve_entity_resolution_with_event_target() -> None:
    session = AsyncMock()
    service = ReviewService(session)

    item_id = uuid4()
    actor_id = uuid4()
    event_id = uuid4()

    item = ReviewItem(
        id=item_id,
        review_type=ReviewType.ENTITY_RESOLUTION,
        status=ReviewStatus.PENDING,
        subject_json={
            "candidate_name": "Test Militia",
            "link_kind": "event_actor",
            "target_type": "event",
            "target_id": str(event_id),
            "event_role": "attacker",
        },
        candidates_json=[],
    )
    actor = Actor(id=actor_id, canonical_name="Test Militia Org", actor_type=ActorType.ARMED_GROUP)

    service._review.get = AsyncMock(return_value=item)
    service._actors.get = AsyncMock(return_value=actor)
    service._events.add_actor = AsyncMock()
    service._review.resolve = AsyncMock()

    result = await service.resolve_entity_resolution(
        item_id, resolved_actor_id=actor_id, principal=_principal()
    )

    assert result is item
    service._events.add_actor.assert_awaited_once_with(
        event_id=event_id, actor_id=actor_id, role="attacker"
    )
    service._review.resolve.assert_awaited_once()


@pytest.mark.asyncio
async def test_resolve_entity_resolution_with_claim_target() -> None:
    session = AsyncMock()
    service = ReviewService(session)

    item_id = uuid4()
    actor_id = uuid4()
    claim_id = uuid4()

    item = ReviewItem(
        id=item_id,
        review_type=ReviewType.ENTITY_RESOLUTION,
        status=ReviewStatus.PENDING,
        subject_json={
            "candidate_name": "Test Militia",
            "link_kind": "subject",
            "target_type": "claim",
            "target_id": str(claim_id),
        },
        candidates_json=[],
    )
    actor = Actor(id=actor_id, canonical_name="Test Militia Org", actor_type=ActorType.ARMED_GROUP)
    claim = Claim(id=claim_id, claim_text="Test claim text")

    service._review.get = AsyncMock(return_value=item)
    service._actors.get = AsyncMock(return_value=actor)
    service._claims.get = AsyncMock(return_value=claim)
    service._claims.set_actor = AsyncMock()
    service._review.resolve = AsyncMock()

    result = await service.resolve_entity_resolution(
        item_id, resolved_actor_id=actor_id, principal=_principal()
    )

    assert result is item
    service._claims.set_actor.assert_awaited_once_with(claim, role="subject", actor_id=actor_id)
    service._review.resolve.assert_awaited_once()


@pytest.mark.asyncio
async def test_resolve_entity_resolution_without_target_links_succeeds_without_key_error() -> None:
    session = AsyncMock()
    service = ReviewService(session)

    item_id = uuid4()
    actor_id = uuid4()

    # Subject without link_kind, target_type, or target_id (e.g. seeded demo item or unlinked mention)
    item = ReviewItem(
        id=item_id,
        review_type=ReviewType.ENTITY_RESOLUTION,
        status=ReviewStatus.PENDING,
        subject_json={
            "extracted_name": "Kata'ib Sayyid al-Shuhada",
            "context": "Statement claiming responsibility",
        },
        candidates_json=[],
    )
    actor = Actor(id=actor_id, canonical_name="Islamic Resistance in Iraq", actor_type=ActorType.ARMED_GROUP)

    service._review.get = AsyncMock(return_value=item)
    service._actors.get = AsyncMock(return_value=actor)
    service._review.resolve = AsyncMock()

    result = await service.resolve_entity_resolution(
        item_id, resolved_actor_id=actor_id, principal=_principal()
    )

    assert result is item
    service._review.resolve.assert_awaited_once()


@pytest.mark.asyncio
async def test_resolve_entity_resolution_with_incomplete_target_raises_conflict() -> None:
    session = AsyncMock()
    service = ReviewService(session)

    item_id = uuid4()
    actor_id = uuid4()

    # Incomplete target: link_kind is provided without target_type/target_id
    item = ReviewItem(
        id=item_id,
        review_type=ReviewType.ENTITY_RESOLUTION,
        status=ReviewStatus.PENDING,
        subject_json={
            "candidate_name": "Test Militia",
            "link_kind": "subject",
        },
        candidates_json=[],
    )
    actor = Actor(id=actor_id, canonical_name="Test Militia Org", actor_type=ActorType.ARMED_GROUP)

    service._review.get = AsyncMock(return_value=item)
    service._actors.get = AsyncMock(return_value=actor)

    with pytest.raises(ConflictError, match="Incomplete review subject"):
        await service.resolve_entity_resolution(
            item_id, resolved_actor_id=actor_id, principal=_principal()
        )


@pytest.mark.asyncio
async def test_resolve_entity_resolution_with_unsupported_link_kind_raises_conflict() -> None:
    session = AsyncMock()
    service = ReviewService(session)

    item_id = uuid4()
    actor_id = uuid4()
    claim_id = uuid4()

    item = ReviewItem(
        id=item_id,
        review_type=ReviewType.ENTITY_RESOLUTION,
        status=ReviewStatus.PENDING,
        subject_json={
            "candidate_name": "Test Militia",
            "link_kind": "invalid_kind",
            "target_type": "claim",
            "target_id": str(claim_id),
        },
        candidates_json=[],
    )
    actor = Actor(id=actor_id, canonical_name="Test Militia Org", actor_type=ActorType.ARMED_GROUP)

    service._review.get = AsyncMock(return_value=item)
    service._actors.get = AsyncMock(return_value=actor)

    with pytest.raises(ConflictError, match="Unsupported review subject"):
        await service.resolve_entity_resolution(
            item_id, resolved_actor_id=actor_id, principal=_principal()
        )


@pytest.mark.asyncio
async def test_resolve_entity_resolution_actor_not_found_raises_not_found() -> None:
    session = AsyncMock()
    service = ReviewService(session)

    item_id = uuid4()
    actor_id = uuid4()

    item = ReviewItem(
        id=item_id,
        review_type=ReviewType.ENTITY_RESOLUTION,
        status=ReviewStatus.PENDING,
        subject_json={},
        candidates_json=[],
    )

    service._review.get = AsyncMock(return_value=item)
    service._actors.get = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError, match="Actor .* not found"):
        await service.resolve_entity_resolution(
            item_id, resolved_actor_id=actor_id, principal=_principal()
        )


@pytest.mark.asyncio
async def test_resolve_entity_resolution_wrong_review_type_raises_conflict() -> None:
    session = AsyncMock()
    service = ReviewService(session)

    item_id = uuid4()
    actor_id = uuid4()

    item = ReviewItem(
        id=item_id,
        review_type=ReviewType.HIGH_IMPACT_EVENT,
        status=ReviewStatus.PENDING,
        subject_json={},
        candidates_json=[],
    )

    service._review.get = AsyncMock(return_value=item)

    with pytest.raises(ConflictError, match="not an entity-resolution item"):
        await service.resolve_entity_resolution(
            item_id, resolved_actor_id=actor_id, principal=_principal()
        )


@pytest.mark.asyncio
async def test_acknowledge_high_impact_event_success() -> None:
    session = AsyncMock()
    service = ReviewService(session)

    item_id = uuid4()
    item = ReviewItem(
        id=item_id,
        review_type=ReviewType.HIGH_IMPACT_EVENT,
        status=ReviewStatus.PENDING,
        subject_json={"event_title": "Missile launch"},
        candidates_json=[],
    )

    service._review.get = AsyncMock(return_value=item)
    service._review.resolve = AsyncMock()

    result = await service.acknowledge_high_impact_event(
        item_id, principal=_principal(), note="Acknowledged by analyst"
    )

    assert result is item
    service._review.resolve.assert_awaited_once()


@pytest.mark.asyncio
async def test_reject_review_item_success() -> None:
    session = AsyncMock()
    service = ReviewService(session)

    item_id = uuid4()
    item = ReviewItem(
        id=item_id,
        review_type=ReviewType.ENTITY_RESOLUTION,
        status=ReviewStatus.PENDING,
        subject_json={},
        candidates_json=[],
    )

    service._review.get = AsyncMock(return_value=item)
    service._review.resolve = AsyncMock()

    result = await service.reject(item_id, principal=_principal())

    assert result is item
    service._review.resolve.assert_awaited_once()


@pytest.mark.asyncio
async def test_already_resolved_item_raises_conflict() -> None:
    session = AsyncMock()
    service = ReviewService(session)

    item_id = uuid4()
    item = ReviewItem(
        id=item_id,
        review_type=ReviewType.ENTITY_RESOLUTION,
        status=ReviewStatus.APPROVED,
        subject_json={},
        candidates_json=[],
    )

    service._review.get = AsyncMock(return_value=item)

    with pytest.raises(ConflictError, match="already approved"):
        await service.resolve_entity_resolution(
            item_id, resolved_actor_id=uuid4(), principal=_principal()
        )
