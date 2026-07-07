"""initial schema

Revision ID: 20260707_0001
Revises:
Create Date: 2026-07-07
"""

from collections.abc import Sequence

import sqlalchemy as sa

revision: str = "20260707_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    from alembic import op as alembic_op

    alembic_op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(64)),
        sa.Column("first_name", sa.String(128)),
        sa.Column("language_code", sa.String(8), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    alembic_op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)
    alembic_op.create_table(
        "downloads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.telegram_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("title", sa.String(255)),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("file_size", sa.Integer()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    alembic_op.create_index("ix_downloads_status", "downloads", ["status"])
    alembic_op.create_index(
        "ix_downloads_user_created", "downloads", ["user_id", sa.text("created_at DESC")]
    )


def downgrade() -> None:
    from alembic import op as alembic_op

    alembic_op.drop_index("ix_downloads_user_created", table_name="downloads")
    alembic_op.drop_index("ix_downloads_status", table_name="downloads")
    alembic_op.drop_table("downloads")
    alembic_op.drop_index("ix_users_telegram_id", table_name="users")
    alembic_op.drop_table("users")
