import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud import lead as lead_crud
from app.db.dependencies import get_db
from app.schemas.lead import (
    LeadListResponse,
    LeadResponse,
)
from app.services.website_discovery import (
    discover_website,
)

from app.services.email_extraction import (
    extract_email,
)

from app.services.phone_extraction import (
    extract_phone,
)

from app.services.buyer_verification import (
    verify_buyer,
)

from app.services.india_sourcing import (
    detect_india_sourcing,
)

from app.services.import_activity import (
    detect_import_activity,
)

from app.services.bulk_buyer import (
    detect_bulk_buyer,
)

from app.services.lead_scoring import (
    calculate_final_score,
)

router = APIRouter(
    prefix="/leads",
    tags=["Leads"],
)


# ============================================================
# LIST / SEARCH / FILTER LEADS
# ============================================================

@router.get(
    "",
    response_model=LeadListResponse,
)
def get_leads(
    page: int = Query(
        1,
        ge=1,
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
    ),
    search: str | None = Query(
        None,
        description="Search by company name or ABN",
    ),
    state: str | None = Query(
        None,
        description="Filter by Australian state",
    ),

    country_code: str | None = Query(
        None,
        min_length=2,
        max_length=2,
        description="Filter by country code, e.g. AU, US, GB",
    ),
    classification: str | None = Query(
        None,
        description="Filter by lead classification",
    ),
    min_score: int | None = Query(
        None,
        ge=0,
        description="Minimum lead score",
    ),
    db: Session = Depends(get_db),
):
    """
    Return paginated leads with optional search and filters.
    """

    leads, total = lead_crud.get_leads(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        state=state,
        classification=classification,
        min_score=min_score,
        country_code=country_code,
    )

    pages = (
        math.ceil(total / page_size)
        if total > 0
        else 0
    )

    return {
        "items": leads,
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": pages,
    }


# ============================================================
# GET SINGLE LEAD
# ============================================================

@router.get(
    "/{lead_id}",
    response_model=LeadResponse,
)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """
    Return complete details for one lead.
    """

    lead = lead_crud.get_lead(
        db=db,
        lead_id=lead_id,
    )

    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    return lead


# ============================================================
# ENRICH LEAD
# ============================================================

@router.post(
    "/{lead_id}/enrich",
    response_model=LeadResponse,
    status_code=status.HTTP_200_OK,
)
def     enrich_lead(
    lead_id: int,
    db: Session = Depends(get_db),
):
    """
    Enrich a lead with website and email information.

    Current steps:
        1. Find the lead.
        2. Discover the company website.
        3. Extract public business email.
        4. Save website and email to PostgreSQL.

    Phone, verification, import activity, India sourcing,
    bulk buyer detection and final scoring are not performed yet.
    """

    # --------------------------------------------------------
    # Get lead
    # --------------------------------------------------------

    lead = lead_crud.get_lead(
        db=db,
        lead_id=lead_id,
    )

    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
        # --------------------------------------------------------
    # Discover website
    # --------------------------------------------------------

    website = discover_website(
        company_name=lead.company_name,
        state=lead.state,
        postcode=lead.postcode,
    )

    print("ENRICH DEBUG - DISCOVERED WEBSITE:", website)
    print("ENRICH DEBUG - LEAD WEBSITE BEFORE:", lead.website)

    if website:
        lead.website = website

    print("ENRICH DEBUG - LEAD WEBSITE AFTER:", lead.website)

    # --------------------------------------------------------
    # Extract public business email
    # --------------------------------------------------------

    if lead.website:
        print(
            "ENRICH DEBUG - EXTRACTING EMAIL FROM:",
            lead.website,
        )

        email = extract_email(
            lead.website,
        )

        print(
            "ENRICH DEBUG - EXTRACTED EMAIL:",
            email,
        )

        if email:
            lead.email = email

        print(
            "ENRICH DEBUG - LEAD EMAIL AFTER:",
            lead.email,
        )

    # --------------------------------------------------------
    # Extract public business phone
    # --------------------------------------------------------

    if lead.website:
        print(
            "ENRICH DEBUG - EXTRACTING PHONE FROM:",
            lead.website,
        )

        phone = extract_phone(
            lead.website,
        )

        print(
            "ENRICH DEBUG - EXTRACTED PHONE:",
            phone,
        )

        if phone:
            lead.phone = phone

        print(
            "ENRICH DEBUG - LEAD PHONE AFTER:",
            lead.phone,
        )
    # --------------------------------------------------------
    # Save basic contact enrichment immediately
    # --------------------------------------------------------

    db.add(lead)
    
    db.commit() 
    
    db.refresh(lead)

    # --------------------------------------------------------
    # Verify buyer
    # --------------------------------------------------------

    if lead.website:
        verification_status = verify_buyer(
            company_name=lead.company_name,
            website=lead.website,
            email=lead.email,
            state=lead.state,
            postcode=lead.postcode,
        )

        lead.verification_status = verification_status

    # --------------------------------------------------------
    # Detect India sourcing
    # --------------------------------------------------------

    india_sourcing = detect_india_sourcing(
        company_name=lead.company_name,
        website=lead.website,
        state=lead.state,
        postcode=lead.postcode,
    )

    lead.india_sourcing = india_sourcing

    # --------------------------------------------------------
    # Detect import activity
    # --------------------------------------------------------

    import_activity = detect_import_activity(
        company_name=lead.company_name,
        website=lead.website,
        state=lead.state,
        postcode=lead.postcode,
    )

    lead.import_activity = import_activity

    # --------------------------------------------------------
    # Detect bulk buyer
    # --------------------------------------------------------

    bulk_buyer = detect_bulk_buyer(
        company_name=lead.company_name,
        website=lead.website,
        state=lead.state,
        postcode=lead.postcode,
    )

    lead.bulk_buyer = bulk_buyer

   # --------------------------------------------------------
   # Calculate final lead score
   # --------------------------------------------------------

    final_score, final_classification = calculate_final_score(
        lead_score=lead.lead_score,
        verification_status=lead.verification_status,
        import_activity=lead.import_activity,
        india_sourcing=lead.india_sourcing,
        bulk_buyer=lead.bulk_buyer,
    )

    lead.lead_score = final_score
    lead.classification = final_classification


    # --------------------------------------------------------
    # Save enrichment
    # --------------------------------------------------------

    db.add(lead)

    db.commit()

    db.refresh(lead)

    # --------------------------------------------------------
    # Return updated lead
    # --------------------------------------------------------

    return lead
    # --------------------------------------------------------
    # Get lead
    # --------------------------------------------------------

    lead = lead_crud.get_lead(
        db=db,
        lead_id=lead_id,
    )

    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    # --------------------------------------------------------
    # Discover website
    # --------------------------------------------------------

    website = discover_website(
        company_name=lead.company_name,
        state=lead.state,
        postcode=lead.postcode,
    )

    # --------------------------------------------------------
    # Save website
    # --------------------------------------------------------

    if website:
        lead.website = website

        db.add(lead)
        db.commit()
        db.refresh(lead)

    # --------------------------------------------------------
    # Return lead
    # --------------------------------------------------------

    return lead
