import fitz
import io
from PIL import Image
from pathlib import Path
import os
import hashlib

# REFACTOR: A kevésbé értelmezhető részek kiszervezése külön segédfüggvényekbe.
def extract_images_from_pdf(source_file_pdf: Path, output_dir: Path) -> int:
    """
    Képek kimentése PDF fájlokból
    
    Args:
        source_file_pdf (Path): A bemeneti PDF fájl.
        output_dir (Path): A képek célmappája.

    Returns:
        int: Kimentett képek száma.
    """
    pdf_file = fitz.open(source_file_pdf)
    source_file_pdf = Path(source_file_pdf)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    saved_image_hash_set = set()
    image_counter = 0 

    for page_index in range(len(pdf_file)):
        page = pdf_file.load_page(page_index)
        image_list = page.get_images(full=True)

        info_of_texts_on_page = []

        extracted_text_info = page.get_text("dict")
        for block in extracted_text_info.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    info_of_text_on_page_dict = {}
                    text_content = span['text']
                    x, y = span['origin']
                    
                    info_of_text_on_page_dict["text"] = text_content
                    info_of_text_on_page_dict["x"] = x
                    info_of_text_on_page_dict["y"] = y
                    info_of_texts_on_page.append(info_of_text_on_page_dict)


        if not image_list:
            print(f"[!] Nincs kép a {page_index+1}. oldalon.")

        texts_to_retrieve = []
        for image_index, img in enumerate(image_list, start=1):
            xref = img[0]
            
            base_image = pdf_file.extract_image(xref)
            image_bytes = base_image["image"]

            image_ext = base_image["ext"]

            image_hash = hashlib.md5(image_bytes).hexdigest()
            
            found_bbox = page.get_image_bbox(img)

            if found_bbox.x0 < found_bbox.x1 and found_bbox.y0 < found_bbox.y1:
                
                image_rect = found_bbox

                if image_hash not in saved_image_hash_set:
                    image_counter += 1

                    current_image_filename = f"image_{image_counter}.{image_ext}"
                    image_path = f"{output_dir}/image_{image_counter}.{image_ext}"
                    
                    with open(image_path, "wb") as image_file:
                        image_file.write(image_bytes)
                    saved_image_hash_set.add(image_hash)

                x0, y0, x1, y1 = image_rect

                for element in info_of_texts_on_page:
                    text, x, y = element.values()
                    
                    if x > x0 and x < x1 and y > y0 and y < y1:
                        texts_to_retrieve.append({"overlapping_image": current_image_filename, "page": page_index, "text": text, "x": x, "y": y})
                
                placeholder_text = f"[IMAGE: {current_image_filename}]"

                page.add_redact_annot(image_rect, text=placeholder_text)
                # print(f"Added redaction to image {image_index + 1} on page {page_index + 1} at {image_rect}")
        
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE)

        for element in texts_to_retrieve:
            _, page, text, x, y = element.values()
            page_to_insert = pdf_file.load_page(page)
            page_to_insert.insert_text(fitz.Point(x, y), text, fontname="helv")
    
    
    # pdf_file.save(source_file_pdf, incremental=True, encryption=PDF_ENCRYPT_KEEP) 
    # metódus rövidebb változata
    pdf_file.saveIncr()
    pdf_file.close()
    return image_counter