from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class Document:
    filename: str
    project: str
    category: str
    uploader_discord_id: str
    drive_file_id: str
    checksum_sha256: str
    tags: list[str] = field(default_factory=list)
    version: int = 1
    is_latest: bool = True
    id: str = field(default_factory=lambda: str(uuid4()))
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
