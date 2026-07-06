import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1 import clips
from app.core.database import Base, get_db
from app.models.tables import SourceVideo, VideoClip


class ClipCoverTextTest(unittest.TestCase):
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
                title="直播回放",
                file_uri="data/files/source.mp4",
                source="self_recorded",
                license="self_owned",
                status="uploaded",
            )
            clip = VideoClip(
                id="clip-1",
                video_id=video.id,
                start_sec=10,
                end_sec=42,
                title="直播切片方法",
                summary="讲解如何定位直播切片。",
                tags=["直播切片"],
                cover_text="旧封面文案",
                score=0.88,
                status="approved",
                risk_level="low",
            )
            db.add(video)
            db.add(clip)
            db.commit()

    def tearDown(self):
        self.client.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_updates_clip_cover_text(self):
        response = self.client.patch(
            "/api/v1/video-ops/clips/clip-1/cover-text",
            headers={"X-API-Key": "dev-live-stream-clip-agent"},
            json={"cover_text": "直播切片先找痛点"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["cover_text"], "直播切片先找痛点")

        with self.session_factory() as db:
            clip = db.get(VideoClip, "clip-1")
            self.assertEqual(clip.cover_text, "直播切片先找痛点")


if __name__ == "__main__":
    unittest.main()
