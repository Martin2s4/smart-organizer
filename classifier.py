
import re

# Extension → Category mapping
EXTENSION_MAP = {
    # Documents
    ".pdf": "Documents",
    ".doc": "Documents",
    ".docx": "Documents",
    ".txt": "Documents",
    ".odt": "Documents",
    ".rtf": "Documents",
    # Spreadsheets
    ".xls": "Spreadsheets",
    ".xlsx": "Spreadsheets",
    ".csv": "Spreadsheets",
    # Presentations
    ".ppt": "Presentations",
    ".pptx": "Presentations",
    # Images
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".gif": "Images",
    ".bmp": "Images",
    ".svg": "Images",
    ".webp": "Images",
    ".ico": "Images",
    # Videos
    ".mp4": "Videos",
    ".mkv": "Videos",
    ".avi": "Videos",
    ".mov": "Videos",
    ".wmv": "Videos",
    ".flv": "Videos",
    # Audio
    ".mp3": "Audio",
    ".wav": "Audio",
    ".flac": "Audio",
    ".aac": "Audio",
    ".ogg": "Audio",
    # Code
    ".py": "Code",
    ".js": "Code",
    ".ts": "Code",
    ".java": "Code",
    ".c": "Code",
    ".cpp": "Code",
    ".cs": "Code",
    ".go": "Code",
    ".rs": "Code",
    ".php": "Code",
    ".rb": "Code",
    ".html": "Code",
    ".css": "Code",
    ".sql": "Code",
    ".sh": "Code",
    ".bat": "Code",
    ".json": "Code",
    ".xml": "Code",
    ".yaml": "Code",
    ".yml": "Code",
    # Archives
    ".zip": "Archives",
    ".tar": "Archives",
    ".gz": "Archives",
    ".rar": "Archives",
    ".7z": "Archives",
    # Executables
    ".exe": "Executables",
    ".msi": "Executables",
    ".dmg": "Executables",
    ".deb": "Executables",
    ".apk": "Executables",
}

# Keyword patterns → Sub-category override (checked before extension map)
KEYWORD_PATTERNS = [
    (r"invoice|receipt|payment|billing|tax|finance|budget|salary|payslip", "Finance"),
    (r"lecture|notes|assignment|exam|quiz|lab|report|thesis|research|course", "Academic"),
    (r"resume|cv|cover.?letter|portfolio", "Career"),
    (r"screenshot|screen.?shot|capture|snip", "Screenshots"),
    (r"backup|bak|restore", "Backups"),
    (r"setup|install|installer", "Installers"),
]


def classify_file(file_info: dict) -> str:
  
    name_lower = file_info["name"].lower()
    ext = file_info["extension"]

    # 1. Check keyword patterns first (smarter classification)
    for pattern, category in KEYWORD_PATTERNS:
        if re.search(pattern, name_lower):
            return category

    # 2. Fall back to extension map
    return EXTENSION_MAP.get(ext, "Miscellaneous")


def classify_all(files: list[dict]) -> list[dict]:
    """Adds a 'category' key to each file dict."""
    for f in files:
        f["category"] = classify_file(f)
    return files