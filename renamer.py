"""
renamer.py — Generates smart, enterprise-style file names.
Format: [Category]_[YYYY-MM-DD]_[NNN][.ext]
"""

import os


def generate_name(file_info: dict, counter: int) -> str:
    """
    Generates a new filename like: Image_2026-02-20_001.jpg
    """
    category = file_info.get("category", "File")
    date = file_info.get("modified", "0000-00-00")
    ext = file_info.get("extension", "")
    padded = str(counter).zfill(3)
    return f"{category}_{date}_{padded}{ext}"


def assign_new_names(files: list[dict]) -> list[dict]:
    """
    Assigns a 'new_name' field to every file dict.
    Counter is per-category so numbering stays clean.
    """
    counters: dict[str, int] = {}
    for f in files:
        cat = f.get("category", "Miscellaneous")
        counters[cat] = counters.get(cat, 0) + 1
        f["new_name"] = generate_name(f, counters[cat])
    return files


def preview_renames(files: list[dict]) -> list[tuple[str, str]]:
    """Returns (old_name, new_name) pairs for display."""
    return [(f["name"], f["new_name"]) for f in files]