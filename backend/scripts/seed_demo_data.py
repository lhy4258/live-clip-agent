from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal, init_database
from app.models.tables import (
    AgentTask,
    AiCallLog,
    ChainRun,
    ClipReview,
    PublishPlan,
    SourceVideo,
    TranscriptSegmentModel,
    VideoClip,
)


DEMO_VIDEO_IDS = ["demo-video-1", "demo-video-2", "demo-video-3"]
DEMO_CLIP_IDS = ["demo-clip-1", "demo-clip-2", "demo-clip-3", "demo-clip-4", "demo-clip-5"]
DEMO_TASK_IDS = [
    "demo-task-transcribe-succeeded",
    "demo-task-detect-running",
    "demo-task-export-pending",
    "demo-task-export-failed",
]


def delete_existing_demo_data() -> None:
    db = SessionLocal()
    try:
        for model in [ClipReview, PublishPlan]:
            for row in db.scalars(select(model).where(model.clip_id.in_(DEMO_CLIP_IDS))).all():
                db.delete(row)

        for row in db.scalars(select(ChainRun).where(ChainRun.id.like("demo-%"))).all():
            db.delete(row)
        for row in db.scalars(select(AiCallLog).where(AiCallLog.id.like("demo-%"))).all():
            db.delete(row)
        for row in db.scalars(select(AgentTask).where(AgentTask.id.in_(DEMO_TASK_IDS))).all():
            db.delete(row)
        for row in db.scalars(select(TranscriptSegmentModel).where(TranscriptSegmentModel.video_id.in_(DEMO_VIDEO_IDS))).all():
            db.delete(row)
        for row in db.scalars(select(VideoClip).where(VideoClip.id.in_(DEMO_CLIP_IDS))).all():
            db.delete(row)
        for row in db.scalars(select(SourceVideo).where(SourceVideo.id.in_(DEMO_VIDEO_IDS))).all():
            db.delete(row)
        db.commit()
    finally:
        db.close()


