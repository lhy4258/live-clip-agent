import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1 import clips
from app.core.database import Base, get_db
from app.models.tables import SourceVideo, VideoClip


class ClipSourceVideoApiTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, class_=Session)

        app = FastAPI()
        app.include_router(clips.router, prefix="/api/v1")

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
                title="7月直播回放：切片方法论",
                file_uri="data/files/source.mp4",
                source="self_recorded",
                license="self_owned",
            )
            clip = VideoClip(
                id="clip-1",
                video_id=video.id,
                start_sec=10,
                end_sec=42,
                title="直播切片方法",
                summary="讲解如何定位直播切片。",
                tags=["直播切片"],
                cover_text="先找痛点",
                score=0.88,
                status="candidate",
                is_editable=True,
                edit_suggestion="建议把标题写得更具体。",
                edit_reason="标题没有直接说明用户收益。",
                risk_level="low",
            )
            db.add_all([video, clip])
            db.commit()

    def tearDown(self):
        self.client.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_list_clips_includes_source_video_title(self):
        response = self.client.get(
            "/api/v1/video-ops/clips",
            headers={"X-API-Key": "dev-live-stream-clip-agent"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload[0]["source_video_title"], "7月直播回放：切片方法论")
        self.assertTrue(payload[0]["is_editable"])
        self.assertEqual(payload[0]["edit_suggestion"], "建议把标题写得更具体。")
        self.assertEqual(payload[0]["edit_reason"], "标题没有直接说明用户收益。")

    def test_get_clip_includes_source_video_title(self):
        response = self.client.get(
            "/api/v1/video-ops/clips/clip-1",
            headers={"X-API-Key": "dev-live-stream-clip-agent"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["source_video_title"], "7月直播回放：切片方法论")


if __name__ == "__main__":
    unittest.main()
