import { Play, RotateCcw, Square } from 'lucide-react'
import { useState } from 'react'
import { cn, formatBytes, formatDateTime, formatPercent } from '../../lib/utils'
import type { ProcessInfo } from '../../types'
import { Button } from '../ui/Button'
import { Drawer } from '../ui/Drawer'
import { ProcessStatusBadge, ProcessStatusDot } from '../ui/Status'
import { EmptyState, LoadingState } from '../ui/States'
import { Badge } from '../ui/Badge'

export function ProcessTable({
  processes,
  loading,
  busy,
  onStart,
  onStop,
  onRestart,
}: {
  processes: ProcessInfo[]
  loading?: boolean
  busy?: string | null
  onStart: (name: string) => void
  onStop: (name: string) => void
  onRestart: (name: string) => void
}) {
  const [selected, setSelected] = useState<ProcessInfo | null>(null)

  if (loading && !processes.length) return <LoadingState label="Loading processes…" />
  if (!processes.length) {
    return (
      <EmptyState
        title="NO MANAGED PROCESSES"
        description="The backend process registry returned empty. Start workers from the API or experiments."
      />
    )
  }

  const detail = selected
    ? processes.find((p) => p.name === selected.name) ?? selected
    : null

  return (
    <>
      <div className="overflow-x-auto rounded-xl border border-border bg-card">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="border-b border-border bg-muted/40 text-[11px] uppercase tracking-[0.12em] text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-medium">Process</th>
              <th className="px-4 py-3 font-medium">PID</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">CPU</th>
              <th className="px-4 py-3 font-medium">Memory</th>
              <th className="px-4 py-3 font-medium">Threads</th>
              <th className="px-4 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {processes.map((p) => {
              const stats = p.stats
              const isBusy = busy === p.name
              return (
                <tr
                  key={p.name}
                  onClick={() => setSelected(p)}
                  className={cn(
                    'cursor-pointer border-b border-border/70 last:border-0 transition-colors',
                    'hover:bg-accent-muted/40',
                    detail?.name === p.name && 'bg-accent-muted/30',
                  )}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2.5">
                      <ProcessStatusDot status={p.status} />
                      <span className="font-medium capitalize">{p.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs tabular-nums text-muted-foreground">
                    {p.pid ?? '—'}
                  </td>
                  <td className="px-4 py-3">
                    <ProcessStatusBadge status={p.status} />
                  </td>
                  <td className="px-4 py-3 tabular-nums">
                    {formatPercent(stats?.cpu_percent)}
                  </td>
                  <td className="px-4 py-3 tabular-nums">
                    {stats?.memory_rss_mb != null
                      ? `${stats.memory_rss_mb.toFixed(1)} MB`
                      : formatBytes(stats?.memory_rss)}
                  </td>
                  <td className="px-4 py-3 tabular-nums">{stats?.num_threads ?? '—'}</td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <div className="flex flex-wrap gap-1.5">
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={isBusy || p.status === 'running'}
                        onClick={() => onStart(p.name)}
                      >
                        <Play className="h-3.5 w-3.5" />
                        Start
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={isBusy || p.status !== 'running'}
                        onClick={() => onStop(p.name)}
                      >
                        <Square className="h-3.5 w-3.5" />
                        Stop
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        disabled={isBusy}
                        onClick={() => onRestart(p.name)}
                      >
                        <RotateCcw className="h-3.5 w-3.5" />
                        Restart
                      </Button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <Drawer
        open={!!detail}
        onClose={() => setSelected(null)}
        title={detail ? `Process · ${detail.name}` : 'Process'}
      >
        {detail ? <ProcessDetail process={detail} /> : null}
      </Drawer>
    </>
  )
}

function ProcessDetail({ process }: { process: ProcessInfo }) {
  const stats = process.stats
  const rows: { label: string; value: string }[] = [
    { label: 'Name', value: process.name },
    { label: 'PID', value: process.pid != null ? String(process.pid) : '—' },
    { label: 'Status', value: String(process.status) },
    { label: 'CPU', value: formatPercent(stats?.cpu_percent) },
    {
      label: 'Memory (RSS)',
      value:
        stats?.memory_rss_mb != null
          ? `${stats.memory_rss_mb.toFixed(2)} MB`
          : formatBytes(stats?.memory_rss),
    },
    { label: 'Threads', value: stats?.num_threads != null ? String(stats.num_threads) : '—' },
    {
      label: 'Create time',
      value: stats?.create_time != null ? formatDateTime(stats.create_time) : '—',
    },
  ]

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-2">
        <ProcessStatusBadge status={process.status} />
        <Badge variant="outline" className="font-mono text-[11px]">
          PID {process.pid ?? '—'}
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {rows.map((row) => (
          <div
            key={row.label}
            className="rounded-lg border border-border/80 bg-muted/25 px-3 py-2.5"
          >
            <p className="text-[10px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
              {row.label}
            </p>
            <p className="mt-1 truncate text-sm font-medium tabular-nums capitalize">
              {row.value}
            </p>
          </div>
        ))}
      </div>

      <p className="text-xs leading-relaxed text-muted-foreground">
        Stats are read live from the backend (psutil). Click a row anytime to refresh this detail
        view with the latest poll.
      </p>
    </div>
  )
}
