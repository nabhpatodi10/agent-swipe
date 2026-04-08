from __future__ import annotations

import secrets
from urllib.parse import quote

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi_users.router.common import ErrorCode
from fastapi_users.router.oauth import (
    CSRF_TOKEN_COOKIE_NAME,
    CSRF_TOKEN_KEY,
    STATE_TOKEN_AUDIENCE,
    generate_csrf_token,
    generate_state_token,
)
from fastapi_users.jwt import decode_jwt

from app.auth import auth_backend, get_user_manager, google_oauth_client
from app.config import settings


router = APIRouter(prefix="/auth/google", tags=["auth"])


def _frontend_callback_url() -> str:
    return f"{settings.FRONTEND_APP_URL.rstrip('/')}/oauth/google/callback"


def _redirect_with_error(error: str) -> RedirectResponse:
    url = f"{_frontend_callback_url()}#error={quote(error)}"
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/authorize")
async def authorize_google(
    response: Response,
    scopes: list[str] = Query(default=["openid", "email", "profile"]),
) -> dict[str, str]:
    csrf_token = generate_csrf_token()
    state = generate_state_token({CSRF_TOKEN_KEY: csrf_token}, settings.JWT_SECRET)
    authorization_url = await google_oauth_client.get_authorization_url(
        settings.GOOGLE_OAUTH_REDIRECT_URI,
        state,
        scopes,
    )

    response.set_cookie(
        CSRF_TOKEN_COOKIE_NAME,
        csrf_token,
        max_age=3600,
        path="/",
        secure=settings.REFRESH_TOKEN_COOKIE_SECURE,
        httponly=True,
        samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,
    )
    return {"authorization_url": authorization_url}


@router.get("/callback")
async def callback_google(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    user_manager=Depends(get_user_manager),
    strategy=Depends(auth_backend.get_strategy),
) -> Response:
    try:
        state_data = decode_jwt(state, settings.JWT_SECRET, [STATE_TOKEN_AUDIENCE])
    except jwt.DecodeError:
        return _redirect_with_error(ErrorCode.ACCESS_TOKEN_DECODE_ERROR)
    except jwt.ExpiredSignatureError:
        return _redirect_with_error(ErrorCode.ACCESS_TOKEN_ALREADY_EXPIRED)

    cookie_csrf_token = request.cookies.get(CSRF_TOKEN_COOKIE_NAME)
    state_csrf_token = state_data.get(CSRF_TOKEN_KEY)
    if (
        not cookie_csrf_token
        or not state_csrf_token
        or not secrets.compare_digest(cookie_csrf_token, state_csrf_token)
    ):
        return _redirect_with_error(ErrorCode.OAUTH_INVALID_STATE)

    try:
        token = await google_oauth_client.get_access_token(
            code, settings.GOOGLE_OAUTH_REDIRECT_URI
        )
        account_id, account_email = await google_oauth_client.get_id_email(
            token["access_token"]
        )
    except Exception:
        return _redirect_with_error("oauth_exchange_failed")

    if account_email is None:
        return _redirect_with_error(ErrorCode.OAUTH_NOT_AVAILABLE_EMAIL)

    try:
        user = await user_manager.oauth_callback(
            google_oauth_client.name,
            token["access_token"],
            account_id,
            account_email,
            token.get("expires_at"),
            token.get("refresh_token"),
            request,
            associate_by_email=True,
            is_verified_by_default=True,
        )
    except Exception:
        return _redirect_with_error(ErrorCode.OAUTH_USER_ALREADY_EXISTS)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
        )

    access_token = await strategy.write_token(user)
    redirect_url = (
        f"{_frontend_callback_url()}#access_token={quote(access_token)}&token_type=bearer"
    )
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    await user_manager.on_after_login(user, request, response)
    response.delete_cookie(
        CSRF_TOKEN_COOKIE_NAME,
        path="/",
        secure=settings.REFRESH_TOKEN_COOKIE_SECURE,
        httponly=True,
        samesite=settings.REFRESH_TOKEN_COOKIE_SAMESITE,
    )
    return response

