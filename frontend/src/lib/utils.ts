import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatBytes(bytes: number | null | undefined): string {
  if (bytes == null || Number.isNaN(bytes)) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function formatMs(ms: number | null | undefined): string {
  if (ms == null || Number.isNaN(ms)) return '—'
  if (ms < 1) return `${(ms * 1000).toFixed(0)} µs`
  if (ms < 10) return `${ms.toFixed(2)} ms`
  return `${ms.toFixed(1)} ms`
}

export function formatPercent(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—'
  return `${value.toFixed(1)}%`
}

export function formatTimestamp(ts: number | string | null | undefined): string {
  if (ts == null) return '—'
  const date =
    typeof ts === 'number'
      ? new Date(ts > 1e12 ? ts : ts * 1000)
      : new Date(ts)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function formatDateTime(ts: number | string | null | undefined): string {
  if (ts == null) return '—'
  const date =
    typeof ts === 'number'
      ? new Date(ts > 1e12 ? ts : ts * 1000)
      : new Date(ts)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString()
}

export function capitalize(s: string): string {
  if (!s) return s
  return s.charAt(0).toUpperCase() + s.slice(1)
}
