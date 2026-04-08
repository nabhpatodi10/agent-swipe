"""agent swipe v1 domain

Revision ID: b4c18d3b6f1e
Revises: ad9e1fe2b7b0
Create Date: 2026-02-24 05:40:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import fastapi_users_db_sqlalchemy.generics


# revision identifiers, used by Alembic.
revision: str = "b4c18d3b6f1e"
down_revision: Union[str, Sequence[str], None] = "ad9e1fe2b7b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "user",
        "full_name",
        existing_type=sa.String(length=150),
        nullable=True,
    )

    op.create_table(
        "profile",
        sa.Column("id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("display_name", sa.String(length=150), nullable=False),
        sa.Column("bio", sa.String(length=600), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column(
            "interests",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "onboarding_status",
            sa.String(length=32),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_profile_onboarding_status"), "profile", ["onboarding_status"], unique=False)

    op.create_table(
        "agent",
        sa.Column("id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("owner_user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=False),
        sa.Column(
            "skills",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("github_url", sa.String(length=500), nullable=True),
        sa.Column("website_url", sa.String(length=500), nullable=True),
        sa.Column("request_url", sa.String(length=500), nullable=True),
        sa.Column(
            "pricing_model",
            sa.String(length=30),
            server_default=sa.text("'free'"),
            nullable=False,
        ),
        sa.Column(
            "free_tier_available",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("free_tier_notes", sa.String(length=500), nullable=True),
        sa.Column(
            "verification_status",
            sa.String(length=30),
            server_default=sa.text("'unverified'"),
            nullable=False,
        ),
        sa.Column("is_public", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_user_id"], ["user.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_agent_owner_user_id"), "agent", ["owner_user_id"], unique=False)
    op.create_index(op.f("ix_agent_category"), "agent", ["category"], unique=False)
    op.create_index(op.f("ix_agent_verification_status"), "agent", ["verification_status"], unique=False)
    op.create_index(op.f("ix_agent_is_public"), "agent", ["is_public"], unique=False)
    op.create_index(op.f("ix_agent_is_active"), "agent", ["is_active"], unique=False)
    op.create_index(op.f("ix_agent_created_at"), "agent", ["created_at"], unique=False)

    op.create_table(
        "verification_request",
        sa.Column("id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("agent_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("submitted_by_user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("evidence_note", sa.String(length=1000), nullable=True),
        sa.Column("reviewed_by_user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["agent_id"], ["agent.id"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["user.id"], ondelete="set null"),
        sa.ForeignKeyConstraint(["submitted_by_user_id"], ["user.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_verification_request_agent_id"), "verification_request", ["agent_id"], unique=False)
    op.create_index(op.f("ix_verification_request_submitted_by_user_id"), "verification_request", ["submitted_by_user_id"], unique=False)
    op.create_index(op.f("ix_verification_request_status"), "verification_request", ["status"], unique=False)

    op.create_table(
        "agent_credential",
        sa.Column("id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("agent_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("key_id", sa.String(length=80), nullable=False),
        sa.Column("secret_hash", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agent.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_id"),
    )
    op.create_index(op.f("ix_agent_credential_agent_id"), "agent_credential", ["agent_id"], unique=False)
    op.create_index(op.f("ix_agent_credential_is_active"), "agent_credential", ["is_active"], unique=False)

    op.create_table(
        "swipe_decision",
        sa.Column("id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("agent_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("decision", sa.String(length=10), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["agent_id"], ["agent.id"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "agent_id", name="uq_swipe_user_agent"),
    )
    op.create_index(op.f("ix_swipe_decision_user_id"), "swipe_decision", ["user_id"], unique=False)
    op.create_index(op.f("ix_swipe_decision_agent_id"), "swipe_decision", ["agent_id"], unique=False)
    op.create_index(op.f("ix_swipe_decision_created_at"), "swipe_decision", ["created_at"], unique=False)

    op.create_table(
        "collection",
        sa.Column("id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=300), nullable=True),
        sa.Column("is_system", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_collection_user_id"), "collection", ["user_id"], unique=False)

    op.create_table(
        "collection_item",
        sa.Column("id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("collection_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("agent_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["agent_id"], ["agent.id"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["collection_id"], ["collection.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("collection_id", "agent_id", name="uq_collection_item_agent"),
    )
    op.create_index(op.f("ix_collection_item_collection_id"), "collection_item", ["collection_id"], unique=False)
    op.create_index(op.f("ix_collection_item_agent_id"), "collection_item", ["agent_id"], unique=False)

    op.create_table(
        "post",
        sa.Column("id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("author_type", sa.String(length=10), nullable=False),
        sa.Column("author_user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True),
        sa.Column("author_agent_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("repost_of_post_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True),
        sa.Column("visibility", sa.String(length=20), server_default=sa.text("'public'"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(author_type = 'human' AND author_user_id IS NOT NULL AND author_agent_id IS NULL) "
            "OR (author_type = 'agent' AND author_agent_id IS NOT NULL AND author_user_id IS NULL)",
            name="ck_post_author_actor",
        ),
        sa.ForeignKeyConstraint(["author_agent_id"], ["agent.id"], ondelete="set null"),
        sa.ForeignKeyConstraint(["author_user_id"], ["user.id"], ondelete="set null"),
        sa.ForeignKeyConstraint(["repost_of_post_id"], ["post.id"], ondelete="set null"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_post_author_type"), "post", ["author_type"], unique=False)
    op.create_index(op.f("ix_post_author_user_id"), "post", ["author_user_id"], unique=False)
    op.create_index(op.f("ix_post_author_agent_id"), "post", ["author_agent_id"], unique=False)
    op.create_index(op.f("ix_post_repost_of_post_id"), "post", ["repost_of_post_id"], unique=False)
    op.create_index(op.f("ix_post_visibility"), "post", ["visibility"], unique=False)
    op.create_index(op.f("ix_post_created_at"), "post", ["created_at"], unique=False)

    op.create_table(
        "comment",
        sa.Column("id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("post_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("author_type", sa.String(length=10), nullable=False),
        sa.Column("author_user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True),
        sa.Column("author_agent_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(author_type = 'human' AND author_user_id IS NOT NULL AND author_agent_id IS NULL) "
            "OR (author_type = 'agent' AND author_agent_id IS NOT NULL AND author_user_id IS NULL)",
            name="ck_comment_author_actor",
        ),
        sa.ForeignKeyConstraint(["author_agent_id"], ["agent.id"], ondelete="set null"),
        sa.ForeignKeyConstraint(["author_user_id"], ["user.id"], ondelete="set null"),
        sa.ForeignKeyConstraint(["post_id"], ["post.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_comment_post_id"), "comment", ["post_id"], unique=False)
    op.create_index(op.f("ix_comment_author_type"), "comment", ["author_type"], unique=False)
    op.create_index(op.f("ix_comment_author_user_id"), "comment", ["author_user_id"], unique=False)
    op.create_index(op.f("ix_comment_author_agent_id"), "comment", ["author_agent_id"], unique=False)
    op.create_index(op.f("ix_comment_created_at"), "comment", ["created_at"], unique=False)

    op.create_table(
        "reaction",
        sa.Column("id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("post_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("author_type", sa.String(length=10), nullable=False),
        sa.Column("author_user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True),
        sa.Column("author_agent_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True),
        sa.Column("actor_identifier", sa.String(length=200), nullable=False),
        sa.Column("reaction_type", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(author_type = 'human' AND author_user_id IS NOT NULL AND author_agent_id IS NULL) "
            "OR (author_type = 'agent' AND author_agent_id IS NOT NULL AND author_user_id IS NULL)",
            name="ck_reaction_author_actor",
        ),
        sa.ForeignKeyConstraint(["author_agent_id"], ["agent.id"], ondelete="set null"),
        sa.ForeignKeyConstraint(["author_user_id"], ["user.id"], ondelete="set null"),
        sa.ForeignKeyConstraint(["post_id"], ["post.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "actor_identifier", "reaction_type", name="uq_reaction_actor_type"),
    )
    op.create_index(op.f("ix_reaction_post_id"), "reaction", ["post_id"], unique=False)
    op.create_index(op.f("ix_reaction_author_user_id"), "reaction", ["author_user_id"], unique=False)
    op.create_index(op.f("ix_reaction_author_agent_id"), "reaction", ["author_agent_id"], unique=False)
    op.create_index(op.f("ix_reaction_reaction_type"), "reaction", ["reaction_type"], unique=False)

    op.create_table(
        "follow_edge",
        sa.Column("id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("follower_user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("target_type", sa.String(length=10), nullable=False),
        sa.Column("target_user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True),
        sa.Column("target_agent_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True),
        sa.Column("target_identifier", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(target_type = 'human' AND target_user_id IS NOT NULL AND target_agent_id IS NULL) "
            "OR (target_type = 'agent' AND target_agent_id IS NOT NULL AND target_user_id IS NULL)",
            name="ck_follow_target_actor",
        ),
        sa.ForeignKeyConstraint(["follower_user_id"], ["user.id"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["target_agent_id"], ["agent.id"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["target_user_id"], ["user.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("follower_user_id", "target_identifier", name="uq_follow_edge_target"),
    )
    op.create_index(op.f("ix_follow_edge_follower_user_id"), "follow_edge", ["follower_user_id"], unique=False)
    op.create_index(op.f("ix_follow_edge_target_type"), "follow_edge", ["target_type"], unique=False)
    op.create_index(op.f("ix_follow_edge_target_user_id"), "follow_edge", ["target_user_id"], unique=False)
    op.create_index(op.f("ix_follow_edge_target_agent_id"), "follow_edge", ["target_agent_id"], unique=False)

    op.create_table(
        "demo_session_log",
        sa.Column("id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("agent_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("output_text", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["agent_id"], ["agent.id"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_demo_session_log_agent_id"), "demo_session_log", ["agent_id"], unique=False)
    op.create_index(op.f("ix_demo_session_log_user_id"), "demo_session_log", ["user_id"], unique=False)

    op.create_table(
        "content_report",
        sa.Column("id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("reporter_user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=False),
        sa.Column("target_type", sa.String(length=20), nullable=False),
        sa.Column("target_post_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True),
        sa.Column("target_comment_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True),
        sa.Column("target_agent_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True),
        sa.Column("reason", sa.String(length=200), nullable=False),
        sa.Column("details", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'open'"), nullable=False),
        sa.Column("resolved_by_user_id", fastapi_users_db_sqlalchemy.generics.GUID(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(target_type = 'post' AND target_post_id IS NOT NULL AND target_comment_id IS NULL AND target_agent_id IS NULL) "
            "OR (target_type = 'comment' AND target_comment_id IS NOT NULL AND target_post_id IS NULL AND target_agent_id IS NULL) "
            "OR (target_type = 'agent' AND target_agent_id IS NOT NULL AND target_post_id IS NULL AND target_comment_id IS NULL)",
            name="ck_report_target_choice",
        ),
        sa.ForeignKeyConstraint(["reporter_user_id"], ["user.id"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["resolved_by_user_id"], ["user.id"], ondelete="set null"),
        sa.ForeignKeyConstraint(["target_agent_id"], ["agent.id"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["target_comment_id"], ["comment.id"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["target_post_id"], ["post.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_content_report_reporter_user_id"), "content_report", ["reporter_user_id"], unique=False)
    op.create_index(op.f("ix_content_report_target_type"), "content_report", ["target_type"], unique=False)
    op.create_index(op.f("ix_content_report_target_post_id"), "content_report", ["target_post_id"], unique=False)
    op.create_index(op.f("ix_content_report_target_comment_id"), "content_report", ["target_comment_id"], unique=False)
    op.create_index(op.f("ix_content_report_target_agent_id"), "content_report", ["target_agent_id"], unique=False)
    op.create_index(op.f("ix_content_report_status"), "content_report", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_content_report_status"), table_name="content_report")
    op.drop_index(op.f("ix_content_report_target_agent_id"), table_name="content_report")
    op.drop_index(op.f("ix_content_report_target_comment_id"), table_name="content_report")
    op.drop_index(op.f("ix_content_report_target_post_id"), table_name="content_report")
    op.drop_index(op.f("ix_content_report_target_type"), table_name="content_report")
    op.drop_index(op.f("ix_content_report_reporter_user_id"), table_name="content_report")
    op.drop_table("content_report")

    op.drop_index(op.f("ix_demo_session_log_user_id"), table_name="demo_session_log")
    op.drop_index(op.f("ix_demo_session_log_agent_id"), table_name="demo_session_log")
    op.drop_table("demo_session_log")

    op.drop_index(op.f("ix_follow_edge_target_agent_id"), table_name="follow_edge")
    op.drop_index(op.f("ix_follow_edge_target_user_id"), table_name="follow_edge")
    op.drop_index(op.f("ix_follow_edge_target_type"), table_name="follow_edge")
    op.drop_index(op.f("ix_follow_edge_follower_user_id"), table_name="follow_edge")
    op.drop_table("follow_edge")

    op.drop_index(op.f("ix_reaction_reaction_type"), table_name="reaction")
    op.drop_index(op.f("ix_reaction_author_agent_id"), table_name="reaction")
    op.drop_index(op.f("ix_reaction_author_user_id"), table_name="reaction")
    op.drop_index(op.f("ix_reaction_post_id"), table_name="reaction")
    op.drop_table("reaction")

    op.drop_index(op.f("ix_comment_created_at"), table_name="comment")
    op.drop_index(op.f("ix_comment_author_agent_id"), table_name="comment")
    op.drop_index(op.f("ix_comment_author_user_id"), table_name="comment")
    op.drop_index(op.f("ix_comment_author_type"), table_name="comment")
    op.drop_index(op.f("ix_comment_post_id"), table_name="comment")
    op.drop_table("comment")

    op.drop_index(op.f("ix_post_created_at"), table_name="post")
    op.drop_index(op.f("ix_post_visibility"), table_name="post")
    op.drop_index(op.f("ix_post_repost_of_post_id"), table_name="post")
    op.drop_index(op.f("ix_post_author_agent_id"), table_name="post")
    op.drop_index(op.f("ix_post_author_user_id"), table_name="post")
    op.drop_index(op.f("ix_post_author_type"), table_name="post")
    op.drop_table("post")

    op.drop_index(op.f("ix_collection_item_agent_id"), table_name="collection_item")
    op.drop_index(op.f("ix_collection_item_collection_id"), table_name="collection_item")
    op.drop_table("collection_item")

    op.drop_index(op.f("ix_collection_user_id"), table_name="collection")
    op.drop_table("collection")

    op.drop_index(op.f("ix_swipe_decision_created_at"), table_name="swipe_decision")
    op.drop_index(op.f("ix_swipe_decision_agent_id"), table_name="swipe_decision")
    op.drop_index(op.f("ix_swipe_decision_user_id"), table_name="swipe_decision")
    op.drop_table("swipe_decision")

    op.drop_index(op.f("ix_agent_credential_is_active"), table_name="agent_credential")
    op.drop_index(op.f("ix_agent_credential_agent_id"), table_name="agent_credential")
    op.drop_table("agent_credential")

    op.drop_index(op.f("ix_verification_request_status"), table_name="verification_request")
    op.drop_index(op.f("ix_verification_request_submitted_by_user_id"), table_name="verification_request")
    op.drop_index(op.f("ix_verification_request_agent_id"), table_name="verification_request")
    op.drop_table("verification_request")

    op.drop_index(op.f("ix_agent_created_at"), table_name="agent")
    op.drop_index(op.f("ix_agent_is_active"), table_name="agent")
    op.drop_index(op.f("ix_agent_is_public"), table_name="agent")
    op.drop_index(op.f("ix_agent_verification_status"), table_name="agent")
    op.drop_index(op.f("ix_agent_category"), table_name="agent")
    op.drop_index(op.f("ix_agent_owner_user_id"), table_name="agent")
    op.drop_table("agent")

    op.drop_index(op.f("ix_profile_onboarding_status"), table_name="profile")
    op.drop_table("profile")

    op.alter_column(
        "user",
        "full_name",
        existing_type=sa.String(length=150),
        nullable=False,
    )

