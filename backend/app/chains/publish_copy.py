from __future__ import annotations

from app.chains.schemas import ClipContext, PublishCopyOutput


class PublishCopyChain:
    """LangChain-compatible wrapper with a deterministic mock fallback."""

    def __init__(self, mock: bool = False) -> None:
        self.mock = mock

    def generate(self, context: ClipContext) -> PublishCopyOutput:
        if self.mock:
            return self._mock_generate(context)

        try:
            return self._langchain_generate(context)
        except Exception:
            return self._mock_generate(context)

    def _langchain_generate(self, context: ClipContext) -> PublishCopyOutput:
        from langchain.chat_models import init_chat_model

        model = init_chat_model(model="gpt-4.1-mini")
        structured_model = model.with_structured_output(PublishCopyOutput)
        return structured_model.invoke(
            [
                (
                    "system",
                    "你是短视频直播切片运营专家。输出务实、可审核、不夸大承诺的中文运营文案。",
                ),
                (
                    "user",
                    f"受众：{context.audience}\n分数：{context.score}\n转写：{context.transcript_text}",
                ),
            ]
        )

    def _mock_generate(self, context: ClipContext) -> PublishCopyOutput:
        topic = "直播高价值切片"
        if "痛点" in context.transcript_text:
            topic = "从痛点找到直播切片"
        elif "案例" in context.transcript_text:
            topic = "用案例复盘直播切片"

        return PublishCopyOutput(
            title=f"三步拆解：{topic}",
            description="基于转写内容提炼收益点、适用人群和行动建议，方便运营人员二次审核。",
            tags=["直播切片", "内容运营", context.audience],
            cover_text="直播切片复盘",
        )
