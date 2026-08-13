from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.identity.models import ApiKey, User
from mei.infrastructure.repositories.identity import IdentityRepository
from mei.shared.config import Settings
from mei.shared.enums import RoleName, UserStatus
from mei.shared.errors import UnauthorizedError
from mei.shared.security import (
    API_KEY_PREFIX,
    encode_access_token,
    generate_api_key,
    hash_api_key,
)
from mei.shared.time import utcnow


@dataclass(frozen=True)
class IssuedApiKey:
    api_key: ApiKey
    plaintext: str

    @property
    def key_id(self) -> UUID:
        return self.api_key.id


class IdentityService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._repo = IdentityRepository(session)

    async def register_user(self, *, email: str, display_name: str, roles: list[RoleName]) -> User:
        user = await self._repo.get_user_by_email(email)
        if user is None:
            user = await self._repo.create_user(email=email, display_name=display_name)

        for role_name in roles:
            role = await self._repo.get_or_create_role(role_name)
            await self._repo.assign_role(user_id=user.id, role_id=role.id)

        return user

    async def issue_api_key(self, *, user_id: UUID, name: str, scopes: list[str]) -> IssuedApiKey:
        plaintext = generate_api_key()
        api_key = await self._repo.create_api_key(
            user_id=user_id,
            name=name,
            key_hash=hash_api_key(plaintext),
            scopes=scopes,
        )
        return IssuedApiKey(api_key=api_key, plaintext=plaintext)

    async def authenticate_api_key(self, plaintext: str) -> ApiKey:
        if not plaintext.startswith(API_KEY_PREFIX):
            raise UnauthorizedError("Malformed API key")

        api_key = await self._repo.find_api_key_by_plaintext(plaintext)
        if api_key is None:
            raise UnauthorizedError("Invalid API key")

        if api_key.expires_at is not None and api_key.expires_at < utcnow():
            raise UnauthorizedError("API key has expired")

        user = await self._repo.get_user(api_key.user_id)
        if user is None or user.status != UserStatus.ACTIVE:
            raise UnauthorizedError("User account is not active")

        await self._repo.touch_api_key(api_key, used_at=utcnow())
        return api_key

    def issue_access_token(self, api_key: ApiKey) -> str:
        return encode_access_token(
            subject=str(api_key.user_id),
            scopes=list(api_key.scopes),
            secret_key=self._settings.app_secret_key,
            issuer=self._settings.jwt_issuer,
            audience=self._settings.jwt_audience,
            ttl_seconds=self._settings.jwt_access_token_ttl_seconds,
        )


__all__ = ["IdentityService", "IssuedApiKey"]
