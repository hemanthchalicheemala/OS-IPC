import { GitCompare, Play, Terminal } from 'lucide-react'
import { useMemo, useState } from 'react'
import { MechanismCompareChart } from '../components/charts/Charts'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { PageFade, PageHeader } from '../components/ui/Page'
import { EmptyState, ErrorState } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { useRealtime } from '../hooks/useRealtime'
import { api } from '../services/api'
import { formatMs } from '../lib/utils'
import type { ExperimentResult } from '../types'

type ComparisonMap = Record<
  string,
  { samples_ms?: number[]; avg_ms?: number | null; min_ms?: number | null; max_ms?: number | null }
>

const MECHANISM_ORDER = ['pipe', 'queue', 'shared_memory']

export function ComparisonPage() {
  const metricsApi = useApi(() => api.getIpcMetrics())
  const { events } = useRealtime()
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ExperimentResult | null>(null)

  const liveLogs = events
    .filter(
      (e) =>
        e.type === 'experiment_log' &&
        (e.data?.experiment_id === 'ipc_latency_comparison' || e.data?.line),
    )
    .slice(0, 30)

  async function runComparison() {
    setRunning(true)
    setError(null)
    try {
      const res = await api.runExperiment('ipc_latency_comparison')
      setResult(res.result)
      void metricsApi.refetch()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Comparison failed')
    } finally {
      setRunning(false)
    }
  }

  const comparison = (result?.result?.comparison ?? null) as ComparisonMap | null

  const chartData = useMemo(() => {
    const raw = comparison
      ? Object.entries(comparison).map(([mechanism, stats]) => ({
          mechanism,
          avg_ms: stats.avg_ms ?? null,
          min_ms: stats.min_ms ?? null,
          max_ms: stats.max_ms ?? null,
        }))
      : Object.entries(metricsApi.data?.per_mechanism ?? {}).map(([mechanism, m]) => ({
          mechanism,
          avg_ms: m.latency_ms.avg,
          min_ms: m.latency_ms.min,
          max_ms: m.latency_ms.max,
        }))

    return [...raw].sort((a, b) => {
      const ai = MECHANISM_ORDER.indexOf(a.mechanism)
      const bi = MECHANISM_ORDER.indexOf(b.mechanism)
      return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi)
    })
  }, [comparison, metricsApi.data])

  return (
    <PageFade>
      <PageHeader
        title="IPC Benchmark"
        description="Compare Pipe, Queue, and Shared Memory latency from real experiment samples and live metrics."
        actions={
          <Button onClick={() => void runComparison()} disabled={running}>
            <Play className="h-4 w-4" />
            {running ? 'Benchmarking…' : 'Run latency comparison'}
          </Button>
        }
      />

      {error ? (
        <div className="mb-4">
          <ErrorState message={error} />
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitCompare className="h-4 w-4 text-accent" />
              Latency by mechanism
            </CardTitle>
            <CardDescription>
              {comparison
                ? 'Latest ipc_latency_comparison experiment results'
                : 'Live /api/ipc/metrics — run the benchmark for fresh samples'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <MechanismCompareChart data={chartData} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Terminal className="h-4 w-4 text-accent" />
              Live output
            </CardTitle>
            <CardDescription>experiment_log stream</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="max-h-72 space-y-1.5 overflow-y-auto font-mono text-[11px]">
              {liveLogs.length === 0 ? (
                <EmptyState
                  title="NO ACTIVE COMMUNICATION"
                  description="Start the latency comparison to stream benchmark logs."
                  icon={Terminal}
                />
              ) : (
                liveLogs.map((ev, i) => (
                  <div
                    key={ev.id ?? i}
                    className="rounded-lg border border-border/60 bg-muted/20 px-2.5 py-1.5 text-muted-foreground"
                  >
                    {String(ev.data?.line ?? ev.type)}
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {comparison ? (
        <Card className="mt-4">
          <CardHeader>
            <CardTitle>Sample summary</CardTitle>
            {typeof result?.result?.explanation === 'string' ? (
              <CardDescription>{result.result.explanation}</CardDescription>
            ) : null}
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-3">
              {Object.entries(comparison)
                .sort(([a], [b]) => {
                  const ai = MECHANISM_ORDER.indexOf(a)
                  const bi = MECHANISM_ORDER.indexOf(b)
                  return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi)
                })
                .map(([mech, stats]) => (
                  <div
                    key={mech}
                    className="rounded-xl border border-border bg-gradient-to-b from-card to-muted/20 p-4 transition-colors hover:border-accent/30"
                  >
                    <div className="mb-3 flex items-center gap-2">
                      <Badge>{mech}</Badge>
                    </div>
                    <dl className="space-y-1.5 text-sm">
                      <div className="flex justify-between gap-2">
                        <dt className="text-muted-foreground">Avg</dt>
                        <dd className="font-medium tabular-nums">{formatMs(stats.avg_ms)}</dd>
                      </div>
                      <div className="flex justify-between gap-2">
                        <dt className="text-muted-foreground">Min</dt>
                        <dd className="font-medium tabular-nums text-success">
                          {formatMs(stats.min_ms)}
                        </dd>
                      </div>
                      <div className="flex justify-between gap-2">
                        <dt className="text-muted-foreground">Max</dt>
                        <dd className="font-medium tabular-nums text-warning">
                          {formatMs(stats.max_ms)}
                        </dd>
                      </div>
                    </dl>
                    <p className="mt-3 border-t border-border/70 pt-2 text-[11px] leading-relaxed text-muted-foreground">
                      samples:{' '}
                      {(stats.samples_ms ?? []).map((s) => formatMs(s)).join(', ') || '—'}
                    </p>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      ) : null}
    </PageFade>
  )
}
