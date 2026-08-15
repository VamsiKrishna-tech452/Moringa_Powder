# ============================================================
# LEAD SCORING
# ============================================================


# ============================================================
# CLASSIFICATION THRESHOLDS
# ============================================================

HIGH_POTENTIAL_THRESHOLD = 100
MEDIUM_POTENTIAL_THRESHOLD = 60


# ============================================================
# BASE SCORE
# ============================================================

def calculate_base_score(
    lead_score: int | None,
) -> int:

    if lead_score is None:
        return 0

    return max(
        0,
        lead_score,
    )


# ============================================================
# ENRICHMENT ADJUSTMENTS
# ============================================================

def calculate_enrichment_adjustment(
    verification_status: str | None = None,
    import_activity: str | None = None,
    india_sourcing: str | None = None,
    bulk_buyer: str | None = None,
) -> int:

    adjustment = 0

    # --------------------------------------------------------
    # Buyer verification
    # --------------------------------------------------------

    if verification_status == "verified":
        adjustment += 10

    elif verification_status == "unverified":
        adjustment += 0

    # --------------------------------------------------------
    # Import activity
    # --------------------------------------------------------

    if import_activity == "confirmed_importer":
        adjustment += 20

    elif import_activity == "likely_importer":
        adjustment += 10

    # --------------------------------------------------------
    # India sourcing
    # --------------------------------------------------------

    if india_sourcing == "confirmed_india_source":
        adjustment += 20

    elif india_sourcing == "likely_india_source":
        adjustment += 10

    # --------------------------------------------------------
    # Bulk buyer
    # --------------------------------------------------------

    if bulk_buyer == "confirmed_bulk_buyer":
        adjustment += 20

    elif bulk_buyer == "likely_bulk_buyer":
        adjustment += 10

    return adjustment


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_lead(
    score: int,
) -> str:

    if score >= 60:
        return "High potential"

    if score >= 40:
        return "Good potential"

    if score >= 20:
        return "Possible"

    return "Low relevance"

# ============================================================
# FINAL SCORE
# ============================================================

def calculate_final_score(
    lead_score: int | None = None,
    verification_status: str | None = None,
    import_activity: str | None = None,
    india_sourcing: str | None = None,
    bulk_buyer: str | None = None,
) -> tuple[int, str]:

    base_score = calculate_base_score(
        lead_score
    )

    enrichment_adjustment = (
        calculate_enrichment_adjustment(
            verification_status=verification_status,
            import_activity=import_activity,
            india_sourcing=india_sourcing,
            bulk_buyer=bulk_buyer,
        )
    )

    final_score = (
        base_score
        + enrichment_adjustment
    )

    classification = classify_lead(
        final_score
    )

    return (
        final_score,
        classification,
    )
