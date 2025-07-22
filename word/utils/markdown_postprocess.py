"""
Markdown utófeldolgozó segédfüggvények a markdown kimenet tisztításához és normalizálásához további feldolgozás előtt (pl. Unstructured használata esetén).
Kezeli a táblázatokat, kódrészleteket, címsorokat, listákat és a felesleges üres sorokat.
"""

import re


def fix_markdown_tables(lines):
    """
    Gondoskodik arról, hogy a markdown táblázatok körül üres sorok legyenek, és a szintaxis helyes legyen.

    Args:
        lines (list[str]): A markdown fájl sorai.

    Returns:
        list[str]: A módosított sorok listája.
    """
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Detect table header (at least two | and ---)
        if "|" in line and re.match(r"^\s*\|?(.+\|)+\s*$", line):
            # Check if next line is a separator (---)
            if i + 1 < len(lines) and re.match(
                r"^\s*\|?\s*:?[-| ]+:?\s*\|?\s*$", lines[i + 1]
            ):
                # Ensure blank line before
                if len(new_lines) > 0 and new_lines[-1].strip() != "":
                    new_lines.append("\n")
                # Add table lines
                while i < len(lines) and (
                    "|" in lines[i] and not lines[i].strip().startswith("```")
                ):
                    new_lines.append(lines[i])
                    i += 1
                # Ensure blank line after
                if i < len(lines) and lines[i].strip() != "":
                    new_lines.append("\n")
                continue
        new_lines.append(line)
        i += 1
    return new_lines


def fix_markdown_headings(lines):
    """
    Gondoskodik arról, hogy a címsorokat üres sorok vegyék körül.

    Args:
        lines (list[str]): A markdown fájl sorai.

    Returns:
        list[str]: A módosított sorok listája.
    """
    new_lines = []
    for i, line in enumerate(lines):
        if re.match(r"^\s*#+ ", line):
            if len(new_lines) > 0 and new_lines[-1].strip() != "":
                new_lines.append("\n")
            new_lines.append(line)
            if i + 1 < len(lines) and lines[i + 1].strip() != "":
                new_lines.append("\n")
            continue
        new_lines.append(line)
    return new_lines


def fix_markdown_lists(lines):
    """
    Gondoskodik arról, hogy a listákat üres sorok vegyék körül, és a listák ne olvadjanak össze bekezdésekkel.

    Args:
        lines (list[str]): A markdown fájl sorai.

    Returns:
        list[str]: A módosított sorok listája.
    """
    new_lines = []
    for i, line in enumerate(lines):
        if re.match(r"^\s*([-*+] |\d+\.)", line):
            if len(new_lines) > 0 and new_lines[-1].strip() != "":
                new_lines.append("\n")
            new_lines.append(line)
            # If next line is not a list, ensure blank line after
            if (
                i + 1 < len(lines)
                and not re.match(r"^\s*([-*+] |\d+\.)", lines[i + 1])
                and lines[i + 1].strip() != ""
            ):
                new_lines.append("\n")
            continue
        new_lines.append(line)
    return new_lines


def normalize_markdown_whitespace(lines):
    """
    Eltávolítja a felesleges üres sorokat (legfeljebb 1 egymást követő üres sor marad).

    Args:
        lines (list[str]): A markdown fájl sorai.

    Returns:
        list[str]: A módosított sorok listája.
    """
    new_lines = []
    blank = False
    for line in lines:
        if line.strip() == "":
            if not blank:
                new_lines.append("\n")
                blank = True
        else:
            new_lines.append(line)
            blank = False
    return new_lines


def clean_markdown_file(md_path):
    """
    Egy markdown fájl tisztítása és normalizálása helyben, minden javító alkalmazásával.

    Args:
        md_path (str): A markdown fájl elérési útja.

    Returns:
        None
    """
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    lines = fix_markdown_tables(lines)
    lines = fix_markdown_headings(lines)
    lines = fix_markdown_lists(lines)
    lines = normalize_markdown_whitespace(lines)
    with open(md_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
