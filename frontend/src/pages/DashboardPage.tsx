import {
  Activity,
  Cpu,
  Gauge,
  MemoryStick,
  MessageSquare,
  Radio,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { LatencyAreaChart, SystemTrendsChart } from '../components/charts/Charts'
import { MetricCard, Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card'
import { PageFade, PageHeader } from '../components/ui/Page'
import { EmptyState, ErrorState, LoadingState } from '../components/ui/States'
import { Badge } from '../components/ui/Badge'
import { usePolling } from '../hooks/useApi'
import { useRealtime } from '../hooks/useRealtime'
import { api } from '../services/api'
import { formatMs, formatPercent, formatTimestamp } from '../lib/utils'
import type { MetricPoint, WsEvent } from '../types'

function eventLabel(ev: WsEvent): string {
  const type = ev.type
  switch (type) {
    case 'process_started':
      return `Process started${ev.process ? `: ${ev.process}` : ''}`
    case 'process_stopped':
      return `Process stopped${ev.process ? `: ${ev.process}` : ''}`
    case 'process_restarted':
      return `Process restarted${ev.process ? `: ${ev.process}` : ''}`
    case 'message_sent':
      return 'Message transmitted over IPC'
    case 'message_delivered':
      return 'Message delivered to receiver'
    case 'mechanism_changed':
      return `IPC mechanism changed${ev.data?.mechanism ? `: ${String(ev.data.mechanism)}` : ''}`
    case 'experiment_started':
      return `Experiment started${ev.data?.title ? `: ${String(ev.data.title)}` : ''}`
    case 'experiment_finished':
      return `Experiment finished${ev.data?.title ? `: ${String(ev.data.title)}` : ''}`
    case 'experiment_log':
      return String(ev.data?.line ?? 'Experiment log')
    case 'stats':
      return 'System stats snapshot'
    case 'connected':
      return 'Realtime channel connected'
    default:
      return type.replace(/_/g, ' ')
  }
}

export function DashboardPage() {
  const { events } = useRealtime()
  const { data, error, loading, refetch } = usePolling(() => api.getSystemStats(), 2000)
  const [series, setSeries] = useState<MetricPoint[]>([])

  useEffect(() => {
    if (!data?.system) return
    const avgLatency =
      data.ipc_metrics?.per_mechanism &&
      Object.values(data.ipc_metrics.per_mechanism)
        .map((m) => m.latency_ms.avg)
        .filter((v): v is number => v != null)
    const latency =
      avgLatency && avgLatency.length
        ? avgLatency.reduce((a, b) => a + b, 0) / avgLatency.length
        : 0

    const point: MetricPoint = {
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      cpu: data.system.cpu_percent ?? 0,
      memory: data.system.memory_percent ?? 0,
      latency,
      msgsPerSec: data.ipc_metrics?.msgs_per_sec ?? 0,
    }
    setSeries((prev) => [...prev, point].slice(-30))
  }, [data])

  const cards = useMemo(() => {
    const ipc = data?.ipc_metrics
    let latHint = '—'
    if (ipc?.per_mechanism) {
      const avgs = Object.values(ipc.per_mechanism)
        .map((m) => m.latency_ms.avg)
        .filter((v): v is number => v != null)
      if (avgs.length) latHint = formatMs(avgs.reduce((a, b) => a + b, 0) / avgs.length)
    }
    const active = Object.values(data?.processes ?? {}).filter(
      (p) => String(p.status ?? '').toLowerCase() === 'running' || (p.pid != null && p.pid > 0),
    ).length
    const processCount = Object.keys(data?.processes ?? {}).length

    return {
      cpu: formatPercent(data?.system.cpu_percent),
      ram: formatPercent(data?.system.memory_percent),
      latency: latHint,
      rate: ipc?.msgs_per_sec != null ? ipc.msgs_per_sec.toFixed(2) : '—',
      success: ipc?.total_success ?? 0,
      active: processCount ? String(active || processCount) : '—',
      processHint: processCount ? `${processCount} managed` : 'Awaiting registry',
    }
  }, [data])

  return (
    <PageFade>
      <PageHeader
        title="Control Center"
        description="Live OS metrics, IPC throughput, and realtime activity from the multiprocessing backend."
      />

      {error ? (
        <div className="mb-4">
          <ErrorState message={error} onRetry={() => void refetch()} />
        </div>
      ) : null}

      {loading && !data ? (
        <LoadingState label="Fetching system stats…" />
      ) : (
        <>
          <div className="mb-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
            <MetricCard
              label="CPU"
              value={cards.cpu}
              hint={`${data?.system.cpu_count ?? '—'} cores`}
              icon={<Cpu className="h-4 w-4" />}
            />
            <MetricCard
              label="RAM"
              value={cards.ram}
              hint="System memory"
              icon={<MemoryStick className="h-4 w-4" />}
            />
            <MetricCard
              label="Active Processes"
              value={cards.active}
              hint={cards.processHint}
              icon={<Radio className="h-4 w-4" />}
            />
            <MetricCard
              label="Messages"
              value={cards.rate}
              hint={`${cards.success} total success · msgs/s`}
              icon={<MessageSquare className="h-4 w-4" />}
            />
            <MetricCard
              label="IPC Latency"
              value={cards.latency}
              hint="Avg across mechanisms"
              icon={<Gauge className="h-4 w-4" />}
              className="sm:col-span-2 xl:col-span-1"
            />
          </div>

          <div className="grid gap-4 xl:grid-cols-3">
            <Card className="xl:col-span-2">
              <CardHeader>
                <CardTitle>System trends</CardTitle>
                <CardDescription>
                  CPU, RAM, and message rate sampled from /api/system/stats
                </CardDescription>
              </CardHeader>
              <CardContent>
                <SystemTrendsChart data={series} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Live System Activity</CardTitle>
                <CardDescription>Human-readable WebSocket events</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
                  {events.length === 0 ? (
                    <EmptyState
                      title="NO ACTIVE COMMUNICATION"
                      description="Events will appear here when processes, messages, or experiments emit realtime updates."
                      icon={Activity}
                    />
                  ) : (
                    events.slice(0, 40).map((ev, i) => (
                      <div
                        key={ev.id ?? `${ev.type}-${ev.timestamp}-${i}`}
                        className="rounded-lg border border-border/70 bg-muted/25 px-3 py-2.5 transition-colors hover:border-accent/25"
                      >
                        <div className="flex items-start gap-2.5">
                          <div className="mt-0.5 rounded-md bg-accent-muted p-1 text-accent">
                            <Activity className="h-3 w-3" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <p className="truncate text-sm font-medium capitalize leading-snug">
                                {eventLabel(ev)}
                              </p>
                              <span className="ml-auto shrink-0 text-[10px] tabular-nums text-muted-foreground">
                                {formatTimestamp(ev.timestamp)}
                              </span>
                            </div>
                            <div className="mt-1 flex flex-wrap items-center gap-1.5">
                              <Badge variant="secondary" className="text-[10px]">
                                {ev.type}
                              </Badge>
                              {ev.process ? (
                                <span className="text-[10px] text-muted-foreground">
                                  {ev.process}
                                </span>
                              ) : null}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            <Card className="xl:col-span-3">
              <CardHeader>
                <CardTitle>IPC Latency Over Time</CardTitle>
                <CardDescription>
                  Average measured latency from IPC metrics snapshots
                </CardDescription>
              </CardHeader>
              <CardContent>
                <LatencyAreaChart data={series} />
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </PageFade>
  )
}
