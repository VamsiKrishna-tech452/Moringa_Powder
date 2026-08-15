import csv
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import engine
from app.models.lead import Lead


DEFAULT_CSV = "data/australia_abn_candidates.csv"


def clean_value(value: str | None) -> str | None:
    """Convert empty CSV values to None and remove surrounding whitespace."""

    if value is None:
        return None

    value = value.strip()

    return value if value else None


def import_leads(csv_file: str) -> tuple[int, int]:
    """
    Import ABN candidates from CSV into PostgreSQL.

    Returns:
        (created_count, skipped_count)
    """

    path = Path(csv_file)

    if not path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {path}"
        )

    created_count = 0
    skipped_count = 0

    print("=" * 70)
    print("ABN LEAD IMPORT")
    print("=" * 70)
    print(f"CSV file: {path}")
    print()

    with path.open(
        "r",
        newline="",
        encoding="utf-8",
    ) as csv_handle:

        reader = csv.DictReader(csv_handle)

        required_columns = {
            "abn",
            "company_name",
            "entity_type",
            "status",
            "gst_status",
            "state",
            "postcode",
            "lead_score",
            "classification",
            "positive_signals",
            "negative_signals",
            "source",
        }

        missing_columns = required_columns - set(
            reader.fieldnames or []
        )

        if missing_columns:
            raise ValueError(
                "CSV is missing required columns: "
                + ", ".join(sorted(missing_columns))
            )

        with Session(engine) as db:

            for row_number, row in enumerate(
                reader,
                start=2,
            ):

                abn = clean_value(row.get("abn"))

                if not abn:
                    print(
                        f"Skipping row {row_number}: missing ABN"
                    )
                    skipped_count += 1
                    continue

                company_name = clean_value(
                    row.get("company_name")
                )

                if not company_name:
                    print(
                        f"Skipping row {row_number}: "
                        f"missing company name"
                    )
                    skipped_count += 1
                    continue

                # --------------------------------------------------
                # Check whether this ABN already exists
                # --------------------------------------------------

                existing_lead = db.scalar(
                    select(Lead).where(
                        Lead.abn == abn
                    )
                )

                if existing_lead:
                    skipped_count += 1
                    continue

                # --------------------------------------------------
                # Parse lead score
                # --------------------------------------------------

                raw_score = clean_value(
                    row.get("lead_score")
                )

                try:
                    lead_score = int(raw_score or 0)
                except ValueError:
                    print(
                        f"Skipping row {row_number}: "
                        f"invalid lead score '{raw_score}'"
                    )
                    skipped_count += 1
                    continue

                # --------------------------------------------------
                # Create Lead
                # --------------------------------------------------

                lead = Lead(
                    abn=abn,
                    company_name=company_name,
                    entity_type=clean_value(
                        row.get("entity_type")
                    ),
                    status=clean_value(
                        row.get("status")
                    ),
                    gst_status=clean_value(
                        row.get("gst_status")
                    ),
                    state=clean_value(
                        row.get("state")
                    ),
                    postcode=clean_value(
                        row.get("postcode")
                    ),
                    lead_score=lead_score,
                    classification=clean_value(
                        row.get("classification")
                    ),
                    positive_signals=clean_value(
                        row.get("positive_signals")
                    ),
                    negative_signals=clean_value(
                        row.get("negative_signals")
                    ),
                    source=clean_value(
                        row.get("source")
                    ),

                    # These will be populated later
                    # by enrichment / verification.
                    website=None,
                    email=None,
                    phone=None,
                    buyer_type=None,
                    import_activity=None,
                    india_sourcing=None,
                    bulk_buyer=None,
                    verification_status="unverified",
                )

                db.add(lead)

                created_count += 1

                # Commit in batches so a large import doesn't
                # keep everything in memory.
                if created_count % 100 == 0:
                    db.commit()

                    print(
                        f"Imported: {created_count}"
                    )

            db.commit()

    print()
    print("=" * 70)
    print("IMPORT COMPLETE")
    print("=" * 70)
    print(f"Created: {created_count}")
    print(f"Skipped: {skipped_count}")
    print(
        f"Total processed: "
        f"{created_count + skipped_count}"
    )
    print("=" * 70)

    return created_count, skipped_count


def main() -> None:
    """Command-line entry point."""

    csv_file = (
        sys.argv[1]
        if len(sys.argv) > 1
        else DEFAULT_CSV
    )

    try:
        import_leads(csv_file)

    except Exception as exc:
        print()
        print("=" * 70)
        print("IMPORT FAILED")
        print("=" * 70)
        print(f"Error: {exc}")
        print("=" * 70)

        raise


if __name__ == "__main__":
    main()
