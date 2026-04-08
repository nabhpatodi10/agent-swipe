from __future__ import annotations

from datetime import datetime, timezone
import re
import secrets
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Agent, Collection, Profile, User


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_slug(value: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    base = base.strip("-")
    return base or "agent"


async def ensure_unique_agent_slug(
    session: AsyncSession, name: str, current_agent_id: Optional[str] = None
) -> str:
    base = normalize_slug(name)
    candidate = base
    for _ in range(6):
        query = select(Agent).where(Agent.slug == candidate)
        existing = await session.scalar(query)
        if existing is None or str(existing.id) == str(current_agent_id):
            return candidate
        candidate = f"{base}-{secrets.token_hex(2)}"
    return f"{base}-{secrets.token_hex(4)}"


async def ensure_profile_for_user(session: AsyncSession, user: User) -> Profile:
    profile = await session.scalar(select(Profile).where(Profile.user_id == user.id))
    if profile is not None:
        return profile

    display_name = user.full_name or user.username
    profile = Profile(
        user_id=user.id,
        display_name=display_name,
        onboarding_status="pending",
        interests=[],
    )
    session.add(profile)
    await session.flush()
    return profile


async def ensure_liked_collection(session: AsyncSession, user_id) -> Collection:
    collection = await session.scalar(
        select(Collection).where(
            Collection.user_id == user_id,
            Collection.name == "Liked",
            Collection.is_system.is_(True),
        )
    )
    if collection is not None:
        return collection

    collection = Collection(
        user_id=user_id,
        name="Liked",
        description="Auto-saved agents from right swipes",
        is_system=True,
    )
    session.add(collection)
    await session.flush()
    return collection

