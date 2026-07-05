from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import ApiKey, DbSession
from app.models.tables import ChainRun
from app.schemas.video_ops import ChainRunRead

router = APIRouter(prefix="/video-ops/chain-runs", tags=["chain-runs"])


@router.get("", response_model=list[ChainRunRead])
def list_chain_runs(db: DbSession, _: ApiKey, trace_id: str | None = None) -> list[ChainRun]:
    query = select(ChainRun).order_by(ChainRun.created_at.desc())
    if trace_id:
        query = query.where(ChainRun.trace_id == trace_id)
    return list(db.scalars(query).all())