def seed_demo_data() -> None:
    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        videos = [
            SourceVideo(
                id="demo-video-1",
                title="7月直播复盘：直播切片方法课",
                file_uri="data/files/demo-live-method.mp4",
                duration_sec=1260,
                source="self_recorded",
                license="self_owned",
                status="transcribed",
            ),
            SourceVideo(
                id="demo-video-2",
                title="AI 工具实操直播：选题到发布",
                file_uri="data/files/demo-ai-tools.mp4",
                duration_sec=1840,
                source="self_recorded",
                license="self_owned",
                status="processing",
            ),
            SourceVideo(
                id="demo-video-3",
                title="短视频运营答疑专场",
                file_uri="data/files/demo-qa-session.mp4",
                duration_sec=980,
                source="course_replay",
                license="authorized",
                status="uploaded",
            ),
        ]
        db.add_all(videos)

        transcripts = [
            TranscriptSegmentModel(
                id="demo-segment-1",
                video_id="demo-video-1",
                start_sec=8,
                end_sec=26,
                text="很多人做直播切片第一步就错了，不应该先找热闹片段，而是先找用户问题。",
                confidence=0.94,
            ),
            TranscriptSegmentModel(
                id="demo-segment-2",
                video_id="demo-video-1",
                start_sec=26,
                end_sec=52,
                text="如果这一段能把痛点、解决方案和行动建议讲完整，它就有成为短视频的基础。",
                confidence=0.92,
            ),
            TranscriptSegmentModel(
                id="demo-segment-3",
                video_id="demo-video-1",
                start_sec=52,
                end_sec=81,
                text="切片标题不要写得太虚，要让用户一眼知道看完能解决什么问题。",
                confidence=0.91,
            ),
            TranscriptSegmentModel(
                id="demo-segment-4",
                video_id="demo-video-2",
                start_sec=120,
                end_sec=146,
                text="AI 工具不是替你完成运营判断，而是帮你把初稿、分类和复盘速度提起来。",
                confidence=0.9,
            ),
            TranscriptSegmentModel(
                id="demo-segment-5",
                video_id="demo-video-2",
                start_sec=146,
                end_sec=176,
                text="每个候选片段都要回到用户场景：这个视频发出去，用户为什么愿意停留。",
                confidence=0.89,
            ),
        ]
        db.add_all(transcripts)

        clips = [
            VideoClip(
                id="demo-clip-1",
                video_id="demo-video-1",
                start_sec=8,
                end_sec=52,
                title="直播切片要先找痛点",
                summary="这一段讲了直播切片的常见误区，并给出从用户问题开始筛选片段的方法。",
                tags=["直播切片", "内容运营", "短视频"],
                cover_text="别先剪热闹，先找痛点",
                score=0.91,
                status="approved",
                risk_level="low",
                export_status="not_started",
            ),
            VideoClip(
                id="demo-clip-2",
                video_id="demo-video-1",
                start_sec=52,
                end_sec=81,
                title="切片标题别写虚",
                summary="这一段强调标题要直接对应用户收益，适合做成运营方法类短视频。",
                tags=["标题", "运营", "转化"],
                cover_text="标题要说清楚收益",
                score=0.84,
                status="candidate",
                risk_level="low",
                export_status="not_started",
            ),
            VideoClip(
                id="demo-clip-3",
                video_id="demo-video-2",
                start_sec=120,
                end_sec=176,
                title="AI 工具帮你提速，不替你判断",
                summary="这一段解释 AI 在运营流程里的作用边界，适合做工具方法论切片。",
                tags=["AI工具", "运营效率", "方法论"],
                cover_text="AI 提速，但判断还得你来",
                score=0.88,
                status="approved",
                risk_level="medium",
                export_status="exported",
                clip_file_uri="data/files/clips/demo-clip-3.mp4",
                exported_at=now,
            ),
            VideoClip(
                id="demo-clip-4",
                video_id="demo-video-2",
                start_sec=210,
                end_sec=248,
                title="从用户停留反推切片价值",
                summary="这一段讲候选切片要回到用户停留理由，内容完整但还需要人工确认。",
                tags=["用户停留", "切片价值"],
                cover_text="用户为什么愿意停留？",
                score=0.79,
                status="candidate",
                is_editable=True,
                edit_suggestion="建议把标题改得更具体，并补充片段里的行动建议。",
                edit_reason="片段有用户停留价值，但标题和摘要还没有直接说明用户能获得什么。",
                risk_level="low",
                export_status="not_started",
            ),
            VideoClip(
                id="demo-clip-5",
                video_id="demo-video-1",
                start_sec=90,
                end_sec=132,
                title="失败导出示例：源视频缺失",
                summary="这条用于展示导出失败后的错误状态和重新入队按钮。",
                tags=["失败示例", "导出任务"],
                cover_text="导出失败也要能追踪",
                score=0.72,
                status="approved",
                risk_level="low",
                export_status="failed",
                export_error="source video not found: data/files/demo-live-method.mp4",
            ),
        ]
        db.add_all(clips)
        db.flush()

        reviews = [
            ClipReview(
                id="demo-review-1",
                clip_id="demo-clip-1",
                label="approved",
                reason="结构完整，适合发布。",
                reviewer="operator",
            ),
            ClipReview(
                id="demo-review-2",
                clip_id="demo-clip-3",
                label="approved",
                reason="方法论清晰，适合做 AI 工具系列。",
                reviewer="operator",
            ),
        ]
        db.add_all(reviews)

        publish_plans = [
            PublishPlan(
                id="demo-plan-1",
                clip_id="demo-clip-1",
                platform="douyin",
                title="直播切片第一步：先找痛点",
                description="别急着剪热闹片段，先判断这一段解决了用户什么问题。",
                hashtags=["直播切片", "短视频运营", "内容运营"],
                status="draft",
            ),
            PublishPlan(
                id="demo-plan-2",
                clip_id="demo-clip-3",
                platform="wechat_channels",
                title="AI 工具能帮运营提速到哪一步？",
                description="AI 可以帮你提速，但运营判断仍然要回到用户场景。",
                hashtags=["AI工具", "运营效率", "视频号"],
                status="ready",
            ),
        ]
        db.add_all(publish_plans)

        tasks = [
            AgentTask(
                id="demo-task-transcribe-succeeded",
                task_type="transcribe_video",
                status="succeeded",
                input_json={"video_id": "demo-video-1"},
                output_json={"segments": 3},
                error_json={},
                trace_id="demo-trace-transcribe-1",
            ),
            AgentTask(
                id="demo-task-detect-running",
                task_type="detect_clips",
                status="running",
                input_json={"video_id": "demo-video-2"},
                output_json={},
                error_json={},
                trace_id="demo-trace-detect-2",
            ),
            AgentTask(
                id="demo-task-export-pending",
                task_type="export_clip_video",
                status="pending",
                input_json={"clip_id": "demo-clip-1", "video_id": "demo-video-1"},
                output_json={},
                error_json={},
                trace_id="demo-trace-export-1",
            ),
            AgentTask(
                id="demo-task-export-failed",
                task_type="export_clip_video",
                status="failed",
                input_json={"clip_id": "demo-clip-5", "video_id": "demo-video-1"},
                output_json={},
                error="source video not found: data/files/demo-live-method.mp4",
                error_json={
                    "code": "task_failed",
                    "message": "source video not found: data/files/demo-live-method.mp4",
                    "error_type": "FileNotFoundError",
                    "stage": "export_clip_video",
                    "details": {"clip_id": "demo-clip-5"},
                    "retryable": True,
                    "recorded_at": now.isoformat(),
                },
                trace_id="demo-trace-export-failed",
            ),
        ]
        db.add_all(tasks)

        chain_runs = [
            ChainRun(
                id="demo-chain-1",
                clip_id="demo-clip-1",
                chain_name="candidate_detection",
                prompt_version="candidate_detection_v1",
                model="mock-llm",
                input_json={"video_id": "demo-video-1", "segments": 3},
                output_json={
                    "candidates": [
                        {
                            "start_sec": 8,
                            "end_sec": 52,
                            "reason": "这一段完整讲了用户痛点和解决方法。",
                            "highlight": "直播切片不要先找热闹，要先找痛点。",
                            "confidence": 0.91,
                        }
                    ]
                },
                latency_ms=120,
                trace_id="demo-trace-detect-1",
            ),
            ChainRun(
                id="demo-chain-2",
                clip_id="demo-clip-1",
                chain_name="clip_scoring",
                prompt_version="clip_scoring_v1",
                model="mock-llm",
                input_json={"clip_id": "demo-clip-1"},
                output_json={"hook": 0.9, "value_point": 0.92, "semantic_score": 0.91},
                latency_ms=95,
                trace_id="demo-trace-detect-1",
            ),
            ChainRun(
                id="demo-chain-3",
                clip_id="demo-clip-3",
                chain_name="publish_copy",
                prompt_version="publish_copy_v1",
                model="mock-llm",
                input_json={"clip_id": "demo-clip-3"},
                output_json={
                    "title": "AI 工具帮你提速，不替你判断",
                    "tags": ["AI工具", "运营效率", "方法论"],
                    "cover_text": "AI 提速，但判断还得你来",
                },
                latency_ms=140,
                trace_id="demo-trace-detect-2",
            ),
            ChainRun(
                id="demo-chain-4",
                clip_id="demo-clip-3",
                chain_name="risk_review",
                prompt_version="risk_review_v1",
                model="mock-llm",
                input_json={"clip_id": "demo-clip-3"},
                output_json={"risk_level": "medium", "reason": "含工具效果表达，建议避免夸大。"},
                latency_ms=80,
                trace_id="demo-trace-detect-2",
            ),
        ]
        db.add_all(chain_runs)

        ai_logs = [
            AiCallLog(
                id="demo-ai-log-1",
                request_id="demo-trace-detect-1",
                model="mock-llm",
                prompt_version="candidate_detection_v1",
                input_hash="demo-hash-1",
                latency_ms=120,
                token_in=820,
                token_out=180,
                cost_estimate=0,
            ),
            AiCallLog(
                id="demo-ai-log-2",
                request_id="demo-trace-detect-2",
                model="mock-llm",
                prompt_version="publish_copy_v1",
                input_hash="demo-hash-2",
                latency_ms=140,
                token_in=620,
                token_out=160,
                cost_estimate=0,
            ),
        ]
        db.add_all(ai_logs)
        db.commit()
    finally:
        db.close()


def main() -> None:
    init_database()
    delete_existing_demo_data()
    seed_demo_data()
    print("Demo data seeded.")
    print("Videos: demo-video-1, demo-video-2, demo-video-3")
    print("Clips: demo-clip-1 ... demo-clip-5")
    print("Job ids for 任务监控:")
    for task_id in DEMO_TASK_IDS:
        print(f"- {task_id}")


if __name__ == "__main__":
    main()
