import re
from datetime import datetime, timezone


def normalize_token(value: str) -> str:
    cleaned = re.sub(r'[^A-Za-z0-9_-]+', '_', value.strip())
    return re.sub(r'_+', '_', cleaned).strip('_') or 'untitled'


def build_filename(project: str, category: str, title: str, version: int, extension: str, date_format: str) -> str:
    date_token = datetime.now(timezone.utc).strftime(date_format)
    return (
        f"{normalize_token(project)}_{normalize_token(category)}_"
        f"{date_token}_{normalize_token(title)}_v{version:02d}.{extension.lower()}"
    )
