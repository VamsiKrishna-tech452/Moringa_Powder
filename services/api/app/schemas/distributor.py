from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DistributorBase(BaseModel):
    company_name: str
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    country: str | None = None

    source: str | None = None
    verification_status: str | None = None
    notes: str | None = None

    product: str | None = None
    buyer_type: str | None = None
    import_activity: str | None = None
    india_sourcing: str | None = None
    bulk_buyer: str | None = None


class DistributorCreate(DistributorBase):
    pass


class DistributorUpdate(BaseModel):
    company_name: str | None = None
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    country: str | None = None

    source: str | None = None
    verification_status: str | None = None
    notes: str | None = None

    product: str | None = None
    buyer_type: str | None = None
    import_activity: str | None = None
    india_sourcing: str | None = None
    bulk_buyer: str | None = None
    last_verified_at: datetime | None = None


class DistributorResponse(DistributorBase):
    id: int
    created_at: datetime
    last_verified_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class DistributorListResponse(BaseModel):
    items: list[DistributorResponse]
    page: int
    page_size: int
    total: int
    pages: int

from pydantic import BaseModel, Field


class DistributorIngestItem(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    country: str | None = "Australia"
    source: str | None = None
    verification_status: str | None = "unverified"
    notes: str | None = None

    product: str | None = "Moringa Leaf Powder"
    buyer_type: str | None = None
    import_activity: str | None = None
    india_sourcing: str | None = None
    bulk_buyer: str | None = None


class DistributorIngestRequest(BaseModel):
    records: list[DistributorIngestItem]


class DistributorIngestResponse(BaseModel):
    total_received: int
    created: int
    duplicates: int
    created_ids: list[int]
    duplicate_ids: list[int]
