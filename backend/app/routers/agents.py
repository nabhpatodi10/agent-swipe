from __future__ import annotations

from datetime import datetime
import ipaddress
import time
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
import httpx
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import UUID

from app.agent_security import generate_key_id, generate_secret, hash_secret
from app.api_schemas import (
    AgentCreate,
    AgentCredentialCreate,
    AgentCredentialRead,
    AgentCredentialSecretRead,
    AgentRead,
    AgentUpdate,
    DemoChatRequest,
    DemoChatResponse,
    VerificationRequestCreate,
    VerificationRequestRead,
)
from app.config import settings
from app.dependencies import get_current_active_user, get_session
from app.domain_utils import ensure_unique_agent_slug, utcnow
from app.models import (
    Agent,
    AgentCredential,
    DemoSessionLog,
    User,
    VerificationRequest,
    VerificationRequestStatus,
    VerificationStatus,
)
from app.rate_limiter import rate_limiter


router = APIRouter(prefix="/agents", tags=["agents"])


async def _get_agent_or_404(session: AsyncSession, agent_id: UUID) -> Agent:
    agent = await session.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


def _normalize_skills(skills: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for skill in skills:
        normalized = skill.strip()
        if not normalized:
            continue
        lowered = normalized.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        result.append(normalized)
    return result


def _assert_owner(agent: Agent, user: User) -> None:
    if str(agent.owner_user_id) != str(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can perform this action.",
        )


def _is_private_host(hostname: str | None) -> bool:
    if not hostname:
        return True
    lowered = hostname.lower()
    if lowered in {"localhost"}:
        return True
    try:
        ip = ipaddress.ip_address(lowered)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
        )
    except ValueError:
        return False


def _validate_request_url(url: str | None) -> str | None:
    if url is None:
        return None
    normalized = url.strip()
    if not normalized:
        return None

    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="request_url must be a valid http/https URL.",
        )

    # Secure-cookie mode is treated as production mode for stricter URL safety.
    if settings.REFRESH_TOKEN_COOKIE_SECURE:
        if parsed.scheme != "https":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="request_url must use https in production.",
            )
        if _is_private_host(parsed.hostname):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="request_url cannot point to localhost/private networks in production.",
            )

    return normalized


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
async def create_agent(
    payload: AgentCreate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> AgentRead:
    skills = _normalize_skills(payload.skills)
    if not skills:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="At least one skill is required.")

    slug = await ensure_unique_agent_slug(session, payload.name)
    agent = Agent(
        owner_user_id=user.id,
        name=payload.name.strip(),
        slug=slug,
        description=payload.description.strip(),
        skills=skills,
        category=payload.category.strip(),
        github_url=payload.github_url,
        website_url=payload.website_url,
        request_url=_validate_request_url(payload.request_url),
        pricing_model=payload.pricing_model,
        free_tier_available=payload.free_tier_available,
        free_tier_notes=payload.free_tier_notes,
        is_public=payload.is_public,
        verification_status=VerificationStatus.UNVERIFIED.value,
    )
    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return AgentRead.model_validate(agent)


