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
# from processing.preprocessor import (
#     remove_empty_pages,
#     remove_toc_by_field,
#     remove_toc_by_paragraphs,
#     remove_toc_by_table,
#     remove_toc_by_text,
#     remove_toc_by_xml,
# )
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

    if remove_headers:
        for page_index in range(0, len(pdf_file)):
            page = pdf_file.load_page(page_index)
            page_dict = page.get_text('dict')

            blocks_on_page = page_dict.get('blocks')
            first_block_on_page = blocks_on_page[0]
            first_bbox = first_block_on_page['bbox']
            
            first_x0, first_y0, first_x1, first_y1 = first_bbox
            if first_x0 <= 72 and first_y0 <= 36:
                page.add_redact_annot(first_bbox, text=None)
            
            page.apply_redactions()

        headers_removed = True
        # print("Fejlécek eltávolítva")

    # if remove_footers:
        

