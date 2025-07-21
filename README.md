# Dokumentum Konvertáló Rendszer - Részletes Rendszerleírás

## Áttekintés

Ez a projekt egy dokumentumfeldolgozó pipeline, amely képes PDF és DOCX fájlokat több lépésben feldolgozni, konvertálni, gazdagítani, és különböző formátumokba exportálni. A rendszer támogatja a képek és táblázatok automatikus összefoglalását mesterséges intelligencia segítségével, valamint a dokumentumok szerkezetének és tartalmának tisztítását, strukturálását.

## Fő funkciók

- **Többlépcsős feldolgozás:** Előfeldolgozás, utófeldolgozás, konvertálás Markdown formátumba, JSON-ba, AI-alapú gazdagítás, végső szöveg export.
- **Képek és táblázatok összefoglalása:** OpenAI API használatával.
- **Automatikus könyvtár- és fájlkezelés:** Bemeneti, kimeneti, backup, log és egyéb mappák automatikus létrehozása, tisztítása.
- **Strukturált naplózás:** JSON formátumú naplók, érzékeny adatok szűrése.
- **Parancssori vezérlés:** Rugalmas pipeline futtatás argumentumokkal.

## Főbb könyvtárak és fájlok

### 1. `main.py`

A parancssori belépési pont. Feladata:

- Argumentumok feldolgozása (`--input`, `--input-dir`, `--steps`, `--clear`)
- Naplózás inicializálása
- Pipeline indítása egy fájlon vagy mappán
- Könyvtárak törlése igény szerint

### 2. `core/`

#### `pipeline.py`

A teljes feldolgozási folyamatot vezérli, lépésenként:

- Biztonsági mentés készítése
- Képek kinyerése DOCX-ből
- Előfeldolgozás (fejléc, lábléc, tartalomjegyzék, üres oldalak eltávolítása)
- Utófeldolgozás (rövidítések, lábjegyzetek)
- Markdown konverzió (Docling)
- Markdown → JSON (Unstructured)
- JSON gazdagítás (táblázat/kép összefoglaló)
- TXT export

#### `processing.py`

Az egyes feldolgozási lépések konkrét megvalósítása:

- DOCX elő- és utófeldolgozás
- Markdown generálás és tisztítás
- JSON konverzió és gazdagítás
- TXT export

### 3. `config/`

#### `settings.py`

- Minden fontos elérési út, könyvtár, támogatott kiterjesztés, API kulcsok.
- Dinamikus fájlútvonal-generálás minden bemeneti fájlhoz.

#### `logging_config.py`

- Strukturált naplózás, JSON kimenet, érzékeny adatok szűrése, napi rotáció.

#### `prompts.py`

- AI promptok, rendszerüzenetek (táblázat/kép összefoglaló).

### 4. `services/`

#### `file_service.py`

- Könyvtárak létrehozása, törlése, validáció
- JSON írás/olvasás, rövidítésszótár mentése

#### `api_client.py`

- OpenAI API és Vision API hívások (táblázat/kép összefoglaló)

### 5. `processing/`

#### `enrichment.py`

- Táblázat- és képelemzés, összefoglaló generálás AI segítségével

#### `preprocessor.py`, `postprocessor.py`

- DOCX dokumentumok szerkezeti tisztítása, rövidítések, lábjegyzetek kezelése

### 6. `utils/`

- Képek kinyerése DOCX-ből, Markdown utófeldolgozás, XML dump

### 7. `scripts/`

- `setup_dirs.py`: Szükséges könyvtárak automatikus létrehozása

### 8. `requirements.txt`

- Függőségek listája (AI, OCR, PDF, DOCX, Markdown, JSON, naplózás, stb.)

## Főbb mappák

- `input/` - Bemeneti fájlok (PDF, DOCX)
- `output/` - Kimeneti fájlok (txt, json, md, képek, postprocessing)
- `logs/` - Naplófájlok
- `config/` - Beállítások, naplózás, promptok
- `core/` - Pipeline logika
- `services/` - Segédfüggvények, API hívások
- `processing/` - Feldolgozási lépések
- `utils/` - Képek, markdown, xml segédfüggvények
- `scripts/` - Telepítő/segéd szkriptek

## Folyamatábra (lépések)

1. **Előfeldolgozás:** Fejléc, lábléc, tartalomjegyzék, üres oldalak eltávolítása (csak DOCX)
2. **Utófeldolgozás:** Rövidítések, lábjegyzetek kezelése (csak DOCX)
3. **Konverzió Markdown formátumba** (Docling)
4. **Markdown → JSON** (Unstructured)
5. **JSON gazdagítás:** Táblázat- és képösszefoglalók (OpenAI)
6. **TXT export:** Végső szöveg generálása

## Futtatás

```bash
python main.py --input input/valami.docx --steps 7
python main.py --input-dir input/ --steps 7
python main.py --clear
```

## Függőségek telepítése

```bash
pip install -r requirements.txt
```

## AI és API kulcsok

A `.env` fájlban kell megadni az OpenAI API kulcsot:

```plaintext
OPENAI_API_KEY=...
```

## Naplózás

- Minden lépés naplózva van JSON formátumban a `logs/` mappában.
- Érzékeny adatok automatikusan szűrve.
