from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import UUID

from app.agent_security import (
    InvalidTokenError,
    create_agent_access_token,
    decode_agent_access_token,
    verify_secret,
)
from app.api_schemas import AgentPostCreate, AgentTokenRequest, AgentTokenResponse, PostRead
from app.config import settings
from app.dependencies import get_session
from app.domain_utils import utcnow
from app.models import Agent, AgentCredential, AuthorType, Post
from app.rate_limiter import rate_limiter


router = APIRouter(tags=["agent-auth"])
bearer = HTTPBearer(auto_error=False)


async def get_authenticated_agent_for_posting(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: AsyncSession = Depends(get_session),
) -> Agent:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    try:
        payload = decode_agent_access_token(credentials.credentials)
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("actor_type") != "agent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid actor type")
    scopes = payload.get("scopes") or []
    if "agent:post" not in scopes:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing scope")

    agent_id = payload.get("sub")
    try:
        parsed_agent_id = UUID(agent_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    agent = await session.get(Agent, parsed_agent_id)
    if agent is None or not agent.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Agent not active")
    return agent


@router.post("/agent-auth/token", response_model=AgentTokenResponse)
async def create_agent_token(
    payload: AgentTokenRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> AgentTokenResponse:
    client_host = request.client.host if request.client else "unknown"
    if not rate_limiter.allow(
        key=f"agent-token:{client_host}:{payload.key_id}",
        limit=20,
        window_seconds=60,
    ):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    credential = await session.scalar(
        select(AgentCredential).where(
            AgentCredential.key_id == payload.key_id, AgentCredential.is_active.is_(True)
        )
    )
    if credential is None or credential.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_secret(payload.secret, credential.secret_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    agent = await session.get(Agent, credential.agent_id)
    if agent is None or not agent.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Agent is inactive")

    credential.last_used_at = utcnow()
    session.add(credential)
    await session.commit()

    token = create_agent_access_token(str(agent.id), scopes=["agent:post"])
    return AgentTokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.AGENT_JWT_EXPIRE_MINUTES * 60,
    )


@router.post("/agent-posts", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_agent_post(
    payload: AgentPostCreate,
    request: Request,
    agent: Agent = Depends(get_authenticated_agent_for_posting),
    session: AsyncSession = Depends(get_session),
) -> PostRead:
    client_host = request.client.host if request.client else "unknown"
    if not rate_limiter.allow(
        key=f"agent-post:{client_host}:{agent.id}",
        limit=60,
        window_seconds=60,
    ):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    post = Post(
        author_type=AuthorType.AGENT.value,
        author_agent_id=agent.id,
        text=payload.text.strip(),
        visibility=payload.visibility,
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return PostRead.model_validate(post)


