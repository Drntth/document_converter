"""
Dokumentumfeldolgozó pipeline fő modulja.

Ez a modul kezeli a teljes feldolgozási folyamatot lépésenként, támogatja a mappák és egyedi fájlok feldolgozását.
"""

import os
import shutil
import time
from pathlib import Path
from typing import Union

import config.settings
from config.logging_config import structlog_logger
from core.processing import (
    docling_process_document,
    enrich_json,
    export_text_from_enriched_json,
    postprocess_input_file,
    preprocess_docx,
    unstructured_process_markdown,
)
from services.file_service import ensure_directories
from tqdm import tqdm
from utils.image_extract import (
    extract_images_from_docx,
    replace_image_placeholders_with_markdown,
)
from utils.markdown_postprocess import clean_markdown_file


def process_pipeline(
    input_path: Union[str, Path],
    step_count: int,
    is_directory: bool = False,
    remove_headers: bool = True,
    remove_footers: bool = True,
    remove_toc: bool = True,
    remove_empty: bool = True,
    abbreviation_strategy: str = "inline",
    footnote_handling: str = "remove",
    process_images_with_ai: bool = True,
) -> None:
    """
    Dokumentumfeldolgozó pipeline futtatása lépésenként.

    Args:
        input_path (Union[str, Path]): A bemeneti fájl vagy mappa elérési útja.
        step_count (int): A végrehajtandó lépések száma (1-7).
        is_directory (bool, optional): Ha True, akkor a bemenet egy mappa, és az összes DOCX/PDF fájlt feldolgozza. Alapértelmezett: False.
        remove_headers (bool, optional): Fejlécek eltávolítása. Alapértelmezett: True.
        remove_footers (bool, optional): Láblécek eltávolítása. Alapértelmezett: True.
        remove_toc (bool, optional): Tartalomjegyzék eltávolítása. Alapértelmezett: True.
        remove_empty (bool, optional): Üres oldalak/sorok eltávolítása. Alapértelmezett: True.
        abbreviation_strategy (str, optional): Rövidítések kezelése. Lehetséges értékek: "inline", "section", "none". Alapértelmezett: "inline".
        footnote_handling (str, optional): Lábjegyzetek kezelése. Lehetséges értékek: "remove", "insert", "none". Alapértelmezett: "remove".
        process_images_with_ai (bool, optional): Képek AI általi feldolgozása vagy csak elérési út megjelenítése. Alapértelmezett: True.

    Returns:
        None: Nincs visszatérési érték.

    """
    logger = structlog_logger.bind(
        input_path=str(input_path),
        step_count=str(step_count),
        is_directory=is_directory,
    )
    logger.info(
        "Pipeline indítása", step_count=str(step_count), is_directory=is_directory
    )

    ensure_directories()
    input_path = Path(input_path)
    if is_directory:
        if not input_path.is_dir():
            logger.error(f"A megadott mappa nem létezik vagy nem mappa: {input_path}")
            raise NotADirectoryError(
                f"A megadott mappa nem létezik vagy nem mappa: {input_path}"
            )

        doc_files = list(input_path.glob("*.[dD][oO][cC][xX]")) + list(
            input_path.glob("*.[pP][dD][fF]")
        )
        if not doc_files:
            logger.warning(f"Nem található DOCX vagy PDF fájl a mappában: {input_path}")
            return

        logger.info(f"Talált fájlok száma a mappában: {len(doc_files)}")

        for file_path in doc_files:
            logger.info(f"Feldolgozás kezdése: {file_path}")
            process_single_file(
                file_path,
                step_count,
                remove_headers=remove_headers,
                remove_footers=remove_footers,
                remove_toc=remove_toc,
                remove_empty=remove_empty,
                abbreviation_strategy=abbreviation_strategy,
                footnote_handling=footnote_handling,
                process_images_with_ai=process_images_with_ai,
            )
    else:
        process_single_file(
            input_path,
            step_count,
            remove_headers=remove_headers,
            remove_footers=remove_footers,
            remove_toc=remove_toc,
            remove_empty=remove_empty,
            abbreviation_strategy=abbreviation_strategy,
            footnote_handling=footnote_handling,
            process_images_with_ai=process_images_with_ai,
        )


