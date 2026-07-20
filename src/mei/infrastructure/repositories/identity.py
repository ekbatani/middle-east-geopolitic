from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mei.domain.identity.models import ApiKey, Role, User, UserRole
from mei.shared.security import verify_api_key


class IdentityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_user(self, user_id: UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_user(self, *, email: str, display_name: str) -> User:
        user = User(email=email, display_name=display_name)
        self._session.add(user)
        await self._session.flush()
        return user

    async def get_or_create_role(self, name: str) -> Role:
        result = await self._session.execute(select(Role).where(Role.name == name))
        role = result.scalar_one_or_none()
        if role is None:
            role = Role(name=name)
            self._session.add(role)
            await self._session.flush()
        return role

    async def assign_role(self, *, user_id: UUID, role_id: UUID) -> None:
        existing = await self._session.get(UserRole, (user_id, role_id))
        if existing is None:
            self._session.add(UserRole(user_id=user_id, role_id=role_id))
            await self._session.flush()

    async def create_api_key(
        self,
        *,
        user_id: UUID,
        name: str,
        key_hash: str,
        scopes: list[str],
        expires_at: datetime | None = None,
    ) -> ApiKey:
        api_key = ApiKey(
            user_id=user_id, name=name, key_hash=key_hash, scopes=scopes, expires_at=expires_at
        )
        self._session.add(api_key)
        await self._session.flush()
        return api_key

    async def find_api_key_by_plaintext(self, plaintext: str) -> ApiKey | None:
        """Resolve an API key credential to its row.

        `key_hash` is an argon2 hash, which is salted and therefore cannot
        be looked up by equality. The active key set is small and
        admin-managed, so a linear scan is an acceptable trade-off.
        """
        result = await self._session.execute(select(ApiKey).where(ApiKey.revoked_at.is_(None)))
        for api_key in result.scalars():
            if verify_api_key(plaintext, api_key.key_hash):
                return api_key
        return None

    async def touch_api_key(self, api_key: ApiKey, *, used_at: datetime) -> None:
        api_key.last_used_at = used_at
        await self._session.flush()


__all__ = ["IdentityRepository"]
