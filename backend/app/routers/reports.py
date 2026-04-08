from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_schemas import ReportCreate, ReportRead
from app.dependencies import get_current_active_user, get_session
from app.models import Agent, Comment, ContentReport, Post, ReportTargetType, User


router = APIRouter(tags=["reports"])


@router.post("/reports", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def create_report(
    payload: ReportCreate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> ReportRead:
    report = ContentReport(
        reporter_user_id=user.id,
        target_type=payload.target_type,
        reason=payload.reason.strip(),
        details=payload.details,
    )

    if payload.target_type == ReportTargetType.POST.value:
        post = await session.get(Post, payload.target_id)
        if post is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        report.target_post_id = post.id
    elif payload.target_type == ReportTargetType.COMMENT.value:
        comment = await session.get(Comment, payload.target_id)
        if comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )
        report.target_comment_id = comment.id
    else:
        agent = await session.get(Agent, payload.target_id)
        if agent is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
        report.target_agent_id = agent.id

    session.add(report)
    await session.commit()
    await session.refresh(report)
    return ReportRead.model_validate(report)


