"""
scanner.py — Scans a directory and returns file metadata.
"""

import os
import time


def scan_directory(path: str) -> list[dict]:
    """
    Recursively scan a directory.
    Returns a list of file info dicts.
    """
    if not os.path.isdir(path):
        raise ValueError(f"Path does not exist or is not a directory: {path}")

    files = []
    for root, _, filenames in os.walk(path):
        for name in filenames:
            full_path = os.path.join(root, name)
            try:
                stat = os.stat(full_path)
                files.append({
                    "name": name,
                    "path": full_path,
                    "extension": os.path.splitext(name)[1].lower(),
                    "size_bytes": stat.st_size,
                    "modified": time.strftime(
                        "%Y-%m-%d", time.localtime(stat.st_mtime)
                    ),
                })
            except (PermissionError, FileNotFoundError):
                continue  # Skip inaccessible files

    return files


def human_readable_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"