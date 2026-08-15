import re
from urllib.parse import urljoin, urlparse

import httpx


# ============================================================
# EMAIL EXTRACTION
# ============================================================

EMAIL_PATTERN = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


COMMON_PATHS = [
    "/",
    "/contact",
    "/contact-us",
    "/contactus",
    "/about",
    "/about-us",
]


def extract_emails(html: str) -> list[str]:
    """
    Extract email addresses from HTML.

    This function only extracts publicly visible email-like
    addresses from the supplied HTML.
    """

    if not html:
        return []

    emails = EMAIL_PATTERN.findall(html)

    results = []

    for email in emails:

        email = email.strip().lower()

        if email not in results:
            results.append(email)

    return results


def is_valid_business_email(email: str) -> bool:
    """
    Basic filtering for public business emails.

    This is intentionally conservative.
    """

    if not email:
        return False

    email = email.lower().strip()

    # Ignore obvious placeholder/example addresses.
    blocked = {
        "example@example.com",
        "test@test.com",
        "email@example.com",
        "name@example.com",
        "your@email.com",
    }

    if email in blocked:
        return False

    # Ignore common image/file-looking false positives.
    if email.endswith(
        (
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".webp",
        )
    ):
        return False

    return True


def choose_best_email(
    emails: list[str],
    website: str,
) -> str | None:
    """
    Select the most likely business email.
    """

    valid = [
        email
        for email in emails
        if is_valid_business_email(email)
    ]

    if not valid:
        return None

    parsed = urlparse(website)

    website_domain = (
        parsed.netloc.lower()
        .replace("www.", "")
    )

    # Prefer emails belonging to the discovered website.
    same_domain = []

    for email in valid:

        email_domain = email.split("@", 1)[1].lower()

        if email_domain == website_domain:
            same_domain.append(email)

    if same_domain:

        # Prefer common business mailboxes.
        preferred_prefixes = (
            "info@",
            "sales@",
            "contact@",
            "hello@",
            "enquiries@",
            "inquiries@",
            "admin@",
        )

        for prefix in preferred_prefixes:

            for email in same_domain:

                if email.startswith(prefix):
                    return email

        return same_domain[0]

    # Otherwise return the first valid public business email.
    return valid[0]


def fetch_page(
    url: str,
) -> str | None:
    """
    Fetch a public webpage.

    Returns HTML or None.

    This function does not attempt to bypass
    CAPTCHA or anti-bot protection.
    """

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
            "EMAIL PAGE FETCH ERROR:",
            repr(exc),
        )

        return None

    print(
        "EMAIL PAGE STATUS:",
        response.status_code,
        "|",
        url,
    )

    if response.status_code != 200:
        return None

    content_type = (
        response.headers
        .get("content-type", "")
        .lower()
    )

    if "text/html" not in content_type:
        return None

    return response.text


def extract_email(
    website: str,
) -> str | None:
    """
    Discover the most likely public business email
    from a company's website.

    This function only performs email discovery.

    It does NOT:
        - modify PostgreSQL
        - modify the Lead model
        - extract phone numbers
        - verify the company
    """

    if not website:
        return None

    parsed = urlparse(website)

    if not parsed.scheme:
        website = f"https://{website}"

        parsed = urlparse(website)

    base_url = (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
    )

    checked_urls = []

    all_emails = []

    for path in COMMON_PATHS:

        page_url = urljoin(
            base_url + "/",
            path.lstrip("/"),
        )

        if page_url in checked_urls:
            continue

        checked_urls.append(page_url)

        print(
            "EMAIL SEARCH:",
            page_url,
        )

        html = fetch_page(
            page_url
        )

        if not html:
            continue

        emails = extract_emails(
            html
        )

        print(
            "EMAILS FOUND:",
            len(emails),
        )

        for email in emails:

            if email not in all_emails:
                all_emails.append(email)

        # ----------------------------------------------------
        # If we already found a good business email, stop.
        # ----------------------------------------------------

        best = choose_best_email(
            all_emails,
            website,
        )

        if best:
            print(
                "SELECTED EMAIL:",
                best,
            )

            return best

    print(
        "NO PUBLIC BUSINESS EMAIL FOUND."
    )

    return None
