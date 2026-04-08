from __future__ import annotations

from datetime import datetime
from enum import StrEnum
import uuid_utils as uuid
from typing import Optional

from fastapi_users_db_sqlalchemy import (
    SQLAlchemyBaseOAuthAccountTableUUID,
    SQLAlchemyBaseUserTableUUID,
)
from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class VerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"


class VerificationRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class SwipeDecisionType(StrEnum):
    LEFT = "left"
    RIGHT = "right"


class AuthorType(StrEnum):
    HUMAN = "human"
    AGENT = "agent"


class ReactionType(StrEnum):
    LIKE = "like"
    INSIGHT = "insight"
    CELEBRATE = "celebrate"


class FollowTargetType(StrEnum):
    HUMAN = "human"
    AGENT = "agent"


class ReportTargetType(StrEnum):
    POST = "post"
    COMMENT = "comment"
    AGENT = "agent"


class Base(DeclarativeBase):
    pass


class OAuthAccount(SQLAlchemyBaseOAuthAccountTableUUID, Base):
    __tablename__ = "oauth_account"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid7)

    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "user"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid7)
    username: Mapped[str] = mapped_column(String(length=150), unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(length=150), nullable=True)

    oauth_accounts: Mapped[list[OAuthAccount]] = relationship(
        "OAuthAccount",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    profile: Mapped[Optional["Profile"]] = relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    agents: Mapped[list["Agent"]] = relationship(
        "Agent", back_populates="owner", cascade="all, delete-orphan"
    )
    collections: Mapped[list["Collection"]] = relationship(
        "Collection", back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid7)
    user_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("user.id", ondelete="cascade"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(length=64), index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")


class Profile(Base):
    __tablename__ = "profile"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid7)
    user_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("user.id", ondelete="cascade"), nullable=False, unique=True
    )
    display_name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(String(length=600), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(length=500), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(length=120), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(length=500), nullable=True)
    interests: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    onboarding_status: Mapped[str] = mapped_column(
        String(length=32), nullable=False, server_default="pending", index=True
    )
    onboarding_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")


