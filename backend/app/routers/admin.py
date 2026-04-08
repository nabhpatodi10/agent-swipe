from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import UUID

from app.api_schemas import (
    ReportRead,
    ReportResolveRequest,
    VerificationRejectRequest,
    VerificationRequestRead,
)
from app.dependencies import get_current_superuser, get_session
from app.domain_utils import utcnow
from app.models import (
    Agent,
    ContentReport,
    User,
    VerificationRequest,
    VerificationRequestStatus,
    VerificationStatus,
)


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/verification-requests", response_model=list[VerificationRequestRead])
async def list_verification_requests(
    status_filter: str = Query(default=VerificationRequestStatus.PENDING.value),
    _: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_session),
) -> list[VerificationRequestRead]:
    rows = (
        await session.scalars(
            select(VerificationRequest)
            .where(VerificationRequest.status == status_filter)
            .order_by(VerificationRequest.created_at.asc())
        )
    ).all()
    return [VerificationRequestRead.model_validate(item) for item in rows]


@router.post("/verification-requests/{request_id}/approve", response_model=VerificationRequestRead)
async def approve_verification_request(
    request_id: UUID,
    admin_user: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_session),
) -> VerificationRequestRead:
    request = await session.get(VerificationRequest, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    agent = await session.get(Agent, request.agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    request.status = VerificationRequestStatus.APPROVED.value
    request.reviewed_by_user_id = admin_user.id
    request.reviewed_at = utcnow()
    request.rejection_reason = None
    agent.verification_status = VerificationStatus.VERIFIED.value
    session.add_all([request, agent])
    await session.commit()
    await session.refresh(request)
    return VerificationRequestRead.model_validate(request)


@router.post("/verification-requests/{request_id}/reject", response_model=VerificationRequestRead)
async def reject_verification_request(
    request_id: UUID,
    payload: VerificationRejectRequest,
    admin_user: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_session),
) -> VerificationRequestRead:
    request = await session.get(VerificationRequest, request_id)
    if request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    agent = await session.get(Agent, request.agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    request.status = VerificationRequestStatus.REJECTED.value
    request.reviewed_by_user_id = admin_user.id
    request.reviewed_at = utcnow()
    request.rejection_reason = payload.reason.strip()
    agent.verification_status = VerificationStatus.UNVERIFIED.value
    session.add_all([request, agent])
    await session.commit()
    await session.refresh(request)
    return VerificationRequestRead.model_validate(request)


@router.get("/reports", response_model=list[ReportRead])
async def list_reports(
    status_filter: str = Query(default="open"),
    _: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_session),
) -> list[ReportRead]:
    reports = (
        await session.scalars(
            select(ContentReport)
            .where(ContentReport.status == status_filter)
            .order_by(ContentReport.created_at.asc())
        )
    ).all()
    return [ReportRead.model_validate(item) for item in reports]


@router.post("/reports/{report_id}/resolve", response_model=ReportRead)
async def resolve_report(
    report_id: UUID,
    _: ReportResolveRequest,
    admin_user: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_session),
) -> ReportRead:
    report = await session.get(ContentReport, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    report.status = "resolved"
    report.resolved_by_user_id = admin_user.id
    report.resolved_at = utcnow()
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return ReportRead.model_validate(report)



