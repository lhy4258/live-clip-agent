from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


class VideoStorageService:
    def __init__(self, storage_dir: str) -> None:
        self.storage_dir = Path(storage_dir)

    def register_path(self, file_uri: str) -> str:
        return file_uri

    async def save_upload(self, upload: UploadFile) -> str:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(upload.filename or "video.mp4").suffix or ".mp4"
        target = self.storage_dir / f"{uuid4()}{suffix}"
        with target.open("wb") as output:
            shutil.copyfileobj(upload.file, output)
        return str(target)
