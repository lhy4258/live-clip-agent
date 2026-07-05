import unittest

from app.services.clip_detection import ClipRuleEngine, TranscriptSegment


class ClipRuleEngineTest(unittest.TestCase):
    def test_generates_candidates_between_20_and_90_seconds(self):
        segments = [
            TranscriptSegment(start_sec=0, end_sec=8, text="今天我们先寒暄一下", confidence=0.92),
            TranscriptSegment(start_sec=8, end_sec=22, text="这个直播切片的核心收益点是三步提升转化", confidence=0.94),
            TranscriptSegment(start_sec=22, end_sec=45, text="第一步抓住痛点，第二步讲清价值，第三步给出行动建议", confidence=0.95),
            TranscriptSegment(start_sec=45, end_sec=62, text="这里有一个案例，复盘后团队马上知道标题怎么写", confidence=0.93),
        ]

        engine = ClipRuleEngine(keywords=["收益点", "痛点", "案例"])
        candidates = engine.generate_candidates(video_id="video-1", segments=segments)

        self.assertGreaterEqual(len(candidates), 1)
        best = candidates[0]
        self.assertEqual(best.video_id, "video-1")
        self.assertGreaterEqual(best.end_sec - best.start_sec, 20)
        self.assertLessEqual(best.end_sec - best.start_sec, 90)
        self.assertIn("收益点", best.transcript_text)
        self.assertGreater(best.score, 0.5)

    def test_filters_repeated_filler_candidates(self):
        segments = [
            TranscriptSegment(start_sec=0, end_sec=10, text="嗯嗯嗯 然后然后然后", confidence=0.8),
            TranscriptSegment(start_sec=10, end_sec=24, text="然后然后然后 嗯嗯嗯", confidence=0.8),
            TranscriptSegment(start_sec=24, end_sec=42, text="嗯嗯嗯 然后然后然后", confidence=0.8),
        ]

        engine = ClipRuleEngine(keywords=["收益点"])
        candidates = engine.generate_candidates(video_id="video-1", segments=segments)

        self.assertEqual(candidates, [])


if __name__ == "__main__":
    unittest.main()
