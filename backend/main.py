from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from app.auth import (
    auth_backend,
    fastapi_users,
    rotate_refresh_token,
    _set_refresh_cookie,
)
from app.config import settings
from app.db import get_async_session
from app.routers import (
    admin_router,
    agent_auth_router,
    agents_router,
    collections_router,
    follows_router,
    google_oauth_router,
    profiles_router,
    reports_router,
    social_router,
    swipe_router,
)
from app.schemas import UserCreate, UserRead, UserUpdate

app = FastAPI(title="Agent Swipe API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

app.include_router(google_oauth_router)

app.include_router(profiles_router)
app.include_router(agents_router)
app.include_router(agent_auth_router)
app.include_router(swipe_router)
app.include_router(collections_router)
app.include_router(social_router)
app.include_router(follows_router)
app.include_router(reports_router)
app.include_router(admin_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/refresh", tags=["auth"])
async def refresh_access_token(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_async_session),
    strategy=Depends(auth_backend.get_strategy),
):
    token = request.cookies.get(settings.REFRESH_TOKEN_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        user, new_refresh = await rotate_refresh_token(token, session)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    access_token = await strategy.write_token(user)
    _set_refresh_cookie(response, new_refresh)
    return {"access_token": access_token, "token_type": "bearer"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
