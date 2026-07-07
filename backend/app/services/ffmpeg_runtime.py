from __future__ import annotations

import os
from pathlib import Path

from app.core.config import Settings, get_settings


def configure_ffmpeg_runtime(settings: Settings | None = None) -> None:
    """Make project-local ffmpeg binaries visible to ffmpeg-python."""
    settings = settings or get_settings()
    paths = [settings.ffmpeg_path, settings.ffprobe_path]
    bin_dirs = [str(Path(path).parent) for path in paths if path]
    if not bin_dirs:
        return

    current_path = os.environ.get("PATH", "")
    path_parts = [part for part in current_path.split(os.pathsep) if part]
    for bin_dir in bin_dirs:
        if bin_dir not in path_parts:
            path_parts.insert(0, bin_dir)
    os.environ["PATH"] = os.pathsep.join(path_parts)
