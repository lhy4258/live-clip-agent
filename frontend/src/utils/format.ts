export type StatusTagType = 'success' | 'info' | 'warning' | 'danger'

export function tagType(status = ''): StatusTagType {
  if (['succeeded', 'approved', 'low', 'exported'].includes(status)) return 'success'
  if (['failed', 'rejected', 'high'].includes(status)) return 'danger'
  if (['running', 'pending', 'exporting', 'medium'].includes(status)) return 'warning'
  return 'info'
}

export function statusText(status = '') {
  const labels: Record<string, string> = {
    uploaded: '已上传',
    processing: '处理中',
    transcribed: '已转写',
    candidate: '待确认',
    clips_detected: '已生成候选',
    approved: '已确认',
    rejected: '已拒绝',
    needs_edit: '待确认',
    pending: '排队中',
    running: '运行中',
    succeeded: '已完成',
    failed: '失败',
  }
  return labels[status] || status || '-'
}

export function riskText(risk = '') {
  const labels: Record<string, string> = {
    unknown: '未知',
    low: '低',
    medium: '中',
    high: '高',
  }
  return labels[risk] || risk || '-'
}

export function exportStatusText(status = '') {
  const labels: Record<string, string> = {
    not_started: '未导出',
    pending: '排队中',
    exporting: '导出中',
    exported: '已导出',
    failed: '失败',
  }
  return labels[status] || status || '-'
}

export function sourceText(source = '') {
  const labels: Record<string, string> = {
    self_recorded: '自录直播',
    course_replay: '课程回放',
  }
  return labels[source] || source || '-'
}

export function licenseText(license = '') {
  const labels: Record<string, string> = {
    self_owned: '自有授权',
    authorized: '已授权',
  }
  return labels[license] || license || '-'
}

export function platformText(platform = '') {
  const labels: Record<string, string> = {
    douyin: '抖音',
    wechat_channels: '视频号',
    xiaohongshu: '小红书',
    bilibili: 'B站',
  }
  return labels[platform] || platform || '-'
}

export function publishPlanStatusText(status = '') {
  const labels: Record<string, string> = {
    draft: '草稿',
    ready: '待发布',
    published: '已发布',
  }
  return labels[status] || status || '-'
}

export function formatDateTime(value = '') {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

export function formatTime(seconds: number) {
  const minute = Math.floor(seconds / 60)
  const second = Math.floor(seconds % 60)
  return `${minute}:${second.toString().padStart(2, '0')}`
}
