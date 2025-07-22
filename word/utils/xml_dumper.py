"""
XML dumpoló segédfüggvények Word dokumentumokhoz.
Lehetővé teszi a dokumentum XML szerkezetének vizsgálatát, instrText és bekezdés dumpolását.
"""

from lxml import etree


def dump_document_xml(doc):
    """
    Kiírja a teljes dokumentum XML-t szépen formázva.

    Args:
        doc (Document): python-docx Document objektum.

    Returns:
        None
    """
    xml_content = doc._part.blob
    tree = etree.fromstring(xml_content)
    print(etree.tostring(tree, pretty_print=True, encoding="unicode"))


def dump_first_paragraphs(doc, max_paragraphs=10):
    """
    Kiírja az első néhány bekezdés (w:p) nyers XML-jét.

    Args:
        doc (Document): python-docx Document objektum.
        max_paragraphs (int, optional): Hány bekezdést írjon ki. Alapértelmezett: 10.

    Returns:
        None
    """
    xml_content = doc._part.blob
    tree = etree.fromstring(xml_content)

    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = tree.findall(".//w:body/w:p", namespaces=ns)

    for i, p in enumerate(paragraphs[:max_paragraphs]):
        print(f"\n--- Bekezdés #{i + 1} ---")
        print(etree.tostring(p, pretty_print=True, encoding="unicode"))


def dump_instr_texts(doc):
    """
    Kilistázza az összes <w:instrText> tartalmát, ahol mezőkód lehet.

    Args:
        doc (Document): python-docx Document objektum.

    Returns:
        None
    """
    xml_content = doc._part.blob
    tree = etree.fromstring(xml_content)

    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    instrs = tree.findall(".//w:instrText", namespaces=ns)

    for i, instr in enumerate(instrs):
        text = instr.text.strip() if instr.text else ""
        if "TOC" in text or "PAGEREF" in text or "HYPERLINK" in text:
            print(f"[{i}] instrText: {text}")
