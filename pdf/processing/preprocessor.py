"""
Előfeldolgozási lépések PDF dokumentumokhoz.
Tartalmazza a tartalomjegyzék, üres oldalak, fejléc/lábléc eltávolítását és kapcsolódó segédfüggvényeket.
"""

import re
import fitz
from fitz import Document


VERBOSED_PAGE_NUMBER_PATTERN = r"Oldal \d+ / \d+"
"""
Olyan dokumentumoknál, ahol az oldalszám jelölése pl.: 'Oldal 1 / 146'.
"""

PAGE_NUMBER_PATTERN = r"\d+"
"""
Olyan dokumentumoknál, ahol az oldalszám jelölése pl.: '1'.
"""

EN_DASH_PAGE_NUMBER_PATTERN = r"\u2013 \d+ \u2013"
"""
Olyan dokumentumoknál, ahol az oldalszám jelölése pl.: '— 1 —'.
"""

# a fenti regex-ek kombinálva
COMBINED_PAGE_NUMBER_PATTERN = f"{VERBOSED_PAGE_NUMBER_PATTERN}|"\
                                f"{PAGE_NUMBER_PATTERN}|"\
                                f"{EN_DASH_PAGE_NUMBER_PATTERN}"
"""
A VERBOSED_PAGE_NUMBER_PATTERN, PAGE_NUMBER_PATTERN és EN_DASH_PAGE_NUMBER_PATTERN 
reguláris kifejezés minták kombinálva
"""

COORDS_OF_THE_TOP_LEFT_CORNER_OF_A_PAGE_IN_TUPLE = (0.0, 0.0, 0.0, 0.0)
"""
Egy PDF oldal bal felső sarkának koordinátái tuple-ben megadva.\n
Olyan esetekre, amikor egy szöveget körülhatároló tégalap objektumot (Rect) kell keresni.
"""

def remove_page_numbers(pdf_document: Document) -> Document:

    print("remove_page_numbers függvény eleje")
    for page_index in range(0, len(pdf_document)):
        page = pdf_document.load_page(page_index)

        page_x0, page_y0, page_x1, page_y1 = page.bound()

        tables_on_page = page.find_tables()
        
        page_blocks = page.get_text('blocks')

        try:
            page_number_element_candidates = []
    
            for block in page_blocks:
                text_in_the_block = block[4].lstrip(" \n \n").rstrip(" \n \n")
                match = re.fullmatch(COMBINED_PAGE_NUMBER_PATTERN, text_in_the_block)
                if match:
                    page_number_element_candidates.append(block)
            
            if len(page_number_element_candidates) > 0:
                min_distance = float('inf')

                closest_candidate_rect = COORDS_OF_THE_TOP_LEFT_CORNER_OF_A_PAGE_IN_TUPLE
                closest_candidate = page_number_element_candidates[0]

                for candidate in page_number_element_candidates:
                    (candidate_x0, candidate_y0, candidate_x1, candidate_y1, 
                                                text_in_candidate, *_) = candidate

                    text_in_candidate = text_in_candidate.lstrip(" \n \n").rstrip(" \n \n")
                    current_page_indicator = re.search(PAGE_NUMBER_PATTERN, text_in_candidate).group(0)
                    if int(current_page_indicator) <= len(pdf_document):

                        # distance = math.sqrt((page_x1 - candidate_x1)**2 + (page_y1 - candidate_y1)**2) Euklidészi távolság két pont között.
                        # Manhattan távolság a két y koordináta között.
                        distance = abs(page_y1 - candidate_y1) 

                        if distance <= min_distance:
                            min_distance = distance
                            
                            closest_candidate_rect = (candidate_x0, candidate_y0, 
                                                        candidate_x1, candidate_y1)
                            closest_candidate = candidate
                
                is_closest_candidate_inside_a_table = False

                (closest_candidate_x0, closest_candidate_y0, 
                    closest_candidate_x1, closest_candidate_y1) = closest_candidate_rect
                
                index = 0
                while index < len(tables_on_page.tables) and not is_closest_candidate_inside_a_table:
                    table_x0, table_y0, table_x1, table_y1 = tables_on_page[index].bbox

                    # REFACTOR: Elágazás kiszervezése külön függvénybe, például: is_inside_a_table()
                    if ( 
                        (closest_candidate_x0 > table_x0 and closest_candidate_x0 < table_x1 
                            and closest_candidate_y0 > table_y0 and closest_candidate_y0 < table_y1) and 
                        (closest_candidate_x1 > table_x0 and closest_candidate_x1 < table_x1 
                            and closest_candidate_y1 > table_y0 and closest_candidate_y1 < table_y1) 
                    ):
                        is_closest_candidate_inside_a_table = True
                    
                    index += 1
                
                if not is_closest_candidate_inside_a_table:
                    page.add_redact_annot(closest_candidate_rect, text=None)
                    print("Oldalszám megjelölve")

            page.apply_redactions()
            print("Oldalszám eltávolítva")
        
        
        except Exception as e:
            print(f"{str(e)}")
            continue

    return pdf_document