import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.crud import distributor as distributor_crud
from app.db.dependencies import get_db
from app.schemas.distributor import (
    DistributorCreate,
    DistributorListResponse,
    DistributorResponse,
    DistributorUpdate,
    DistributorIngestRequest,
    DistributorIngestResponse,
)


router = APIRouter(
    prefix="/distributors",
    tags=["Distributors"],
)


# ============================================================
# CREATE DISTRIBUTOR
# ============================================================

@router.post(
    "",
    response_model=DistributorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_distributor(
    distributor: DistributorCreate,
    db: Session = Depends(get_db),
):
    return distributor_crud.create_distributor(
        db,
        distributor,
    )


# ============================================================
# AUTOMATED INGESTION
# ============================================================

@router.post(
    "/ingest",
    response_model=DistributorIngestResponse,
    status_code=status.HTTP_200_OK,
)
def ingest_distributor_data(
    payload: DistributorIngestRequest,
    db: Session = Depends(get_db),
):
    created, duplicates = distributor_crud.ingest_distributors(
        db,
        payload.records,
    )

    return {
        "total_received": len(payload.records),
        "created": len(created),
        "duplicates": len(duplicates),
        "created_ids": [
            distributor.id
            for distributor in created
        ],
        "duplicate_ids": [
            distributor.id
            for distributor in duplicates
        ],
    }


# ============================================================
# LIST DISTRIBUTORS
# ============================================================

@router.get(
    "",
    response_model=DistributorListResponse,
)
def get_distributors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    country: str | None = None,
    verification_status: str | None = None,
    db: Session = Depends(get_db),
):
    distributors, total = distributor_crud.get_distributors(
        db,
        page=page,
        page_size=page_size,
        search=search,
        country=country,
        verification_status=verification_status,
    )

    pages = math.ceil(total / page_size) if total > 0 else 0

    return {
        "items": distributors,
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": pages,
    }


# ============================================================
# GET SINGLE DISTRIBUTOR
# ============================================================

@router.get(
    "/{distributor_id}",
    response_model=DistributorResponse,
)
def get_distributor(
    distributor_id: int,
    db: Session = Depends(get_db),
):
    distributor = distributor_crud.get_distributor(
        db,
        distributor_id,
    )

    if distributor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Distributor not found",
        )

    return distributor


# ============================================================
# UPDATE DISTRIBUTOR
# ============================================================

@router.put(
    "/{distributor_id}",
    response_model=DistributorResponse,
)
def update_distributor(
    distributor_id: int,
    distributor: DistributorUpdate,
    db: Session = Depends(get_db),
):
    db_distributor = distributor_crud.get_distributor(
        db,
        distributor_id,
    )

    if db_distributor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Distributor not found",
        )

    return distributor_crud.update_distributor(
        db,
        db_distributor,
        distributor,
    )


# ============================================================
# DELETE DISTRIBUTOR
# ============================================================

@router.delete(
    "/{distributor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_distributor(
    distributor_id: int,
    db: Session = Depends(get_db),
):
    db_distributor = distributor_crud.get_distributor(
        db,
        distributor_id,
    )

    if db_distributor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Distributor not found",
        )

    distributor_crud.delete_distributor(
        db,
        db_distributor,
    )
