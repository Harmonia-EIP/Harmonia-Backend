"""Schéma initial (état avant Alembic, créé jusqu'ici par create_all).

Les bases existantes ne rejouent pas cette révision : migrate.py les
marque directement en 0001 (alembic stamp) puis applique la suite.

Revision ID: 0001
Revises:
Create Date: 2026-11-25
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("description", sa.String()),
    )
    op.create_index("ix_roles_code", "roles", ["code"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "role_id",
            sa.Integer(),
            sa.ForeignKey("roles.id", ondelete="RESTRICT"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "user_info",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("avatar_url", sa.String()),
    )
    op.create_index("ix_user_info_username", "user_info", ["username"], unique=True)

    op.create_table(
        "user_params",
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("color_1", sa.String(7), nullable=False),
        sa.Column("color_2", sa.String(7), nullable=False),
        sa.Column("color_3", sa.String(7), nullable=False),
        sa.Column("last_color_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "last_color_id >= 1 AND last_color_id <= 3",
            name="ck_user_params_last_color_id",
        ),
    )

    op.create_table(
        "history",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(1000), nullable=False),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_history_user_last_used", "history", ["user_id", "last_used_at"]
    )


def downgrade() -> None:
    op.drop_table("history")
    op.drop_table("user_params")
    op.drop_table("user_info")
    op.drop_table("users")
    op.drop_table("roles")
