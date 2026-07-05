from __future__ import annotations

from dataclasses import dataclass


EXAGGERATED_TERMS = ("100%", "保证", "马上翻倍", "必爆", "躺赚", "稳赚", "零风险")
SENSITIVE_TERMS = ("违法", "刷单", "黑产")


@dataclass(frozen=True)
class RiskReviewResult:
    risk_level: str
    reasons: list[str]


def inspect_publish_copy(title: str, description: str, tags: list[str], cover_text: str) -> RiskReviewResult:
    joined = " ".join([title, description, cover_text, " ".join(tags)])
    reasons: list[str] = []

    if any(term in joined for term in EXAGGERATED_TERMS):
        reasons.append("夸大承诺")
    if any(term in joined for term in SENSITIVE_TERMS):
        reasons.append("敏感表达")

    if reasons:
        return RiskReviewResult(risk_level="high", reasons=reasons)
    return RiskReviewResult(risk_level="low", reasons=[])
