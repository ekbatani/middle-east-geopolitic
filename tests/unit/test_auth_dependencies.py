from uuid import uuid4

import pytest

from mei.infrastructure.auth.dependencies import require_scopes
from mei.infrastructure.auth.principal import Principal
from mei.shared.enums import Scope
from mei.shared.errors import ForbiddenError


def _principal(*scopes: Scope) -> Principal:
    return Principal(user_id=uuid4(), scopes=frozenset(str(s) for s in scopes))


def test_require_scopes_allows_when_scope_present() -> None:
    check = require_scopes(Scope.INTELLIGENCE_READ)
    principal = _principal(Scope.INTELLIGENCE_READ)

    assert check(principal) is principal


def test_require_scopes_rejects_when_scope_missing() -> None:
    check = require_scopes(Scope.EVENTS_APPROVE)
    principal = _principal(Scope.INTELLIGENCE_READ)

    with pytest.raises(ForbiddenError):
        check(principal)


def test_require_scopes_requires_all_listed_scopes() -> None:
    check = require_scopes(Scope.INTELLIGENCE_READ, Scope.EVENTS_APPROVE)
    principal = _principal(Scope.INTELLIGENCE_READ)

    with pytest.raises(ForbiddenError):
        check(principal)


def test_principal_has_scope() -> None:
    principal = _principal(Scope.INTELLIGENCE_READ)

    assert principal.has_scope(Scope.INTELLIGENCE_READ)
    assert not principal.has_scope(Scope.EVENTS_APPROVE)
