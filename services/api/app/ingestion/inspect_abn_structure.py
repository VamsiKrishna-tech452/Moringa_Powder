import sys
import xml.etree.ElementTree as ET


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def inspect_first_abr(xml_file: str):
    for event, element in ET.iterparse(
        xml_file,
        events=("end",),
    ):
        if local_name(element.tag) != "ABR":
            continue

        print("=" * 70)
        print("ABR ELEMENT ATTRIBUTES")
        print("=" * 70)

        for key, value in element.attrib.items():
            print(f"{local_name(key)} = {value}")

        print("\n" + "=" * 70)
        print("ABR CHILD ELEMENTS")
        print("=" * 70)

        for child in element.iter():
            if child is element:
                continue

            tag = local_name(child.tag)
            text = (child.text or "").strip()

            if text:
                print(f"{tag} = {text}")
            else:
                print(f"{tag}")

        element.clear()
        break


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "Usage: "
            "python -m app.ingestion.inspect_abn_structure "
            "/path/to/file.xml"
        )
        sys.exit(1)

    inspect_first_abr(sys.argv[1])
