import csv
from pathlib import Path

import requests


API_URL = "http://localhost:8000/api/v1/distributors/ingest"
BATCH_SIZE = 50


def normalize_record(row: dict) -> dict:
    return {
        "company_name": (row.get("company_name") or "").strip(),
        "website": (row.get("website") or "").strip() or None,
        "email": (row.get("email") or "").strip() or None,
        "phone": (row.get("phone") or "").strip() or None,
        "country": (row.get("country") or "Australia").strip(),
        "source": (row.get("source") or "CSV Import").strip(),
        "verification_status": (
            row.get("verification_status") or "unverified"
        ).strip(),
        "notes": (row.get("notes") or "").strip() or None,
        "product": (
            row.get("product") or "Moringa Leaf Powder"
        ).strip(),
        "buyer_type": (row.get("buyer_type") or "").strip() or None,
        "import_activity": (
            row.get("import_activity") or ""
        ).strip() or None,
        "india_sourcing": (
            row.get("india_sourcing") or ""
        ).strip() or None,
        "bulk_buyer": (
            row.get("bulk_buyer") or ""
        ).strip() or None,
    }


def send_batch(records: list[dict]) -> dict:
    response = requests.post(
        API_URL,
        json={"records": records},
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def import_csv(file_path: str) -> None:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"CSV file not found: {file_path}"
        )

    records = []

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        for row in reader:
            record = normalize_record(row)

            if not record["company_name"]:
                continue

            records.append(record)

    print(f"Records loaded: {len(records)}")

    total_created = 0
    total_duplicates = 0

    for start in range(0, len(records), BATCH_SIZE):
        batch = records[start:start + BATCH_SIZE]

        print(
            f"\nSending batch "
            f"{start + 1}-{start + len(batch)}..."
        )

        result = send_batch(batch)

        created = result.get("created", 0)
        duplicates = result.get("duplicates", 0)

        total_created += created
        total_duplicates += duplicates

        print(f"Received: {result.get('total_received', 0)}")
        print(f"Created: {created}")
        print(f"Duplicates: {duplicates}")

        print(
            f"Created IDs: "
            f"{result.get('created_ids', [])}"
        )

        print(
            f"Duplicate IDs: "
            f"{result.get('duplicate_ids', [])}"
        )

    print("\n========== IMPORT COMPLETE ==========")
    print(f"Total records: {len(records)}")
    print(f"Total created: {total_created}")
    print(f"Total duplicates: {total_duplicates}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Import distributor data into Moringa Powder API"
    )

    parser.add_argument(
        "csv_file",
        help="Path to distributor CSV file",
    )

    args = parser.parse_args()

    import_csv(args.csv_file)
