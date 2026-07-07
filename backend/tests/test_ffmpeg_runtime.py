import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services.ffmpeg_runtime import configure_ffmpeg_runtime


class FfmpegRuntimeTest(unittest.TestCase):
    def test_configure_ffmpeg_runtime_adds_configured_bin_dirs_to_path(self):
        settings = SimpleNamespace(
            ffmpeg_path=r"C:\project\tools\ffmpeg\bin\ffmpeg.exe",
            ffprobe_path=r"C:\project\tools\ffmpeg\bin\ffprobe.exe",
        )

        with patch.dict(os.environ, {"PATH": r"C:\Windows\System32"}):
            configure_ffmpeg_runtime(settings)

            path_parts = os.environ["PATH"].split(os.pathsep)

        self.assertEqual(path_parts[0], r"C:\project\tools\ffmpeg\bin")
        self.assertIn(r"C:\Windows\System32", path_parts)


if __name__ == "__main__":
    unittest.main()
