from __future__ import annotations


def build_init_sql() -> str:
    return """
CREATE TABLE IF NOT EXISTS source_videos (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  file_uri TEXT NOT NULL,
  duration_sec DOUBLE PRECISION,
  source TEXT NOT NULL,
  license TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'uploaded',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_tasks (
  id TEXT PRIMARY KEY,
  task_type TEXT NOT NULL,
  status TEXT NOT NULL,
  input_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  output_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  error TEXT,
  error_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  trace_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE agent_tasks
  ADD COLUMN IF NOT EXISTS error_json JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS transcript_segments (
  id TEXT PRIMARY KEY,
  video_id TEXT NOT NULL REFERENCES source_videos(id) ON DELETE CASCADE,
  start_sec DOUBLE PRECISION NOT NULL,
  end_sec DOUBLE PRECISION NOT NULL,
  text TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS video_clips (
  id TEXT PRIMARY KEY,
  video_id TEXT NOT NULL REFERENCES source_videos(id) ON DELETE CASCADE,
  start_sec DOUBLE PRECISION NOT NULL,
  end_sec DOUBLE PRECISION NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  cover_text TEXT NOT NULL DEFAULT '',
  score DOUBLE PRECISION NOT NULL,
  status TEXT NOT NULL DEFAULT 'candidate',
  risk_level TEXT NOT NULL DEFAULT 'unknown',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS clip_reviews (
  id TEXT PRIMARY KEY,
  clip_id TEXT NOT NULL REFERENCES video_clips(id) ON DELETE CASCADE,
  label TEXT NOT NULL,
  reason TEXT NOT NULL DEFAULT '',
  reviewer TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS publish_plans (
  id TEXT PRIMARY KEY,
  clip_id TEXT NOT NULL REFERENCES video_clips(id) ON DELETE CASCADE,
  platform TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  hashtags JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL DEFAULT 'draft',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_call_logs (
  id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL,
  model TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  input_hash TEXT NOT NULL,
  latency_ms INTEGER NOT NULL DEFAULT 0,
  token_in INTEGER NOT NULL DEFAULT 0,
  token_out INTEGER NOT NULL DEFAULT 0,
  cost_estimate DOUBLE PRECISION NOT NULL DEFAULT 0,
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chain_runs (
  id TEXT PRIMARY KEY,
  clip_id TEXT,
  chain_name TEXT NOT NULL,
  prompt_version TEXT NOT NULL,
  model TEXT NOT NULL,
  input_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  output_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  latency_ms INTEGER NOT NULL DEFAULT 0,
  error TEXT,
  trace_id TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_transcript_segments_video_time
  ON transcript_segments(video_id, start_sec);

CREATE INDEX IF NOT EXISTS ix_video_clips_status_score
  ON video_clips(status, score);

CREATE INDEX IF NOT EXISTS ix_chain_runs_trace_id
  ON chain_runs(trace_id);
""".strip()


def split_sql_statements(sql: str) -> list[str]:
    return [statement.strip() for statement in sql.split(";") if statement.strip()]
