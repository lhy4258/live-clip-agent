from __future__ import annotations

from pathlib import Path

from app.services.ffmpeg_runtime import configure_ffmpeg_runtime


class ExportClipVideoTool:
    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)

    def run(self, *, source_file_uri: str, start_sec: float, end_sec: float, clip_id: str) -> str:
        if end_sec <= start_sec:
            raise ValueError("clip end_sec must be greater than start_sec")

        source_path = Path(source_file_uri)
        if not source_path.exists():
            raise FileNotFoundError(f"source video not found: {source_file_uri}")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"{clip_id}.mp4"
        temp_path = self.output_dir / f"{clip_id}.tmp.mp4"
        if temp_path.exists():
            temp_path.unlink()

        duration = end_sec - start_sec
        try:
            import ffmpeg

            configure_ffmpeg_runtime()
            (
                ffmpeg.input(str(source_path), ss=start_sec)
                .output(
                    str(temp_path),
                    t=duration,
                    vcodec="libx264",
                    acodec="aac",
                    movflags="+faststart",
                )
                .overwrite_output()
                .run(quiet=True)
            )
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

        temp_path.replace(output_path)
        return str(output_path)
