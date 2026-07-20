from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from mei.application.services.identity import IdentityService
from mei.infrastructure.auth.principal import Principal
from mei.infrastructure.database.session import get_session
from mei.shared.config import Settings, get_settings
from mei.shared.errors import ForbiddenError, UnauthorizedError
from mei.shared.security import API_KEY_PREFIX, decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Principal:
    """Authenticate via either a bearer API key or a JWT minted from one.

    API keys (`mei_...`) are the durable credential; the JWT is a
    short-lived session token exchanged for one via `POST /auth/token`
    (section 26.1 of the implementation design).
    """
    if credentials is None:
        raise UnauthorizedError("Missing bearer token")

    token = credentials.credentials

    if token.startswith(API_KEY_PREFIX):
        identity_service = IdentityService(session, settings)
        api_key = await identity_service.authenticate_api_key(token)
        return Principal(
            user_id=api_key.user_id, scopes=frozenset(api_key.scopes), api_key_id=api_key.id
        )

    try:
        payload = decode_access_token(
            token,
            secret_key=settings.app_secret_key,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
    except Exception as exc:
        raise UnauthorizedError("Invalid or expired access token") from exc

    return Principal(user_id=UUID(payload["sub"]), scopes=frozenset(payload.get("scopes", [])))


PrincipalDep = Annotated[Principal, Depends(get_current_principal)]


def require_scopes(*required: str) -> Callable[[PrincipalDep], Principal]:
    """Build a dependency that authenticates and requires every scope in `required`."""

    def _check(principal: PrincipalDep) -> Principal:
        missing = [scope for scope in required if not principal.has_scope(scope)]
        if missing:
            raise ForbiddenError(f"Missing required scope(s): {', '.join(missing)}")
        return principal

    return _check


__all__ = ["PrincipalDep", "get_current_principal", "require_scopes"]
