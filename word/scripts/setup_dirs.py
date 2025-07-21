"""
Könyvtárak és alapmappák létrehozása a projekt futtatásához.
Futtatásával minden szükséges mappa automatikusan létrejön.
"""

from services.file_service import ensure_directories

if __name__ == "__main__":
    ensure_directories()
    print("Szükséges könyvtárak létrehozva.")
