import { useMemo } from 'react'
import { IpcVisualizer } from '../components/ipc/IpcVisualizer'
import { Badge } from '../components/ui/Badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { PageFade, PageHeader } from '../components/ui/Page'
import { ErrorState, LoadingState } from '../components/ui/States'
import { usePolling } from '../hooks/useApi'
import { useRealtime } from '../hooks/useRealtime'
import { api } from '../services/api'
import { formatMs } from '../lib/utils'

export function IpcPage() {
  const { liveMessages } = useRealtime()
  const statusApi = usePolling(() => api.getIpcStatus(), 3000)
  const metricsApi = usePolling(() => api.getIpcMetrics(), 2000)
  const processesApi = usePolling(() => api.getProcesses(), 2500)

  const lastMessage = liveMessages[0] ?? null
  const mechanism = String(statusApi.data?.mechanism ?? 'pipe')
  const mechMetrics = metricsApi.data?.per_mechanism?.[mechanism]

  const rows = useMemo(() => {
    const per = metricsApi.data?.per_mechanism ?? {}
    return Object.entries(per).map(([name, m]) => ({ name, ...m }))
  }, [metricsApi.data])

  return (
    <PageFade>
      <PageHeader
        title="IPC Control"
        description="Visualize Alice → mechanism → Bob traffic with live process nodes and measured metrics."
        actions={<Badge>Active: {mechanism.replace('_', ' ')}</Badge>}
      />

      {statusApi.error ? (
        <div className="mb-4">
          <ErrorState message={statusApi.error} onRetry={() => void statusApi.refetch()} />
        </div>
      ) : null}

      {statusApi.loading && !statusApi.data ? (
        <LoadingState />
      ) : (
        <div className="space-y-4">
          <IpcVisualizer
            mechanism={mechanism}
            lastMessage={lastMessage}
            processes={processesApi.data?.processes ?? statusApi.data?.processes ?? []}
            metrics={{
              latency_ms: mechMetrics?.latency_ms.avg,
              success: mechMetrics?.count_success ?? metricsApi.data?.total_success,
              fail: mechMetrics?.count_fail ?? metricsApi.data?.total_fail,
            }}
          />

          <div className="grid gap-4 md:grid-cols-3">
            <Card className="bg-surface/30">
              <CardHeader>
                <CardTitle>Throughput</CardTitle>
                <CardDescription>Rolling msgs/sec</CardDescription>
              </CardHeader>
              <CardContent className="text-2xl font-semibold tabular-nums text-accent">
                {(metricsApi.data?.msgs_per_sec ?? 0).toFixed(2)}
              </CardContent>
            </Card>
            <Card className="bg-surface/30">
              <CardHeader>
                <CardTitle>Success</CardTitle>
                <CardDescription>Total successful sends</CardDescription>
              </CardHeader>
              <CardContent className="text-2xl font-semibold tabular-nums text-success">
                {metricsApi.data?.total_success ?? 0}
              </CardContent>
            </Card>
            <Card className="bg-surface/30">
              <CardHeader>
                <CardTitle>Failures</CardTitle>
                <CardDescription>Total failed sends</CardDescription>
              </CardHeader>
              <CardContent className="text-2xl font-semibold tabular-nums text-danger">
                {metricsApi.data?.total_fail ?? 0}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Per-mechanism metrics</CardTitle>
              <CardDescription>Measured from live IPC — not fabricated</CardDescription>
            </CardHeader>
            <CardContent>
              {rows.length === 0 ? (
                <p className="py-8 text-center text-sm text-muted-foreground">
                  Send messages to populate metrics
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[560px] text-left text-sm">
                    <thead className="border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
                      <tr>
                        <th className="px-2 py-2 font-medium">Mechanism</th>
                        <th className="px-2 py-2 font-medium">Success</th>
                        <th className="px-2 py-2 font-medium">Fail</th>
                        <th className="px-2 py-2 font-medium">Avg latency</th>
                        <th className="px-2 py-2 font-medium">Samples</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((r) => (
                        <tr key={r.name} className="border-b border-border/60 last:border-0">
                          <td className="px-2 py-2 font-medium capitalize">
                            {r.name.replace('_', ' ')}
                          </td>
                          <td className="px-2 py-2 tabular-nums text-success">{r.count_success}</td>
                          <td className="px-2 py-2 tabular-nums text-danger">{r.count_fail}</td>
                          <td className="px-2 py-2 tabular-nums">{formatMs(r.latency_ms.avg)}</td>
                          <td className="px-2 py-2 tabular-nums">{r.latency_ms.samples}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </PageFade>
  )
}
