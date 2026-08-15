import re
from urllib.parse import quote_plus

import httpx


# ============================================================
# IMPORT ACTIVITY
# ============================================================

IMPORT_TERMS = [
    "importer",
    "importers",
    "imports",
    "importing",
    "direct importer",
    "direct import",
    "imported from",
    "imported into",
    "international sourcing",
    "global sourcing",
    "overseas supplier",
    "overseas suppliers",
]


STRONG_IMPORT_TERMS = [
    "importer",
    "importers",
    "direct importer",
    "direct import",
    "imported from",
    "imported into",
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
        "IMPORT SEARCH QUERY:"
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
            "IMPORT SEARCH ERROR:",
            repr(exc),
        )

        return "", False

    print(
        "IMPORT SEARCH STATUS:",
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
                "IMPORT SEARCH BLOCKED: "
                "DuckDuckGo challenge detected."
            )

            return "", False

        return html, True

    if response.status_code == 202:

        print(
            "IMPORT SEARCH BLOCKED: "
            "DuckDuckGo returned HTTP 202."
        )

        return "", False

    print(
        "IMPORT SEARCH FAILED: HTTP",
        response.status_code,
    )

    return "", False


# ============================================================
# IMPORT EVIDENCE EXTRACTION
# ============================================================

def extract_import_evidence(
    html: str,
) -> tuple[int, int]:

    text = normalize_text(
        html
    )

    strong_matches = 0
    total_matches = 0

    for term in IMPORT_TERMS:

        count = text.count(
            term
        )

        total_matches += count

        if term in STRONG_IMPORT_TERMS:
            strong_matches += count

    return (
        strong_matches,
        total_matches,
    )


# ============================================================
# TRADE DATA PROVIDER
# ============================================================

def trade_data_provider(
    company_name: str,
    state: str | None = None,
    postcode: str | None = None,
) -> tuple[str | None, bool]:
    """
    Trade-data provider interface.

    Returns:

        evidence, available

    Currently no paid trade-data API is configured.

    Later this function can connect to a provider such as
    a shipment/trade-intelligence API without changing the
    rest of the enrichment pipeline.
    """

    print(
        "TRADE DATA PROVIDER: "
        "No provider configured."
    )

    return None, False


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
            "IMPORT WEBSITE STATUS:",
            response.status_code,
            "|",
            website,
        )

        if response.status_code != 200:
            return "", False

        return response.text, True

    except Exception as exc:

        print(
            "IMPORT WEBSITE ERROR:",
            repr(exc),
        )

        return "", False


# ============================================================
# COMBINE EVIDENCE
# ============================================================

def combine_evidence(
    public_html: str,
    website_html: str,
    trade_evidence: str | None,
) -> tuple[int, int]:

    combined_text = "\n".join(
        [
            public_html,
            website_html,
            trade_evidence or "",
        ]
    )

    strong_matches, total_matches = (
        extract_import_evidence(
            combined_text
        )
    )

    return (
        strong_matches,
        total_matches,
    )


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_import_activity(
    strong_matches: int,
    total_matches: int,
    trade_available: bool = False,
) -> str:

    # Strong trade-data evidence
    if trade_available:
        return "confirmed_importer"

    # Public evidence
    if strong_matches >= 2:
        return "confirmed_importer"

    if strong_matches >= 1:
        return "likely_importer"

    if total_matches >= 3:
        return "likely_importer"

    return "no_import_evidence"


# ============================================================
# MAIN IMPORT ACTIVITY DETECTOR
# ============================================================

def detect_import_activity(
    company_name: str,
    website: str | None = None,
    state: str | None = None,
    postcode: str | None = None,
) -> str:
    """
    Detect publicly available evidence of import activity.

    Possible results:

        confirmed_importer
        likely_importer
        no_import_evidence
        import_activity_unavailable
    """

    if not company_name:
        return "no_import_evidence"

    # --------------------------------------------------------
    # Public web queries
    # --------------------------------------------------------

    queries = [
        f'"{company_name}" importer Australia',
        f'"{company_name}" imports Australia',
        f'"{company_name}" importing Australia',
    ]

    if state and postcode:

        queries.append(
            f'"{company_name}" {state} {postcode} importer'
        )

    # --------------------------------------------------------
    # Public web evidence
    # --------------------------------------------------------

    public_html = []

    successful_searches = 0

    for query in queries:

        html, available = search_web(
            query
        )

        if available:

            successful_searches += 1

            if html:
                public_html.append(
                    html
                )

    # --------------------------------------------------------
    # Website evidence
    # --------------------------------------------------------

    website_html, website_available = (
        get_website_evidence(
            website
        )
    )

    # --------------------------------------------------------
    # Trade data evidence
    # --------------------------------------------------------

    trade_evidence, trade_available = (
        trade_data_provider(
            company_name=company_name,
            state=state,
            postcode=postcode,
        )
    )

    # --------------------------------------------------------
    # No usable source
    # --------------------------------------------------------

    if (
        successful_searches == 0
            and not trade_available
    ):

        print(
            "IMPORT ACTIVITY SEARCH UNAVAILABLE"
        )

        return "import_activity_unavailable"

    # --------------------------------------------------------
    # Combine evidence
    # --------------------------------------------------------

    combined_public_html = "\n".join(
        public_html
    )

    strong_matches, total_matches = (
        combine_evidence(
            public_html=combined_public_html,
            website_html=website_html,
            trade_evidence=trade_evidence,
        )
    )

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    result = classify_import_activity(
        strong_matches=strong_matches,
        total_matches=total_matches,
        trade_available=trade_available,
    )

    print(
        "IMPORT SEARCH SUCCESSFUL:",
        successful_searches,
    )

    print(
        "TRADE DATA AVAILABLE:",
        trade_available,
    )

    print(
        "IMPORT STRONG MATCHES:",
        strong_matches,
    )

    print(
        "IMPORT TOTAL MATCHES:",
        total_matches,
    )

    print(
        "IMPORT ACTIVITY RESULT:",
        result,
    )

    return result
