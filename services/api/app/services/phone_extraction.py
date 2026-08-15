import re
from urllib.parse import urljoin, urlparse

import httpx


# ============================================================
# PHONE EXTRACTION
# ============================================================

COMMON_PATHS = [
    "/",
    "/contact",
    "/contact-us",
    "/contactus",
    "/about",
    "/about-us",
    "/pages/locations",
]


# Australian mobile numbers:
# 04xx xxx xxx
AU_MOBILE_PATTERN = re.compile(
    r"(?<!\d)"
    r"(04\d{2})"
    r"[\s.-]?"
    r"(\d{3})"
    r"[\s.-]?"
    r"(\d{3})"
    r"(?!\d)"
)


# Australian landline numbers:
# (02) xxxx xxxx
# (03) xxxx xxxx
# (07) xxxx xxxx
# (08) xxxx xxxx
AU_LANDLINE_PATTERN = re.compile(
    r"(?<!\d)"
    r"(\(?0[2378]\)?)[\s.-]?"
    r"(\d{4})"
    r"[\s.-]?"
    r"(\d{4})"
    r"(?!\d)"
)


# Australian international mobile:
# +61 4xx xxx xxx
AU_INTL_MOBILE_PATTERN = re.compile(
    r"(?<!\d)"
    r"\+?61[\s.-]?"
    r"(4\d{2})[\s.-]?"
    r"(\d{3})[\s.-]?"
    r"(\d{3})"
    r"(?!\d)"
)


def normalize_phone(phone: str) -> str:
    """
    Normalize a phone number into a readable format.
    """

    phone = phone.strip()

    phone = phone.replace(
        "\u00a0",
        " ",
    )

    phone = re.sub(
        r"\s+",
        " ",
        phone,
    )

    return phone


def normalize_australian_mobile(
    prefix: str,
    middle: str,
    last: str,
) -> str:
    """
    Convert Australian mobile parts into:
    04xx xxx xxx
    """

    return (
        f"{prefix} "
        f"{middle} "
        f"{last}"
    )


def normalize_international_mobile(
    prefix: str,
    middle: str,
    last: str,
) -> str:
    """
    Convert +61 mobile into Australian local format.
    """

    return (
        f"0{prefix} "
        f"{middle} "
        f"{last}"
    )


def normalize_australian_landline(
    area: str,
    first: str,
    last: str,
) -> str:
    """
    Convert Australian landline into:
    (08) xxxx xxxx
    """

    area = area.replace(
        "(",
        "",
    ).replace(
        ")",
        "",
    )

    return (
        f"({area}) "
        f"{first} "
        f"{last}"
    )


def is_valid_phone(
    phone: str,
) -> bool:
    """
    Validate an extracted Australian phone number.
    """

    if not phone:
        return False

    digits = re.sub(
        r"\D",
        "",
        phone,
    )

    # Australian local mobile.
    if len(digits) == 10 and digits.startswith("04"):
        return True

    # Australian local landline.
    if len(digits) == 10 and digits.startswith(
        (
            "02",
            "03",
            "07",
            "08",
        )
    ):
        return True

    # Australian international mobile.
    if len(digits) == 11 and digits.startswith("614"):
        return True

    return False


def extract_tel_links(
    html: str,
) -> list[str]:
    """
    Extract phone numbers from tel: links.

    These are considered high-confidence phone candidates.
    """

    if not html:
        return []

    pattern = re.compile(
        r'href=["\']tel:([^"\']+)["\']',
        re.IGNORECASE,
    )

    matches = pattern.findall(
        html
    )

    results = []

    for match in matches:

        phone = normalize_phone(
            match
        )

        # Convert international Australian mobile.
        intl_match = AU_INTL_MOBILE_PATTERN.fullmatch(
            phone
        )

        if intl_match:

            phone = normalize_international_mobile(
                intl_match.group(1),
                intl_match.group(2),
                intl_match.group(3),
            )

        if not is_valid_phone(phone):
            continue

        if phone not in results:
            results.append(phone)

    return results


