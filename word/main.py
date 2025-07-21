"""
A parancssori belépési pont a dokumentumfeldolgozó pipeline-hoz.
Ez a modul kezeli az argumentumokat, naplózást és a pipeline indítását.
"""

import argparse
from core.pipeline import process_pipeline
from config.logging_config import structlog_logger
from services.file_service import clear_directories

logger = structlog_logger


def parse_args():
    """
    Feldolgozza a parancssori argumentumokat.
    Returns:
        argparse.Namespace: A feldolgozott argumentumokat tartalmazó objektum.
    """
    logger.debug("Parancssori argumentumok feldolgozása")
    parser = argparse.ArgumentParser(
        description="Dokumentumfeldolgozó pipeline PDF és DOCX fájlokhoz"
    )
    parser.add_argument(
        "--input",
        help="Bemeneti fájl elérési útja (PDF vagy DOCX formátumú)",
    )
    parser.add_argument(
        "--input-dir",
        help="Bemeneti mappa elérési útja, amely DOCX vagy PDF fájlokat tartalmaz",
    )
    parser.add_argument(
        "--steps",
        type=int,
        choices=range(1, 8),
        default=7,
        help="Futtatandó lépések:\n"
        "  1: Előfeldolgozás (preprocessing: fejléc, lábléc, tartalomjegyzék, üres sorok/oldalak eltávolítása)\n"
        "  2: Utófeldolgozás (postprocessing: rövidítések, lábjegyzetek)\n"
        "  3: Dokumentum (PDF/DOCX) konvertálása Markdown formátumba (Docling)\n"
        "  4: Markdown fájl feldolgozása JSON formátumba (Unstructured)\n"
        "  5: JSON tartalom gazdagítása táblázat- és képösszefoglalókkal (OpenAI)\n"
        "  6: Gazdagított JSON exportálása TXT fájlba\n"
        "  7: Minden lépés egymás után",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Törli az input, output és log mappák tartalmát a pipeline futtatása előtt",
    )
    args = parser.parse_args()

    if not args.clear and (args.input is None and args.input_dir is None):
        parser.error(
            "Legalább az egyik argumentum szükséges: --input vagy --input-dir, kivéve ha --clear van megadva"
        )
    if args.input is not None and args.input_dir is not None:
        parser.error("Csak az egyik argumentum adható meg: --input vagy --input-dir")

    logger.info(
        "Argumentumok sikeresen feldolgozva",
        input=args.input,
        input_dir=args.input_dir,
        steps=args.steps,
        clear=args.clear,
    )
    return args


def main():
    """
    A fő program belépési pontja. Elindítja a pipeline-t a megadott argumentumok alapján.
    """
    logger.info("Dokumentumfeldolgozó pipeline indítása")
    try:
        args = parse_args()
        if args.clear:
            logger.info("Input, output és log mappák tartalmának törlése")
            clear_directories()
            logger.info("Mappák tartalma sikeresen törölve")
        if args.input:
            process_pipeline(args.input, args.steps)
            logger.info("Pipeline sikeresen lefutott")
        elif args.input_dir:
            process_pipeline(args.input_dir, args.steps, is_directory=True)
            logger.info("Pipeline sikeresen lefutott")
    except Exception as e:
        logger.error("Hiba történt a pipeline futtatása során", exc_info=e)
        raise


if __name__ == "__main__":
    main()
