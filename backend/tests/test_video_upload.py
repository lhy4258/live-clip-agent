import unittest
import shutil
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1 import videos
from app.core.database import Base, get_db
from app.models.tables import SourceVideo


class VideoUploadTest(unittest.TestCase):
    def setUp(self):
        self.storage_dir = Path(__file__).resolve().parents[1] / "data" / "files" / f"test-upload-{uuid.uuid4()}"
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

    def tearDown(self):
        self.client.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        shutil.rmtree(self.storage_dir, ignore_errors=True)

    def test_upload_video_saves_file_and_creates_source_video(self):
        settings = SimpleNamespace(storage_dir=str(self.storage_dir))

        with patch("app.api.v1.videos.get_settings", return_value=settings, create=True):
            response = self.client.post(
                "/api/v1/video-ops/videos/upload",
                headers={"X-API-Key": "dev-live-stream-clip-agent"},
                data={
                    "title": "本地上传直播",
                    "source": "self_recorded",
                    "license": "self_owned",
                    "duration_sec": "125.5",
                },
                files={"file": ("live-demo.mp4", b"fake video bytes", "video/mp4")},
            )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["title"], "本地上传直播")
        self.assertEqual(payload["source"], "self_recorded")
        self.assertEqual(payload["license"], "self_owned")
        self.assertEqual(payload["duration_sec"], 125.5)
        self.assertTrue(payload["file_uri"].endswith(".mp4"))

        saved_path = Path(payload["file_uri"])
        self.assertTrue(saved_path.exists())
        self.assertEqual(saved_path.read_bytes(), b"fake video bytes")

        with self.session_factory() as db:
            videos_in_db = list(db.scalars(select(SourceVideo)).all())

        self.assertEqual(len(videos_in_db), 1)
        self.assertEqual(videos_in_db[0].file_uri, payload["file_uri"])

    def test_upload_video_requires_video_file(self):
        settings = SimpleNamespace(storage_dir=str(self.storage_dir))

        with patch("app.api.v1.videos.get_settings", return_value=settings, create=True):
            response = self.client.post(
                "/api/v1/video-ops/videos/upload",
                headers={"X-API-Key": "dev-live-stream-clip-agent"},
                data={
                    "title": "错误文件",
                    "source": "self_recorded",
                    "license": "self_owned",
                },
                files={"file": ("notes.txt", b"not video", "text/plain")},
            )

        self.assertEqual(response.status_code, 415)
        self.assertIn("Only video uploads are supported", response.text)


if __name__ == "__main__":
    unittest.main()
