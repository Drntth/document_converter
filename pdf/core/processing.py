"""
Feldolgozási logika: dokumentum előfeldolgozás, konverzió, gazdagítás, export.
Minden lépés külön függvényben, abszolút importokkal, PEP 257 docstringekkel.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Dict

import config.settings

from docling.document_converter import DocumentConverter
import fitz
# from processing.enrichment import summarize_image, summarize_table
# from processing.postprocessor import (
#     extract_abbreviations,
#     insert_abbreviations,
#     insert_footnotes,
#     prepend_abbreviation_section,
#     remove_abbreviation_phrases,
#     remove_footnote_references,
# )
from processing.preprocessor import (
    remove_page_numbers
)
# from services.file_service import save_abbreviations, validate_document, write_json
# from unstructured.partition.auto import partition

def preprocess_pdf(
        source_file: Path, 
        remove_headers: bool, 
        remove_footers: bool, 
        # remove_toc: bool,
        # remove_empty: bool
) -> Path:
    
    """
    Fő előfeldolgozó függvény választható lépésekkel. (Word projektből átemelve)

    Args:
        source_file (Path): A bemeneti dokumentum elérési útja.
        remove_headers (bool): Fejlécek eltávolítása.
        remove_footers (bool): Láblécek eltávolítása.
        remove_toc (bool): Tartalomjegyzék eltávolítása.
        remove_empty (bool): Üres oldalak/sorok eltávolítása.

    Returns:
        Path: Az előfeldolgozott dokumentum elérési útja.
    """

    headers_removed = False
    footers_removed = False

    pdf_file = fitz.open(source_file)
    print("preprocess_pdf függvény eleje")
    if remove_headers:
        print("Fejlécek eltávolítása...")
        for page_index in range(0, len(pdf_file)):
            page = pdf_file.load_page(page_index)
            page_dict = page.get_text('dict')

            blocks_on_page = page_dict.get('blocks')
            first_block_on_page = blocks_on_page[0]
            # print(f"{page_index+1} - {first_block_on_page}")
            first_bbox = first_block_on_page['bbox']
            
            first_x0, first_y0, first_x1, first_y1 = first_bbox
            if first_x0 <= 72 and first_y0 <= 38:
                page.add_redact_annot(first_bbox, text=None)
                print(f"Fejléc megjelölve a(z) {page_index+1}.oldalon")
            
            page.apply_redactions()
            print(f"Fejléc eltávolítva a(z) {page_index+1}.oldalon")

        headers_removed = True
        print("Fejlécek eltávolítva")
    
    if remove_footers:
        print("Láblécek eltávolítása...")
        pdf_file = remove_page_numbers(pdf_document=pdf_file)

        footers_removed = True
        print("Láblécek eltávolítva")

    pdf_file.saveIncr()
    pdf_file.close()

    return source_file
        

