"""
Előfeldolgozási lépések PDF dokumentumokhoz.
Tartalmazza a tartalomjegyzék, üres oldalak, fejléc/lábléc eltávolítását és kapcsolódó segédfüggvényeket.
"""

import re
import fitz
from fitz import Document

# Olyan dokumentumoknál,
# ahol az oldalszám jelölése pl.: Oldal 1 / 146 
VERBOSED_PAGE_NUMBER_PATTERN = r"Oldal \d+ / \d+"

def remove_verbosed_page_numbers(pdf_document: Document) -> int:
    
    removed_verbosed_page_number_indicators = 0

    for page_index in range(0, len(pdf_document)):
        page = pdf_document.load_page(page_index)

        
        try:

            page_blocks = page.get_text('blocks')
            page_number_element = None

            for block in page_blocks:
                text_in_the_block = block[4].rstrip("\n")
                if re.match(VERBOSED_PAGE_NUMBER_PATTERN, text_in_the_block):
                        page_number_element = block
            
            x0, y0, x1, y1, _, _ = page_number_element
            if x1 >= 329 and y1 >= 792:
                page.add_redact_annot((x0, y0, x1, y1), text=None)
            
            page.apply_redactions()
            removed_verbosed_page_number_indicators += 1
        
        except Exception:
            continue
    
    return removed_verbosed_page_number_indicators