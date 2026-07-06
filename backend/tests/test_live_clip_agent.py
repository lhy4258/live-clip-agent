import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.agents.live_clip_agent import LiveClipAgent
from app.chains.schemas import CandidateClipOutput, CandidateDetectionOutput
from app.core.database import Base
from app.models.tables import ChainRun, SourceVideo, TranscriptSegmentModel, VideoClip
from app.services.clip_detection import TranscriptSegment
from app.tools.candidate_detection_tool import CandidateDetectionTool


class FakeTranscriptionTool:
    def run(self, video_uri, duration_sec=None):
        return [
            TranscriptSegment(
                start_sec=0,
                end_sec=12,
                text=f"转写来自 {video_uri}",
                confidence=0.93,
            )
        ]


class FakeCandidateDetectionChain:
    def detect(self, segments):
        return CandidateDetectionOutput(
            candidates=[
                CandidateClipOutput(
                    start_sec=0,
                    end_sec=32,
                    reason="这一段完整回答了直播切片从哪里开始的问题。",
                    highlight="直播切片先找明确问题，再找精彩片段。",
                    confidence=0.86,
                    transcript_text="开场说明不要先剪热闹片段。接着讲要先定位用户真实问题。",
                )
            ]
        )


class LiveClipAgentTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, class_=Session)
        self.db = self.session_factory()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def add_video_with_transcript(self):
        video = SourceVideo(
            id="video-1",
            title="直播复盘",
            file_uri="data/files/live.mp4",
            source="self_recorded",
            license="self_owned",
            status="transcribed",
        )
        self.db.add(video)
        self.db.add_all(
            [
                TranscriptSegmentModel(
                    id="segment-1",
                    video_id=video.id,
                    start_sec=0,
                    end_sec=14,
                    text="开场说明不要先剪热闹片段。",
                    confidence=0.91,
                ),
                TranscriptSegmentModel(
                    id="segment-2",
                    video_id=video.id,
                    start_sec=14,
                    end_sec=32,
                    text="接着讲要先定位用户真实问题。",
                    confidence=0.92,
                ),
            ]
        )
        self.db.commit()
        return video

    def test_detect_clips_uses_candidate_detection_chain_tool(self):
        video = self.add_video_with_transcript()
        agent = LiveClipAgent(
            self.db,
            candidate_detection_tool=CandidateDetectionTool(chain=FakeCandidateDetectionChain()),
        )

        created = agent.detect_clips(video_id=video.id, trace_id="trace-1")

        self.assertEqual(created, 1)
        clip = self.db.scalars(select(VideoClip)).one()
        self.assertEqual(clip.start_sec, 0)
        self.assertEqual(clip.end_sec, 32)
        self.assertGreaterEqual(clip.score, 0.86)
        self.assertEqual(clip.status, "candidate")

        chain_names = [row.chain_name for row in self.db.scalars(select(ChainRun)).all()]
        self.assertIn("candidate_detection", chain_names)
        candidate_run = self.db.scalars(
            select(ChainRun).where(ChainRun.chain_name == "candidate_detection")
        ).one()
        self.assertEqual(candidate_run.output_json["candidates"][0]["highlight"], "直播切片先找明确问题，再找精彩片段。")

    def test_transcribe_video_uses_transcription_tool_and_saves_segments(self):
        video = SourceVideo(
            id="video-2",
            title="待转写直播",
            file_uri="data/files/live-2.mp4",
            source="self_recorded",
            license="self_owned",
            status="uploaded",
        )
        self.db.add(video)
        self.db.commit()
        agent = LiveClipAgent(self.db, transcription_tool=FakeTranscriptionTool())

        count = agent.transcribe_video(video.id)

        self.assertEqual(count, 1)
        refreshed = self.db.get(SourceVideo, video.id)
        self.assertEqual(refreshed.status, "transcribed")
        segment = self.db.scalars(
            select(TranscriptSegmentModel).where(TranscriptSegmentModel.video_id == video.id)
        ).one()
        self.assertEqual(segment.text, "转写来自 data/files/live-2.mp4")


if __name__ == "__main__":
    unittest.main()
