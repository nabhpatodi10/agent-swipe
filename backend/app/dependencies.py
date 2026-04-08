from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import fastapi_users
from app.db import get_async_session
from app.models import User


CurrentUserDep = Depends(fastapi_users.current_user(active=True))
CurrentSuperuserDep = Depends(fastapi_users.current_user(active=True, superuser=True))
SessionDep = Depends(get_async_session)


async def get_current_active_user(
    user: User = CurrentUserDep,
) -> User:
    return user


async def get_current_superuser(
    user: User = CurrentSuperuserDep,
) -> User:
    return user


async def get_session(session: AsyncSession = SessionDep) -> AsyncSession:
    return session

