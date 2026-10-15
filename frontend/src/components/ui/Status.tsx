import { cn } from '../../lib/utils'
import type { ConnectionState } from '../../hooks/useWebSocket'
import type { ProcessStatus } from '../../types'

export function ConnectionPill({ state }: { state: ConnectionState }) {
  const label =
    state === 'connected' ? 'Connected' : state === 'connecting' ? 'Connecting…' : 'Disconnected'
  const color =
    state === 'connected'
      ? 'bg-success'
      : state === 'connecting'
        ? 'bg-warning'
        : 'bg-danger'

  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-2.5 py-1 text-xs text-muted-foreground">
      <span className={cn('h-1.5 w-1.5 rounded-full', color)} />
      {label}
    </span>
  )
}

export function ProcessStatusDot({ status }: { status: ProcessStatus }) {
  const s = String(status).toLowerCase()
  const color =
    s === 'running'
      ? 'bg-success'
      : s === 'crashed' || s === 'error'
        ? 'bg-danger'
        : 'bg-zinc-500'

  return <span className={cn('inline-block h-2 w-2 rounded-full', color)} title={status} />
}

export function ProcessStatusBadge({ status }: { status: ProcessStatus }) {
  const s = String(status).toLowerCase()
  const styles =
    s === 'running'
      ? 'bg-success/15 text-success'
      : s === 'crashed' || s === 'error'
        ? 'bg-danger/15 text-danger'
        : 'bg-muted text-muted-foreground'

  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium', styles)}>
      <ProcessStatusDot status={status} />
      {status}
    </span>
  )
}
