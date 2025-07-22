import os
import re
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
INPUT_DIR = os.path.join(BASE_DIR, "input")
BACKUP_DIR = os.path.join(INPUT_DIR, "backup")

# 1. Törli az output és logs mappákat
for folder in [OUTPUT_DIR, LOGS_DIR]:
    if os.path.exists(folder):
        shutil.rmtree(folder)
        print(f"Törölve: {folder}")
    else:
        print(f"Nem létezik: {folder}")

# 2. Törli az input mappa tartalmát (de magát a mappát nem)

for item in os.listdir(INPUT_DIR):
    item_path = os.path.join(INPUT_DIR, item)
    if item == "backup":
        continue
    if os.path.isdir(item_path):
        shutil.rmtree(item_path)
    else:
        os.remove(item_path)
print("Törölve az input mappa tartalma (backup kivételével)")

# 3. Backupból visszamásolás, _backup utótag eltávolítása
for fname in os.listdir(BACKUP_DIR):
    src = os.path.join(BACKUP_DIR, fname)
    # Eltávolítjuk az _backup utótagot a kiterjesztés előtt
    new_fname = re.sub(r"_backup(?=\.[^.]+$)", "", fname)
    dst = os.path.join(INPUT_DIR, new_fname)
    shutil.copy2(src, dst)
    print(f"Visszamásolva: {src} -> {dst}")

print("Workspace reset kész!")
