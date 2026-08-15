import csv
import sys
from pathlib import Path

from app.ingestion.abn_stream_collector import (
    get_abn_status,
    get_gst_status,
    calculate_lead_score,
    classify_lead,
    find_text,
    local_name,
)

import xml.etree.ElementTree as ET


DEFAULT_MINIMUM_SCORE = 25


def process_xml_file(
    xml_file: str,
    writer,
    minimum_score: int,
) -> dict:

    records_scanned = 0
    active_records = 0
    cancelled_records = 0
    candidates_found = 0

    print()
    print("=" * 70)
    print(f"PROCESSING: {xml_file}")
    print("=" * 70)

    for event, element in ET.iterparse(
        xml_file,
        events=("end",),
    ):

        if local_name(element.tag) != "ABR":
            continue

        records_scanned += 1

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

        status = get_abn_status(
            element
        )

        gst_status = get_gst_status(
            element
        )

        # ----------------------------------------------------
        # Ignore unknown status
        # ----------------------------------------------------

        if status == "unknown":

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
        # Score candidate
        # ----------------------------------------------------

        (
            score,
            positive_matches,
            negative_matches,
        ) = calculate_lead_score(
            company_name,
            entity_type,
        )

        if score < minimum_score:

            element.clear()

            continue

        candidates_found += 1

        classification = classify_lead(
            score
        )

        writer.writerow(
            {
                "abn": abn or "",
                "company_name": company_name or "",
                "entity_type": entity_type or "",
                "status": status,
                "gst_status": gst_status,
                "state": state or "",
                "postcode": postcode or "",
                "lead_score": score,
                "classification": classification,
                "positive_signals": "; ".join(
                    positive_matches
                ),
                "negative_signals": "; ".join(
                    negative_matches
                ),
                "source": "Australian ABN Bulk Extract",
            }
        )

        element.clear()

    return {
        "records_scanned": records_scanned,
        "active_records": active_records,
        "cancelled_records": cancelled_records,
        "candidates_found": candidates_found,
    }


def collect_abn_candidates(
    xml_files: list[str],
    output_file: str,
    minimum_score: int = DEFAULT_MINIMUM_SCORE,
):

    output_path = Path(
        output_file
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
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
    ]

    total_records = 0
    total_active = 0
    total_cancelled = 0
    total_candidates = 0

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for xml_file in xml_files:

            stats = process_xml_file(
                xml_file,
                writer,
                minimum_score,
            )

            total_records += stats[
                "records_scanned"
            ]

            total_active += stats[
                "active_records"
            ]

            total_cancelled += stats[
                "cancelled_records"
            ]

            total_candidates += stats[
                "candidates_found"
            ]

            print(
                f"Records scanned: {stats['records_scanned']}"
            )

            print(
                f"Active:          {stats['active_records']}"
            )

            print(
                f"Cancelled:       {stats['cancelled_records']}"
            )

            print(
                f"Candidates:      {stats['candidates_found']}"
            )

    print()
    print("=" * 70)
    print("ABN BULK COLLECTION COMPLETE")
    print("=" * 70)

    print(
        f"Total records scanned: {total_records}"
    )

    print(
        f"Total active records:  {total_active}"
    )

    print(
        f"Total cancelled:       {total_cancelled}"
    )

    print(
        f"Total candidates:      {total_candidates}"
    )

    print(
        f"CSV output:            {output_path}"
    )


if __name__ == "__main__":

    if len(sys.argv) < 2:

        print(
            "Usage:"
        )

        print(
            "python -m app.ingestion.abn_bulk_collector "
            "<xml_file1> [xml_file2 ...]"
        )

        print()
        print(
            "Example:"
        )

        print(
            "python -m app.ingestion.abn_bulk_collector "
            "~/Downloads/public_split_1_10/20260805_Public01.xml"
        )

        sys.exit(1)

    xml_files = sys.argv[1:]

    output_file = (
        "data/australia_abn_candidates.csv"
    )

    collect_abn_candidates(
        xml_files=xml_files,
        output_file=output_file,
        minimum_score=DEFAULT_MINIMUM_SCORE,
    )
