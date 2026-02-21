"""
organizer.py — Moves files into categorized subfolders inside the output directory.
"""

import os
import shutil
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger("smart_organizer")

MAX_WORKERS = 8  # Move up to 8 files simultaneously


def _move_single(f: dict, output_dir: str) -> dict:
    """Moves a single file. Called in parallel."""
    category = f.get("category", "Miscellaneous")
    new_name = f.get("new_name", f["name"])
    dest_folder = os.path.join(output_dir, category)
    dest_path = os.path.join(dest_folder, new_name)

    result = {
        "original": f["path"],
        "destination": dest_path,
        "category": category,
        "size_bytes": f["size_bytes"],
        "status": "pending",
    }

    try:
        os.makedirs(dest_folder, exist_ok=True)

        # Avoid overwriting: append counter if needed
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(dest_path)
            i = 1
            while os.path.exists(f"{base}_{i}{ext}"):
                i += 1
            dest_path = f"{base}_{i}{ext}"
            result["destination"] = dest_path

        shutil.move(f["path"], dest_path)
        result["status"] = "success"
        logger.info(f"Moved: {f['path']} → {dest_path}")

    except PermissionError:
        result["status"] = "error_permission"
        logger.warning(f"Permission denied: {f['path']}")
    except Exception as e:
        result["status"] = f"error: {e}"
        logger.error(f"Failed to move {f['path']}: {e}")

    return result


def organize_files(files: list[dict], output_dir: str, dry_run: bool = False) -> list[dict]:
    """
    Moves files into output_dir/Category/ using parallel threads for speed.
    Returns a list of result dicts with status.
    """
    if dry_run:
        return [
            {
                "original": f["path"],
                "destination": os.path.join(output_dir, f.get("category", "Miscellaneous"), f.get("new_name", f["name"])),
                "category": f.get("category", "Miscellaneous"),
                "size_bytes": f["size_bytes"],
                "status": "dry_run",
            }
            for f in files
        ]

    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_move_single, f, output_dir): f for f in files}
        for future in as_completed(futures):
            results.append(future.result())

    return results