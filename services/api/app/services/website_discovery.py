from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import (
    parse_qs,
    quote_plus,
    unquote,
    urljoin,
    urlparse,
)

import httpx


# ============================================================
# SEARCH RESULT PARSER
# ============================================================


class SearchResultParser(HTMLParser):
    """
    Extract href links from DuckDuckGo HTML results.
    """

    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return

        attributes = dict(attrs)
        href = attributes.get("href")

        if href:
            self.links.append(href)


# ============================================================
# BLOCKED / DIRECTORY DOMAINS
# ============================================================


BLOCKED_DOMAINS = {
    # Social media
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "tiktok.com",
    "x.com",
    "twitter.com",

    # Search engines
    "google.com",
    "bing.com",
    "duckduckgo.com",

    # General directories / databases
    "aubiz.net",
    "auscompanies.com",
    "opengovau.com",
    "b2bhint.com",
    "dnb.com",
    "yellowpages.com.au",
    "truelocal.com.au",
    "hotfrog.com.au",
    "startlocal.com.au",
    "zoominfo.com",
    "crunchbase.com",
    "yelp.com",

    # Government / registration sites
    "abr.gov.au",
    "abr.business.gov.au",
    "asic.gov.au",

    # Trade / company intelligence platforms
    "volza.com",
    "importgenius.com",
    "panjiva.com",
    "tradekey.com",
    "alibaba.com",
    "made-in-china.com",
}


# ============================================================
# DOMAIN HELPERS
# ============================================================


def normalize_domain(url: str) -> str:
    """
    Return normalized hostname without www.
    """

    try:
        parsed = urlparse(url)

        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    except Exception:
        return ""


def normalize_url(url: str) -> str:
    """
    Normalize URL for storage.
    """

    url = url.strip()

    if url.startswith("//"):
        url = "https:" + url

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)

    if not parsed.netloc:
        return ""

    return (
        f"{parsed.scheme}://"
        f"{parsed.netloc}"
        f"{parsed.path or '/'}"
    )


def is_blocked_domain(domain: str) -> bool:
    """
    Check whether domain belongs to a blocked directory/platform.
    """

    domain = domain.lower().strip()

    for blocked in BLOCKED_DOMAINS:
        if domain == blocked or domain.endswith("." + blocked):
            return True

    return False


def is_candidate_website(url: str) -> bool:
    """
    Determine whether a URL looks like a real company website.
    """

    domain = normalize_domain(url)

    if not domain:
        return False

    if is_blocked_domain(domain):
        return False

    # Ignore obvious files
    lowered = url.lower()

    if lowered.endswith(
        (
            ".pdf",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
        )
    ):
        return False

    # Ignore localhost / IP addresses
    if domain in {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
    }:
        return False

    return True


# ============================================================
# DUCKDUCKGO URL EXTRACTION
# ============================================================


def unwrap_duckduckgo_url(href: str) -> str:
    """
    Convert DuckDuckGo redirect URLs into the real destination URL.

    Example:

    //duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com
    """

    if not href:
        return ""

    if href.startswith("//"):
        href = "https:" + href

    parsed = urlparse(href)

    # DuckDuckGo redirect
    if (
        "duckduckgo.com" in parsed.netloc
        and parsed.path.startswith("/l/")
    ):
        query = parse_qs(parsed.query)

        destination = query.get("uddg")

        if destination:
            return unquote(destination[0])

    return href


# ============================================================
# SEARCH LINKS
# ============================================================


def extract_search_links(html: str) -> list[str]:
    """
    Extract actual website URLs from DuckDuckGo HTML.
    """

    parser = SearchResultParser()

    parser.feed(html)

    results: list[str] = []

    for href in parser.links:

        href = unwrap_duckduckgo_url(href)

        if not href:
            continue

        if href.startswith("/"):
            href = urljoin(
                "https://html.duckduckgo.com",
                href,
            )

        href = normalize_url(href)

        if not href:
            continue

        if is_candidate_website(href):
            results.append(href)

    return results


