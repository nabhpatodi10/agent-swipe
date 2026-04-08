from __future__ import annotations

from typing import Optional
from uuid_utils.compat import UUID

from fastapi_users import schemas
from fastapi_users.schemas import BaseOAuthAccountMixin


class UserRead(BaseOAuthAccountMixin, schemas.BaseUser[UUID]):
    username: str
    full_name: Optional[str] = None


class UserCreate(schemas.BaseUserCreate):
    username: str
    full_name: Optional[str] = None


class UserUpdate(schemas.BaseUserUpdate):
    username: Optional[str] = None
    full_name: Optional[str] = None

