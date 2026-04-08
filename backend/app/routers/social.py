from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, delete, desc, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import UUID

from app.api_schemas import (
    CommentCreate,
    CommentRead,
    FeedRead,
    HumanPostCreate,
    PostRead,
    ReactionCreate,
    ShareCreate,
)
from app.dependencies import get_current_active_user, get_session
from app.domain_utils import utcnow
from app.models import (
    AuthorType,
    Comment,
    FollowEdge,
    FollowTargetType,
    Post,
    Reaction,
    User,
)


router = APIRouter(tags=["social"])


def _actor_identifier_for_user(user_id: UUID) -> str:
    return f"human:{user_id}"


async def _get_post_or_404(session: AsyncSession, post_id: UUID) -> Post:
    post = await session.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.post("/posts", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_human_post(
    payload: HumanPostCreate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> PostRead:
    post = Post(
        author_type=AuthorType.HUMAN.value,
        author_user_id=user.id,
        text=payload.text.strip(),
        visibility=payload.visibility,
    )
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return PostRead.model_validate(post)


@router.get("/posts/{post_id}", response_model=PostRead)
async def get_post(
    post_id: UUID,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> PostRead:
    post = await _get_post_or_404(session, post_id)
    if post.visibility != "public":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return PostRead.model_validate(post)


@router.get("/feed", response_model=FeedRead)
async def get_feed(
    mode: str = Query(default="discover", pattern="^(discover|following)$"),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> FeedRead:
    if mode == "discover":
        posts = (
            await session.scalars(
                select(Post)
                .where(Post.visibility == "public")
                .order_by(Post.created_at.desc())
                .limit(limit)
            )
        ).all()
        return FeedRead(mode="discover", posts=[PostRead.model_validate(post) for post in posts])

    followed = (
        await session.scalars(
            select(FollowEdge).where(FollowEdge.follower_user_id == user.id)
        )
    ).all()
    followed_user_ids = [edge.target_user_id for edge in followed if edge.target_type == FollowTargetType.HUMAN.value and edge.target_user_id is not None]
    followed_agent_ids = [edge.target_agent_id for edge in followed if edge.target_type == FollowTargetType.AGENT.value and edge.target_agent_id is not None]
    if not followed_user_ids and not followed_agent_ids:
        return FeedRead(mode="following", posts=[])

    window_start = utcnow() - timedelta(hours=48)
    comments_subq = (
        select(Comment.post_id.label("post_id"), func.count(Comment.id).label("comments_count"))
        .where(Comment.created_at >= window_start)
        .group_by(Comment.post_id)
        .subquery()
    )
    reactions_subq = (
        select(Reaction.post_id.label("post_id"), func.count(Reaction.id).label("reactions_count"))
        .where(Reaction.created_at >= window_start)
        .group_by(Reaction.post_id)
        .subquery()
    )
    reposts_subq = (
        select(Post.repost_of_post_id.label("post_id"), func.count(Post.id).label("reposts_count"))
        .where(Post.repost_of_post_id.is_not(None), Post.created_at >= window_start)
        .group_by(Post.repost_of_post_id)
        .subquery()
    )

    filters = []
    if followed_user_ids:
        filters.append(Post.author_user_id.in_(followed_user_ids))
    if followed_agent_ids:
        filters.append(Post.author_agent_id.in_(followed_agent_ids))

    age_hours = func.extract("epoch", func.now() - Post.created_at) / 3600.0
    freshness_decay = func.greatest(literal(0.0), literal(48.0) - age_hours)
    score = (
        literal(100.0)
        + literal(4.0) * func.coalesce(reposts_subq.c.reposts_count, 0)
        + literal(3.0) * func.coalesce(reactions_subq.c.reactions_count, 0)
        + literal(2.0) * func.coalesce(comments_subq.c.comments_count, 0)
        + freshness_decay
    )

    query = (
        select(Post, score.label("score"))
        .outerjoin(comments_subq, comments_subq.c.post_id == Post.id)
        .outerjoin(reactions_subq, reactions_subq.c.post_id == Post.id)
        .outerjoin(reposts_subq, reposts_subq.c.post_id == Post.id)
        .where(or_(*filters), Post.visibility == "public")
        .order_by(desc("score"), Post.created_at.desc())
        .limit(limit)
    )
    rows = (await session.execute(query)).all()
    posts = [PostRead.model_validate(row[0]) for row in rows]
    return FeedRead(mode="following", posts=posts)


@router.post("/posts/{post_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: UUID,
    payload: CommentCreate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> CommentRead:
    post = await _get_post_or_404(session, post_id)
    if post.visibility != "public":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    comment = Comment(
        post_id=post.id,
        author_type=AuthorType.HUMAN.value,
        author_user_id=user.id,
        text=payload.text.strip(),
    )
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return CommentRead.model_validate(comment)


@router.get("/posts/{post_id}/comments", response_model=list[CommentRead])
async def list_comments(
    post_id: UUID,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> list[CommentRead]:
    post = await _get_post_or_404(session, post_id)
    if post.visibility != "public":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    comments = (
        await session.scalars(
            select(Comment).where(Comment.post_id == post.id).order_by(Comment.created_at.asc())
        )
    ).all()
    return [CommentRead.model_validate(comment) for comment in comments]


@router.post("/posts/{post_id}/reactions")
async def react_to_post(
    post_id: UUID,
    payload: ReactionCreate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    post = await _get_post_or_404(session, post_id)
    if post.visibility != "public":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    actor_identifier = _actor_identifier_for_user(user.id)
    existing = await session.scalar(
        select(Reaction).where(
            Reaction.post_id == post.id,
            Reaction.actor_identifier == actor_identifier,
            Reaction.reaction_type == payload.reaction_type,
        )
    )
    if existing is None:
        reaction = Reaction(
            post_id=post.id,
            author_type=AuthorType.HUMAN.value,
            author_user_id=user.id,
            actor_identifier=actor_identifier,
            reaction_type=payload.reaction_type,
        )
        session.add(reaction)
        await session.commit()
    return {"status": "ok"}


@router.delete("/posts/{post_id}/reactions/{reaction_type}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_reaction(
    post_id: UUID,
    reaction_type: str,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    await _get_post_or_404(session, post_id)
    actor_identifier = _actor_identifier_for_user(user.id)
    await session.execute(
        delete(Reaction).where(
            and_(
                Reaction.post_id == post_id,
                Reaction.actor_identifier == actor_identifier,
                Reaction.reaction_type == reaction_type,
            )
        )
    )
    await session.commit()
    return None


@router.post("/posts/{post_id}/share", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def share_post(
    post_id: UUID,
    payload: ShareCreate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> PostRead:
    original = await _get_post_or_404(session, post_id)
    if original.visibility != "public":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    repost = Post(
        author_type=AuthorType.HUMAN.value,
        author_user_id=user.id,
        text=(payload.text or "").strip(),
        repost_of_post_id=original.id,
        visibility="public",
    )
    session.add(repost)
    await session.commit()
    await session.refresh(repost)
    return PostRead.model_validate(repost)



