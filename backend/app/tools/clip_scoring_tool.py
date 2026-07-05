from __future__ import annotations

from app.chains.clip_scoring import ClipScoringChain
from app.chains.schemas import ClipContext, ClipScoreOutput
from app.core.config import get_settings


class ClipScoringTool:
    def __init__(self, chain: ClipScoringChain | None = None) -> None:
        self.chain = chain if chain is not None else ClipScoringChain(mock=get_settings().llm_mock)

    def run(self, context: ClipContext) -> ClipScoreOutput:
        return self.chain.score(context)
