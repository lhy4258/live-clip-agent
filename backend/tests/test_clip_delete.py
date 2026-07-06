import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1 import clips
from app.core.database import Base, get_db
from app.models.tables import ClipReview, PublishPlan, SourceVideo, VideoClip


class ClipDeleteApiTest(unittest.TestCase):
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
            )
            rejected_clip = VideoClip(
                id="clip-rejected",
                video_id=video.id,
                start_sec=10,
                end_sec=42,
                title="可删除切片",
                summary="已经拒绝的切片允许从审核区删除。",
                tags=["删除"],
                cover_text="",
                score=0.7,
                status="rejected",
                risk_level="low",
            )
            approved_clip = VideoClip(
                id="clip-approved",
                video_id=video.id,
                start_sec=50,
                end_sec=80,
                title="已确认切片",
                summary="已确认切片不允许误删。",
                tags=["确认"],
                cover_text="",
                score=0.9,
                status="approved",
                risk_level="low",
            )
            review = ClipReview(
                clip_id=rejected_clip.id,
                label="rejected",
                reason="不适合发布",
                reviewer="operator",
            )
            plan = PublishPlan(
                clip_id=rejected_clip.id,
                platform="douyin",
                title="旧发布计划",
                description="删除切片时同步清理。",
                hashtags=["删除"],
                status="draft",
            )
            db.add_all([video, rejected_clip, approved_clip, review, plan])
            db.commit()

    def tearDown(self):
        self.client.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_delete_rejected_clip_removes_related_review_and_publish_plan(self):
        response = self.client.delete(
            "/api/v1/video-ops/clips/clip-rejected",
            headers={"X-API-Key": "dev-live-stream-clip-agent"},
        )

        self.assertEqual(response.status_code, 204)
        with self.session_factory() as db:
            self.assertIsNone(db.get(VideoClip, "clip-rejected"))
            self.assertEqual(db.scalars(select(ClipReview).where(ClipReview.clip_id == "clip-rejected")).all(), [])
            self.assertEqual(db.scalars(select(PublishPlan).where(PublishPlan.clip_id == "clip-rejected")).all(), [])

    def test_delete_approved_clip_is_rejected(self):
        response = self.client.delete(
            "/api/v1/video-ops/clips/clip-approved",
            headers={"X-API-Key": "dev-live-stream-clip-agent"},
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("Approved clips cannot be deleted", response.text)
        with self.session_factory() as db:
            self.assertIsNotNone(db.get(VideoClip, "clip-approved"))


if __name__ == "__main__":
    unittest.main()
