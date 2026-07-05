from __future__ import annotations

from app.chains.publish_copy import PublishCopyChain
from app.chains.schemas import ClipContext, PublishCopyOutput
from app.core.config import get_settings


class PublishCopyTool:
    def __init__(self, chain: PublishCopyChain | None = None) -> None:
        self.chain = chain if chain is not None else PublishCopyChain(mock=get_settings().llm_mock)

    def run(self, context: ClipContext) -> PublishCopyOutput:
        return self.chain.generate(context)
