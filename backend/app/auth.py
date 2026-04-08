from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from typing import Optional
from uuid_utils.compat import UUID

from fastapi import Depends, Request, Response
from fastapi_users import FastAPIUsers, exceptions
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.manager import BaseUserManager, UUIDIDMixin
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.exceptions import GetIdEmailError, GetProfileError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_async_session
from app.domain_utils import ensure_liked_collection, ensure_profile_for_user
from app.models import OAuthAccount, RefreshToken, User


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.JWT_SECRET,
        lifetime_seconds=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


async def get_user_db(
    session=Depends(get_async_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase[User, UUID], None]:
    yield SQLAlchemyUserDatabase(session, User, OAuthAccount)


def _hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        settings.REFRESH_TOKEN_COOKIE_NAME,
        refresh_token,
        max_age=max_age,
        httponly=True,
        secure=settings.REFRESH_TOKEN_COOKIE_SECURE,
        samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,
        path="/",
    )


async def _create_refresh_token(
    user: User, session: AsyncSession
) -> str:
    token = secrets.token_urlsafe(64)
    refresh = RefreshToken(
        user_id=user.id,
        token_hash=_hash_refresh_token(token),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    session.add(refresh)
    await session.commit()
    return token


async def rotate_refresh_token(
    token: str, session: AsyncSession
) -> tuple[User, str]:
    token_hash = _hash_refresh_token(token)
    refresh = await session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    if refresh is None:
        raise ValueError("Invalid refresh token")

    now = datetime.now(timezone.utc)
    if refresh.revoked_at is not None or refresh.expires_at <= now:
        raise ValueError("Expired refresh token")

    refresh.revoked_at = now
    session.add(refresh)
    await session.commit()

    user = await session.get(User, refresh.user_id)
    if user is None:
        raise ValueError("User not found")

    new_token = await _create_refresh_token(user, session)
    return user, new_token


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    reset_password_token_secret = settings.JWT_SECRET
    verification_token_secret = settings.JWT_SECRET

    async def _generate_unique_username(self, base: str) -> str:
        candidate = "".join(ch for ch in base.lower() if ch.isalnum() or ch in "._-")
        candidate = candidate.strip("._-") or "user"

        session = self.user_db.session
        existing = await session.scalar(select(User).where(User.username == candidate))
        if existing is None:
            return candidate

        for _ in range(5):
            suffix = secrets.token_hex(2)
            candidate_with_suffix = f"{candidate}_{suffix}"
            existing = await session.scalar(
                select(User).where(User.username == candidate_with_suffix)
            )
            if existing is None:
                return candidate_with_suffix

        return f"{candidate}_{secrets.token_hex(4)}"

    async def oauth_callback(
        self,
        oauth_name: str,
        access_token: str,
        account_id: str,
        account_email: str,
        expires_at: int | None = None,
        refresh_token: str | None = None,
        request: Request | None = None,
        *,
        associate_by_email: bool = False,
        is_verified_by_default: bool = False,
    ) -> User:
        oauth_account_dict = {
            "oauth_name": oauth_name,
            "access_token": access_token,
            "account_id": account_id,
            "account_email": account_email,
            "expires_at": expires_at,
            "refresh_token": refresh_token,
        }

        try:
            user = await self.get_by_oauth_account(oauth_name, account_id)
        except exceptions.UserNotExists:
            try:
                user = await self.get_by_email(account_email)
                if not associate_by_email:
                    raise exceptions.UserAlreadyExists()
                user = await self.user_db.add_oauth_account(user, oauth_account_dict)
            except exceptions.UserNotExists:
                profile = None
                if oauth_name == "google":
                    try:
                        profile = await google_oauth_client.get_profile(access_token)
                    except GetProfileError:
                        profile = None

                full_name = None
                if isinstance(profile, dict):
                    full_name = profile.get("name")

                username_base = account_email.split("@")[0]
                username = await self._generate_unique_username(username_base)

                password = self.password_helper.generate()
                user_dict = {
                    "email": account_email,
                    "hashed_password": self.password_helper.hash(password),
                    "is_verified": is_verified_by_default,
                    "username": username,
                    "full_name": full_name,
                }
                user = await self.user_db.create(user_dict)
                user = await self.user_db.add_oauth_account(user, oauth_account_dict)
                await self.on_after_register(user, request)
        else:
            for existing_oauth_account in user.oauth_accounts:
                if (
                    existing_oauth_account.account_id == account_id
                    and existing_oauth_account.oauth_name == oauth_name
                ):
                    user = await self.user_db.update_oauth_account(
                        user, existing_oauth_account, oauth_account_dict
                    )

        return user

    async def on_after_login(
        self,
        user: User,
        request: Request | None = None,
        response: Response | None = None,
    ) -> None:
        if response is None:
            return
        refresh_token = await _create_refresh_token(user, self.user_db.session)
        _set_refresh_cookie(response, refresh_token)

    async def on_after_register(self, user: User, request: Request | None = None) -> None:
        await ensure_profile_for_user(self.user_db.session, user)
        await ensure_liked_collection(self.user_db.session, user.id)
        await self.user_db.session.commit()


async def get_user_manager(
    user_db=Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)


fastapi_users = FastAPIUsers[User, UUID](get_user_manager, [auth_backend])


class GoogleOIDCOAuth2(GoogleOAuth2):
    async def get_profile(self, token: str) -> dict:
        async with self.get_httpx_client() as client:
            response = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={**self.request_headers, "Authorization": f"Bearer {token}"},
            )
            if response.status_code >= 400:
                raise GetProfileError(response=response)
            return response.json()

    async def get_id_email(self, token: str) -> tuple[str, Optional[str]]:
        try:
            profile = await self.get_profile(token)
        except GetProfileError as e:
            raise GetIdEmailError(response=e.response) from e

        return profile.get("sub", ""), profile.get("email")


google_oauth_client = GoogleOIDCOAuth2(
    settings.GOOGLE_OAUTH_CLIENT_ID,
    settings.GOOGLE_OAUTH_CLIENT_SECRET,
    scopes=["openid", "email", "profile"],
)

