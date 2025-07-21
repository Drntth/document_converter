"""
Markdown postprocess utility functions for cleaning and normalizing markdown output before further processing (e.g. with Unstructured).
Handles tables, code blocks, headings, lists, and whitespace normalization.
"""

import re


def fix_markdown_tables(lines):
    """
    Ensures that markdown tables are surrounded by blank lines and have correct syntax.
    Args:
        lines (list of str): Lines of the markdown file.
    Returns:
        list of str: Modified lines.
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
    Ensures that headings are surrounded by blank lines.
    Args:
        lines (list of str): Lines of the markdown file.
    Returns:
        list of str: Modified lines.
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
    Ensures that lists are surrounded by blank lines and consecutive lists are not merged with paragraphs.
    Args:
        lines (list of str): Lines of the markdown file.
    Returns:
        list of str: Modified lines.
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
    Removes excessive blank lines (max 1 consecutive blank line).
    Args:
        lines (list of str): Lines of the markdown file.
    Returns:
        list of str: Modified lines.
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
    Cleans and normalizes a markdown file in-place using all fixers.
    Args:
        md_path (str): Path to the markdown file.
    """
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    lines = fix_markdown_tables(lines)
    lines = fix_markdown_headings(lines)
    lines = fix_markdown_lists(lines)
    lines = normalize_markdown_whitespace(lines)
    with open(md_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
