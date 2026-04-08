from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_schemas import OnboardingRead, ProfileRead, ProfileUpdate
from app.domain_utils import ensure_profile_for_user, utcnow
from app.models import User
from app.dependencies import get_current_active_user, get_session


router = APIRouter(prefix="/me", tags=["profiles"])


@router.get("/profile", response_model=ProfileRead)
async def get_my_profile(
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    profile = await ensure_profile_for_user(session, user)
    await session.commit()
    await session.refresh(profile)
    return ProfileRead.model_validate(profile)


@router.patch("/profile", response_model=ProfileRead)
async def update_my_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> ProfileRead:
    profile = await ensure_profile_for_user(session, user)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(profile, key, value)

    if profile.display_name and profile.display_name.strip():
        profile.onboarding_status = "partial"
    profile.updated_at = utcnow()

    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return ProfileRead.model_validate(profile)


@router.get("/onboarding", response_model=OnboardingRead)
async def get_onboarding_status(
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> OnboardingRead:
    profile = await ensure_profile_for_user(session, user)
    await session.commit()
    return OnboardingRead(
        onboarding_status=profile.onboarding_status,
        onboarding_completed_at=profile.onboarding_completed_at,
    )


@router.post("/onboarding/complete", response_model=OnboardingRead)
async def complete_onboarding(
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> OnboardingRead:
    profile = await ensure_profile_for_user(session, user)
    profile.onboarding_status = "completed"
    profile.onboarding_completed_at = utcnow()
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return OnboardingRead(
        onboarding_status=profile.onboarding_status,
        onboarding_completed_at=profile.onboarding_completed_at,
    )


