import unittest

from app.chains.publish_copy import PublishCopyChain
from app.chains.schemas import ClipContext


class PublishCopyChainTest(unittest.TestCase):
    def test_mock_chain_returns_structured_publish_copy(self):
        chain = PublishCopyChain(mock=True)
        result = chain.generate(
            ClipContext(
                clip_id="clip-1",
                transcript_text="这段讲了如何从直播转写里找到痛点、收益点和案例。",
                audience="内容运营",
                score=0.82,
            )
        )

        self.assertTrue(result.title)
        self.assertTrue(result.description)
        self.assertGreaterEqual(len(result.tags), 1)
        self.assertTrue(result.cover_text)
        self.assertEqual(result.prompt_version, "publish-copy-v1")


if __name__ == "__main__":
    unittest.main()
