from __future__ import annotations

from app.chains.schemas import PublishCopyOutput, RiskReviewOutput
from app.services.risk_rules import inspect_publish_copy


class RiskReviewChain:
    def __init__(self, mock: bool = False) -> None:
        self.mock = mock

    def review(self, copy: PublishCopyOutput) -> RiskReviewOutput:
        if self.mock:
            return self._rule_review(copy)
        try:
            return self._langchain_review(copy)
        except Exception:
            return self._rule_review(copy)

    def _langchain_review(self, copy: PublishCopyOutput) -> RiskReviewOutput:
        from langchain.chat_models import init_chat_model

        model = init_chat_model(model="gpt-4.1-mini")
        structured_model = model.with_structured_output(RiskReviewOutput)
        return structured_model.invoke(
            [
                ("system", "你负责审核短视频运营文案风险，重点检查夸大承诺和敏感表达。"),
                ("user", f"{copy.title}\n{copy.description}\n{copy.tags}\n{copy.cover_text}"),
            ]
        )

    def _rule_review(self, copy: PublishCopyOutput) -> RiskReviewOutput:
        result = inspect_publish_copy(copy.title, copy.description, copy.tags, copy.cover_text)
        return RiskReviewOutput(risk_level=result.risk_level, reasons=result.reasons)
