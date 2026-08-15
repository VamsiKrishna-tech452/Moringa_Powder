from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Lead(Base):
    __tablename__ = "leads"

    __table_args__ = (
        UniqueConstraint(
            "abn",
            name="uq_leads_abn",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    abn: Mapped[str] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )

    company_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    ) 

    country_code: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
       index=True,
    )

    registration_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,

    )

    entity_type: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    gst_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    state: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )

    postcode: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    lead_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
    )

    classification: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    positive_signals: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    negative_signals: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    website: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    buyer_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    import_activity: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    india_sourcing: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    bulk_buyer: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    verification_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="unverified",
    )

    source: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
