"""
A dokumentumfeldolgozó pipeline fő modulja.
Ez a modul kezeli a teljes feldolgozási folyamatot lépésenként, támogatja a mappák és egyedi fájlok feldolgozását.
"""

import os
import shutil
import time
from typing import Union
from pathlib import Path
from tqdm import tqdm

from core.processing import (
    docling_process_document,
    unstructured_process_markdown,
    enrich_json,
    export_text_from_enriched_json,
    preprocess_docx,
    postprocess_input_file,
)
from services.file_service import ensure_directories
from config.logging_config import structlog_logger
import config.settings
from utils.markdown_postprocess import clean_markdown_file
from utils.image_extract import (
    extract_images_from_docx,
    replace_image_placeholders_with_markdown,
)


def process_pipeline(
    source: Union[str, Path],
    steps: int,
    is_directory: bool = False,
    remove_headers: bool = True,
    remove_footers: bool = True,
    remove_toc: bool = True,
    remove_empty: bool = True,
    abbreviation_strategy: str = "inline",
    footnote_handling: str = "remove",
) -> None:
    """
    Dokumentumfeldolgozó pipeline futtatása lépésenként.

    Args:
        source (Union[str, Path]): A bemeneti fájl vagy mappa elérési útja.
        steps (int): A végrehajtandó lépések száma (1-7).
        is_directory (bool): Ha True, akkor a source egy mappa, és az összes DOCX/PDF fájlt feldolgozza.
        remove_headers (bool): Fejlécek eltávolítása.
        remove_footers (bool): Láblécek eltávolítása.
        remove_toc (bool): Tartalomjegyzék eltávolítása.
        remove_empty (bool): Üres oldalak/sorok eltávolítása.
        abbreviation_strategy (str): Rövidítések kezelése. Lehetséges értékek: "inline", "section", "none".
        footnote_handling (str): Lábjegyzetek kezelése. Lehetséges értékek: "remove", "insert".
    """
    logger = structlog_logger.bind(
        source=str(source), steps=str(steps), is_directory=is_directory
    )
    logger.info("Pipeline indítása", steps=str(steps), is_directory=is_directory)

    ensure_directories()
    source = Path(source)
    if is_directory:
        if not source.is_dir():
            logger.error(f"A megadott mappa nem létezik vagy nem mappa: {source}")
            raise NotADirectoryError(
                f"A megadott mappa nem létezik vagy nem mappa: {source}"
            )

        files = list(source.glob("*.[dD][oO][cC][xX]")) + list(
            source.glob("*.[pP][dD][fF]")
        )
        if not files:
            logger.warning(f"Nem található DOCX vagy PDF fájl a mappában: {source}")
            return

        logger.info(f"Talált fájlok száma a mappában: {len(files)}")

        for source_file in files:
            logger.info(f"Feldolgozás kezdése: {source_file}")
            process_single_file(
                source_file,
                steps,
                remove_headers=remove_headers,
                remove_footers=remove_footers,
                remove_toc=remove_toc,
                remove_empty=remove_empty,
                abbreviation_strategy=abbreviation_strategy,
                footnote_handling=footnote_handling,
            )
    else:
        process_single_file(
            source,
            steps,
            remove_headers=remove_headers,
            remove_footers=remove_footers,
            remove_toc=remove_toc,
            remove_empty=remove_empty,
            abbreviation_strategy=abbreviation_strategy,
            footnote_handling=footnote_handling,
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
) -> None:
    """
    Egyetlen fájl feldolgozása a pipeline lépéseivel.

    Args:
        source_file (Path): A bemeneti fájl elérési útja.
        steps (int): A végrehajtandó lépések száma (1-7).
        remove_headers (bool): Fejlécek eltávolítása.
        remove_footers (bool): Láblécek eltávolítása.
        remove_toc (bool): Tartalomjegyzék eltávolítása.
        remove_empty (bool): Üres oldalak/sorok eltávolítása.
        abbreviation_strategy (str): Rövidítések kezelése.
        footnote_handling (str): Lábjegyzetek kezelése.
    """
    logger = structlog_logger.bind(source_file=str(source_file), steps=str(steps))
    is_docx = source_file.suffix.lower() == ".docx"

    paths = config.settings.get_paths_for_file(str(source_file))

    total_steps = min(steps, 7) if steps != 7 else 6
    with tqdm(
        total=total_steps,
        desc=f"Dokumentum konverziós lépések: {source_file.name}",
        unit="lépés",
    ) as pbar:
        try:
            start_pipeline_time = time.time()
            processed_file = source_file

            start_time = time.time()
            logger.info("Biztonsági mentés készítése indítása", step="0")

            if not source_file.exists():
                logger.error(f"Forrásfájl nem található: {source_file}")
                raise FileNotFoundError(f"Forrásfájl nem található: {source_file}")

            backup_file = os.path.join(
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
                images_dir = Path(config.settings.OUTPUT_IMAGES) / source_file.stem
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

                markdown_file = docling_process_document(processed_file)

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

                enrich_json(str(source_file), output_json_file)

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
