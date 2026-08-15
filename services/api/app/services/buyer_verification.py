import re
from urllib.parse import urlparse

import httpx


# ============================================================
# BUYER VERIFICATION
# ============================================================


def normalize_text(
    value: str | None,
) -> str:
    """
    Normalize text for comparison.
    """

    if not value:
        return ""

    value = value.lower()

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def company_tokens(
    company_name: str,
) -> list[str]:
    """
    Extract meaningful company-name tokens.
    """

    normalized = normalize_text(
        company_name
    )

    ignored = {
        "pty",
        "ltd",
        "limited",
        "company",
        "co",
        "and",
        "the",
        "au",
        "australia",
        "adelaide",
    }

    tokens = []

    for token in normalized.split():

        if token in ignored:
            continue

        if len(token) < 3:
            continue

        if token not in tokens:
            tokens.append(token)

    return tokens


def fetch_website(
    website: str,
) -> tuple[str | None, str | None]:
    """
    Fetch the public website.

    Returns:
        final_url, html
    """

    if not website:
        return None, None

    parsed = urlparse(
        website
    )

    if not parsed.scheme:
        website = (
            f"https://{website}"
        )

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

    except Exception as exc:

        print(
            "VERIFICATION FETCH ERROR:",
            repr(exc),
        )

        return None, None

    print(
        "VERIFICATION PAGE STATUS:",
        response.status_code,
        "|",
        website,
    )

    if response.status_code != 200:
        return None, None

    content_type = (
        response.headers
        .get(
            "content-type",
            "",
        )
        .lower()
    )

    if "text/html" not in content_type:
        return None, None

    return (
        str(response.url),
        response.text,
    )


def domain_matches_company(
    website: str,
    company_name: str,
) -> bool:
    """
    Check whether meaningful company-name words
    appear in the domain.
    """

    parsed = urlparse(
        website
    )

    domain = normalize_text(
        parsed.netloc
    )

    tokens = company_tokens(
        company_name
    )

    if not tokens:
        return False

    matches = 0

    for token in tokens:

        if token in domain:
            matches += 1

    return matches >= 1


def company_name_matches_website(
    html: str,
    company_name: str,
) -> bool:
    """
    Check whether meaningful company-name words
    appear in the website HTML.
    """

    page_text = normalize_text(
        html
    )

    tokens = company_tokens(
        company_name
    )

    if not tokens:
        return False

    matches = 0

    for token in tokens:

        if token in page_text:
            matches += 1

    required = min(
        2,
        len(tokens),
    )

    return matches >= required


def location_matches_website(
    html: str,
    state: str | None,
    postcode: str | None,
) -> bool:
    """
    Check whether the website contains the lead's
    state or postcode.
    """

    page_text = normalize_text(
        html
    )

    if state:

        normalized_state = normalize_text(
            state
        )

        if normalized_state in page_text:
            return True

    if postcode:

        postcode_text = str(
            postcode
        ).strip()

        if postcode_text and postcode_text in html:
            return True

    return False


def email_domain_matches_website(
    email: str | None,
    website: str,
) -> bool:
    """
    Check whether the email domain matches
    the website domain.
    """

    if not email:
        return False

    parsed = urlparse(
        website
    )

    website_domain = (
        parsed.netloc
        .lower()
        .removeprefix("www.")
    )

    email_parts = email.lower().split(
        "@",
        1,
    )

    if len(email_parts) != 2:
        return False

    email_domain = (
        email_parts[1]
        .strip()
        .removeprefix("www.")
    )

    return (
        email_domain == website_domain
    )


def verify_buyer(
    company_name: str,
    website: str | None,
    email: str | None = None,
    state: str | None = None,
    postcode: str | None = None,
) -> str:
    """
    Determine confidence that a website belongs
    to the supplied buyer.

    Possible results:

        verified
        likely_verified
        unverified

    This function only performs public website checks.

    It does NOT:
        - modify PostgreSQL
        - modify the Lead model
        - verify ABN registration directly
        - perform government authentication
        - perform payment verification
    """

    if not website:

        print(
            "VERIFICATION: No website available."
        )

        return "unverified"

    # --------------------------------------------------------
    # Fetch website
    # --------------------------------------------------------

    final_url, html = fetch_website(
        website
    )

    if not html:

        print(
            "VERIFICATION: Website unavailable."
        )

        return "unverified"

    # --------------------------------------------------------
    # Verification signals
    # --------------------------------------------------------

    domain_match = domain_matches_company(
        final_url or website,
        company_name,
    )

    name_match = company_name_matches_website(
        html,
        company_name,
    )

    location_match = location_matches_website(
        html,
        state,
        postcode,
    )

    email_match = email_domain_matches_website(
        email,
        final_url or website,
    )

    print(
        "VERIFICATION SIGNALS:"
    )

    print(
        "DOMAIN MATCH:",
        domain_match,
    )

    print(
        "COMPANY NAME MATCH:",
        name_match,
    )

    print(
        "LOCATION MATCH:",
        location_match,
    )

    print(
        "EMAIL DOMAIN MATCH:",
        email_match,
    )

    # --------------------------------------------------------
    # Score verification evidence
    # --------------------------------------------------------

    score = 0

    if domain_match:
        score += 2

    if name_match:
        score += 3

    if location_match:
        score += 2

    if email_match:
        score += 2

    print(
        "VERIFICATION SCORE:",
        score,
    )

    # --------------------------------------------------------
    # Final classification
    # --------------------------------------------------------

    if score >= 6:

        print(
            "VERIFICATION RESULT:",
            "verified",
        )

        return "verified"

    if score >= 3:

        print(
            "VERIFICATION RESULT:",
            "likely_verified",
        )

        return "likely_verified"

    print(
        "VERIFICATION RESULT:",
        "unverified",
    )

    return "unverified"
