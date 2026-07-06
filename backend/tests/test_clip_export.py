import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1 import clips
from app.core.database import Base, get_db
from app.jobs import pipeline
from app.models.tables import AgentTask, SourceVideo, VideoClip


class ClipExportApiTest(unittest.TestCase):
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

    def tearDown(self):
        self.client.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def add_clip(self, status="approved", export_status="not_started"):
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
                cover_text="先找问题",
                score=0.88,
                status=status,
                risk_level="low",
                export_status=export_status,
            )
            db.add(video)
            db.add(clip)
            db.commit()

    def test_export_rejects_clip_that_is_not_approved(self):
        self.add_clip(status="candidate")

        response = self.client.post(
            "/api/v1/video-ops/clips/clip-1/export",
            headers={"X-API-Key": "dev-live-stream-clip-agent"},
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("Only approved clips can be exported", response.text)

    def test_export_approved_clip_creates_task_and_marks_clip_pending(self):
        self.add_clip()

        with patch("app.api.v1.clips.enqueue_clip_export_task", return_value=True) as enqueue:
            response = self.client.post(
                "/api/v1/video-ops/clips/clip-1/export",
                headers={"X-API-Key": "dev-live-stream-clip-agent"},
            )

        self.assertEqual(response.status_code, 202)
        payload = response.json()
        self.assertEqual(payload["task_type"], "export_clip_video")
        self.assertEqual(payload["status"], "pending")
        self.assertEqual(payload["input_json"]["clip_id"], "clip-1")
        enqueue.assert_called_once_with(payload["id"], "clip-1")

        with self.session_factory() as db:
            refreshed = db.get(VideoClip, "clip-1")
            self.assertEqual(refreshed.export_status, "pending")
            self.assertIsNone(refreshed.export_error)

    def test_export_rejects_clip_that_is_already_pending_or_exporting(self):
        for export_status in ["pending", "exporting"]:
            with self.subTest(export_status=export_status):
                Base.metadata.drop_all(self.engine)
                Base.metadata.create_all(self.engine)
                self.add_clip(export_status=export_status)

                with patch("app.api.v1.clips.enqueue_clip_export_task") as enqueue:
                    response = self.client.post(
                        "/api/v1/video-ops/clips/clip-1/export",
                        headers={"X-API-Key": "dev-live-stream-clip-agent"},
                    )

                self.assertEqual(response.status_code, 409)
                self.assertIn("Clip export is already queued or running", response.text)
                enqueue.assert_not_called()

class ClipExportJobTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine, class_=Session)
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
                cover_text="先找问题",
                score=0.88,
                status="approved",
                risk_level="low",
                export_status="pending",
            )
            task = AgentTask(
                id="task-1",
                task_type="export_clip_video",
                status="pending",
                input_json={"clip_id": "clip-1"},
                output_json={},
                error_json={},
                trace_id="trace-1",
            )
            db.add(video)
            db.add(clip)
            db.add(task)
            db.commit()

    def tearDown(self):
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_export_clip_video_job_writes_export_result_to_clip_and_task(self):
        tool = unittest.mock.Mock()
        tool.run.return_value = "data/files/clips/clip-1.mp4"

        with (
            patch.object(pipeline, "SessionLocal", self.session_factory),
            patch.object(pipeline, "ExportClipVideoTool", return_value=tool),
        ):
            pipeline.export_clip_video_job("task-1", "clip-1")

        with self.session_factory() as db:
            clip = db.get(VideoClip, "clip-1")
            task = db.get(AgentTask, "task-1")

        tool.run.assert_called_once_with(
            source_file_uri="data/files/source.mp4",
            start_sec=10,
            end_sec=42,
            clip_id="clip-1",
        )
        self.assertEqual(clip.export_status, "exported")
        self.assertEqual(clip.clip_file_uri, "data/files/clips/clip-1.mp4")
        self.assertIsNone(clip.export_error)
        self.assertIsNotNone(clip.exported_at)
        self.assertEqual(task.status, "succeeded")
        self.assertEqual(task.output_json["clip_file_uri"], "data/files/clips/clip-1.mp4")

    def test_export_clip_video_job_records_failure_on_clip_and_task(self):
        tool = unittest.mock.Mock()
        tool.run.side_effect = RuntimeError("ffmpeg failed")

        with (
            patch.object(pipeline, "SessionLocal", self.session_factory),
            patch.object(pipeline, "ExportClipVideoTool", return_value=tool),
        ):
            with self.assertRaises(RuntimeError):
                pipeline.export_clip_video_job("task-1", "clip-1")

        with self.session_factory() as db:
            clip = db.get(VideoClip, "clip-1")
            task = db.scalars(select(AgentTask)).one()

        self.assertEqual(clip.export_status, "failed")
        self.assertEqual(clip.export_error, "ffmpeg failed")
        self.assertEqual(task.status, "failed")
        self.assertEqual(task.error_json["message"], "ffmpeg failed")
        self.assertEqual(task.error_json["stage"], "export_clip_video")


if __name__ == "__main__":
    unittest.main()
