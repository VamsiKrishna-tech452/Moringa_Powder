from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LeadResponse(BaseModel):
    id: int
    abn: str | None
    company_name: str

    entity_type: str | None = None
    status: str | None = None
    gst_status: str | None = None

    state: str | None = None
    postcode: str | None = None
    country: str | None = None
    country_code: str | None = None
    registration_number: str | None = None

    lead_score: int
    classification: str | None = None

    positive_signals: str | None = None
    negative_signals: str | None = None

    website: str | None = None
    email: str | None = None
    phone: str | None = None

    buyer_type: str | None = None
    import_activity: str | None = None
    india_sourcing: str | None = None
    bulk_buyer: str | None = None

    verification_status: str | None = None
    source: str | None = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class LeadListResponse(BaseModel):
    items: list[LeadResponse]

    page: int
    page_size: int
    total: int
    pages: int
