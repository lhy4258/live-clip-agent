import sys
import shutil
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.services.transcription import TranscriptionService
from app.tools.transcription_tool import TranscriptionTool


class FakeFfmpegCommand:
    def __init__(self, source: str) -> None:
        self.source = source
        self.output_path = ""
        self.output_kwargs = {}

    def output(self, output_path: str, **kwargs):
        self.output_path = output_path
        self.output_kwargs = kwargs
        return self

    def overwrite_output(self):
        return self

    def run(self, quiet: bool):
        Path(self.output_path).write_bytes(b"mp3")


class TranscriptionServiceTest(unittest.TestCase):
    def setUp(self):
        self.temp_roots: list[Path] = []

    def tearDown(self):
        for temp_root in self.temp_roots:
            shutil.rmtree(temp_root, ignore_errors=True)
        test_asr_root = Path(__file__).resolve().parents[1] / "data" / "test-asr"
        try:
            test_asr_root.rmdir()
        except OSError:
            pass

    def settings(self, **overrides):
        values = {
            "asr_provider": "aliyun_qwen3_asr_flash",
            "asr_model": "qwen3-asr-flash",
            "asr_api_key": "test-key",
            "asr_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            "asr_max_duration_sec": 300,
            "asr_max_payload_bytes": 10 * 1024 * 1024,
            "asr_segment_duration_sec": 30,
            "asr_request_timeout_sec": 60,
            "ffmpeg_path": None,
            "ffprobe_path": None,
            "storage_dir": "data/files",
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_qwen3_asr_flash_posts_openai_compatible_payload_and_splits_text(self):
        calls = []

        def fake_post(url, headers, payload, timeout):
            calls.append((url, headers, payload, timeout))
            return {
                "choices": [
                    {
                        "message": {
                            "content": "第一段讲用户痛点。第二段讲解决方法。",
                        }
                    }
                ]
            }

        service = TranscriptionService(settings=self.settings(), http_post=fake_post)

        segments = service.transcribe("https://example.com/live.wav", duration_sec=60)

        self.assertGreaterEqual(len(segments), 1)
        self.assertEqual("".join(segment.text for segment in segments), "第一段讲用户痛点。第二段讲解决方法。")
        self.assertEqual(segments[0].start_sec, 0)
        self.assertLessEqual(segments[-1].end_sec, 60)

        url, headers, payload, timeout = calls[0]
        self.assertEqual(url, "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
        self.assertEqual(headers["Authorization"], "Bearer test-key")
        self.assertEqual(timeout, 60)
        self.assertEqual(payload["model"], "qwen3-asr-flash")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["asr_options"]["enable_itn"], False)
        audio = payload["messages"][0]["content"][0]["input_audio"]
        self.assertEqual(audio["data"], "https://example.com/live.wav")
        self.assertNotIn("format", audio)

    def test_local_video_is_extracted_with_ffmpeg_and_sent_as_base64_data_url(self):
        temp_root = Path(__file__).resolve().parents[1] / "data" / "test-asr" / str(uuid.uuid4())
        temp_root.mkdir(parents=True, exist_ok=True)
        self.temp_roots.append(temp_root)
        source = temp_root / "source.mp4"
        source.write_bytes(b"mp4")
        commands = []
        calls = []

        def fake_input(source_path: str):
            command = FakeFfmpegCommand(source_path)
            commands.append(command)
            return command

        def fake_post(url, headers, payload, timeout):
            calls.append(payload)
            return {"choices": [{"message": {"content": "本地视频已经完成转写。"}}]}

        fake_ffmpeg = SimpleNamespace(input=fake_input, probe=lambda _: {"format": {"duration": "42"}})
        service = TranscriptionService(
            settings=self.settings(storage_dir=str(temp_root)),
            http_post=fake_post,
        )

        with patch.dict(sys.modules, {"ffmpeg": fake_ffmpeg}):
            segments = service.transcribe(str(source))

        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0].source, str(source))
        self.assertEqual(commands[0].output_kwargs["vn"], None)
        self.assertEqual(commands[0].output_kwargs["acodec"], "libmp3lame")
        self.assertEqual(commands[0].output_kwargs["ac"], 1)
        self.assertEqual(commands[0].output_kwargs["audio_bitrate"], "32k")
        audio_data = calls[0]["messages"][0]["content"][0]["input_audio"]["data"]
        self.assertTrue(audio_data.startswith("data:audio/mpeg;base64,"))
        self.assertEqual(segments[0].text, "本地视频已经完成转写。")

    def test_qwen3_asr_flash_rejects_audio_over_five_minutes(self):
        service = TranscriptionService(settings=self.settings(), http_post=lambda *_: {})

        with self.assertRaisesRegex(ValueError, "5 分钟"):
            service.transcribe("https://example.com/too-long.wav", duration_sec=301)

    def test_mock_provider_keeps_local_demo_output(self):
        service = TranscriptionService(settings=self.settings(asr_provider="mock"))

        segments = service.transcribe("data/files/demo.mp4")

        self.assertGreaterEqual(len(segments), 1)
        self.assertIn("用户痛点", segments[0].text)

    def test_transcription_tool_uses_configured_service_by_default(self):
        with patch("app.tools.transcription_tool.TranscriptionService") as service_cls:
            service_cls.return_value.transcribe.return_value = []

            TranscriptionTool().run("data/files/demo.mp4", duration_sec=60)

        service_cls.assert_called_once_with()
        service_cls.return_value.transcribe.assert_called_once_with("data/files/demo.mp4", duration_sec=60)


if __name__ == "__main__":
    unittest.main()
