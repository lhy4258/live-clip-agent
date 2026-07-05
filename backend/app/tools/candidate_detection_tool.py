from __future__ import annotations

from app.chains.candidate_detection import CandidateDetectionChain
from app.chains.schemas import CandidateDetectionOutput
from app.core.config import get_settings
from app.services.clip_detection import TranscriptSegment


class CandidateDetectionTool:
    def __init__(self, chain=None) -> None:
        self.chain = chain if chain is not None else CandidateDetectionChain(mock=get_settings().llm_mock)

    def run(self, segments: list[TranscriptSegment]) -> CandidateDetectionOutput:
        return self.chain.detect(segments)
