from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import UUID

from app.api_schemas import (
    AgentSummary,
    CollectionCreate,
    CollectionItemCreate,
    CollectionRead,
    CollectionUpdate,
)
from app.dependencies import get_current_active_user, get_session
from app.domain_utils import ensure_liked_collection, utcnow
from app.models import Agent, Collection, CollectionItem, User


router = APIRouter(prefix="/collections", tags=["collections"])


async def _get_owned_collection(
    session: AsyncSession, collection_id: UUID, user: User
) -> Collection:
    collection = await session.scalar(
        select(Collection).where(Collection.id == collection_id, Collection.user_id == user.id)
    )
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return collection


async def _serialize_collection(
    session: AsyncSession, collection: Collection
) -> CollectionRead:
    agents = (
        await session.scalars(
            select(Agent)
            .join(CollectionItem, CollectionItem.agent_id == Agent.id)
            .where(CollectionItem.collection_id == collection.id)
            .order_by(CollectionItem.created_at.desc())
        )
    ).all()
    return CollectionRead(
        id=collection.id,
        user_id=collection.user_id,
        name=collection.name,
        description=collection.description,
        is_system=collection.is_system,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
        items=[AgentSummary.model_validate(agent) for agent in agents],
    )


@router.post("", response_model=CollectionRead, status_code=status.HTTP_201_CREATED)
async def create_collection(
    payload: CollectionCreate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> CollectionRead:
    collection = Collection(
        user_id=user.id,
        name=payload.name.strip(),
        description=payload.description,
        is_system=False,
    )
    session.add(collection)
    await session.commit()
    await session.refresh(collection)
    return await _serialize_collection(session, collection)


@router.get("", response_model=list[CollectionRead])
async def list_collections(
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> list[CollectionRead]:
    await ensure_liked_collection(session, user.id)
    await session.commit()

    collections = (
        await session.scalars(
            select(Collection)
            .where(Collection.user_id == user.id)
            .order_by(Collection.is_system.desc(), Collection.created_at.asc())
        )
    ).all()
    return [await _serialize_collection(session, collection) for collection in collections]


@router.patch("/{collection_id}", response_model=CollectionRead)
async def update_collection(
    collection_id: UUID,
    payload: CollectionUpdate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> CollectionRead:
    collection = await _get_owned_collection(session, collection_id, user)
    if collection.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System collections cannot be edited.",
        )

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(collection, key, value)
    collection.updated_at = utcnow()
    session.add(collection)
    await session.commit()
    await session.refresh(collection)
    return await _serialize_collection(session, collection)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: UUID,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    collection = await _get_owned_collection(session, collection_id, user)
    if collection.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System collections cannot be deleted.",
        )
    await session.delete(collection)
    await session.commit()
    return None


@router.post("/{collection_id}/items", response_model=CollectionRead)
async def add_collection_item(
    collection_id: UUID,
    payload: CollectionItemCreate,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> CollectionRead:
    collection = await _get_owned_collection(session, collection_id, user)
    agent = await session.get(Agent, payload.agent_id)
    if agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    existing = await session.scalar(
        select(CollectionItem).where(
            CollectionItem.collection_id == collection.id,
            CollectionItem.agent_id == agent.id,
        )
    )
    if existing is None:
        session.add(CollectionItem(collection_id=collection.id, agent_id=agent.id))
        await session.commit()
    return await _serialize_collection(session, collection)


@router.delete("/{collection_id}/items/{agent_id}", response_model=CollectionRead)
async def remove_collection_item(
    collection_id: UUID,
    agent_id: UUID,
    user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_session),
) -> CollectionRead:
    collection = await _get_owned_collection(session, collection_id, user)
    await session.execute(
        delete(CollectionItem).where(
            CollectionItem.collection_id == collection.id, CollectionItem.agent_id == agent_id
        )
    )
    await session.commit()
    return await _serialize_collection(session, collection)



