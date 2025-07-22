"""
JSON gazdagítási lépések, táblázat- és képösszefoglalók, metaadatok kezelése.
A modul célja, hogy a feldolgozott JSON-t OpenAI vagy más szolgáltatások segítségével bővítse.
"""

import base64
import os

import config.settings
from bs4 import BeautifulSoup
from config.prompts import TABLE_SUMMARY_PROMPT, TABLE_SYSTEM_MESSAGE
from services.api_client import call_openai_api, call_openai_vision_api


def summarize_table(html_content: str) -> str:
    """
    Összefoglalja a táblázat tartalmát az OpenAI API segítségével.

    Args:
        html_content (str): A HTML táblázat tartalma.

    Returns:
        str: A táblázat szöveges összefoglalója.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    prompt: str = TABLE_SUMMARY_PROMPT.format(table_data=soup)
    summary: str = call_openai_api(prompt, TABLE_SYSTEM_MESSAGE)
    return summary


def summarize_image(image_path: str) -> str:
    """
    Kép szöveges leírásának generálása OpenAI Vision API segítségével.

    Args:
        image_path (str): A kép relatív vagy abszolút elérési útja (output/images/...).

    Returns:
        str: A kép szöveges leírása.
    """
    output_dir: str = config.settings.OUTPUT_DIR
    abs_image_path: str = (
        os.path.join(output_dir, image_path)
        if not os.path.isabs(image_path)
        else image_path
    )
    base64_image: str = encode_image(abs_image_path)
    return call_openai_vision_api(base64_image)


def encode_image(image_path: str) -> str:
    """
    Képfájl base64 kódolása szöveggé.

    Args:
        image_path (str): A képfájl elérési útja.

    Returns:
        str: Base64 kódolt kép szövegként.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
