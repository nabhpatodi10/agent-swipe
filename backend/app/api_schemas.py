from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from typing_extensions import Annotated

from pydantic import BaseModel, BeforeValidator, Field
from uuid_utils.compat import UUID


def _coerce_uuid(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return str(value)


UUIDField = Annotated[UUID, BeforeValidator(_coerce_uuid)]


class ProfileRead(BaseModel):
    id: UUIDField
    user_id: UUIDField
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    website_url: Optional[str] = None
    interests: list[str]
    onboarding_status: str
    onboarding_completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    bio: Optional[str] = Field(default=None, max_length=600)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    location: Optional[str] = Field(default=None, max_length=120)
    website_url: Optional[str] = Field(default=None, max_length=500)
    interests: Optional[list[str]] = None


class OnboardingRead(BaseModel):
    onboarding_status: str
    onboarding_completed_at: Optional[datetime] = None


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str = Field(min_length=1, max_length=2000)
    skills: list[str] = Field(min_length=1)
    category: str = Field(min_length=1, max_length=80)
    github_url: Optional[str] = Field(default=None, max_length=500)
    website_url: Optional[str] = Field(default=None, max_length=500)
    request_url: Optional[str] = Field(default=None, max_length=500)
    pricing_model: Literal["free", "freemium", "paid"]
    free_tier_available: bool = False
    free_tier_notes: Optional[str] = Field(default=None, max_length=500)
    is_public: bool = True


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    description: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    skills: Optional[list[str]] = None
    category: Optional[str] = Field(default=None, min_length=1, max_length=80)
    github_url: Optional[str] = Field(default=None, max_length=500)
    website_url: Optional[str] = Field(default=None, max_length=500)
    request_url: Optional[str] = Field(default=None, max_length=500)
    pricing_model: Optional[Literal["free", "freemium", "paid"]] = None
    free_tier_available: Optional[bool] = None
    free_tier_notes: Optional[str] = Field(default=None, max_length=500)
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class AgentRead(BaseModel):
    id: UUIDField
    owner_user_id: UUIDField
    name: str
    slug: str
    description: str
    skills: list[str]
    category: str
    github_url: Optional[str] = None
    website_url: Optional[str] = None
    request_url: Optional[str] = None
    pricing_model: str
    free_tier_available: bool
    free_tier_notes: Optional[str] = None
    verification_status: str
    is_public: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AgentSummary(BaseModel):
    id: UUIDField
    slug: str
    name: str
    description: str
    category: str
    verification_status: str
    website_url: Optional[str] = None
    github_url: Optional[str] = None

    model_config = {"from_attributes": True}


class SwipeDecisionRequest(BaseModel):
    agent_id: UUIDField
    decision: Literal["left", "right"]


class VerificationRequestCreate(BaseModel):
    evidence_note: Optional[str] = Field(default=None, max_length=1000)


class VerificationRequestRead(BaseModel):
    id: UUIDField
    agent_id: UUIDField
    submitted_by_user_id: UUIDField
    status: str
    evidence_note: Optional[str] = None
    reviewed_by_user_id: Optional[UUIDField] = None
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentCredentialCreate(BaseModel):
    label: Optional[str] = Field(default=None, max_length=120)


class AgentCredentialRead(BaseModel):
    id: UUIDField
    agent_id: UUIDField
    key_id: str
    label: Optional[str] = None
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime
    revoked_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AgentCredentialSecretRead(BaseModel):
    credential_id: UUIDField
    key_id: str
    secret: str
    created_at: datetime


class AgentTokenRequest(BaseModel):
    key_id: str
    secret: str


class AgentTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class HumanPostCreate(BaseModel):
    text: str = Field(min_length=1)
    visibility: Literal["public"] = "public"


class AgentPostCreate(BaseModel):
    text: str = Field(min_length=1)
    visibility: Literal["public"] = "public"


class PostRead(BaseModel):
    id: UUIDField
    author_type: str
    author_user_id: Optional[UUIDField] = None
    author_agent_id: Optional[UUIDField] = None
    text: str
    repost_of_post_id: Optional[UUIDField] = None
    visibility: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CommentCreate(BaseModel):
    text: str = Field(min_length=1)


class CommentRead(BaseModel):
    id: UUIDField
    post_id: UUIDField
    author_type: str
    author_user_id: Optional[UUIDField] = None
    author_agent_id: Optional[UUIDField] = None
    text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReactionCreate(BaseModel):
    reaction_type: Literal["like", "insight", "celebrate"]


class ShareCreate(BaseModel):
    text: Optional[str] = None


class FollowCreate(BaseModel):
    target_type: Literal["human", "agent"]
    target_user_id: Optional[UUIDField] = None
    target_agent_id: Optional[UUIDField] = None


class FollowRead(BaseModel):
    id: UUIDField
    follower_user_id: UUIDField
    target_type: str
    target_user_id: Optional[UUIDField] = None
    target_agent_id: Optional[UUIDField] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FollowerRead(BaseModel):
    user_id: UUIDField
    username: str
    full_name: Optional[str] = None


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=300)


class CollectionUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=300)


class CollectionRead(BaseModel):
    id: UUIDField
    user_id: UUIDField
    name: str
    description: Optional[str] = None
    is_system: bool
    created_at: datetime
    updated_at: datetime
    items: list[AgentSummary] = Field(default_factory=list)


class CollectionItemCreate(BaseModel):
    agent_id: UUIDField


class FeedRead(BaseModel):
    mode: Literal["discover", "following"]
    posts: list[PostRead]


class DemoChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=16000)
    session_id: Optional[str] = Field(default=None, max_length=120)


class DemoChatResponse(BaseModel):
    reply: str
    meta: dict = Field(default_factory=dict)


class ReportCreate(BaseModel):
    target_type: Literal["post", "comment", "agent"]
    target_id: UUIDField
    reason: str = Field(min_length=1, max_length=200)
    details: Optional[str] = Field(default=None, max_length=1000)


class ReportRead(BaseModel):
    id: UUIDField
    reporter_user_id: UUIDField
    target_type: str
    target_post_id: Optional[UUIDField] = None
    target_comment_id: Optional[UUIDField] = None
    target_agent_id: Optional[UUIDField] = None
    reason: str
    details: Optional[str] = None
    status: str
    resolved_by_user_id: Optional[UUIDField] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportResolveRequest(BaseModel):
    status: Literal["resolved"]


class VerificationRejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)

