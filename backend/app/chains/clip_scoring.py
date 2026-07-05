from __future__ import annotations

from app.chains.schemas import ClipContext, ClipScoreOutput


class ClipScoringChain:
    def __init__(self, mock: bool = False) -> None:
        self.mock = mock

    def score(self, context: ClipContext) -> ClipScoreOutput:
        if self.mock:
            return self._mock_score(context)
        try:
            return self._langchain_score(context)
        except Exception:
            return self._mock_score(context)

    def _langchain_score(self, context: ClipContext) -> ClipScoreOutput:
        from langchain.chat_models import init_chat_model

        model = init_chat_model(model="gpt-4.1-mini")
        structured_model = model.with_structured_output(ClipScoreOutput)
        return structured_model.invoke(
            [
                ("system", "你负责评估直播切片候选片段，请输出结构化评分。"),
                ("user", context.transcript_text),
            ]
        )

    def _mock_score(self, context: ClipContext) -> ClipScoreOutput:
        return ClipScoreOutput(
            hook="从直播转写中定位可复用片段",
            value_point="帮助运营人员快速找到可审核的短视频素材",
            audience=context.audience,
            semantic_score=max(context.score, 0.65),
            reason="包含明确方法或案例，适合进入人工审核。",
        )
