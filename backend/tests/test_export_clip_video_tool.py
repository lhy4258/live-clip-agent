import sys
import shutil
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.tools.export_clip_video_tool import ExportClipVideoTool


class FakeFfmpegCommand:
    def __init__(self, source: str, ss: float) -> None:
        self.source = source
        self.ss = ss
        self.output_path = ""
        self.output_kwargs = {}

    def output(self, output_path: str, **kwargs):
        self.output_path = output_path
        self.output_kwargs = kwargs
        return self

    def overwrite_output(self):
        return self

    def run(self, quiet: bool):
        Path(self.output_path).write_bytes(b"exported mp4")


class ExportClipVideoToolTest(unittest.TestCase):
    def setUp(self):
        self.temp_root = Path(__file__).resolve().parents[1] / "data" / "test-export-tool" / str(uuid.uuid4())
        self.temp_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_run_invokes_ffmpeg_and_returns_clip_file_uri(self):
        source_path = self.temp_root / "source.mp4"
        output_dir = self.temp_root / "clips"
        source_path.write_bytes(b"source mp4")
        command_holder = {}

        def fake_input(source: str, ss: float):
            command = FakeFfmpegCommand(source, ss)
            command_holder["command"] = command
            return command

        fake_ffmpeg = SimpleNamespace(input=fake_input)

        with patch.dict(sys.modules, {"ffmpeg": fake_ffmpeg}):
            clip_file_uri = ExportClipVideoTool(output_dir).run(
                source_file_uri=str(source_path),
                start_sec=10,
                end_sec=42,
                clip_id="clip-1",
            )

        command = command_holder["command"]
        self.assertEqual(command.source, str(source_path))
        self.assertEqual(command.ss, 10)
        self.assertEqual(command.output_kwargs["t"], 32)
        self.assertEqual(command.output_kwargs["vcodec"], "libx264")
        self.assertTrue(clip_file_uri.endswith("clip-1.mp4"))
        self.assertEqual(Path(clip_file_uri).read_bytes(), b"exported mp4")

    def test_run_rejects_invalid_time_range(self):
        source_path = self.temp_root / "source.mp4"
        source_path.write_bytes(b"source mp4")

        with self.assertRaises(ValueError):
            ExportClipVideoTool(self.temp_root / "clips").run(
                source_file_uri=str(source_path),
                start_sec=42,
                end_sec=10,
                clip_id="clip-1",
            )

    def test_run_rejects_missing_source_video(self):
        with self.assertRaises(FileNotFoundError):
            ExportClipVideoTool(self.temp_root / "clips").run(
                source_file_uri=str(self.temp_root / "missing.mp4"),
                start_sec=10,
                end_sec=42,
                clip_id="clip-1",
            )


if __name__ == "__main__":
    unittest.main()
