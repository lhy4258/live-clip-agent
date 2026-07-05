import unittest

from app.services.risk_rules import inspect_publish_copy


class RiskReviewTest(unittest.TestCase):
    def test_flags_exaggerated_promises(self):
        result = inspect_publish_copy(
            title="100%让你的直播间爆单",
            description="这个方法保证马上翻倍。",
            tags=["直播切片"],
            cover_text="必爆单",
        )

        self.assertEqual(result.risk_level, "high")
        self.assertIn("夸大承诺", result.reasons)

    def test_accepts_practical_copy(self):
        result = inspect_publish_copy(
            title="三步找到直播高价值切片",
            description="用时间戳、痛点和案例筛选可复用片段。",
            tags=["直播切片", "内容运营"],
            cover_text="切片复盘方法",
        )

        self.assertEqual(result.risk_level, "low")
        self.assertEqual(result.reasons, [])


if __name__ == "__main__":
    unittest.main()
