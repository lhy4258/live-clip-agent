from __future__ import annotations

from app.chains.publish_copy import PublishCopyOutput
from app.chains.risk_review import RiskReviewChain
from app.chains.schemas import RiskReviewOutput
from app.core.config import get_settings


class RiskReviewTool:
    def __init__(self, chain: RiskReviewChain | None = None) -> None:
        self.chain = chain if chain is not None else RiskReviewChain(mock=get_settings().llm_mock)

    def run(self, copy: PublishCopyOutput) -> RiskReviewOutput:
        return self.chain.review(copy)
