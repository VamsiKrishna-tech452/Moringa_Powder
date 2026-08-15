import sys
import xml.etree.ElementTree as ET


def local_name(tag: str) -> str:
    """Remove XML namespace from a tag."""
    return tag.split("}", 1)[-1]


def inspect_abn_file(xml_file: str, max_records: int = 5):
    print(f"Reading: {xml_file}")
    print(f"Inspecting first {max_records} ABR records...\n")

    record_count = 0

    for event, elem in ET.iterparse(xml_file, events=("end",)):
        if local_name(elem.tag) != "ABR":
            continue

        record_count += 1

        print("=" * 70)
        print(f"ABR RECORD #{record_count}")

        def find_text(parent, name):
            for child in parent.iter():
                if local_name(child.tag) == name:
                    if child.text:
                        return child.text.strip()
            return None

        abn = find_text(elem, "ABN")
        entity_type = find_text(elem, "EntityTypeText")
        business_name = find_text(elem, "NonIndividualNameText")
        state = find_text(elem, "State")
        postcode = find_text(elem, "Postcode")

        print(f"ABN:            {abn}")
        print(f"Entity Type:    {entity_type}")
        print(f"Business Name:  {business_name}")
        print(f"State:          {state}")
        print(f"Postcode:       {postcode}")

        print("\nABR attributes:")
        for key, value in elem.attrib.items():
            print(f"  {local_name(key)} = {value}")

        elem.clear()

        if record_count >= max_records:
            break

    print("\n" + "=" * 70)
    print(f"Inspection complete. Records inspected: {record_count}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print(
            "python -m app.ingestion.inspect_abn_xml "
            "/path/to/file.xml"
        )
        sys.exit(1)

    xml_file = sys.argv[1]

    inspect_abn_file(xml_file)
