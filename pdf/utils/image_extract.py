import fitz
import io
from PIL import Image
from pathlib import Path
import os
import hashlib


# NOTE: Nem minden esetben szűri ki az ugyanolyan képeket
# TODO: Duplikált képek kiszűrése!
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
    
    image_counter = 0 

    for page_index in range(len(pdf_file)):
        page = pdf_file.load_page(page_index)  # load the page
        image_list = page.get_images(full=True)  # get images on the page

        if not image_list:
            print(f"[!] Nincs kép a {page_index+1}. oldalon.")

        for image_index, img in enumerate(image_list, start=1):
            xref = img[0]
            
            base_image = pdf_file.extract_image(xref)
            image_bytes = base_image["image"]

            image_ext = base_image["ext"]

            image_hash = hashlib.md5(image_bytes).hexdigest()
            
            found_bbox = page.get_image_bbox(img)

            if found_bbox.x0 < found_bbox.x1 and found_bbox.y0 < found_bbox.y1:
                
                image_counter += 1

                image_rect = found_bbox

                current_image_filename = f"image_{image_counter}.{image_ext}"
                image_path = f"{output_dir}/image_{image_counter}.{image_ext}"
                
                with open(image_path, "wb") as image_file:
                    image_file.write(image_bytes)

                # print(f"{image_hash} - {image_rect}")

                placeholder_text = f"[IMAGE: {current_image_filename}]"

                image_rect.y1 = 175
                page.add_redact_annot(image_rect, text=placeholder_text)
                print(f"Added redaction to image {image_index + 1} on page {page_index + 1} at {image_rect}")
        
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_REMOVE)

    pdf_file.save(source_file_pdf, garbage=3, deflate=True)
    pdf_file.close()
    return image_counter