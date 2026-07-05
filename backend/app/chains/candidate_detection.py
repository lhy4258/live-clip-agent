from __future__ import annotations

from app.chains.schemas import CandidateClipOutput, CandidateDetectionOutput
from app.services.clip_detection import ClipRuleEngine, TranscriptSegment


class CandidateDetectionChain:
    """Find candidate clip ranges from timestamped transcript segments."""

    def __init__(self, mock: bool = False) -> None:
        self.mock = mock

    def detect(self, segments: list[TranscriptSegment]) -> CandidateDetectionOutput:
        if self.mock:
            return self._mock_detect(segments)
        try:
            return self._langchain_detect(segments)
        except Exception:
            return self._mock_detect(segments)

    def _langchain_detect(self, segments: list[TranscriptSegment]) -> CandidateDetectionOutput:
        from langchain.chat_models import init_chat_model

        model = init_chat_model(model="gpt-4.1-mini")
        structured_model = model.with_structured_output(CandidateDetectionOutput)
        payload = [
            {
                "start_sec": segment.start_sec,
                "end_sec": segment.end_sec,
                "text": segment.text,
                "confidence": segment.confidence,
            }
            for segment in segments
        ]
        return structured_model.invoke(
            [
                (
                    "system",
                    "你负责从直播转写中选择适合短视频切片的候选时间段。"
                    "只能使用用户给出的时间戳，不要编造不存在的时间。"
                    "优先选择包含明确问题、痛点、方法、案例或结论的片段。",
                ),
                ("user", str(payload)),
            ]
        )

    def _mock_detect(self, segments: list[TranscriptSegment]) -> CandidateDetectionOutput:
        engine = ClipRuleEngine(keywords=["收益点", "痛点", "案例", "方法", "步骤", "建议"])
        candidates = []
        for candidate in engine.generate_candidates(video_id="mock-video", segments=segments)[:5]:
            candidates.append(
                CandidateClipOutput(
                    start_sec=candidate.start_sec,
                    end_sec=candidate.end_sec,
                    reason="片段包含明确方法、案例或痛点，适合进入人工审核。",
                    highlight=self._highlight(candidate.transcript_text),
                    confidence=max(candidate.score, 0.65),
                    transcript_text=candidate.transcript_text,
                )
            )
        return CandidateDetectionOutput(candidates=candidates)

    def _highlight(self, text: str) -> str:
        stripped = text.replace("\n", " ").strip()
        return stripped[:48] if stripped else "直播切片候选片段"