def extract_phone_numbers(
    html: str,
) -> list[str]:
    """
    Extract Australian phone numbers from HTML.

    The patterns are intentionally strict to avoid matching
    IDs, timestamps, tracking numbers, image dimensions,
    JavaScript values, etc.
    """

    if not html:
        return []

    results = []

    # --------------------------------------------------------
    # Australian mobile numbers.
    # --------------------------------------------------------

    for match in AU_MOBILE_PATTERN.finditer(
        html
    ):

        phone = normalize_australian_mobile(
            match.group(1),
            match.group(2),
            match.group(3),
        )

        if phone not in results:
            results.append(phone)

    # --------------------------------------------------------
    # Australian landline numbers.
    # --------------------------------------------------------

    for match in AU_LANDLINE_PATTERN.finditer(
        html
    ):

        phone = normalize_australian_landline(
            match.group(1),
            match.group(2),
            match.group(3),
        )

        if phone not in results:
            results.append(phone)

    # --------------------------------------------------------
    # International Australian mobile numbers.
    # --------------------------------------------------------

    for match in AU_INTL_MOBILE_PATTERN.finditer(
        html
    ):

        phone = normalize_international_mobile(
            match.group(1),
            match.group(2),
            match.group(3),
        )

        if phone not in results:
            results.append(phone)

    return [
        phone
        for phone in results
        if is_valid_phone(phone)
    ]


def fetch_page(
    url: str,
) -> str | None:
    """
    Fetch a public webpage.

    Does not attempt to bypass CAPTCHA
    or anti-bot protection.
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
            "PHONE PAGE FETCH ERROR:",
            repr(exc),
        )

        return None

    print(
        "PHONE PAGE STATUS:",
        response.status_code,
        "|",
        url,
    )

    if response.status_code != 200:
        return None

    content_type = (
        response.headers
        .get(
            "content-type",
            "",
        )
        .lower()
    )

    if "text/html" not in content_type:
        return None

    return response.text


def choose_best_phone(
    phones: list[str],
) -> str | None:
    """
    Choose the most likely business phone.

    Preference:
        1. Australian mobile
        2. Australian landline
    """

    if not phones:
        return None

    for phone in phones:

        digits = re.sub(
            r"\D",
            "",
            phone,
        )

        if digits.startswith("04"):
            return phone

    for phone in phones:

        digits = re.sub(
            r"\D",
            "",
            phone,
        )

        if digits.startswith(
            (
                "02",
                "03",
                "07",
                "08",
            )
        ):
            return phone

    return phones[0]


def extract_phone(
    website: str,
) -> str | None:
    """
    Discover the most likely public business phone
    number from a company's website.

    This function only performs phone discovery.

    It does NOT:
        - modify PostgreSQL
        - modify the Lead model
        - extract email
        - verify the company
    """

    if not website:
        return None

    parsed = urlparse(
        website
    )

    if not parsed.scheme:
        website = (
            f"https://{website}"
        )

        parsed = urlparse(
            website
        )

    base_url = (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
    )

    checked_urls = []

    all_phones = []

    for path in COMMON_PATHS:

        page_url = urljoin(
            base_url + "/",
            path.lstrip("/"),
        )

        if page_url in checked_urls:
            continue

        checked_urls.append(
            page_url
        )

        print(
            "PHONE SEARCH:",
            page_url,
        )

        html = fetch_page(
            page_url
        )

        if not html:
            continue

        # ----------------------------------------------------
        # First: tel: links.
        # ----------------------------------------------------

        tel_phones = extract_tel_links(
            html
        )

        print(
            "TEL PHONES FOUND:",
            len(tel_phones),
        )

        for phone in tel_phones:

            if phone not in all_phones:
                all_phones.append(phone)

        # ----------------------------------------------------
        # Second: strict Australian phone patterns.
        # ----------------------------------------------------

        text_phones = extract_phone_numbers(
            html
        )

        print(
            "TEXT PHONES FOUND:",
            len(text_phones),
        )

        for phone in text_phones:

            if phone not in all_phones:
                all_phones.append(phone)

        # ----------------------------------------------------
        # Select a valid phone.
        # ----------------------------------------------------

        best = choose_best_phone(
            all_phones
        )

        if best:

            print(
                "SELECTED PHONE:",
                best,
            )

            return best

    print(
        "NO PUBLIC BUSINESS PHONE FOUND."
    )

    return None
