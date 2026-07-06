from __future__ import annotations

import base64
import json
import mimetypes
import re
import urllib.request
from pathlib import Path
from uuid import uuid4

from app.core.config import Settings, get_settings
from app.services.clip_detection import TranscriptSegment


VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".flv", ".m4v"}
AUDIO_SUFFIXES = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".opus"}


class TranscriptionService:
    """ASR boundary. Mock output keeps local demos possible without model setup."""

    def __init__(
        self,
        mock: bool | None = None,
        settings: Settings | None = None,
        http_post=None,
    ) -> None:
        self.settings = settings or get_settings()
        self.provider = "mock" if mock is True else self.settings.asr_provider
        self.http_post = http_post or self._post_json

    def transcribe(self, video_uri: str, duration_sec: float | None = None) -> list[TranscriptSegment]:
        if self.provider == "mock":
            return self._mock_segments()
        if self.provider == "aliyun_qwen3_asr_flash":
            return self._transcribe_with_qwen3_asr_flash(video_uri, duration_sec)
        raise ValueError(f"Unsupported ASR provider: {self.provider}")

    def _transcribe_with_qwen3_asr_flash(
        self,
        video_uri: str,
        duration_sec: float | None,
    ) -> list[TranscriptSegment]:
        duration = duration_sec if duration_sec is not None else self._probe_duration(video_uri)
        if duration is not None and duration > self.settings.asr_max_duration_sec:
            raise ValueError("qwen3-asr-flash 只适合 5 分钟以内的音频，请先切分视频后再转写")
        if not self.settings.asr_api_key:
            raise ValueError("ASR_API_KEY is required when ASR_PROVIDER=aliyun_qwen3_asr_flash")

        audio_input = self._audio_input_data(video_uri)
        payload = {
            "model": self.settings.asr_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_input,
                            },
                        }
                    ],
                }
            ],
            "asr_options": {"enable_itn": False},
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.asr_api_key}",
            "Content-Type": "application/json",
        }
        result = self.http_post(
            self.settings.asr_base_url,
            headers,
            payload,
            self.settings.asr_request_timeout_sec,
        )
        text = self._extract_text(result)
        return self._segments_from_text(text, duration)

    def _audio_input_data(self, video_uri: str) -> str:
        if self._is_url(video_uri):
            return video_uri

        path = Path(video_uri)
        if not path.exists():
            raise FileNotFoundError(f"source video not found: {video_uri}")

        audio_path = path
        if path.suffix.lower() in VIDEO_SUFFIXES:
            audio_path = self._extract_audio(path)
        elif path.suffix.lower() not in AUDIO_SUFFIXES:
            raise ValueError(f"Unsupported ASR input file type: {path.suffix}")

        return self._data_url(audio_path)

    def _extract_audio(self, source_path: Path) -> Path:
        output_dir = Path(self.settings.storage_dir) / "asr-audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{source_path.stem}-{uuid4().hex}.mp3"

        import ffmpeg

        (
            ffmpeg.input(str(source_path))
            .output(str(output_path), vn=None, acodec="libmp3lame", ac=1, audio_bitrate="32k")
            .overwrite_output()
            .run(quiet=True)
        )
        return output_path

    def _data_url(self, audio_path: Path) -> str:
        payload = audio_path.read_bytes()
        mime_type = mimetypes.guess_type(audio_path.name)[0] or "audio/mpeg"
        encoded = base64.b64encode(payload).decode("ascii")
        data_url = f"data:{mime_type};base64,{encoded}"
        if len(data_url.encode("utf-8")) > self.settings.asr_max_payload_bytes:
            raise ValueError("qwen3-asr-flash 本地音频 Base64 后超过 10MB，请压缩或切分后再转写")
        return data_url

    def _probe_duration(self, video_uri: str) -> float | None:
        if self._is_url(video_uri):
            return None
        path = Path(video_uri)
        if not path.exists():
            return None
        try:
            import ffmpeg

            duration = ffmpeg.probe(str(path)).get("format", {}).get("duration")
            return float(duration) if duration is not None else None
        except Exception:
            return None

    def _extract_text(self, result: dict) -> str:
        choices = result.get("choices") if isinstance(result, dict) else None
        if isinstance(choices, list) and choices:
            message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
            content = message.get("content")
            if isinstance(content, str):
                return content.strip()
            if isinstance(content, list):
                texts = [item.get("text", "") for item in content if isinstance(item, dict)]
                return " ".join(text.strip() for text in texts if text.strip())
        output = result.get("output") if isinstance(result, dict) else None
        if isinstance(output, dict) and isinstance(output.get("text"), str):
            return output["text"].strip()
        raise ValueError("ASR response does not contain transcribed text")

    def _segments_from_text(self, text: str, duration_sec: float | None) -> list[TranscriptSegment]:
        cleaned = text.strip()
        if not cleaned:
            return []

        chunks = [chunk.strip() for chunk in re.split(r"(?<=[。！？!?])", cleaned) if chunk.strip()]
        if not chunks:
            chunks = [cleaned]

        total_duration = duration_sec or max(len(chunks) * self.settings.asr_segment_duration_sec, 1)
        total_chars = sum(len(chunk) for chunk in chunks) or 1
        cursor = 0.0
        segments: list[TranscriptSegment] = []
        for index, chunk in enumerate(chunks):
            if index == len(chunks) - 1:
                end_sec = float(total_duration)
            else:
                end_sec = cursor + total_duration * len(chunk) / total_chars
            segments.append(TranscriptSegment(round(cursor, 3), round(end_sec, 3), chunk, 0.9))
            cursor = end_sec
        return segments

    def _post_json(self, url: str, headers: dict, payload: dict, timeout: int) -> dict:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _is_url(self, value: str) -> bool:
        return value.startswith("http://") or value.startswith("https://")

    def _mock_segments(self) -> list[TranscriptSegment]:
        return [
            TranscriptSegment(0, 12, "今天这段直播我们先说明用户痛点。", 0.93),
            TranscriptSegment(12, 34, "核心收益点是用时间轴快速找到能复用的讲解片段。", 0.95),
            TranscriptSegment(34, 58, "第一步看停顿，第二步看案例，第三步看观众是否能马上行动。", 0.94),
            TranscriptSegment(58, 78, "这个方法适合内容运营复盘直播录制。", 0.92),
        ]
