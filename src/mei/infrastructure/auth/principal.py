from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Principal:
    """The authenticated caller of an API request: a user, identified via
    an API key or a JWT minted from one, carrying the scopes it may act with.
    """

    user_id: UUID
    scopes: frozenset[str]
    api_key_id: UUID | None = None

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes


__all__ = ["Principal"]
