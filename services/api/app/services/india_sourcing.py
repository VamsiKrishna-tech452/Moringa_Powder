import re
from urllib.parse import quote_plus

import httpx


# ============================================================
# INDIA SOURCING TERMS
# ============================================================

INDIA_TERMS = [
    "india",
    "indian supplier",
    "indian suppliers",
    "indian manufacturer",
    "indian manufacturers",
    "supplier from india",
    "suppliers from india",
    "sourced from india",
    "sourcing from india",
    "products from india",
    "made in india",
    "india supplier",
    "india suppliers",
]


STRONG_INDIA_TERMS = [
    "indian supplier",
    "indian suppliers",
    "indian manufacturer",
    "indian manufacturers",
    "supplier from india",
    "suppliers from india",
    "sourced from india",
    "sourcing from india",
    "products from india",
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
        "INDIA SEARCH QUERY:"
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
            "INDIA SEARCH ERROR:",
            repr(exc),
        )

        return "", False

    print(
        "INDIA SEARCH STATUS:",
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
                "INDIA SEARCH BLOCKED: "
                "DuckDuckGo challenge detected."
            )

            return "", False

        return html, True

    if response.status_code == 202:

        print(
            "INDIA SEARCH BLOCKED: "
            "DuckDuckGo returned HTTP 202."
        )

        return "", False

    print(
        "INDIA SEARCH FAILED: HTTP",
        response.status_code,
    )

    return "", False


# ============================================================
# INDIA SOURCING EVIDENCE
# ============================================================

def extract_india_evidence(
    html: str,
) -> tuple[int, int]:

    text = normalize_text(
        html
    )

    strong_matches = 0
    total_matches = 0

    for term in INDIA_TERMS:

        count = text.count(
            term
        )

        total_matches += count

        if term in STRONG_INDIA_TERMS:
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
            "INDIA WEBSITE STATUS:",
            response.status_code,
            "|",
            website,
        )

        if response.status_code != 200:
            return "", False

        return response.text, True

    except Exception as exc:

        print(
            "INDIA WEBSITE ERROR:",
            repr(exc),
        )

        return "", False

# ============================================================
# INDIA SOURCING DATA PROVIDER
# ============================================================

def india_data_provider(
    company_name: str,
    state: str | None = None,
    postcode: str | None = None,
) -> tuple[str | None, bool]:
    """
    India-sourcing data provider interface.

    Currently no external provider is configured.

    Returns:

        evidence, available
    """

    print(
        "INDIA DATA PROVIDER: "
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

    return extract_india_evidence(
        combined_text
    )


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_india_sourcing(
    strong_matches: int,
    total_matches: int,
) -> str:

    if strong_matches >= 2:
        return "confirmed_india_source"

    if strong_matches >= 1:
        return "likely_india_source"

    if total_matches >= 3:
        return "likely_india_source"

    return "no_india_source_evidence"
	

# ============================================================
# MAIN INDIA SOURCING DETECTOR
# ============================================================

def detect_india_sourcing(
    company_name: str,
    website: str | None = None,
    state: str | None = None,
    postcode: str | None = None,
) -> str:
    """
    Detect publicly available evidence that a buyer
    sources products from India.

    Possible results:

        confirmed_india_source
        likely_india_source
        no_india_source_evidence
        india_sourcing_unavailable

    This function does NOT:

        - modify PostgreSQL
        - modify the Lead model
        - claim customs-level confirmation
        - use private data
    """

    if not company_name:
        return "no_india_source_evidence"

    # --------------------------------------------------------
    # Build search queries
    # --------------------------------------------------------

    queries = [
        f'"{company_name}" India supplier',
        f'"{company_name}" Indian supplier',
        f'"{company_name}" India sourcing',
        f'"{company_name}" imports India',
    ]

    if state and postcode:

        queries.append(
            f'"{company_name}" {state} {postcode} India'
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
    # No reliable source
    # --------------------------------------------------------

    if (
        successful_searches == 0
    ):

        print(
            "INDIA SOURCING SEARCH UNAVAILABLE"
        )

        return "india_sourcing_unavailable"

    # --------------------------------------------------------
    # Combine evidence
    # --------------------------------------------------------

    combined_html = "\n".join(
        all_html
    )

    strong_matches, total_matches = (
        extract_india_evidence(
            combined_html
        )
    )

    # Website evidence is only used as supporting evidence.
    if website_html:

        website_strong, website_total = (
            extract_india_evidence(
                website_html
            )
        )

        strong_matches += website_strong
        total_matches += website_total

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    result = classify_india_sourcing(
        strong_matches=strong_matches,
        total_matches=total_matches,
    )

    print(
        "INDIA SEARCH SUCCESSFUL:",
        successful_searches,
    )

    print(
        "INDIA STRONG MATCHES:",
        strong_matches,
    )

    print(
        "INDIA TOTAL MATCHES:",
        total_matches,
    )

    print(
        "INDIA SOURCING RESULT:",
        result,
    )

    return result
