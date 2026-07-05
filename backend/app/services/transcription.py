from __future__ import annotations

from app.services.clip_detection import TranscriptSegment


class TranscriptionService:
    """ASR boundary. Mock output keeps local demos possible without model setup."""

    def __init__(self, mock: bool = True) -> None:
        self.mock = mock

    def transcribe(self, video_uri: str) -> list[TranscriptSegment]:
        if self.mock:
            return [
                TranscriptSegment(0, 12, "今天这段直播我们先说明用户痛点。", 0.93),
                TranscriptSegment(12, 34, "核心收益点是用时间轴快速找到能复用的讲解片段。", 0.95),
                TranscriptSegment(34, 58, "第一步看停顿，第二步看案例，第三步看观众是否能马上行动。", 0.94),
                TranscriptSegment(58, 78, "这个方法适合内容运营复盘直播录制。", 0.92),
            ]
        raise NotImplementedError(f"Whisper-compatible ASR is not configured for {video_uri}")
