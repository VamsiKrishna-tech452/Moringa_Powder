import re
from urllib.parse import quote_plus

import httpx


# ============================================================
# BULK BUYER TERMS
# ============================================================

BULK_BUYER_TERMS = [
    "wholesale",
    "wholesaler",
    "wholesalers",
    "bulk",
    "bulk orders",
    "bulk order",
    "bulk buying",
    "large quantities",
    "large quantity",
    "distributor",
    "distributors",
    "distribution",
    "foodservice",
    "food service",
    "commercial quantities",
    "trade quantities",
]


STRONG_BULK_BUYER_TERMS = [
    "bulk orders",
    "bulk order",
    "bulk buying",
    "large quantities",
    "commercial quantities",
    "trade quantities",
]


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(
    value: str | None,
) -> str:

    if not value:
        return ""

    value = value.lower()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


# ============================================================
# PUBLIC WEB SEARCH
# ============================================================

def search_web(
    query: str,
) -> tuple[str, bool]:

    encoded_query = quote_plus(
        query
    )

    url = (
        "https://html.duckduckgo.com/html/"
        f"?q={encoded_query}"
    )

    print(
        "BULK BUYER SEARCH QUERY:"
    )

    print(
        query
    )

    try:

        response = httpx.get(
            url,
            timeout=15,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/150.0 Safari/537.36"
                ),
            },
        )

    except Exception as exc:

        print(
            "BULK BUYER SEARCH ERROR:",
            repr(exc),
        )

        return "", False

    print(
        "BULK BUYER SEARCH STATUS:",
        response.status_code,
    )

    if response.status_code == 200:

        html = response.text

        challenge_markers = [
            "challenge-form",
            "anomaly-modal",
            "Please complete the following challenge",
            "anomaly.js",
        ]

        if any(
            marker in html
            for marker in challenge_markers
        ):

            print(
                "BULK BUYER SEARCH BLOCKED: "
                "DuckDuckGo challenge detected."
            )

            return "", False

        return html, True

    if response.status_code == 202:

        print(
            "BULK BUYER SEARCH BLOCKED: "
            "DuckDuckGo returned HTTP 202."
        )

        return "", False

    print(
        "BULK BUYER SEARCH FAILED: HTTP",
        response.status_code,
    )

    return "", False


# ============================================================
# BULK BUYER EVIDENCE
# ============================================================

def extract_bulk_buyer_evidence(
    html: str,
) -> tuple[int, int]:

    text = normalize_text(
        html
    )

    strong_matches = 0
    total_matches = 0

    for term in BULK_BUYER_TERMS:

        count = text.count(
            term
        )

        total_matches += count

        if term in STRONG_BULK_BUYER_TERMS:

            strong_matches += count

    return (
        strong_matches,
        total_matches,
    )


# ============================================================
# WEBSITE EVIDENCE
# ============================================================

def get_website_evidence(
    website: str | None,
) -> tuple[str, bool]:

    if not website:
        return "", False

    try:

        response = httpx.get(
            website,
            timeout=15,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/150.0 Safari/537.36"
                ),
            },
        )

        print(
            "BULK BUYER WEBSITE STATUS:",
            response.status_code,
            "|",
            website,
        )

        if response.status_code != 200:
            return "", False

        return response.text, True

    except Exception as exc:

        print(
            "BULK BUYER WEBSITE ERROR:",
            repr(exc),
        )

        return "", False


# ============================================================
# BULK BUYER DATA PROVIDER
# ============================================================

def bulk_buyer_data_provider(
    company_name: str,
    state: str | None = None,
    postcode: str | None = None,
) -> tuple[str | None, bool]:

    """
    Future interface for a trade-data or business-data provider.

    Currently no external provider is configured.

    Returns:

        evidence, available
    """

    print(
        "BULK BUYER DATA PROVIDER: "
        "No provider configured."
    )

    return None, False


# ============================================================
# COMBINE EVIDENCE
# ============================================================

def combine_evidence(
    public_html: str,
    website_html: str,
    provider_evidence: str | None,
) -> tuple[int, int]:

    combined_text = "\n".join(
        [
            public_html,
            website_html,
            provider_evidence or "",
        ]
    )

    return extract_bulk_buyer_evidence(
        combined_text
    )


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_bulk_buyer(
    strong_matches: int,
    total_matches: int,
    provider_available: bool = False,
) -> str:

    if provider_available:
        return "confirmed_bulk_buyer"

    if strong_matches >= 2:
        return "confirmed_bulk_buyer"

    if strong_matches >= 1:
        return "likely_bulk_buyer"

    if total_matches >= 3:
        return "likely_bulk_buyer"

    return "no_bulk_buyer_evidence"


# ============================================================
# MAIN BULK BUYER DETECTOR
# ============================================================

def detect_bulk_buyer(
    company_name: str,
    website: str | None = None,
    state: str | None = None,
    postcode: str | None = None,
) -> str:

    """
    Detect publicly available evidence that a company
    operates as a bulk buyer, wholesaler, distributor,
    or commercial-volume purchaser.

    Possible results:

        confirmed_bulk_buyer
        likely_bulk_buyer
        no_bulk_buyer_evidence
        bulk_buyer_unavailable

    This function does NOT:

        - modify PostgreSQL
        - modify the Lead model
        - claim customs-level confirmation
        - use private data
    """

    if not company_name:
        return "no_bulk_buyer_evidence"

    # --------------------------------------------------------
    # Build search queries
    # --------------------------------------------------------

    queries = [
        f'"{company_name}" wholesale Australia',
        f'"{company_name}" wholesaler Australia',
        f'"{company_name}" bulk orders Australia',
        f'"{company_name}" distributor Australia',
    ]

    if state and postcode:

        queries.append(
            f'"{company_name}" {state} {postcode} wholesale'
        )

    # --------------------------------------------------------
    # Public search
    # --------------------------------------------------------

    all_html = []

    successful_searches = 0

    for query in queries:

        html, available = search_web(
            query
        )

        if available:

            successful_searches += 1

            if html:
                all_html.append(
                    html
                )

    # --------------------------------------------------------
    # Website
    # --------------------------------------------------------

    website_html, website_available = (
        get_website_evidence(
            website
        )
    )

    # --------------------------------------------------------
    # Provider
    # --------------------------------------------------------

    provider_evidence, provider_available = (
        bulk_buyer_data_provider(
            company_name=company_name,
            state=state,
            postcode=postcode,
        )
    )

    # --------------------------------------------------------
    # No reliable source
    # --------------------------------------------------------

    if (
        successful_searches == 0
        and not provider_available
    ):

        print(
            "BULK BUYER SEARCH UNAVAILABLE"
        )

        return "bulk_buyer_unavailable"

    # --------------------------------------------------------
    # Combine evidence
    # --------------------------------------------------------

    combined_public_html = "\n".join(
        all_html
    )

    strong_matches, total_matches = (
        combine_evidence(
            public_html=combined_public_html,
            website_html=website_html,
            provider_evidence=provider_evidence,
        )
    )

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    result = classify_bulk_buyer(
        strong_matches=strong_matches,
        total_matches=total_matches,
        provider_available=provider_available,
    )

    print(
        "BULK BUYER SEARCH SUCCESSFUL:",
        successful_searches,
    )

    print(
        "BULK BUYER DATA PROVIDER AVAILABLE:",
        provider_available,
    )

    print(
        "BULK BUYER STRONG MATCHES:",
        strong_matches,
    )

    print(
        "BULK BUYER TOTAL MATCHES:",
        total_matches,
    )

    print(
        "BULK BUYER RESULT:",
        result,
    )

    return result
