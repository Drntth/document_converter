"""
Fájl- és könyvtárkezelő segédfüggvények, validációk, strukturált JSON mentés és naplózás támogatása.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Union

# from config.logging_config import structlog_logger
from config.settings import (
    BACKUP_DIR,
    INPUT_DIR,
    LOGS_DIR,
    OUTPUT_DIR,
    OUTPUT_IMAGES,
    OUTPUT_JSON,
    OUTPUT_MARKDOWN,
    POSTPROCESSING_DIR,
    SUPPORTED_EXTENSIONS,
)


def ensure_directories() -> None:
    """
    Létrehozza a szükséges könyvtárakat, ha még nem léteznek.

    A függvény ellenőrzi és létrehozza az alábbi könyvtárakat:
        - INPUT_DIR: Bemeneti könyvtár
        - OUTPUT_DIR: Kimeneti könyvtár
        - OUTPUT_MARKDOWN: Markdown kimenetek könyvtára
        - OUTPUT_JSON: JSON kimenetek könyvtára
        - BACKUP_DIR: Biztonsági mentések könyvtára
        - POSTPROCESSING_DIR: Utófeldolgozási könyvtár
        - LOGS_DIR: Log könyvtár

    Returns:
        None

    Raises:
        OSError: Ha a könyvtárak létrehozása sikertelen.
    """
    # logger = structlog_logger.bind(function="ensure_directories")

    directories = [
        INPUT_DIR,
        BACKUP_DIR,
        OUTPUT_DIR,
        OUTPUT_MARKDOWN,
        OUTPUT_JSON,
        POSTPROCESSING_DIR,
        OUTPUT_IMAGES,
    ]

    for path in directories:
        try:
            os.makedirs(path, exist_ok=True)
            # logger.debug("Könyvtár ellenőrizve/létrehozva", directory=str(path))
        except OSError as e:
            # logger.error(
            #     "Hiba a könyvtár létrehozása közben",
            #     directory=str(path),
            #     error=str(e),
            #     exc_info=True,
            # )
            raise


def clear_directories() -> None:
    """
    Törli az input, output és log mappák tartalmát.

    A függvény törli a mappák tartalmát:
        - INPUT_DIR
        - OUTPUT_DIR (beleértve OUTPUT_MARKDOWN és OUTPUT_JSON almappákat)
        - LOGS_DIR

    Returns:
        None

    Raises:
        OSError: Ha a fájlok vagy mappák törlése sikertelen.
    """
    # logger = structlog_logger.bind(function="clear_directories")

    directories = [
        INPUT_DIR,
        OUTPUT_DIR,
        OUTPUT_MARKDOWN,
        OUTPUT_JSON,
        LOGS_DIR,
    ]

    for directory in directories:
        directory_path = Path(directory)
        if directory_path.exists() and directory_path.is_dir():
            try:
                for item in directory_path.iterdir():
                    if item.is_file():
                        item.unlink()
                        # logger.debug("Fájl törölve", path=str(item))
                    elif item.is_dir():
                        shutil.rmtree(item)
                        # logger.debug("Mappa törölve", path=str(item))
                # logger.info("Könyvtár tartalma törölve", directory=str(directory))
            except OSError as e:
                # logger.error(
                #     "Hiba a könyvtár tartalmának törlése közben",
                #     directory=str(directory),
                #     error=str(e),
                #     exc_info=True,
                # )
                raise
        else:
            print("Könyvtár nem létezik vagy nem mappa", directory=str(directory))
            # logger.debug(
            #     "Könyvtár nem létezik vagy nem mappa", directory=str(directory)
            # )


def validate_document(source_file: Union[str, Path]) -> None:
    """
    Ellenőrzi a dokumentumfájl létezését és formátumát.

    A függvény két alapvető ellenőrzést végez:
        1. A fájl fizikai létezésének ellenőrzése a fájlrendszerben.
        2. A fájl kiterjesztésének ellenőrzése a támogatott formátumok listája (config.SUPPORTED_EXTENSIONS) alapján (kis- és nagybetű érzéketlen összehasonlítás).

    Args:
        source_file (Union[str, Path]): Az ellenőrizendő fájl elérési útja. Stringként vagy pathlib.Path objektumként is megadható.

    Returns:
        None

    Raises:
        FileNotFoundError: Ha a fájl nem található a megadott elérési úton.
        ValueError: Ha a fájl kiterjesztése nem szerepel a támogatott formátumok listájában (config.SUPPORTED_EXTENSIONS).

    Notes:
        - A támogatott fájlformátumokat a config.SUPPORTED_EXTENSIONS listában kell meghatározni.
        - A kiterjesztés-ellenőrzés kis- és nagybetűérzéketlen.
    """
    # logger = structlog_logger.bind(function="validate_document")
    source_file = Path(source_file)

    # logger.debug("Fájl ellenőrzése", source_file=str(source_file))

    if not source_file.exists():
        # logger.error("A fájl nem található", source_file=str(source_file))
        raise FileNotFoundError(f"A fájl nem található: {source_file}")

    if source_file.suffix.lower() not in SUPPORTED_EXTENSIONS:
        # logger.error(
        #     "Nem támogatott fájlformátum",
        #     source_file=str(source_file),
        #     supported_extensions=", ".join(SUPPORTED_EXTENSIONS),
        # )
        raise ValueError(
            f"A fájl nem támogatott formátumú: {source_file}. "
            f"Támogatott formátumok: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    # logger.info("Fájl validáció sikeres", source_file=str(source_file))


def write_json(data: List[Dict], output_path: str) -> None:
    """
    JSON adatokat ír fájlba.

    Args:
        data (List[Dict]): A kiírandó adatok listája.
        output_path (str): A kimeneti JSON fájl elérési útja.

    Returns:
        None
    """
    # logger = structlog_logger.bind(function="write_json")
    output_path = Path(output_path)

    # logger.debug("JSON fájl írása", output_path=str(output_path))

    try:
        os.makedirs(output_path.parent, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        # logger.info("JSON fájl sikeresen írva", output_path=str(output_path))
    except (OSError, json.JSONEncodeError) as e:
        # logger.error(
        #     "Hiba a JSON fájl írása közben",
        #     output_path=str(output_path),
        #     error=str(e),
        #     exc_info=True,
        # )
        raise


def save_abbreviations(abbreviations: Dict[str, str], path: str) -> None:
    """
    Rövidítésszótár mentése JSON fájlba.

    Args:
        abbreviations (Dict[str, str]): A rövidítések szótára.
        path (str): A fájl elérési útja.

    Returns:
        None
    """

    # logger = structlog_logger.bind(
    #     function="save_abbreviations",
    #     output_path=path,
    #     total_abbreviations=len(abbreviations),
    #     operation="abbreviation_export",
    # )

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(abbreviations, f, indent=2, ensure_ascii=False)
        # logger.info(
        #     "Rövidítésszótár sikeresen elmentve",
        #     file_size=f"{os.path.getsize(path) / 1024:.2f} KB",
        # )
    except Exception as e:
        # logger.error("Hiba a rövidítésszótár mentésekor", error=str(e), exc_info=True)
        raise