def process_single_file(
    source_file: Path,
    steps: int,
    remove_headers: bool = True,
    remove_footers: bool = True,
    remove_toc: bool = True,
    remove_empty: bool = True,
    abbreviation_strategy: str = "inline",
    footnote_handling: str = "remove",
    process_images_with_ai: bool = True,
) -> None:
    """
    Egyetlen fájl feldolgozása a pipeline lépéseivel.

    Args:
        source_file (Path): A bemeneti fájl elérési útja.
        steps (int): A végrehajtandó lépések száma (1-7).
        remove_headers (bool, optional): Fejlécek eltávolítása. Alapértelmezett: True.
        remove_footers (bool, optional): Láblécek eltávolítása. Alapértelmezett: True.
        remove_toc (bool, optional): Tartalomjegyzék eltávolítása. Alapértelmezett: True.
        remove_empty (bool, optional): Üres oldalak/sorok eltávolítása. Alapértelmezett: True.
        abbreviation_strategy (str, optional): Rövidítések kezelése. Alapértelmezett: "inline".
        footnote_handling (str, optional): Lábjegyzetek kezelése. Alapértelmezett: "remove".
        process_images_with_ai (bool, optional): Képek AI általi feldolgozása vagy csak elérési út megjelenítése. Alapértelmezett: True.

    Returns:
        None: Nincs visszatérési érték.

    """
    logger = structlog_logger.bind(source_file=str(source_file), steps=str(steps))
    is_docx: bool = source_file.suffix.lower() == ".docx"
    paths = config.settings.get_paths_for_file(str(source_file))
    total_steps: int = min(steps, 7) if steps != 7 else 6

    with tqdm(
        total=total_steps,
        desc=f"Dokumentum konverziós lépések: {source_file.name}",
        unit="lépés",
    ) as pbar:
        try:
            start_pipeline_time: float = time.time()
            processed_file: Path = source_file
            start_time: float = time.time()
            logger.info("Biztonsági mentés készítése indítása", step="0")

            if not source_file.exists():
                logger.error(f"Forrásfájl nem található: {source_file}")
                raise FileNotFoundError(f"Forrásfájl nem található: {source_file}")

            backup_file: str = os.path.join(
                config.settings.BACKUP_DIR,
                f"{source_file.stem}_backup{source_file.suffix}",
            )
            logger.debug(
                f"Biztonsági mentés fájl: {backup_file}, létezik: {Path(backup_file).exists()}"
            )

            if Path(backup_file).exists():
                logger.warning(
                    f"Biztonsági mentés már létezik: {backup_file}, nem írjuk felül"
                )
            else:
                shutil.copy2(source_file, backup_file)
                logger.info(
                    "Biztonsági mentés készítése befejeződött",
                    context={
                        "source_file": str(source_file),
                        "backup_file": str(backup_file),
                        "duration": time.time() - start_time,
                    },
                )

            pbar.update(0)

            # Képek kimentése a backup után, preprocess előtt
            if is_docx:
                images_dir: Path = (
                    Path(config.settings.OUTPUT_IMAGES) / source_file.stem
                )
                extract_images_from_docx(source_file, images_dir)

            if steps >= 1 or steps == 7:
                start_time = time.time()
                logger.info(
                    "Lépés 1: DOCX dokumentum előfeldolgozás (fejléc, lábléc, tartalomjegyzék, üres sorok/oldalak eltávolítása) indítása",
                    step="1",
                )

                if not is_docx:
                    logger.info("Nem DOCX fájl, az előfeldolgozás kihagyása")
                    processed_file = source_file
                else:
                    processed_file = preprocess_docx(
                        source_file=processed_file,
                        remove_headers=remove_headers,
                        remove_footers=remove_footers,
                        remove_toc=remove_toc,
                        remove_empty=remove_empty,
                    )

                logger.info(
                    "Lépés 1: DOCX dokumentum előfeldolgozás (fejléc, lábléc, tartalomjegyzék, üres sorok/oldalak eltávolítása) befejeződött",
                    context={
                        "source_file": str(processed_file),
                        "processed_file": str(processed_file),
                        "duration": time.time() - start_time,
                    },
                )

                pbar.update(1)

            if steps >= 2 or steps == 7:
                start_time = time.time()
                logger.info(
                    "Lépés 2: DOCX dokumentum utófeldolgozás (rövidítések, lábjegyzetek, mellékletek kezelése) indítása",
                    step="2",
                )

                if not is_docx:
                    logger.info("Nem DOCX fájl, az utófeldolgozás kihagyása")
                    processed_file = source_file
                else:
                    processed_file = postprocess_input_file(
                        source_file=processed_file,
                        abbreviation_strategy=abbreviation_strategy,
                        footnote_handling=footnote_handling,
                    )

                logger.info(
                    "Lépés 2: DOCX dokumentum utófeldolgozás (rövidítések, lábjegyzetek, mellékletek kezelése) befejeződött",
                    context={
                        "source_file": str(processed_file),
                        "processed_file": str(processed_file),
                        "duration": time.time() - start_time,
                    },
                )

                pbar.update(1)

            if steps >= 3 or steps == 7:
                start_time = time.time()
                logger.info(
                    "Lépés 3: Dokumentum (PDF/DOCX) konvertálása Markdown formátumba (Docling) indítása",
                    step="3",
                )

                markdown_file: str = docling_process_document(processed_file)
                clean_markdown_file(markdown_file)
                replace_image_placeholders_with_markdown(
                    Path(markdown_file), source_file.stem
                )

                logger.info(
                    "Lépés 3: Dokumentum (PDF/DOCX) konvertálása Markdown formátumba (Docling) befejeződött",
                    context={
                        "source_file": str(source_file),
                        "markdown_file": str(markdown_file),
                        "duration": time.time() - start_time,
                    },
                )

                pbar.update(1)

            if steps >= 4 or steps == 7:
                start_time = time.time()
                logger.info(
                    "Lépés 4: Markdown fájl konvertálása JSON formátumba (Unstructured) indítása",
                    step="4",
                )

                markdown_file = paths["markdown_output"]
                if not Path(markdown_file).exists():
                    logger.error(f"Markdown fájl nem található: {markdown_file}")
                    raise FileNotFoundError(
                        f"Markdown fájl nem található: {markdown_file}"
                    )

                unstructured_process_markdown(str(source_file), markdown_file)

                logger.info(
                    "Lépés 4: Markdown fájl konvertálása JSON formátumba (Unstructured) befejeződött",
                    context={
                        "markdown_file": str(markdown_file),
                        "output_json_file": str(paths["json_output"]),
                        "duration": time.time() - start_time,
                    },
                )

                pbar.update(1)

            if steps >= 5 or steps == 7:
                start_time = time.time()
                logger.info(
                    "Lépés 5: JSON tartalom gazdagítása táblázat- és képösszefoglalókkal indítása",
                    step="5",
                )

                output_json_file = paths["json_output"]
                if not Path(output_json_file).exists():
                    logger.error(f"JSON fájl nem található: {output_json_file}")
                    raise FileNotFoundError(
                        f"JSON fájl nem található: {output_json_file}"
                    )

                enrich_json(
                    source_file=str(source_file),
                    input_json_path=output_json_file,
                    process_images_with_ai=process_images_with_ai,
                )

                logger.info(
                    "Lépés 5: JSON tartalom gazdagítása táblázat- és képösszefoglalókkal befejeződött",
                    context={
                        "output_json_file": str(output_json_file),
                        "enriched_json_file": str(paths["enriched_json_output"]),
                        "duration": time.time() - start_time,
                    },
                )

                pbar.update(1)

            if steps >= 6 or steps == 7:
                start_time = time.time()
                logger.info(
                    "Lépés 6: Gazdagított JSON exportálása TXT fájlba indítása",
                    step="6",
                )

                enriched_json_file = paths["enriched_json_output"]
                if not Path(enriched_json_file).exists():
                    logger.error(
                        f"Gazdagított JSON fájl nem található: {enriched_json_file}"
                    )
                    raise FileNotFoundError(
                        f"Gazdagított JSON fájl nem található: {enriched_json_file}"
                    )

                export_text_from_enriched_json(str(source_file), enriched_json_file)

                logger.info(
                    "Lépés 6: Gazdagított JSON exportálása TXT fájlba befejeződött",
                    context={
                        "enriched_json_file": str(enriched_json_file),
                        "output_txt_file": str(paths["txt_output"]),
                        "duration": time.time() - start_time,
                    },
                )

                pbar.update(1)

            if steps == 7:
                logger.info(
                    "Lépés 7: Az összes lépés végrehajtása befejeződött",
                    context={"total_duration": time.time() - start_pipeline_time},
                )

            logger.info(
                "Fájl feldolgozása sikeresen befejeződött", source_file=str(source_file)
            )

        except Exception as e:
            logger.error(
                "Feldolgozási hiba a pipeline-ban",
                error=str(e),
                exception=str(e.__traceback__),
                step=str(min(steps, 7)),
            )
            raise
