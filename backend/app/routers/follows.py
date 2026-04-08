from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import UUID

from app.api_schemas import FollowCreate, FollowRead, FollowerRead
from app.dependencies import get_current_active_user, get_session
from app.models import Agent, FollowEdge, FollowTargetType, User


router = APIRouter(tags=["follows"])


def _build_target_identifier(target_type: str, target_user_id, target_agent_id) -> str:
    if target_type == FollowTargetType.HUMAN.value:
        return f"human:{target_user_id}"
    return f"agent:{target_agent_id}"


async def _validate_follow_target(
    payload: FollowCreate, user: User, session: AsyncSession
) -> tuple[str, UUID | None, UUID | None]:
    if payload.target_type == FollowTargetType.HUMAN.value:
        if payload.target_user_id is None or payload.target_agent_id is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="target_user_id is required for target_type=human.",
            )
        if str(payload.target_user_id) == str(user.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot follow yourself."
            )
        target = await session.get(User, payload.target_user_id)
        if target is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return payload.target_type, target.id, None

    if payload.target_agent_id is None or payload.target_user_id is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="target_agent_id is required for target_type=agent.",
        )
    target_agent = await session.get(Agent, payload.target_agent_id)
    if target_agent is None or not target_agent.is_public:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return payload.target_type, None, target_agent.id


@router.post("/follows", response_model=FollowRead, status_code=status.HTTP_201_CREATED)
async def follow_target(
    payload: FollowCreate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> FollowRead:
    target_type, target_user_id, target_agent_id = await _validate_follow_target(
        payload, user, session
    )
    target_identifier = _build_target_identifier(target_type, target_user_id, target_agent_id)
    existing = await session.scalar(
        select(FollowEdge).where(
            FollowEdge.follower_user_id == user.id,
            FollowEdge.target_identifier == target_identifier,
        )
    )
    if existing is not None:
        return FollowRead.model_validate(existing)

    edge = FollowEdge(
        follower_user_id=user.id,
        target_type=target_type,
        target_user_id=target_user_id,
        target_agent_id=target_agent_id,
        target_identifier=target_identifier,
    )
    session.add(edge)
    await session.commit()
    await session.refresh(edge)
    return FollowRead.model_validate(edge)


@router.delete("/follows", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_target(
    payload: FollowCreate = Body(...),
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    target_type, target_user_id, target_agent_id = await _validate_follow_target(
        payload, user, session
    )
    target_identifier = _build_target_identifier(target_type, target_user_id, target_agent_id)
    edge = await session.scalar(
        select(FollowEdge).where(
            FollowEdge.follower_user_id == user.id,
            FollowEdge.target_identifier == target_identifier,
        )
    )
    if edge is not None:
        await session.delete(edge)
        await session.commit()
    return None


@router.get("/me/following", response_model=list[FollowRead])
async def list_following(
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> list[FollowRead]:
    edges = (
        await session.scalars(
            select(FollowEdge)
            .where(FollowEdge.follower_user_id == user.id)
            .order_by(FollowEdge.created_at.desc())
        )
    ).all()
    return [FollowRead.model_validate(edge) for edge in edges]


@router.get("/users/{user_id}/followers", response_model=list[FollowerRead])
async def list_user_followers(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> list[FollowerRead]:
    target = await session.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    rows = await session.execute(
        select(User.id, User.username, User.full_name)
        .join(FollowEdge, FollowEdge.follower_user_id == User.id)
        .where(
            FollowEdge.target_type == FollowTargetType.HUMAN.value,
            FollowEdge.target_user_id == target.id,
        )
        .order_by(FollowEdge.created_at.desc())
    )
    return [
        FollowerRead(user_id=row.id, username=row.username, full_name=row.full_name)
        for row in rows.all()
    ]


@router.get("/agents/{agent_id}/followers", response_model=list[FollowerRead])
async def list_agent_followers(
    agent_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> list[FollowerRead]:
    agent = await session.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    rows = await session.execute(
        select(User.id, User.username, User.full_name)
        .join(FollowEdge, FollowEdge.follower_user_id == User.id)
        .where(
            FollowEdge.target_type == FollowTargetType.AGENT.value,
            FollowEdge.target_agent_id == agent.id,
        )
        .order_by(FollowEdge.created_at.desc())
    )
    return [
        FollowerRead(user_id=row.id, username=row.username, full_name=row.full_name)
        for row in rows.all()
    ]



