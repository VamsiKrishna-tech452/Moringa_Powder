from typing import Any

import requests

from app.ingestion.australia_collector import (
    collect_and_ingest,
)


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

USER_AGENT = (
    "MoringaDistributorIntelligence/0.1 "
    "(Australian buyer discovery)"
)


SEARCH_TERMS = [
    "moringa",
    "organic food",
    "health food",
    "superfood",
    "natural products",
    "food distributor",
    "food wholesaler",
]


def build_query(
    search_term: str,
) -> str:
    """
    Build an Overpass query for Australian
    businesses whose OSM name contains the
    supplied search term.
    """

    escaped_term = search_term.replace('"', '\\"')

    return f"""
[out:json][timeout:60];

area["ISO3166-1"="AU"]->.australia;

(
  nwr["name"~"{escaped_term}",i](area.australia);
);

out center tags;
"""


def search_osm(
    search_term: str,
) -> list[dict[str, Any]]:
    """
    Search OpenStreetMap through Overpass.
    """

    query = build_query(search_term)

    response = requests.post(
        OVERPASS_URL,
        data=query,
        headers={
            "User-Agent": USER_AGENT,
        },
        timeout=90,
    )

    response.raise_for_status()

    data = response.json()

    return data.get("elements", [])


def osm_element_to_business(
    element: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert an OSM element into the format expected
    by australia_collector.normalize_business().
    """

    tags = element.get("tags", {})

    website = (
        tags.get("website")
        or tags.get("contact:website")
    )

    email = (
        tags.get("email")
        or tags.get("contact:email")
    )

    phone = (
        tags.get("phone")
        or tags.get("contact:phone")
    )

    address_parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:suburb"),
        tags.get("addr:state"),
        tags.get("addr:postcode"),
    ]

    address = ", ".join(
        part
        for part in address_parts
        if part
    )

    return {
        "name": tags.get("name", ""),
        "website": website,
        "email": email,
        "phone": phone,
        "address": address,
        "source": "OpenStreetMap / Overpass",
    }


def discover_australian_businesses(
    search_terms: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Discover Australian businesses from OSM.
    """

    terms = search_terms or SEARCH_TERMS

    businesses = []

    for term in terms:
        print(f"Searching OSM for: {term}")

        elements = search_osm(term)

        print(
            f"  Found {len(elements)} OSM results"
        )

        for element in elements:
            business = osm_element_to_business(
                element
            )

            if business["name"]:
                businesses.append(business)

    return businesses


def collect_and_ingest_osm(
    search_terms: list[str] | None = None,
) -> dict:
    """
    Discover businesses from OSM, normalize them,
    and send them through the existing ingestion API.
    """

    businesses = discover_australian_businesses(
        search_terms
    )

    print(
        f"\nTotal discovered: {len(businesses)}"
    )

    result = collect_and_ingest(
        businesses
    )

    return result


if __name__ == "__main__":
    result = collect_and_ingest_osm()

    print("\n========== OSM IMPORT COMPLETE ==========")
    print(
        f"Received: "
        f"{result.get('total_received', 0)}"
    )
    print(
        f"Created: "
        f"{result.get('created', 0)}"
    )
    print(
        f"Duplicates: "
        f"{result.get('duplicates', 0)}"
    )
    print(
        f"Created IDs: "
        f"{result.get('created_ids', [])}"
    )
    print(
        f"Duplicate IDs: "
        f"{result.get('duplicate_ids', [])}"
    )
