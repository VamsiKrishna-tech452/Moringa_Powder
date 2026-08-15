"""add country to leads

Revision ID: 019bbe7fe01d
Revises: 0314dec8152f
Create Date: 2026-08-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "019bbe7fe01d"
down_revision: Union[str, Sequence[str], None] = "0314dec8152f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "leads",
        sa.Column(
            "country",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_leads_country",
        "leads",
        ["country"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_leads_country",
        table_name="leads",
    )

    op.drop_column(
        "leads",
        "country",
    )
