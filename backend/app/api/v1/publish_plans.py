from __future__ import annotations

from fastapi import APIRouter, Response
from sqlalchemy import select

from app.api.deps import ApiKey, DbSession
from app.models.tables import PublishPlan, VideoClip
from app.services.exporter import PublishPlanExportRow, export_publish_plans_csv, export_publish_plans_json

router = APIRouter(prefix="/video-ops/publish-plans", tags=["publish-plans"])


@router.get("/export")
def export_publish_plans(db: DbSession, _: ApiKey, format: str = "csv") -> Response:
    rows = []
    query = select(PublishPlan, VideoClip).join(VideoClip, PublishPlan.clip_id == VideoClip.id)
    for plan, clip in db.execute(query).all():
        rows.append(
            PublishPlanExportRow(
                clip_id=plan.clip_id,
                platform=plan.platform,
                title=plan.title,
                description=plan.description,
                hashtags=plan.hashtags,
                start_sec=clip.start_sec,
                end_sec=clip.end_sec,
                status=plan.status,
            )
        )
    if format == "json":
        return Response(export_publish_plans_json(rows), media_type="application/json")
    return Response(export_publish_plans_csv(rows), media_type="text/csv")
