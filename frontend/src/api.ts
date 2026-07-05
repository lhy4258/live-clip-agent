import type { AgentJob, ChainRun, SourceVideo, TranscriptSegment, VideoClip } from './types'

const base = '/api/v1/video-ops'

function apiKey() {
  return localStorage.getItem('video_ops_api_key') || 'dev-live-stream-clip-agent'
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  headers.set('X-API-Key', apiKey())
  headers.set('X-Request-ID', crypto.randomUUID())
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
  if (options.body && !isFormData && !headers.has('content-type')) headers.set('content-type', 'application/json')

  const response = await fetch(`${base}${path}`, { ...options, headers })
  if (!response.ok) throw new Error(await response.text())
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export function listVideos() {
  return request<SourceVideo[]>('/videos')
}

export function createVideo(payload: {
  title: string
  file_uri: string
  source: string
  license: string
  duration_sec?: number | null
}) {
  return request<SourceVideo>('/videos', { method: 'POST', body: JSON.stringify(payload) })
}

export function uploadVideo(payload: {
  title: string
  source: string
  license: string
  duration_sec?: number | null
  file: File
}) {
  const form = new FormData()
  form.append('title', payload.title)
  form.append('source', payload.source)
  form.append('license', payload.license)
  if (payload.duration_sec !== null && payload.duration_sec !== undefined) {
    form.append('duration_sec', String(payload.duration_sec))
  }
  form.append('file', payload.file)
  return request<SourceVideo>('/videos/upload', { method: 'POST', body: form })
}

export function getVideo(videoId: string) {
  return request<SourceVideo>(`/videos/${videoId}`)
}

export function listTranscripts(videoId: string) {
  return request<TranscriptSegment[]>(`/videos/${videoId}/transcripts`)
}

export function startTranscribe(videoId: string) {
  return request<AgentJob>(`/videos/${videoId}/transcribe`, { method: 'POST' })
}

export function startDetectClips(videoId: string) {
  return request<AgentJob>(`/videos/${videoId}/detect-clips`, { method: 'POST' })
}

export function getJob(jobId: string) {
  return request<AgentJob>(`/jobs/${jobId}`)
}

export function retryJob(jobId: string) {
  return request<AgentJob>(`/jobs/${jobId}/retry`, { method: 'POST' })
}

export function deleteJob(jobId: string) {
  return request<void>(`/jobs/${jobId}`, { method: 'DELETE' })
}

export function listClips(statusFilter?: string) {
  const query = statusFilter ? `?status_filter=${encodeURIComponent(statusFilter)}` : ''
  return request<VideoClip[]>(`/clips${query}`)
}

export function getClip(clipId: string) {
  return request<VideoClip>(`/clips/${clipId}`)
}

export function reviewClip(clipId: string, payload: { label: string; reason: string; reviewer: string }) {
  return request<VideoClip>(`/clips/${clipId}/review`, { method: 'POST', body: JSON.stringify(payload) })
}

export function createPublishPlan(clipId: string, platform: string) {
  return request(`/clips/${clipId}/publish-plan`, { method: 'POST', body: JSON.stringify({ platform }) })
}

export function exportPublishPlansUrl(format: 'csv' | 'json') {
  return `${base}/publish-plans/export?format=${format}`
}

export function listChainRuns(traceId?: string) {
  const query = traceId ? `?trace_id=${encodeURIComponent(traceId)}` : ''
  return request<ChainRun[]>(`/chain-runs${query}`)
}