# ============================================================
# COMPANY NAME HELPERS
# ============================================================


def clean_company_name(company_name: str) -> str:
    """
    Remove common Australian company suffixes.
    """

    value = company_name.upper()

    suffixes = [
        "PTY LTD",
        "PTY. LTD.",
        "LIMITED",
        "LTD",
        "INC",
        "INC.",
        "LLC",
    ]

    for suffix in suffixes:
        value = value.replace(suffix, " ")

    # Remove punctuation
    value = re.sub(
        r"[^A-Z0-9 ]+",
        " ",
        value,
    )

    # Normalize whitespace
    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def company_tokens(company_name: str) -> list[str]:
    """
    Return useful company-name tokens.
    """

    cleaned = clean_company_name(company_name)

    stop_words = {
        "PTY",
        "LTD",
        "LIMITED",
        "THE",
        "AND",
        "OF",
        "AUSTRALIA",
        "ADELAIDE",
    }

    tokens = []

    for token in cleaned.split():

        if len(token) < 3:
            continue

        if token in stop_words:
            continue

        tokens.append(token.lower())

    return tokens


# ============================================================
# WEBSITE SCORING
# ============================================================


def score_website(
    url: str,
    company_name: str,
) -> int:

    domain = normalize_domain(url)

    if not domain:
        return -1000

    if is_blocked_domain(domain):
        return -1000

    score = 0

    domain_without_tld = domain

    if domain_without_tld.startswith("www."):
        domain_without_tld = domain_without_tld[4:]

    # --------------------------------------------------------
    # Australian business domain
    # --------------------------------------------------------

    if domain.endswith(".com.au"):
        score += 40

    elif domain.endswith(".au"):
        score += 25

    elif domain.endswith(".com"):
        score += 20

    # --------------------------------------------------------
    # Company name matching
    # --------------------------------------------------------

    tokens = company_tokens(company_name)

    domain_text = re.sub(
        r"[^a-z0-9]+",
        " ",
        domain_without_tld.lower(),
    )

    matched_tokens = 0

    for token in tokens:

        if token in domain_text:
            matched_tokens += 1

    score += matched_tokens * 20

    # --------------------------------------------------------
    # Exact-ish company phrase
    # --------------------------------------------------------

    compact_company = "".join(tokens)
    compact_domain = re.sub(
        r"[^a-z0-9]",
        "",
        domain_without_tld.lower(),
    )

    if compact_company and compact_company in compact_domain:
        score += 100

    # --------------------------------------------------------
    # Penalize directory-looking paths
    # --------------------------------------------------------

    path = urlparse(url).path.lower()

    directory_words = [
        "/company/",
        "/companies/",
        "/business/",
        "/businesses/",
        "/profile/",
        "/directory/",
        "/search/",
        "/listing/",
        "/listings/",
    ]

    for word in directory_words:

        if word in path:
            score -= 60

    # --------------------------------------------------------
    # Prefer homepage
    # --------------------------------------------------------

    if path in ("", "/"):
        score += 15

    return score


   # ============================================================
   # SEARCH DUCKDUCKGO 
   # ============================================================

def search_duckduckgo(
    query: str,
) -> list[str]:
    url = "https://html.duckduckgo.com/html/"

    print("SEARCH QUERY:")
    print(query)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/150.0 Safari/537.36"
        ),
    }

    try:
        response = httpx.get(
            url,
            params={"q": query},
            timeout=5,
            follow_redirects=True,
            headers=headers,
        )

    except Exception as exc:
        print(
            "SEARCH ERROR:",
            repr(exc),
        )
        return []

    print(
        "SEARCH STATUS:",
        response.status_code,
    )

    if response.status_code == 200:
        if not response.text.strip():
            print("SEARCH RESPONSE WAS EMPTY.")
            return []

        links = extract_search_links(
            response.text
        )

        print(
            "EXTRACTED LINKS:",
            len(links),
        )

        return links

    if response.status_code == 202:
        print(
            "SEARCH RETURNED 202 - "
            "TRYING LITE FALLBACK..."
        )

        return search_duckduckgo_lite(
            query
        )

    print(
        "SEARCH FAILED:",
        response.status_code,
    )

    return []


