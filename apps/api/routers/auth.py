from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from apps.api.audit import audit
from apps.api.dependencies import SessionDep, SettingsDep
from mei.application.services.identity import IdentityService
from mei.infrastructure.auth.principal import Principal
from mei.shared.errors import UnauthorizedError
from mei.shared.security import API_KEY_PREFIX

router = APIRouter(prefix="/auth", tags=["auth"])

_bearer_scheme = HTTPBearer()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scopes: list[str]


@router.post("/token", response_model=TokenResponse)
async def issue_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer_scheme)],
    session: SessionDep,
    settings: SettingsDep,
) -> TokenResponse:
    """Exchange a durable API key for a short-lived JWT (section 26.1)."""
    if not credentials.credentials.startswith(API_KEY_PREFIX):
        raise UnauthorizedError("Expected an API key (mei_...) to exchange for a token")

    identity_service = IdentityService(session, settings)
    api_key = await identity_service.authenticate_api_key(credentials.credentials)
    access_token = identity_service.issue_access_token(api_key)

    await audit(
        session,
        Principal(user_id=api_key.user_id, scopes=frozenset(api_key.scopes), api_key_id=api_key.id),
        "auth.token_issued",
        resource_type="api_key",
        resource_id=str(api_key.id),
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=settings.jwt_access_token_ttl_seconds,
        scopes=list(api_key.scopes),
    )
