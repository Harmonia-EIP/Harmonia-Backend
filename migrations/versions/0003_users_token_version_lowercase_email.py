"""Utilisateurs : version de token (révocation) + emails en minuscules.

Les emails ne sont passés en minuscules que s'ils n'entrent pas en
conflit avec un autre compte (les recherches sont de toute façon
insensibles à la casse).

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-25
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
        "token_version INTEGER NOT NULL DEFAULT 0"
    )
    op.execute(
        """
        UPDATE users AS u
        SET email = lower(u.email)
        WHERE u.email <> lower(u.email)
          AND NOT EXISTS (
              SELECT 1 FROM users AS o
              WHERE o.id <> u.id AND lower(o.email) = lower(u.email)
          )
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS token_version")
