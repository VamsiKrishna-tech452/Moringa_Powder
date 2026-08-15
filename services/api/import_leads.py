import csv
from datetime import datetime

import psycopg2


DATABASE_URL = (
    "postgresql://lead_user:lead_password"
    "@127.0.0.1:55432/lead_platform"
)

CSV_FILE = "data/australia_abn_candidates.csv"


def main():
    connection = psycopg2.connect(DATABASE_URL)

    try:
        with connection:
            with connection.cursor() as cursor:
                with open(
                    CSV_FILE,
                    newline="",
                    encoding="utf-8",
                ) as file:

                    reader = csv.DictReader(file)

                    rows = []

                    for row in reader:
                        rows.append(
                            (
                                row["abn"],
                                row["company_name"],
                                "Australia",
                                row["entity_type"] or None,
                                row["status"] or None,
                                row["gst_status"] or None,
                                row["state"] or None,
                                row["postcode"] or None,
                                int(row["lead_score"] or 0),
                                row["classification"] or None,
                                row["positive_signals"] or None,
                                row["negative_signals"] or None,
                                row["source"] or None,
                                "unverified",
                                datetime.utcnow(),
                                datetime.utcnow(),
                            )
                        )

                cursor.executemany(
                    """
                    INSERT INTO leads (
                        abn,
                        company_name,
                        country,
                        entity_type,
                        status,
                        gst_status,
                        state,
                        postcode,
                        lead_score,
                        classification,
                        positive_signals,
                        negative_signals,
                        source,
                        verification_status,
			created_at,
                        updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """,
                    rows,
                )

                print(f"Imported {len(rows)} leads")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
