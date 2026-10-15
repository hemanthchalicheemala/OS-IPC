import {
  Beaker,
  Brain,
  Clock,
  GitCompare,
  Lock,
  MessageSquare,
  Network,
  Play,
  Share2,
  Shuffle,
  type LucideIcon,
} from 'lucide-react'
import { formatMs } from '../../lib/utils'
import type { ExperimentInfo, ExperimentResult } from '../../types'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card'
import { EmptyState } from '../ui/States'

const EXPERIMENT_META: Record<
  string,
  { icon: LucideIcon; concept: string }
> = {
  pipe_basic: { icon: Network, concept: 'Anonymous pipes · unidirectional IPC' },
  queue_basic: { icon: MessageSquare, concept: 'Multiprocessing queues · message passing' },
  shared_memory: { icon: Share2, concept: 'Shared memory · concurrent access' },
  shm_sync: { icon: Lock, concept: 'Locks / semaphores · synchronization' },
  process_lifecycle: { icon: Shuffle, concept: 'Process create · join · terminate' },
  ipc_latency_comparison: { icon: GitCompare, concept: 'Benchmark · pipe vs queue vs SHM' },
  ml_spam: { icon: Brain, concept: 'TF-IDF + Logistic Regression' },
  timing: { icon: Clock, concept: 'Scheduling · elapsed timing' },
}

function resolveMeta(id: string) {
  if (EXPERIMENT_META[id]) return EXPERIMENT_META[id]
  const lower = id.toLowerCase()
  if (lower.includes('pipe')) return { icon: Network, concept: 'Pipe-based IPC' }
  if (lower.includes('queue')) return { icon: MessageSquare, concept: 'Queue-based IPC' }
  if (lower.includes('shm') || lower.includes('shared'))
    return { icon: Share2, concept: 'Shared memory' }
  if (lower.includes('sync') || lower.includes('lock'))
    return { icon: Lock, concept: 'Synchronization' }
  if (lower.includes('ml') || lower.includes('spam'))
    return { icon: Brain, concept: 'Machine learning' }
  if (lower.includes('compar') || lower.includes('latency'))
    return { icon: GitCompare, concept: 'Performance comparison' }
  if (lower.includes('process') || lower.includes('life'))
    return { icon: Shuffle, concept: 'Process lifecycle' }
  return { icon: Beaker, concept: 'OS viva experiment' }
}

export function ExperimentCard({
  experiment,
  running,
  onRun,
}: {
  experiment: ExperimentInfo
  running?: boolean
  onRun: (id: string) => void
}) {
  const meta = resolveMeta(experiment.id)
  const Icon = meta.icon

  return (
    <Card className="group flex h-full flex-col overflow-hidden hover:border-accent/30">
      <CardHeader className="flex-1">
        <div className="mb-3 flex items-start justify-between gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-accent/25 bg-accent-muted text-accent transition-colors group-hover:border-accent/45">
            <Icon className="h-[18px] w-[18px]" />
          </div>
          <Badge variant="outline" className="font-mono text-[10px]">
            {experiment.id}
          </Badge>
        </div>
        <CardTitle className="text-base">{experiment.title}</CardTitle>
        <CardDescription className="mt-1.5 leading-relaxed">
          {experiment.description}
        </CardDescription>
      </CardHeader>
      <CardContent className="mt-auto space-y-3">
        <p className="text-[11px] uppercase tracking-[0.1em] text-muted-foreground">
          OS concept · <span className="normal-case tracking-normal text-foreground/80">{meta.concept}</span>
        </p>
        <Button
          size="sm"
          className="w-full"
          disabled={running}
          onClick={() => onRun(experiment.id)}
        >
          <Play className="h-3.5 w-3.5" />
          {running ? 'Running…' : 'Run experiment'}
        </Button>
      </CardContent>
    </Card>
  )
}

export function ExperimentResultView({ result }: { result: ExperimentResult | null }) {
  if (!result) {
    return (
      <EmptyState
        title="NO RESULTS YET"
        description="Run an experiment to see live output, timing, and the viva explanation."
        icon={Beaker}
      />
    )
  }

  return (
    <div className="space-y-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant={result.success ? 'success' : 'danger'}>
          {result.success ? 'success' : 'failed'}
        </Badge>
        <span className="font-medium">{result.title}</span>
        {result.elapsed_ms != null ? (
          <span className="text-xs text-muted-foreground">{formatMs(result.elapsed_ms)}</span>
        ) : null}
      </div>
      {result.error ? <p className="text-danger">{result.error}</p> : null}
      {typeof result.result?.explanation === 'string' ? (
        <p className="rounded-lg border border-accent/20 bg-accent-muted/50 p-3 text-muted-foreground leading-relaxed">
          {result.result.explanation}
        </p>
      ) : null}
      <pre className="max-h-80 overflow-auto rounded-lg border border-border bg-background p-3 font-mono text-[11px] leading-relaxed">
        {JSON.stringify(result.result ?? result, null, 2)}
      </pre>
    </div>
  )
}
