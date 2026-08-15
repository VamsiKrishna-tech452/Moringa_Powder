import sys
import xml.etree.ElementTree as ET


# ============================================================
# Lead scoring configuration
# ============================================================

POSITIVE_KEYWORDS = {
    "moringa": 60,
    "superfood": 45,
    "health food": 40,
    "organic food": 40,
    "food distributor": 40,
    "food wholesaler": 40,
    "food wholesale": 35,
    "natural products": 35,
    "health food store": 35,
    "organic grocery": 35,
    "food importer": 35,
    "supplement": 25,
    "nutrition": 25,
    "grocery": 20,
    "grocer": 20,
    "wholesale": 15,
    "distributor": 15,
    "organic": 15,
    "importer": 10,
    "food": 10,
}


NEGATIVE_KEYWORDS = {
    "physiotherapy": -40,
    "physio": -40,
    "clinic": -35,
    "beauty": -35,
    "beauty studio": -40,
    "wellness studio": -35,
    "training studio": -30,
    "gym": -30,
    "fitness": -25,
    "aircraft": -40,
    "machinery": -40,
    "automotive": -40,
    "petroleum": -40,
    "fuel": -40,
    "mining": -35,
    "insurance": -35,
    "seafood": -30,
    "marine": -30,
    "construction": -25,
    "engineering": -25,
    "motor": -25,
    "plumbing": -25,
    "electrical": -25,
    "real estate": -25,
    "property": -20,
    "finance": -30,
    "accounting": -25,
    "legal": -25,
    "pharmaceutical": -25,
    "pharmacy": -20,
    "wine": -20,
    "superannuation": -40,
}


# ============================================================
# XML helpers
# ============================================================

def local_name(tag: str) -> str:
    """Remove XML namespace from a tag."""
    return tag.split("}", 1)[-1]


def find_text(parent, name: str) -> str | None:
    """Find the first matching XML element and return its text."""

    for child in parent.iter():
        if local_name(child.tag) == name:
            if child.text:
                return child.text.strip()

    return None


# ============================================================
# ABN / GST status
# ============================================================

def get_abn_status(element) -> str:
    """
    Extract ABN status from:

        <ABN status="ACT" ABNStatusFromDate="...">
    """

    for child in element:
        if local_name(child.tag) == "ABN":
            status = child.attrib.get("status")

            if status:
                return status

    return "unknown"


def get_gst_status(element) -> str:
    """
    Extract GST status from:

        <GST status="ACT" GSTStatusFromDate="...">
    """

    for child in element:
        if local_name(child.tag) == "GST":
            status = child.attrib.get("status")

            if status:
                return status

    return "unknown"


# ============================================================
# Lead scoring
# ============================================================

def calculate_lead_score(
    company_name: str | None,
    entity_type: str | None,
) -> tuple[int, list[str], list[str]]:
    """
    Calculate a preliminary Moringa buyer relevance score.

    Strong phrases take precedence over component words
    to prevent double-counting.

    This is a candidate-ranking score only.
    It does NOT confirm that a company is a buyer.
    """

    text = " ".join(
        value
        for value in (
            company_name,
            entity_type,
        )
        if value
    ).lower()

    score = 0

    positive_matches = []
    negative_matches = []

    # --------------------------------------------------------
    # Strong positive signals
    # --------------------------------------------------------

    strong_positive_keywords = {
        "moringa": 60,
        "superfood": 45,
        "health food": 40,
        "organic food": 40,
        "food distributor": 40,
        "food wholesaler": 40,
        "food wholesale": 35,
        "natural products": 35,
        "health food store": 35,
        "organic grocery": 35,
        "food importer": 35,
    }

    # --------------------------------------------------------
    # Standalone positive signals
    # --------------------------------------------------------

    medium_positive_keywords = {
        "supplement": 25,
        "nutrition": 25,
        "grocery": 20,
        "grocer": 20,
        "wholesale": 15,
        "distributor": 15,
        "organic": 15,
        "importer": 10,
        "food": 10,
    }

    # --------------------------------------------------------
    # Apply strong signals first
    # --------------------------------------------------------

    matched_strong_phrases = set()

    for keyword, points in strong_positive_keywords.items():
        if keyword in text:
            score += points

            positive_matches.append(
                f"{keyword} (+{points})"
            )

            matched_strong_phrases.add(keyword)

    # --------------------------------------------------------
    # Apply standalone signals
    #
    # Avoid double-counting words already represented
    # by stronger phrases.
    # --------------------------------------------------------

    for keyword, points in medium_positive_keywords.items():

        if keyword not in text:
            continue

        # "superfood" contains "food"
        if keyword == "food":
            if "superfood" in text:
                continue

            if any(
                phrase in matched_strong_phrases
                for phrase in (
                    "health food",
                    "organic food",
                    "food distributor",
                    "food wholesaler",
                    "food wholesale",
                    "health food store",
                    "food importer",
                )
            ):
                continue

        # "organic food" / "organic grocery"
        # already represent organic.
        if keyword == "organic":
            if (
                "organic food" in matched_strong_phrases
                or "organic grocery" in matched_strong_phrases
            ):
                continue

        # "food distributor" already represents distributor.
        if keyword == "distributor":
            if "food distributor" in matched_strong_phrases:
                continue

        # Strong wholesale phrases already represent wholesale.
        if keyword == "wholesale":
            if any(
                phrase in matched_strong_phrases
                for phrase in (
                    "food wholesale",
                    "food wholesaler",
                )
            ):
                continue

        score += points

        positive_matches.append(
            f"{keyword} (+{points})"
        )

    # --------------------------------------------------------
    # Negative signals
    # --------------------------------------------------------

    for keyword, points in NEGATIVE_KEYWORDS.items():

        if keyword in text:
            score += points

            negative_matches.append(
                f"{keyword} ({points})"
            )

    score = max(score, 0)

    return (
        score,
        positive_matches,
        negative_matches,
    )


