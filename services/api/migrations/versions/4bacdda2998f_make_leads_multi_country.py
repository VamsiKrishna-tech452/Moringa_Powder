"""make leads multi country

Revision ID: 4bacdda2998f
Revises: 019bbe7fe01d
Create Date: 2026-08-11
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4bacdda2998f"
down_revision: Union[str, Sequence[str], None] = "019bbe7fe01d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --------------------------------------------------------
    # Allow ABN to be NULL for non-Australian companies
    # --------------------------------------------------------

    op.alter_column(
        "leads",
        "abn",
        existing_type=sa.String(length=20),
        nullable=True,
    )

    # --------------------------------------------------------
    # Add generic country code
    # --------------------------------------------------------

    op.add_column(
        "leads",
        sa.Column(
            "country_code",
            sa.String(length=2),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_leads_country_code",
        "leads",
        ["country_code"],
        unique=False,
    )

    # --------------------------------------------------------
    # Add generic registration/company identifier
    # --------------------------------------------------------

    op.add_column(
        "leads",
        sa.Column(
            "registration_number",
            sa.String(length=100),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_leads_registration_number",
        "leads",
        ["registration_number"],
        unique=False,
    )

    # --------------------------------------------------------
    # Populate existing Australian records
    #
    # Existing ABN becomes the generic registration number.
    # --------------------------------------------------------

    op.execute(
        """
        UPDATE leads
        SET
            country_code = 'AU',
            registration_number = abn
        WHERE abn IS NOT NULL
        """
    )


def downgrade() -> None:
    # Remove registration number index/column
    op.drop_index(
        "ix_leads_registration_number",
        table_name="leads",
    )

    op.drop_column(
        "leads",
        "registration_number",
    )

    # Remove country code index/column
    op.drop_index(
        "ix_leads_country_code",
        table_name="leads",
    )

    op.drop_column(
        "leads",
        "country_code",
    )

    # Restore ABN requirement
    op.alter_column(
        "leads",
        "abn",
        existing_type=sa.String(length=20),
        nullable=False,
    )
