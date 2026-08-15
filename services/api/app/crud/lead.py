from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.lead import Lead


def get_leads(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    state: str | None = None,
    classification: str | None = None,
    min_score: int | None = None,
    country_code: str | None = None,
):
    query = select(Lead)

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    if search:
        search_pattern = f"%{search.strip()}%"

        query = query.where(
            or_(
                Lead.company_name.ilike(search_pattern),
                Lead.abn.ilike(search_pattern),
            )
        )


    # ---------------------------------------------------------
    # Country
    # ---------------------------------------------------------

    if country_code:
        query = query.where(
            Lead.country_code == country_code.upper()
        )

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    if state:
        query = query.where(
            Lead.state == state.upper()
        )

    # ---------------------------------------------------------
    # Classification
    # ---------------------------------------------------------

    if classification:
        query = query.where(
            Lead.classification == classification
        )

    # ---------------------------------------------------------
    # Minimum lead score
    # ---------------------------------------------------------

    if min_score is not None:
        query = query.where(
            Lead.lead_score >= min_score
        )

    # ---------------------------------------------------------
    # Total count
    # ---------------------------------------------------------

    count_query = select(
        func.count()
    ).select_from(
        query.subquery()
    )

    total = db.scalar(count_query) or 0

    # ---------------------------------------------------------
    # Ordering
    #
    # Highest potential leads first.
    # ---------------------------------------------------------

    query = query.order_by(
        Lead.lead_score.desc(),
        Lead.company_name.asc(),
    )

    # ---------------------------------------------------------
    # Pagination
    # ---------------------------------------------------------

    offset = (page - 1) * page_size

    query = query.offset(offset).limit(page_size)

    leads = list(
        db.scalars(query).all()
    )

    return leads, total


def get_lead(
    db: Session,
    lead_id: int,
):
    return db.get(
        Lead,
        lead_id,
    )
