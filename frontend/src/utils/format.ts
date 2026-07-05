export type StatusTagType = 'success' | 'info' | 'warning' | 'danger'

export function tagType(status = ''): StatusTagType {
  if (['succeeded', 'approved', 'low'].includes(status)) return 'success'
  if (['failed', 'rejected', 'high'].includes(status)) return 'danger'
  if (['running', 'pending', 'medium'].includes(status)) return 'warning'
  return 'info'
}

export function formatTime(seconds: number) {
  const minute = Math.floor(seconds / 60)
  const second = Math.floor(seconds % 60)
  return `${minute}:${second.toString().padStart(2, '0')}`
}
