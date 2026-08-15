from typing import Any

import requests


AUSTRALIA = "Australia"
DEFAULT_PRODUCT = "Moringa Leaf Powder"

INGEST_API_URL = "http://localhost:8000/api/v1/distributors/ingest"


SEARCH_QUERIES = [
    "moringa distributor Australia",
    "moringa powder Australia",
    "organic superfood distributor Australia",
    "health food distributor Australia",
    "organic food distributor Australia",
    "natural products distributor Australia",
]


def normalize_business(place: dict[str, Any]) -> dict:
    """
    Convert a discovered Australian business into
    the format expected by /distributors/ingest.
    """

    company_name = (
        place.get("company_name")
        or place.get("name")
        or ""
    ).strip()

    website = (
        place.get("website")
        or ""
    ).strip() or None

    phone = (
        place.get("phone")
        or ""
    ).strip() or None

    email = (
        place.get("email")
        or ""
    ).strip() or None

    address = (
        place.get("address")
        or ""
    ).strip()

    return {
        "company_name": company_name,
        "website": website,
        "email": email,
        "phone": phone,
        "country": AUSTRALIA,
        "source": place.get(
            "source",
            "Australia Business Collector",
        ),
        "verification_status": "unverified",
        "notes": (
            f"Discovered from Australian business search. "
            f"Address: {address}"
            if address
            else "Discovered from Australian business search."
        ),
        "product": DEFAULT_PRODUCT,
        "buyer_type": "Potential Distributor",
        "import_activity": "Unknown",
        "india_sourcing": "Unknown",
        "bulk_buyer": "Unknown",
    }


def normalize_businesses(
    businesses: list[dict[str, Any]],
) -> list[dict]:
    """
    Normalize and validate discovered businesses.
    """

    normalized = []

    for business in businesses:
        record = normalize_business(business)

        if not record["company_name"]:
            continue

        normalized.append(record)

    return normalized


def send_to_ingestion_api(
    businesses: list[dict[str, Any]],
) -> dict:
    """
    Send normalized Australian businesses to the
    existing distributor ingestion endpoint.
    """

    records = normalize_businesses(businesses)

    if not records:
        return {
            "total_received": 0,
            "created": 0,
            "duplicates": 0,
            "created_ids": [],
            "duplicate_ids": [],
        }

    response = requests.post(
        INGEST_API_URL,
        json={"records": records},
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def collect_and_ingest(
    businesses: list[dict[str, Any]],
) -> dict:
    """
    Normalize discovered businesses and send them
    directly into the Moringa distributor database.
    """

    return send_to_ingestion_api(businesses)
