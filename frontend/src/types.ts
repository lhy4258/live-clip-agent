export interface SourceVideo {
  id: string
  title: string
  file_uri: string
  duration_sec: number | null
  source: string
  license: string
  status: string
  created_at: string
}

export interface AgentJob {
  id: string
  task_type: string
  status: 'pending' | 'running' | 'succeeded' | 'failed' | 'retrying'
  error: string | null
  trace_id: string
  input_json: Record<string, unknown>
  output_json: Record<string, unknown>
  error_json: Record<string, unknown>
}

export interface TranscriptSegment {
  id: string
  video_id: string
  start_sec: number
  end_sec: number
  text: string
  confidence: number
}

export interface VideoClip {
  id: string
  video_id: string
  start_sec: number
  end_sec: number
  title: string
  summary: string
  tags: string[]
  cover_text: string
  score: number
  status: string
  risk_level: string
}

export interface ChainRun {
  id: string
  clip_id: string | null
  chain_name: string
  prompt_version: string
  model: string
  input_json: Record<string, unknown>
  output_json: Record<string, unknown>
  latency_ms: number
  error: string | null
  trace_id: string
  created_at: string
}
