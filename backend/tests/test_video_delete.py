import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine

from app.api.v1 import videos
from app.core.database import Base, get_db
from app.models.tables import ClipReview, PublishPlan, SourceVideo, TranscriptSegmentModel, VideoClip


class VideoDeleteApiTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, class_=Session)

        app = FastAPI()
        app.include_router(videos.router, prefix="/api/v1")

        def override_db():
            db = self.session_factory()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)

        with self.session_factory() as db:
            video = SourceVideo(
                id="video-1",
                title="直播回放",
                file_uri="data/files/source.mp4",
                source="self_recorded",
                license="self_owned",
            )
            segment = TranscriptSegmentModel(
                id="segment-1",
                video_id=video.id,
                start_sec=0,
                end_sec=12,
                text="直播切片要先找到用户痛点。",
                confidence=0.95,
            )
            clip = VideoClip(
                id="clip-1",
                video_id=video.id,
                start_sec=0,
                end_sec=12,
                title="直播切片痛点",
                summary="从痛点进入切片选题。",
                tags=["切片"],
                cover_text="痛点先行",
                score=0.8,
                status="candidate",
                risk_level="low",
            )
            review = ClipReview(
                clip_id=clip.id,
                label="candidate",
                reason="待审核",
                reviewer="operator",
            )
            plan = PublishPlan(
                clip_id=clip.id,
                platform="douyin",
                title="直播切片痛点",
                description="从痛点进入切片选题。",
                hashtags=["切片"],
                status="draft",
            )
            db.add_all([video, segment, clip, review, plan])
            db.commit()

    def tearDown(self):
        self.client.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_delete_video_removes_related_content(self):
        response = self.client.delete(
            "/api/v1/video-ops/videos/video-1",
            headers={"X-API-Key": "dev-live-stream-clip-agent"},
        )

        self.assertEqual(response.status_code, 204)
        with self.session_factory() as db:
            self.assertIsNone(db.get(SourceVideo, "video-1"))
            self.assertEqual(db.scalars(select(TranscriptSegmentModel)).all(), [])
            self.assertEqual(db.scalars(select(VideoClip)).all(), [])
            self.assertEqual(db.scalars(select(ClipReview)).all(), [])
            self.assertEqual(db.scalars(select(PublishPlan)).all(), [])

    def test_delete_missing_video_returns_404(self):
        response = self.client.delete(
            "/api/v1/video-ops/videos/missing",
            headers={"X-API-Key": "dev-live-stream-clip-agent"},
        )

        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
