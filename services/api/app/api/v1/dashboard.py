from collections import Counter
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.lead import Lead


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


# ============================================================
# DASHBOARD HTML
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[3]


@router.get(
    "",
    response_class=HTMLResponse,
)
def dashboard():

    html_file = (
        BASE_DIR
        / "app"
        / "dashboard"
        / "index.html"
    )

    if not html_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Dashboard HTML not found",
        )

    return HTMLResponse(
        html_file.read_text(
            encoding="utf-8"
        )
    )


# ============================================================
# DASHBOARD STATS
# ============================================================

@router.get("/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
):

    total_candidates = (
        db.scalar(
            select(func.count())
            .select_from(Lead)
        )
        or 0
    )

    high_potential = (
        db.scalar(
            select(func.count())
            .select_from(Lead)
            .where(
                Lead.classification
                == "High potential"
            )
        )
        or 0
    )

    good_potential = (
        db.scalar(
            select(func.count())
            .select_from(Lead)
            .where(
                Lead.classification
                == "Good potential"
            )
        )
        or 0
    )

    possible = (
        db.scalar(
            select(func.count())
            .select_from(Lead)
            .where(
                Lead.classification
                == "Possible"
            )
        )
        or 0
    )

    average_score = (
        db.scalar(
            select(func.avg(Lead.lead_score))
        )
        or 0
    )

    highest_score = (
        db.scalar(
            select(func.max(Lead.lead_score))
        )
        or 0
    )

    lowest_score = (
        db.scalar(
            select(func.min(Lead.lead_score))
        )
        or 0
    )

    state_rows = db.execute(
        select(
            Lead.state,
            func.count()
        )
        .where(
            Lead.state.is_not(None)
        )
        .group_by(Lead.state)
        .order_by(
            func.count().desc()
        )
    ).all()

    states = {
        state: count
        for state, count in state_rows
        if state
    }

    return {
        "total_candidates": total_candidates,
        "high_potential": high_potential,
        "good_potential": good_potential,
        "possible": possible,
        "average_score": round(
            float(average_score),
            2,
        ),
        "highest_score": highest_score,
        "lowest_score": lowest_score,
        "states": states,
    }


# ============================================================
# TOP LEADS
# ============================================================

@router.get("/top-leads")
def top_leads(
    limit: int = Query(
        20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
):

    leads = db.scalars(
        select(Lead)
        .order_by(
            Lead.lead_score.desc(),
            Lead.company_name.asc(),
        )
        .limit(limit)
    ).all()

    return leads


# ============================================================
# SEARCH / FILTER LEADS
# ============================================================

@router.get("/leads")
def dashboard_leads(
    search: str | None = None,
    country: str | None = None,
    state: str | None = None,
    classification: str | None = None,
    minimum_score: int | None = Query(
        None,
        ge=0,
    ),
    limit: int = Query(
        100,
        ge=1,
        le=500,
    ),
    db: Session = Depends(get_db),
):

    query = select(Lead)

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:

        search_value = (
            f"%{search.strip()}%"
        )

        query = query.where(
            (
                Lead.company_name.ilike(
                    search_value
                )
            )
            |
            (
                Lead.abn.ilike(
                    search_value
                )
            )
        )

    # --------------------------------------------------------
    # COUNTRY
    # --------------------------------------------------------

    if country:
        query = query.where(
            Lead.country == country
        )

    # --------------------------------------------------------
    # STATE
    # --------------------------------------------------------

    if state:

        query = query.where(
            Lead.state == state.upper()
        )

    # --------------------------------------------------------
    # CLASSIFICATION
    # --------------------------------------------------------

    if classification:

        query = query.where(
            Lead.classification
            == classification
        )

    # --------------------------------------------------------
    # MINIMUM SCORE
    # --------------------------------------------------------

    if minimum_score is not None:

        query = query.where(
            Lead.lead_score
            >= minimum_score
        )

    # --------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------

    count_query = select(
        func.count()
    ).select_from(
        query.subquery()
    )

    total = (
        db.scalar(count_query)
        or 0
    )

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    leads = db.scalars(
        query
        .order_by(
            Lead.lead_score.desc(),
            Lead.company_name.asc(),
        )
        .limit(limit)
    ).all()

    return {
        "total": total,
        "items": leads,
    }


# ============================================================
# GET SINGLE LEAD
# ============================================================

@router.get("/leads/{lead_id}")
def get_dashboard_lead(
    lead_id: int,
    db: Session = Depends(get_db),
):

    lead = db.get(
        Lead,
        lead_id,
    )

    if lead is None:

        raise HTTPException(
            status_code=404,

            detail="Lead not found",
        )

    return lead
