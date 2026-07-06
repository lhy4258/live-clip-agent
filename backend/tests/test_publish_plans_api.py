import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1 import publish_plans
from app.core.database import Base, get_db
from app.models.tables import PublishPlan, SourceVideo, VideoClip


class PublishPlansApiTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, class_=Session)

        app = FastAPI()
        app.include_router(publish_plans.router, prefix="/api/v1")

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
                status="approved",
                risk_level="low",
            )
            plan = PublishPlan(
                id="plan-1",
                clip_id=clip.id,
                platform="douyin",
                title="直播切片第一步",
                description="先判断这一段解决了用户什么问题。",
                hashtags=["直播切片", "内容运营"],
                status="draft",
            )
            db.add(video)
            db.add(clip)
            db.add(plan)
            db.commit()

    def tearDown(self):
        self.client.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_lists_publish_plans(self):
        response = self.client.get(
            "/api/v1/video-ops/publish-plans",
            headers={"X-API-Key": "dev-live-stream-clip-agent"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["id"], "plan-1")
        self.assertEqual(payload[0]["clip_id"], "clip-1")
        self.assertEqual(payload[0]["title"], "直播切片第一步")
        self.assertEqual(payload[0]["hashtags"], ["直播切片", "内容运营"])
        self.assertIn("created_at", payload[0])


if __name__ == "__main__":
    unittest.main()
