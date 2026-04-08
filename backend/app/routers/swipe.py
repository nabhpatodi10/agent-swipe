from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_schemas import AgentRead, AgentSummary, SwipeDecisionRequest
from app.dependencies import get_current_active_user, get_session
from app.domain_utils import ensure_liked_collection
from app.models import Agent, CollectionItem, SwipeDecision, SwipeDecisionType, User


router = APIRouter(tags=["swipe"])


@router.get("/swipe/next", response_model=list[AgentRead])
async def get_swipe_candidates(
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> list[AgentRead]:
    swiped_subq = select(SwipeDecision.agent_id).where(SwipeDecision.user_id == user.id)
    query = (
        select(Agent)
        .where(
            Agent.is_public.is_(True),
            Agent.is_active.is_(True),
            Agent.owner_user_id != user.id,
            Agent.id.not_in(swiped_subq),
        )
        .order_by(Agent.created_at.desc())
        .limit(limit)
    )
    agents = (await session.scalars(query)).all()
    return [AgentRead.model_validate(agent) for agent in agents]


@router.post("/swipe/decision")
async def submit_swipe_decision(
    payload: SwipeDecisionRequest,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    agent = await session.get(Agent, payload.agent_id)
    if agent is None or not agent.is_public or not agent.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    if str(agent.owner_user_id) == str(user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot swipe your own agent.",
        )

    decision = await session.scalar(
        select(SwipeDecision).where(
            SwipeDecision.user_id == user.id, SwipeDecision.agent_id == agent.id
        )
    )
    if decision is None:
        decision = SwipeDecision(
            user_id=user.id,
            agent_id=agent.id,
            decision=payload.decision,
        )
    else:
        decision.decision = payload.decision

    session.add(decision)

    liked = await ensure_liked_collection(session, user.id)
    if payload.decision == SwipeDecisionType.RIGHT.value:
        existing_item = await session.scalar(
            select(CollectionItem).where(
                CollectionItem.collection_id == liked.id, CollectionItem.agent_id == agent.id
            )
        )
        if existing_item is None:
            session.add(CollectionItem(collection_id=liked.id, agent_id=agent.id))
    else:
        await session.execute(
            delete(CollectionItem).where(
                CollectionItem.collection_id == liked.id, CollectionItem.agent_id == agent.id
            )
        )

    await session.commit()
    return {"status": "ok"}


@router.get("/me/liked-agents", response_model=list[AgentSummary])
async def get_liked_agents(
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> list[AgentSummary]:
    query = (
        select(Agent)
        .join(SwipeDecision, SwipeDecision.agent_id == Agent.id)
        .where(
            SwipeDecision.user_id == user.id,
            SwipeDecision.decision == SwipeDecisionType.RIGHT.value,
        )
        .order_by(SwipeDecision.updated_at.desc())
    )
    agents = (await session.scalars(query)).all()
    return [AgentSummary.model_validate(agent) for agent in agents]