class Agent(Base):
    __tablename__ = "agent"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid7)
    owner_user_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("user.id", ondelete="cascade"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(length=150), nullable=False)
    slug: Mapped[str] = mapped_column(String(length=180), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(length=2000), nullable=False)
    skills: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, server_default="[]", index=False
    )
    category: Mapped[str] = mapped_column(String(length=80), nullable=False, index=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(length=500), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(length=500), nullable=True)
    request_url: Mapped[Optional[str]] = mapped_column(String(length=500), nullable=True)
    pricing_model: Mapped[str] = mapped_column(
        String(length=30), nullable=False, server_default="free"
    )
    free_tier_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    free_tier_notes: Mapped[Optional[str]] = mapped_column(
        String(length=500), nullable=True
    )
    verification_status: Mapped[str] = mapped_column(
        String(length=30),
        nullable=False,
        server_default=VerificationStatus.UNVERIFIED.value,
        index=True,
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    owner: Mapped["User"] = relationship("User", back_populates="agents")
    verification_requests: Mapped[list["VerificationRequest"]] = relationship(
        "VerificationRequest", back_populates="agent", cascade="all, delete-orphan"
    )
    credentials: Mapped[list["AgentCredential"]] = relationship(
        "AgentCredential", back_populates="agent", cascade="all, delete-orphan"
    )


class VerificationRequest(Base):
    __tablename__ = "verification_request"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid7)
    agent_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("agent.id", ondelete="cascade"), nullable=False, index=True
    )
    submitted_by_user_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("user.id", ondelete="cascade"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(length=20),
        nullable=False,
        server_default=VerificationRequestStatus.PENDING.value,
        index=True,
    )
    evidence_note: Mapped[Optional[str]] = mapped_column(String(length=1000), nullable=True)
    reviewed_by_user_id: Mapped[Optional[GUID]] = mapped_column(
        GUID, ForeignKey("user.id", ondelete="set null"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        String(length=500), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    agent: Mapped["Agent"] = relationship("Agent", back_populates="verification_requests")


class AgentCredential(Base):
    __tablename__ = "agent_credential"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid7)
    agent_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("agent.id", ondelete="cascade"), nullable=False, index=True
    )
    key_id: Mapped[str] = mapped_column(String(length=80), nullable=False, unique=True)
    secret_hash: Mapped[str] = mapped_column(String(length=64), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(String(length=120), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", index=True
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    agent: Mapped["Agent"] = relationship("Agent", back_populates="credentials")


class SwipeDecision(Base):
    __tablename__ = "swipe_decision"
    __table_args__ = (UniqueConstraint("user_id", "agent_id", name="uq_swipe_user_agent"),)

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid7)
    user_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("user.id", ondelete="cascade"), nullable=False, index=True
    )
    agent_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("agent.id", ondelete="cascade"), nullable=False, index=True
    )
    decision: Mapped[str] = mapped_column(String(length=10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Collection(Base):
    __tablename__ = "collection"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid7)
    user_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("user.id", ondelete="cascade"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(length=120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(length=300), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship("User", back_populates="collections")
    items: Mapped[list["CollectionItem"]] = relationship(
        "CollectionItem", back_populates="collection", cascade="all, delete-orphan"
    )


class CollectionItem(Base):
    __tablename__ = "collection_item"
    __table_args__ = (
        UniqueConstraint("collection_id", "agent_id", name="uq_collection_item_agent"),
    )

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid7)
    collection_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("collection.id", ondelete="cascade"), nullable=False, index=True
    )
    agent_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("agent.id", ondelete="cascade"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    collection: Mapped["Collection"] = relationship("Collection", back_populates="items")
    agent: Mapped["Agent"] = relationship("Agent")


class Post(Base):
    __tablename__ = "post"
    __table_args__ = (
        CheckConstraint(
            "(author_type = 'human' AND author_user_id IS NOT NULL AND author_agent_id IS NULL) "
            "OR (author_type = 'agent' AND author_agent_id IS NOT NULL AND author_user_id IS NULL)",
            name="ck_post_author_actor",
        ),
    )

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid7)
    author_type: Mapped[str] = mapped_column(String(length=10), nullable=False, index=True)
    author_user_id: Mapped[Optional[GUID]] = mapped_column(
        GUID, ForeignKey("user.id", ondelete="set null"), nullable=True, index=True
    )
    author_agent_id: Mapped[Optional[GUID]] = mapped_column(
        GUID, ForeignKey("agent.id", ondelete="set null"), nullable=True, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    repost_of_post_id: Mapped[Optional[GUID]] = mapped_column(
        GUID, ForeignKey("post.id", ondelete="set null"), nullable=True, index=True
    )
    visibility: Mapped[str] = mapped_column(
        String(length=20), nullable=False, server_default="public", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )
    reactions: Mapped[list["Reaction"]] = relationship(
        "Reaction", back_populates="post", cascade="all, delete-orphan"
    )


class Comment(Base):
    __tablename__ = "comment"
    __table_args__ = (
        CheckConstraint(
            "(author_type = 'human' AND author_user_id IS NOT NULL AND author_agent_id IS NULL) "
            "OR (author_type = 'agent' AND author_agent_id IS NOT NULL AND author_user_id IS NULL)",
            name="ck_comment_author_actor",
        ),
    )

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid7)
    post_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("post.id", ondelete="cascade"), nullable=False, index=True
    )
    author_type: Mapped[str] = mapped_column(String(length=10), nullable=False, index=True)
    author_user_id: Mapped[Optional[GUID]] = mapped_column(
        GUID, ForeignKey("user.id", ondelete="set null"), nullable=True, index=True
    )
    author_agent_id: Mapped[Optional[GUID]] = mapped_column(
        GUID, ForeignKey("agent.id", ondelete="set null"), nullable=True, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    post: Mapped["Post"] = relationship("Post", back_populates="comments")


class Reaction(Base):
    __tablename__ = "reaction"
    __table_args__ = (
        CheckConstraint(
            "(author_type = 'human' AND author_user_id IS NOT NULL AND author_agent_id IS NULL) "
            "OR (author_type = 'agent' AND author_agent_id IS NOT NULL AND author_user_id IS NULL)",
            name="ck_reaction_author_actor",
        ),
        UniqueConstraint(
            "post_id", "actor_identifier", "reaction_type", name="uq_reaction_actor_type"
        ),
    )

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid7)
    post_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("post.id", ondelete="cascade"), nullable=False, index=True
    )
    author_type: Mapped[str] = mapped_column(String(length=10), nullable=False)
    author_user_id: Mapped[Optional[GUID]] = mapped_column(
        GUID, ForeignKey("user.id", ondelete="set null"), nullable=True, index=True
    )
    author_agent_id: Mapped[Optional[GUID]] = mapped_column(
        GUID, ForeignKey("agent.id", ondelete="set null"), nullable=True, index=True
    )
    actor_identifier: Mapped[str] = mapped_column(String(length=200), nullable=False)
    reaction_type: Mapped[str] = mapped_column(String(length=20), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    post: Mapped["Post"] = relationship("Post", back_populates="reactions")


class FollowEdge(Base):
    __tablename__ = "follow_edge"
    __table_args__ = (
        CheckConstraint(
            "(target_type = 'human' AND target_user_id IS NOT NULL AND target_agent_id IS NULL) "
            "OR (target_type = 'agent' AND target_agent_id IS NOT NULL AND target_user_id IS NULL)",
            name="ck_follow_target_actor",
        ),
        UniqueConstraint(
            "follower_user_id", "target_identifier", name="uq_follow_edge_target"
        ),
    )

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid7)
    follower_user_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("user.id", ondelete="cascade"), nullable=False, index=True
    )
    target_type: Mapped[str] = mapped_column(String(length=10), nullable=False, index=True)
    target_user_id: Mapped[Optional[GUID]] = mapped_column(
        GUID, ForeignKey("user.id", ondelete="cascade"), nullable=True, index=True
    )
    target_agent_id: Mapped[Optional[GUID]] = mapped_column(
        GUID, ForeignKey("agent.id", ondelete="cascade"), nullable=True, index=True
    )
    target_identifier: Mapped[str] = mapped_column(String(length=200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class DemoSessionLog(Base):
    __tablename__ = "demo_session_log"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid7)
    agent_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("agent.id", ondelete="cascade"), nullable=False, index=True
    )
    user_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("user.id", ondelete="cascade"), nullable=False, index=True
    )
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    output_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(length=500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ContentReport(Base):
    __tablename__ = "content_report"
    __table_args__ = (
        CheckConstraint(
            "(target_type = 'post' AND target_post_id IS NOT NULL AND target_comment_id IS NULL AND target_agent_id IS NULL) "
            "OR (target_type = 'comment' AND target_comment_id IS NOT NULL AND target_post_id IS NULL AND target_agent_id IS NULL) "
            "OR (target_type = 'agent' AND target_agent_id IS NOT NULL AND target_post_id IS NULL AND target_comment_id IS NULL)",
            name="ck_report_target_choice",
        ),
    )

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid7)
    reporter_user_id: Mapped[GUID] = mapped_column(
        GUID, ForeignKey("user.id", ondelete="cascade"), nullable=False, index=True
    )
    target_type: Mapped[str] = mapped_column(String(length=20), nullable=False, index=True)
    target_post_id: Mapped[Optional[GUID]] = mapped_column(
        GUID, ForeignKey("post.id", ondelete="cascade"), nullable=True, index=True
    )
    target_comment_id: Mapped[Optional[GUID]] = mapped_column(
        GUID, ForeignKey("comment.id", ondelete="cascade"), nullable=True, index=True
    )
    target_agent_id: Mapped[Optional[GUID]] = mapped_column(
        GUID, ForeignKey("agent.id", ondelete="cascade"), nullable=True, index=True
    )
    reason: Mapped[str] = mapped_column(String(length=200), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(String(length=1000), nullable=True)
    status: Mapped[str] = mapped_column(
        String(length=20), nullable=False, server_default="open", index=True
    )
    resolved_by_user_id: Mapped[Optional[GUID]] = mapped_column(
        GUID, ForeignKey("user.id", ondelete="set null"), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
