from uuid import uuid4

from mei.application.services.entity_resolution import (
    ActorCandidate,
    is_auto_resolvable,
    rank_candidates,
)

_IRAN_ID = uuid4()
_IRAQ_ID = uuid4()
_HEZBOLLAH_ID = uuid4()


def _pool() -> list[ActorCandidate]:
    return [
        ActorCandidate(
            actor_id=_IRAN_ID, canonical_name="Iran", aliases=("Islamic Republic of Iran",)
        ),
        ActorCandidate(actor_id=_IRAQ_ID, canonical_name="Iraq"),
        ActorCandidate(
            actor_id=_HEZBOLLAH_ID,
            canonical_name="Hezbollah",
            aliases=("Hizbullah", "Party of God"),
        ),
    ]


def test_exact_name_ranks_first_with_top_score() -> None:
    ranked = rank_candidates("Iran", _pool())
    assert ranked[0].actor_id == _IRAN_ID
    assert ranked[0].score == 100.0


def test_alias_match_ranks_candidate_highly() -> None:
    ranked = rank_candidates("Hizbullah", _pool())
    assert ranked[0].actor_id == _HEZBOLLAH_ID
    assert ranked[0].score >= 90.0


def test_close_misspelling_still_ranks_correct_candidate_first() -> None:
    ranked = rank_candidates("Irn", _pool())
    assert ranked[0].actor_id == _IRAN_ID


def test_ranking_is_sorted_descending() -> None:
    ranked = rank_candidates("Iraq", _pool())
    scores = [c.score for c in ranked]
    assert scores == sorted(scores, reverse=True)


def test_is_auto_resolvable_true_for_clear_high_confidence_match() -> None:
    ranked = rank_candidates("Iran", _pool())
    assert is_auto_resolvable(ranked, auto_threshold=92.0) is True


def test_is_auto_resolvable_false_when_below_threshold() -> None:
    ranked = rank_candidates("Completely unrelated string", _pool())
    assert is_auto_resolvable(ranked, auto_threshold=92.0) is False


def test_is_auto_resolvable_false_for_empty_candidate_pool() -> None:
    assert is_auto_resolvable([], auto_threshold=92.0) is False


def test_is_auto_resolvable_false_when_top_two_are_close() -> None:
    pool = [
        ActorCandidate(actor_id=uuid4(), canonical_name="Al-Amal Group"),
        ActorCandidate(actor_id=uuid4(), canonical_name="Al-Amal Movement"),
    ]
    ranked = rank_candidates("Al-Amal", pool)
    assert ranked[0].score - ranked[1].score < 5.0
    assert is_auto_resolvable(ranked, auto_threshold=85.0) is False
