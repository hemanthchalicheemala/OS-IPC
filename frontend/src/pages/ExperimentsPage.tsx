import { Terminal } from 'lucide-react'
import { useState } from 'react'
import { ExperimentCard, ExperimentResultView } from '../components/experiments/ExperimentCards'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { PageFade, PageHeader } from '../components/ui/Page'
import { EmptyState, ErrorState, LoadingState } from '../components/ui/States'
import { Badge } from '../components/ui/Badge'
import { useApi } from '../hooks/useApi'
import { useRealtime } from '../hooks/useRealtime'
import { api } from '../services/api'
import type { ExperimentResult } from '../types'

export function ExperimentsPage() {
  const listApi = useApi(() => api.getExperiments())
  const resultsApi = useApi(() => api.getExperimentResults())
  const { events } = useRealtime()
  const [runningId, setRunningId] = useState<string | null>(null)
  const [selected, setSelected] = useState<ExperimentResult | null>(null)
  const [runError, setRunError] = useState<string | null>(null)

  const logs = events
    .filter(
      (e) =>
        e.type === 'experiment_log' ||
        e.type === 'experiment_started' ||
        e.type === 'experiment_finished',
    )
    .slice(0, 50)

  async function onRun(id: string) {
    setRunningId(id)
    setRunError(null)
    try {
      const res = await api.runExperiment(id)
      setSelected(res.result)
      void resultsApi.refetch()
    } catch (err) {
      setRunError(err instanceof Error ? err.message : 'Run failed')
    } finally {
      setRunningId(null)
    }
  }

  return (
    <PageFade>
      <PageHeader
        title="Experiments"
        description="Run OS viva demos — pipes, queues, shared memory, sync primitives, lifecycle, and ML."
      />

      {(listApi.error || runError) && (
        <div className="mb-4">
          <ErrorState
            message={runError ?? listApi.error ?? 'Error'}
            onRetry={() => void listApi.refetch()}
          />
        </div>
      )}

      {listApi.loading && !listApi.data ? (
        <LoadingState label="Loading experiments…" />
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="space-y-3 lg:col-span-2">
            <div className="grid gap-3 sm:grid-cols-2">
              {(listApi.data?.experiments ?? []).map((exp) => (
                <ExperimentCard
                  key={exp.id}
                  experiment={exp}
                  running={runningId === exp.id}
                  onRun={onRun}
                />
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Live results</CardTitle>
                <CardDescription>Latest run output & explanation</CardDescription>
              </CardHeader>
              <CardContent>
                <ExperimentResultView result={selected} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Terminal className="h-4 w-4 text-accent" />
                  Live output
                </CardTitle>
                <CardDescription>WebSocket experiment events</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="max-h-56 space-y-1.5 overflow-y-auto font-mono text-[11px]">
                  {logs.length === 0 ? (
                    <EmptyState
                      title="NO ACTIVE COMMUNICATION"
                      description="Experiment logs stream here while a run is in progress."
                      icon={Terminal}
                    />
                  ) : (
                    logs.map((ev, i) => (
                      <div
                        key={ev.id ?? i}
                        className="rounded-lg border border-border/60 bg-muted/20 px-2.5 py-1.5 text-muted-foreground"
                      >
                        <span className="text-accent">{ev.type}</span>
                        {': '}
                        {String(ev.data?.line ?? ev.data?.title ?? '')}
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recent results</CardTitle>
                <CardDescription>Select a run to inspect</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {(resultsApi.data?.results ?? []).length === 0 ? (
                  <p className="py-4 text-center text-xs text-muted-foreground">
                    No completed runs yet
                  </p>
                ) : (
                  (resultsApi.data?.results ?? []).slice(0, 8).map((r) => (
                    <button
                      key={r.run_id ?? `${r.experiment_id}-${r.timestamp}`}
                      type="button"
                      onClick={() => setSelected(r)}
                      className="flex w-full items-center justify-between gap-2 rounded-lg border border-border px-3 py-2.5 text-left text-sm transition-colors hover:border-accent/30 hover:bg-muted/40"
                    >
                      <span className="truncate">{r.title}</span>
                      <Badge variant={r.success ? 'success' : 'danger'}>
                        {r.success ? 'ok' : 'fail'}
                      </Badge>
                    </button>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </PageFade>
  )
}