@router.patch("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: UUID,
    payload: AgentUpdate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> AgentRead:
    agent = await _get_agent_or_404(session, agent_id)
    _assert_owner(agent, user)

    data = payload.model_dump(exclude_unset=True)
    if "skills" in data and data["skills"] is not None:
        data["skills"] = _normalize_skills(data["skills"])
        if not data["skills"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one skill is required.",
            )

    if "name" in data and data["name"]:
        data["slug"] = await ensure_unique_agent_slug(
            session, data["name"], current_agent_id=str(agent.id)
        )
    if "request_url" in data:
        data["request_url"] = _validate_request_url(data["request_url"])

    for key, value in data.items():
        setattr(agent, key, value)
    agent.updated_at = utcnow()

    session.add(agent)
    await session.commit()
    await session.refresh(agent)
    return AgentRead.model_validate(agent)


@router.get("/mine", response_model=list[AgentRead])
async def list_my_agents(
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> list[AgentRead]:
    agents = (
        await session.scalars(
            select(Agent)
            .where(Agent.owner_user_id == user.id)
            .order_by(Agent.created_at.desc())
        )
    ).all()
    return [AgentRead.model_validate(agent) for agent in agents]


@router.get("/discover", response_model=list[AgentRead])
async def discover_agents(
    category: Optional[str] = Query(default=None),
    verified_only: bool = Query(default=False),
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[AgentRead]:
    query = select(Agent).where(Agent.is_public.is_(True), Agent.is_active.is_(True))

    if category:
        query = query.where(Agent.category == category)
    if verified_only:
        query = query.where(Agent.verification_status == VerificationStatus.VERIFIED.value)
    if q:
        ilike = f"%{q.strip()}%"
        query = query.where(
            and_(Agent.name.ilike(ilike) | Agent.description.ilike(ilike), Agent.is_public.is_(True))
        )

    query = query.order_by(Agent.created_at.desc()).limit(limit)
    agents = (await session.scalars(query)).all()
    return [AgentRead.model_validate(agent) for agent in agents]


@router.get("/{slug}", response_model=AgentRead)
async def get_agent_profile(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> AgentRead:
    agent = await session.scalar(
        select(Agent).where(Agent.slug == slug, Agent.is_public.is_(True))
    )
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return AgentRead.model_validate(agent)


@router.post(
    "/{agent_id}/verification-request",
    response_model=VerificationRequestRead,
    status_code=status.HTTP_201_CREATED,
)
async def submit_verification_request(
    agent_id: UUID,
    payload: VerificationRequestCreate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> VerificationRequestRead:
    agent = await _get_agent_or_404(session, agent_id)
    _assert_owner(agent, user)

    existing_pending = await session.scalar(
        select(VerificationRequest).where(
            VerificationRequest.agent_id == agent.id,
            VerificationRequest.status == VerificationRequestStatus.PENDING.value,
        )
    )
    if existing_pending is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending verification request already exists.",
        )

    request = VerificationRequest(
        agent_id=agent.id,
        submitted_by_user_id=user.id,
        status=VerificationRequestStatus.PENDING.value,
        evidence_note=payload.evidence_note,
    )
    session.add(request)
    await session.commit()
    await session.refresh(request)
    return VerificationRequestRead.model_validate(request)


@router.post(
    "/{agent_id}/credentials",
    response_model=AgentCredentialSecretRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_agent_credential(
    agent_id: UUID,
    payload: AgentCredentialCreate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> AgentCredentialSecretRead:
    agent = await _get_agent_or_404(session, agent_id)
    _assert_owner(agent, user)

    key_id = generate_key_id()
    secret = generate_secret()
    credential = AgentCredential(
        agent_id=agent.id,
        key_id=key_id,
        secret_hash=hash_secret(secret),
        label=payload.label,
        is_active=True,
    )
    session.add(credential)
    await session.commit()
    await session.refresh(credential)
    return AgentCredentialSecretRead(
        credential_id=credential.id,
        key_id=credential.key_id,
        secret=secret,
        created_at=credential.created_at,
    )


@router.get("/{agent_id}/credentials", response_model=list[AgentCredentialRead])
async def list_agent_credentials(
    agent_id: UUID,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> list[AgentCredentialRead]:
    agent = await _get_agent_or_404(session, agent_id)
    _assert_owner(agent, user)

    credentials = (
        await session.scalars(
            select(AgentCredential)
            .where(AgentCredential.agent_id == agent.id)
            .order_by(AgentCredential.created_at.desc())
        )
    ).all()
    return [AgentCredentialRead.model_validate(item) for item in credentials]


@router.post("/{agent_id}/credentials/{credential_id}/rotate", response_model=AgentCredentialSecretRead)
async def rotate_agent_credential(
    agent_id: UUID,
    credential_id: UUID,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> AgentCredentialSecretRead:
    agent = await _get_agent_or_404(session, agent_id)
    _assert_owner(agent, user)
    credential = await session.scalar(
        select(AgentCredential).where(
            AgentCredential.id == credential_id, AgentCredential.agent_id == agent.id
        )
    )
    if credential is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")

    new_key = generate_key_id()
    new_secret = generate_secret()
    credential.key_id = new_key
    credential.secret_hash = hash_secret(new_secret)
    credential.is_active = True
    credential.revoked_at = None

    session.add(credential)
    await session.commit()
    await session.refresh(credential)
    return AgentCredentialSecretRead(
        credential_id=credential.id,
        key_id=credential.key_id,
        secret=new_secret,
        created_at=credential.created_at,
    )


@router.delete("/{agent_id}/credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_agent_credential(
    agent_id: UUID,
    credential_id: UUID,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    agent = await _get_agent_or_404(session, agent_id)
    _assert_owner(agent, user)
    credential = await session.scalar(
        select(AgentCredential).where(
            AgentCredential.id == credential_id, AgentCredential.agent_id == agent.id
        )
    )
    if credential is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")
    credential.is_active = False
    credential.revoked_at = utcnow()
    session.add(credential)
    await session.commit()
    return None


@router.post("/{agent_id}/demo/chat", response_model=DemoChatResponse)
async def demo_chat(
    agent_id: UUID,
    payload: DemoChatRequest,
    request: Request,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> DemoChatResponse:
    agent = await _get_agent_or_404(session, agent_id)
    if not agent.request_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "demo_unavailable",
                "message": "Agent has no request_url configured.",
            },
        )

    client_host = request.client.host if request.client else "unknown"
    if not rate_limiter.allow(
        key=f"demo-chat:{client_host}:{user.id}:{agent.id}",
        limit=30,
        window_seconds=60,
    ):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    started_at = time.perf_counter()
    log = DemoSessionLog(agent_id=agent.id, user_id=user.id, input_text=payload.message)
    session.add(log)
    try:
        async with httpx.AsyncClient(timeout=settings.DEMO_REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                agent.request_url,
                json={
                    "message": payload.message,
                    "session_id": payload.session_id or str(user.id),
                    "user_id": str(user.id),
                    "agent_id": str(agent.id),
                    "metadata": {"source": "agent-swipe-demo"},
                },
            )
        elapsed = int((time.perf_counter() - started_at) * 1000)
        log.latency_ms = elapsed
        log.status_code = response.status_code

        if response.status_code >= 400:
            log.error_message = f"Upstream returned {response.status_code}"
            session.add(log)
            await session.commit()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"error": "upstream_error", "status_code": response.status_code},
            )

        data = response.json()
        reply = str(data.get("reply", ""))
        if not reply:
            reply = str(data)
        log.output_text = reply
        session.add(log)
        await session.commit()
        return DemoChatResponse(reply=reply, meta=data.get("meta", {}))
    except httpx.TimeoutException:
        elapsed = int((time.perf_counter() - started_at) * 1000)
        log.latency_ms = elapsed
        log.error_message = "request_timeout"
        session.add(log)
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"error": "request_timeout"},
        )
    except HTTPException:
        raise
    except Exception as exc:
        elapsed = int((time.perf_counter() - started_at) * 1000)
        log.latency_ms = elapsed
        log.error_message = str(exc)[:500]
        session.add(log)
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": "upstream_invalid_response"},
        )



