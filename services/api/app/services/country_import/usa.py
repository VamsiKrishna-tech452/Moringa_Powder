import requests

from app.db.session import SessionLocal
from app.models.lead import Lead


NY_API_URL = "https://data.ny.gov/resource/n9v6-gdp6.json"

BATCH_SIZE = 100


def fetch_new_york_companies(limit: int = BATCH_SIZE):
    params = {
        "$limit": limit,
    }

    response = requests.get(
        NY_API_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def import_new_york_companies():
    records = fetch_new_york_companies()

    db = SessionLocal()

    inserted = 0
    skipped = 0

    try:
        for record in records:
            registration_number = record.get("dos_id")
            company_name = record.get("current_entity_name")

            if not registration_number or not company_name:
                skipped += 1
                continue

            # Prevent duplicate USA registrations
            existing = (
                db.query(Lead)
                .filter(
                    Lead.country_code == "US",
                    Lead.registration_number == registration_number,
                )
                .first()
            )

            if existing:
                skipped += 1
                continue

            lead = Lead(
                abn=None,
                company_name=company_name,
                country="United States",
                country_code="US",
                registration_number=registration_number,
                entity_type=record.get("entity_type"),
                state=record.get("dos_process_state"),
                postcode=record.get("dos_process_zip"),
                source="New York Open Data - Active Corporations",
                lead_score=0,
                classification="Unclassified",
                verification_status="unverified",
            )

            db.add(lead)
            inserted += 1

        db.commit()

        print(f"USA import completed")
        print(f"Records received: {len(records)}")
        print(f"Inserted: {inserted}")
        print(f"Skipped: {skipped}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    import_new_york_companies()
