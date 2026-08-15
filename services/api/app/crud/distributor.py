from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.distributor import Distributor
from app.schemas.distributor import (
    DistributorCreate,
    DistributorUpdate,
    DistributorIngestItem,
)


def create_distributor(
    db: Session,
    distributor: DistributorCreate,
) -> Distributor:

    db_distributor = Distributor(
        company_name=distributor.company_name,
        website=distributor.website,
        email=distributor.email,
        phone=distributor.phone,
        country=distributor.country,
        source=distributor.source,
        verification_status=distributor.verification_status,
        notes=distributor.notes,
        product=distributor.product,
        buyer_type=distributor.buyer_type,
        import_activity=distributor.import_activity,
        india_sourcing=distributor.india_sourcing,
        bulk_buyer=distributor.bulk_buyer,
    )

    db.add(db_distributor)
    db.commit()
    db.refresh(db_distributor)

    return db_distributor


def get_distributor(
    db: Session,
    distributor_id: int,
) -> Distributor | None:

    statement = select(Distributor).where(
        Distributor.id == distributor_id
    )

    return db.scalars(statement).first()


def get_distributors(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    country: str | None = None,
    verification_status: str | None = None,
) -> tuple[list[Distributor], int]:

    # Base query
    statement = select(Distributor)

    # Search by company name
    if search:
        statement = statement.where(
            Distributor.company_name.ilike(f"%{search}%")
        )

    # Filter by country
    if country:
        statement = statement.where(
            Distributor.country.ilike(country)
        )

    # Filter by verification status
    if verification_status:
        statement = statement.where(
            Distributor.verification_status.ilike(verification_status)
        )

    # Get total matching records
    count_statement = select(func.count()).select_from(
        statement.subquery()
    )

    total = db.scalar(count_statement) or 0

    # Calculate pagination offset
    offset = (page - 1) * page_size

    # Get requested page
    statement = (
        statement
        .order_by(Distributor.id)
        .offset(offset)
        .limit(page_size)
    )

    distributors = list(db.scalars(statement).all())

    return distributors, total


def find_duplicate_distributor(
    db: Session,
    distributor: DistributorIngestItem,
) -> Distributor | None:

    company_name = distributor.company_name.strip().lower()

    country = None
    if distributor.country:
        country = distributor.country.strip().lower()

    # 1. Match by company name + country
    statement = select(Distributor).where(
        func.lower(func.trim(Distributor.company_name)) == company_name
    )

    if country:
        statement = statement.where(
            func.lower(func.trim(Distributor.country)) == country
        )

    existing = db.scalars(statement).first()

    if existing:
        return existing

    # 2. Match by email
    if distributor.email:
        email = distributor.email.strip().lower()

        statement = select(Distributor).where(
            func.lower(func.trim(Distributor.email)) == email
        )

        existing = db.scalars(statement).first()

        if existing:
            return existing

    # 3. Match by website
    if distributor.website:
        website = distributor.website.strip().rstrip("/").lower()

        statement = select(Distributor).where(
            func.lower(
                func.rtrim(func.trim(Distributor.website), "/")
            ) == website
        )

        existing = db.scalars(statement).first()

        if existing:
            return existing

    return None


def ingest_distributors(
    db: Session,
    records: list[DistributorIngestItem],
) -> tuple[list[Distributor], list[Distributor]]:

    created_distributors = []
    duplicate_distributors = []

    for record in records:

        existing = find_duplicate_distributor(
            db,
            record,
        )

        if existing:
            duplicate_distributors.append(existing)
            continue

        db_distributor = Distributor(
            company_name=record.company_name.strip(),
            website=record.website,
            email=record.email,
            phone=record.phone,
            country=record.country,
            source=record.source,
            verification_status=record.verification_status,
            notes=record.notes,
            product=record.product,
            buyer_type=record.buyer_type,
            import_activity=record.import_activity,
            india_sourcing=record.india_sourcing,
            bulk_buyer=record.bulk_buyer,
        )

        db.add(db_distributor)

        # Make the record visible to duplicate checks
        # within the same batch.
        db.flush()

        created_distributors.append(db_distributor)

    db.commit()

    for distributor in created_distributors:
        db.refresh(distributor)

    return created_distributors, duplicate_distributors
 


def update_distributor(
    db: Session,
    db_distributor: Distributor,
    distributor: DistributorUpdate,
) -> Distributor:

    update_data = distributor.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_distributor, field, value)

    db.commit()
    db.refresh(db_distributor)

    return db_distributor


def delete_distributor(
    db: Session,
    db_distributor: Distributor,
) -> None:

    db.delete(db_distributor)
    db.commit()
