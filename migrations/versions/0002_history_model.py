"""Historique : nom jusqu'à 1000 caractères + modèle IA utilisé.

Idempotent : ces changements ont pu être appliqués à la main avant
Alembic (anciens scripts migrate_*.py).

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-25
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE history ALTER COLUMN name TYPE VARCHAR(1000)")
    op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS model_id VARCHAR(100)")
    op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS model_name VARCHAR(200)")


def downgrade() -> None:
    op.execute("ALTER TABLE history DROP COLUMN IF EXISTS model_name")
    op.execute("ALTER TABLE history DROP COLUMN IF EXISTS model_id")
