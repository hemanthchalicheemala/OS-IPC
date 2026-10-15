import { useState } from 'react'
import { ProcessTable } from '../components/processes/ProcessTable'
import { PageFade, PageHeader } from '../components/ui/Page'
import { ErrorState } from '../components/ui/States'
import { Button } from '../components/ui/Button'
import { usePolling } from '../hooks/useApi'
import { api } from '../services/api'
import { RefreshCw } from 'lucide-react'

export function ProcessesPage() {
  const { data, error, loading, refetch } = usePolling(() => api.getProcesses(), 2000)
  const [busy, setBusy] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  async function runAction(
    name: string,
    action: (n: string) => Promise<unknown>,
  ) {
    setBusy(name)
    setActionError(null)
    try {
      await action(name)
      await refetch()
    } catch (err) {
      setActionError(err instanceof Error ? err.message : 'Action failed')
    } finally {
      setBusy(null)
    }
  }

  const running = (data?.processes ?? []).filter(
    (p) => String(p.status).toLowerCase() === 'running',
  ).length

  return (
    <PageFade>
      <PageHeader
        title="Processes"
        description="Managed multiprocessing workers with live CPU, memory, and thread stats from the backend."
        actions={
          <div className="flex items-center gap-2">
            <span className="hidden text-xs text-muted-foreground sm:inline">
              {running} running · {(data?.processes ?? []).length} total
            </span>
            <Button variant="outline" size="sm" onClick={() => void refetch()}>
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh
            </Button>
          </div>
        }
      />

      {(error || actionError) && (
        <div className="mb-4">
          <ErrorState
            message={actionError ?? error ?? 'Error'}
            onRetry={() => void refetch()}
          />
        </div>
      )}

      <ProcessTable
        processes={data?.processes ?? []}
        loading={loading}
        busy={busy}
        onStart={(name) => void runAction(name, api.startProcess)}
        onStop={(name) => void runAction(name, api.stopProcess)}
        onRestart={(name) => void runAction(name, api.restartProcess)}
      />
    </PageFade>
  )
}