# ============================================================
# Lead classification
# ============================================================

def classify_lead(score: int) -> str:
    """Convert numerical score into a lead category."""

    if score >= 60:
        return "High potential"

    if score >= 40:
        return "Good potential"

    if score >= 20:
        return "Possible"

    return "Low relevance"


# ============================================================
# ABN XML streaming collector
# ============================================================

def inspect_scored_businesses(
    xml_file: str,
    max_matches: int = 20,
    minimum_score: int = 20,
):
    """
    Stream an ABN XML file and display qualified candidates.

    This function does NOT write to PostgreSQL.
    """

    print(f"Reading: {xml_file}")
    print(f"Minimum score: {minimum_score}")
    print(
        f"Maximum candidates displayed: {max_matches}\n"
    )

    records_scanned = 0
    active_records = 0
    cancelled_records = 0
    unknown_status_records = 0
    candidates_found = 0

    for event, element in ET.iterparse(
        xml_file,
        events=("end",),
    ):

        if local_name(element.tag) != "ABR":
            continue

        records_scanned += 1

        # ----------------------------------------------------
        # Extract basic information
        # ----------------------------------------------------

        abn = find_text(
            element,
            "ABN",
        )

        entity_type = find_text(
            element,
            "EntityTypeText",
        )

        company_name = find_text(
            element,
            "NonIndividualNameText",
        )

        state = find_text(
            element,
            "State",
        )

        postcode = find_text(
            element,
            "Postcode",
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        status = get_abn_status(
            element
        )

        gst_status = get_gst_status(
            element
        )

        # ----------------------------------------------------
        # Ignore records where ABN status cannot be determined
        # ----------------------------------------------------

        if status == "unknown":
            unknown_status_records += 1

            element.clear()

            continue

        # ----------------------------------------------------
        # Ignore cancelled ABNs
        # ----------------------------------------------------

        if status != "ACT":
            cancelled_records += 1

            element.clear()

            continue

        active_records += 1

        # ----------------------------------------------------
        # Score active business
        # ----------------------------------------------------

        (
            score,
            positive_matches,
            negative_matches,
        ) = calculate_lead_score(
            company_name,
            entity_type,
        )

        # ----------------------------------------------------
        # Ignore low relevance
        # ----------------------------------------------------

        if score < minimum_score:
            element.clear()

            continue

        candidates_found += 1

        classification = classify_lead(
            score
        )

        # ----------------------------------------------------
        # Display
        # ----------------------------------------------------

        print("=" * 70)

        print(
            f"CANDIDATE #{candidates_found}"
        )

        print(
            f"ABN:            {abn}"
        )

        print(
            f"Business:       {company_name}"
        )

        print(
            f"Entity Type:    {entity_type}"
        )

        print(
            f"Status:         {status}"
        )

        print(
            f"GST Status:     {gst_status}"
        )

        print(
            f"State:          {state}"
        )

        print(
            f"Postcode:       {postcode}"
        )

        print(
            f"Lead Score:     {score}"
        )

        print(
            f"Classification: {classification}"
        )

        if positive_matches:
            print(
                "Positive:       "
                + ", ".join(positive_matches)
            )

        if negative_matches:
            print(
                "Negative:       "
                + ", ".join(negative_matches)
            )

        element.clear()

        # ----------------------------------------------------
        # Stop after requested number of candidates
        # ----------------------------------------------------

        if candidates_found >= max_matches:
            break

    # ========================================================
    # Summary
    # ========================================================

    print("\n" + "=" * 70)
    print("SCAN COMPLETE")
    print("=" * 70)

    print(
        f"ABR records scanned: {records_scanned}"
    )

    print(
        f"Active records:      {active_records}"
    )

    print(
        f"Cancelled skipped:   {cancelled_records}"
    )

    print(
        f"Unknown status:      {unknown_status_records}"
    )

    print(
        f"Candidates found:    {candidates_found}"
    )


# ============================================================
# Command-line entry point
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(
            "Usage:"
        )

        print(
            "python -m app.ingestion.abn_stream_collector "
            "/path/to/file.xml"
        )

        sys.exit(1)

    xml_file = sys.argv[1]

    inspect_scored_businesses(
        xml_file,
        max_matches=20,
        minimum_score=20,
    )
