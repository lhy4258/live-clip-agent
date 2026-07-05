from __future__ import annotations

from app.services.clip_detection import TranscriptSegment
from app.services.transcription import TranscriptionService


class TranscriptionTool:
    def __init__(self, service: TranscriptionService | None = None) -> None:
        self.service = service if service is not None else TranscriptionService(mock=True)

    def run(self, video_uri: str) -> list[TranscriptSegment]:
        return self.service.transcribe(video_uri)
