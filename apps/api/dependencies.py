from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from mei.infrastructure.auth.dependencies import PrincipalDep, require_scopes
from mei.infrastructure.database.session import get_session
from mei.shared.config import Settings, get_settings

SettingsDep = Annotated[Settings, Depends(get_settings)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]

__all__ = ["PrincipalDep", "SessionDep", "SettingsDep", "require_scopes"]
