import os
from typing import Dict

from dotenv import load_dotenv

load_dotenv()

# API konfiguráció
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
"""str: OpenAI API kulcs, .env fájlból vagy környezeti változókból betöltve."""

TEXT_MODEL_NAME = os.getenv("TEXT_MODEL_NAME", "gpt-4o-mini")
IMAGE_MODEL_NAME = os.getenv("IMAGE_MODEL_NAME", "gpt-4o-mini")
"""str: Az OpenAI model neve, alapértelmezett érték 'gpt-4o-mini'."""

# Könyvtárak
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
"""str: Az alkalmazás gyökérkönyvtárának abszolút elérési útja."""

INPUT_DIR = os.path.join(BASE_DIR, "input")
"""str: Bemeneti fájlok könyvtárának elérési útja."""

BACKUP_DIR = os.path.join(INPUT_DIR, "backup")
"""str: Biztonsági mentések könyvtárának elérési útja."""

OUTPUT_DIR = os.path.join(BASE_DIR, "output")
"""str: Kimeneti fájlok könyvtárának elérési útja."""

OUTPUT_MARKDOWN = os.path.join(OUTPUT_DIR, "markdown")
"""str: Markdown kimenetek könyvtárának elérési útja."""

OUTPUT_JSON = os.path.join(OUTPUT_DIR, "json")
"""str: JSON kimenetek könyvtárának elérési útja."""

POSTPROCESSING_DIR = os.path.join(OUTPUT_DIR, "postprocessing")
"""str: Utófeldolgozási kimenetek könyvtára."""

OUTPUT_IMAGES = os.path.join(OUTPUT_DIR, "images")
"""str: Képek kimentésének alapértelmezett könyvtára."""

LOGS_DIR = os.path.join(BASE_DIR, "logs")

for dir_path in [
    INPUT_DIR,
    BACKUP_DIR,
    OUTPUT_DIR,
    OUTPUT_MARKDOWN,
    OUTPUT_JSON,
    POSTPROCESSING_DIR,
]:
    os.makedirs(dir_path, exist_ok=True)

# Elfogadott bemeneti formátumok

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
"""set[str]: Támogatott fájlkiterjesztések halmaza."""


# Dinamikus fájlútvonal-generálás
def get_paths_for_file(input_file: str) -> Dict[str, str]:
    """
    Generál egy szótárt a bemeneti fájlhoz tartozó kimeneti fájlútvonalakkal.

    A bemeneti fájl nevéből származtatja a kimeneti fájlok neveit.

    Args:
        input_file (str): A bemeneti fájl elérési útja (pl. 'input/doc1.docx').

    Returns:
        Dict[str, str]: A fájlútvonalak szótára, amely kompatibilis a PATHS kulcsokkal.

    Példa:
        >>> get_paths_for_file('input/doc1.docx')
        {
            'input_pdf': 'input/doc1.pdf',
            'input_docx': 'input/doc1.docx',
            'markdown_output': 'output/markdown/doc1.md',
            'json_output': 'output/json/doc1.json',
            'enriched_json_output': 'output/json/doc1_enriched.json',
            'txt_output': 'output/doc1.txt',
            'abbreviations_output': 'output/postprocessing/doc1_abbreviations.json',
        }
    """
    file_name: str = os.path.splitext(os.path.basename(input_file))[0]

    return {
        "input_pdf": os.path.join(INPUT_DIR, f"{file_name}.pdf"),
        "input_docx": os.path.join(INPUT_DIR, f"{file_name}.docx"),
        "markdown_output": os.path.join(OUTPUT_MARKDOWN, f"{file_name}.md"),
        "json_output": os.path.join(OUTPUT_JSON, f"{file_name}.json"),
        "enriched_json_output": os.path.join(OUTPUT_JSON, f"{file_name}_enriched.json"),
        "txt_output": os.path.join(OUTPUT_DIR, f"{file_name}.txt"),
        "abbreviations_output": os.path.join(
            POSTPROCESSING_DIR, f"{file_name}_abbreviations.json"
        ),
    }


# Alapértelmezett PATHS (egy minta fájlhoz, kompatibilitás miatt)
PATHS: Dict[str, str] = get_paths_for_file(os.path.join(INPUT_DIR, "input.docx"))
"""Dict[str, str]: Fájlútvonalak szótárban tárolva a bemeneti fájl alapján.
   
   Kulcsok:
       input_pdf: Bemeneti PDF fájl elérési útja
       input_docx: Bemeneti DOCX fájl elérési útja
       markdown_output: Generált Markdown fájl elérési útja
       json_output: Feldolgozott JSON fájl elérési útja
       enriched_json_output: Dúsított JSON fájl elérési útja
       txt_output: Végső szöveges kimenet elérési útja
       abbreviations_output: Rövidítések JSON fájl elérési útja
"""