def search_duckduckgo_lite(
    query: str,
) -> list[str]:
    url = "https://lite.duckduckgo.com/lite/"

    print("LITE SEARCH QUERY:")
    print(query)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/150.0 Safari/537.36"
        ),
    }

    try:
        response = httpx.get(
            url,
            params={"q": query},
            timeout=5,
            follow_redirects=True,
            headers=headers,
        )

    except Exception as exc:
        print(
            "LITE SEARCH ERROR:",
            repr(exc),
        )
        return []

    print(
        "LITE SEARCH STATUS:",
        response.status_code,
    )

    if response.status_code != 200:
        print(
            "LITE SEARCH FAILED:",
            response.status_code,
        )
        return []

    if not response.text.strip():
        print(
            "LITE SEARCH RESPONSE WAS EMPTY."
        )
        return []

    links = extract_search_links(
        response.text
    )

    print(
        "LITE EXTRACTED LINKS:",
        len(links),
    )

    return links


# ============================================================
# WEBSITE DISCOVERY
# ============================================================

def discover_website(
    company_name: str,
    state: str | None = None,
    postcode: str | None = None,
) -> str | None:
    """
    Discover the most likely official website for a company.

    This function only discovers the website.

    It does NOT:
        - modify PostgreSQL
        - extract email
        - extract phone
        - verify the company
    """

    # --------------------------------------------------------
    # Build several search queries.
    # --------------------------------------------------------

    tokens = company_tokens(
        company_name
    )

    short_name = " ".join(
        tokens[:4]
    )

    queries = [
        f'"{short_name}" Australia',
        f'"{short_name}" official website',
        f'{short_name} website Australia',
    ]

    if state and postcode:
        queries.append(
            f'"{short_name}" {state} {postcode}'
        )

    # --------------------------------------------------------
    # Collect all search results.
    # --------------------------------------------------------

    all_links: list[str] = []

    for query in queries:
        links = search_duckduckgo(
            query
        )

        all_links.extend(
            links
        )

    # --------------------------------------------------------
    # Deduplicate by domain.
    # --------------------------------------------------------

    unique_by_domain: dict[str, str] = {}

    for link in all_links:
        domain = normalize_domain(
            link
        )

        if not domain:
            continue

        if is_blocked_domain(
            domain
        ):
            continue

        if domain not in unique_by_domain:
            unique_by_domain[
                domain
            ] = link

    # --------------------------------------------------------
    # Score candidates.
    # --------------------------------------------------------

    scored = []

    for domain, url in unique_by_domain.items():
        score = score_website(
            url=url,
            company_name=company_name,
        )

        scored.append(
            (
                score,
                url,
                domain,
            )
        )

    # --------------------------------------------------------
    # Highest score first.
    # --------------------------------------------------------

    scored.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    # --------------------------------------------------------
    # Debug output.
    # --------------------------------------------------------

    print(
        "UNIQUE CANDIDATE DOMAINS:",
        len(scored),
    )

    print(
        "TOP CANDIDATES:"
    )

    for score, url, domain in scored[:10]:
        print(
            score,
            "|",
            domain,
            "|",
            url,
        )

    # --------------------------------------------------------
    # No candidates.
    # --------------------------------------------------------

    if not scored:
        return None

    # --------------------------------------------------------
    # Best candidate.
    # --------------------------------------------------------

    best_score, best_url, best_domain = scored[0]

    if best_score < 30:
        print(
            "NO HIGH-CONFIDENCE WEBSITE FOUND."
        )

        return None

    # --------------------------------------------------------
    # Return homepage.
    # --------------------------------------------------------

    parsed = urlparse(
        best_url
    )

    homepage = (
        f"{parsed.scheme}://"
        f"{parsed.netloc}/"
    )

    print(
        "SELECTED WEBSITE:",
        homepage,
        "| SCORE:",
        best_score,
    )

    return homepage
