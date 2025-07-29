import os
import shutil
import time
from pathlib import Path
from typing import Union
from tqdm import tqdm

import config.settings
from services.file_service import ensure_directories
from core.processing import preprocess_pdf
from utils.image_extract import extract_images_from_pdf


# NOTE: Word projektből átemelve
def process_pipeline(
    input_path: Union[str, Path],
    step_count: int,
    is_directory: bool = False,
    # TODO: PDF fájlokkal működő fej- és lábléc eltávolítására alkalmas paraméterek definiálása
    # Ezek majd pdf fájlokkal kompatibilis paraméterek lesznek,
    # Egyelőre itt maradnak kikommentezve referencia gyanánt
    remove_headers: bool = True,
    remove_footers: bool = True,
    # remove_toc: bool = True,
    # remove_empty: bool = True,
    # abbreviation_strategy: str = "inline",
    # footnote_handling: str = "remove",
    # process_images_with_ai: bool = True,
) -> None:
    """
    Dokumentumfeldolgozó pipeline futtatása lépésenként.

    Args:
        input_path (Union[str, Path]): A bemeneti fájl vagy mappa elérési útja.
        step_count (int): A végrehajtandó lépések száma (1-7).
        is_directory (bool, optional): Ha True, akkor a bemenet egy mappa, és az összes DOCX/PDF fájlt feldolgozza. Alapértelmezett: False.

    Returns:
        None: Nincs visszatérési érték.

    """
    # logger = structlog_logger.bind(
    #     input_path=str(input_path),
    #     step_count=str(step_count),
    #     is_directory=is_directory,
    # )
    # logger.info(
    #     "Pipeline indítása", step_count=str(step_count), is_directory=is_directory
    # )

    ensure_directories()
    input_path = Path(input_path)
    if is_directory:
        if not input_path.is_dir():
            # logger.error(f"A megadott mappa nem létezik vagy nem mappa: {input_path}")
            raise NotADirectoryError(
                f"A megadott mappa nem létezik vagy nem mappa: {input_path}"
            )

        doc_files = list(input_path.glob("*.[dD][oO][cC][xX]")) + list(
            input_path.glob("*.[pP][dD][fF]")
        )
        if not doc_files:
            # logger.warning(f"Nem található DOCX vagy PDF fájl a mappában: {input_path}")
            return

        # logger.info(f"Talált fájlok száma a mappában: {len(doc_files)}")

        for file_path in doc_files:
            # logger.info(f"Feldolgozás kezdése: {file_path}")
            process_single_file(
                file_path,
                step_count,
                # TODO: PDF fájlok fej- és lábléceit eltávolító paraméterek alkalmazása
                # remove_headers=remove_headers,
                # remove_footers=remove_footers,
                # remove_toc=remove_toc,
                # remove_empty=remove_empty,
                # abbreviation_strategy=abbreviation_strategy,
                # footnote_handling=footnote_handling,
                # process_images_with_ai=process_images_with_ai,
            )
    else:
        process_single_file(
            input_path,
            step_count,
            # TODO: PDF fájlok fej- és lábléceit eltávolító paraméterek alkalmazása
            remove_headers=remove_headers,
            remove_footers=remove_footers,
            # remove_toc=remove_toc,
            # remove_empty=remove_empty,
            # abbreviation_strategy=abbreviation_strategy,
            # footnote_handling=footnote_handling,
            # process_images_with_ai=process_images_with_ai,
        )

def process_single_file(source_file: Path, steps: int, remove_headers: bool, remove_footers: bool):
    is_pdf: bool = source_file.suffix.lower() == ".pdf"
    paths = config.settings.get_paths_for_file(str(source_file))
    total_steps: int = min(steps, 7) if steps != 7 else 6

    with tqdm(
        total=total_steps, 
        desc=f"Dokumentum konverziós lépések: {source_file.name}",
        unit="lépés",
    ) as progress_bar:
        try:
            start_pipeline_time: float = time.time()
            processed_file: Path = source_file
            start_time: float = time.time()

            if not source_file.exists():
                raise FileNotFoundError(f"Forrásfájl nem található: {source_file}")

            backup_file: str = os.path.join(
                config.settings.BACKUP_DIR,
                f"{source_file.stem}_backup{source_file.suffix}",
            )

            if not Path(backup_file).exists():
                shutil.copy2(source_file, backup_file)
            progress_bar.update(0)

            if is_pdf:
                images_dir: Path = (
                    Path(config.settings.OUTPUT_IMAGES) / source_file.stem
                )
                extract_images_from_pdf(source_file, images_dir)
                print("Képek kimentése befejeződött!")

            if steps >= 1 or steps == 7:
                start_time = time.time()
                processed_file = preprocess_pdf(
                    source_file=source_file, 
                    remove_headers=remove_headers,
                    remove_footers=remove_footers
                )
                progress_bar.update(1)
        except:
            # Csak referencia gyanánt van itt! Majd módosításra kerül.
            # logger.error(
            #     "Feldolgozási hiba a pipeline-ban",
            #     error=str(e),
            #     exception=str(e.__traceback__),
            #     step=str(min(steps, 7)),
            # )
            raise