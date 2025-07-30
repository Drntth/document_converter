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
    remove_headers_from_document,
    remove_page_numbers_from_document
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
        pdf_file = remove_headers_from_document(pdf_file)
        
        headers_removed = True
        print("Fejlécek eltávolítva")
    
    if remove_footers:
        print("Láblécek eltávolítása...")
        pdf_file = remove_page_numbers_from_document(pdf_document=pdf_file)

        footers_removed = True
        print("Láblécek eltávolítva")

    pdf_file.saveIncr()
    pdf_file.close()

    return source_file
        

