import argparse

from core.pipeline import process_pipeline
from services.file_service import clear_directories


def parse_args() -> argparse.Namespace:
    """
    Feldolgozza a parancssori argumentumokat. (Átemelve a Word projektből)

    Returns:
        argparse.Namespace: A feldolgozott argumentumokat tartalmazó objektum.
    """

    parser = argparse.ArgumentParser(
        description="Dokumentumfeldolgozó pipeline PDF és DOCX fájlokhoz"
    )
    parser.add_argument(
        "-i",
        "--input",
        help="Bemeneti fájl elérési útja (PDF vagy DOCX formátumú)",
    )
    parser.add_argument(
        "-id",
        "--input-dir",
        help="Bemeneti mappa elérési útja, amely DOCX vagy PDF fájlokat tartalmaz",
    )
    parser.add_argument(
        "-rh",
        "--remove-headers",
        action="store_true",
        default=True,
        help="Fejlécek eltávolítása a dokumentumból a tisztítás során.",
    )
    parser.add_argument(
        "-rf",
        "--remove-footers",
        action="store_true",
        default=True,
        help="Láblécek eltávolítása a dokumentumból a tisztítás során.",
    )
    parser.add_argument(
        "-rt",
        "--remove-toc",
        action="store_true",
        default=True,
        help="Tartalomjegyzék eltávolítása a dokumentumból a tisztítás során.",
    )
    parser.add_argument(
        "-re",
        "--remove-empty",
        action="store_true",
        default=True,
        help="Üres oldalak és sorok eltávolítása a dokumentumból a tisztítás során.",
    )
    parser.add_argument(
        "-c",
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

    return args

def main() -> None:
    """
    A fő program belépési pontja. (Átemelve a Word projektből)

    Elindítja a pipeline-t a megadott argumentumok alapján.
    """
    try:
        args = parse_args()
        if args.clear:
            # logger.info("Input, output és log mappák tartalmának törlése")
            clear_directories()
            # logger.info("Mappák tartalma sikeresen törölve")
        if args.input:
            process_pipeline(
                args.input,
                args.steps,
                is_directory=False,
                # TODO: PDF fájlok fej- és lábléceit eltávolító paraméterek alkalmazása
                # remove_headers=args.remove_headers,
                # remove_footers=args.remove_footers,
                # remove_toc=args.remove_toc,
                # remove_empty=args.remove_empty,
                # abbreviation_strategy=args.abbreviation_strategy,
                # footnote_handling=args.footnote_handling,
                # process_images_with_ai=args.process_images_with_ai,
            )
            # logger.info("Pipeline sikeresen lefutott")
        elif args.input_dir:
            process_pipeline(
                args.input_dir,
                args.steps,
                is_directory=True,
                # TODO: PDF fájlok fej- és lábléceit eltávolító paraméterek alkalmazása
                # remove_headers=args.remove_headers,
                # remove_footers=args.remove_footers,
                # remove_toc=args.remove_toc,
                # remove_empty=args.remove_empty,
                # abbreviation_strategy=args.abbreviation_strategy,
                # footnote_handling=args.footnote_handling,
                # process_images_with_ai=args.process_images_with_ai,
            )
            # logger.info("Pipeline sikeresen lefutott")
    except Exception as exc:
        # logger.error("Hiba történt a pipeline futtatása során", exc_info=exc)
        raise

if __name__ == "__main__":
    main()