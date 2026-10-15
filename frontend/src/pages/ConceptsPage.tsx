import {
  BookOpen,
  Cpu,
  Layers,
  Lock,
  MemoryStick,
  Network,
  Share2,
  Shuffle,
  type LucideIcon,
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { PageFade, PageHeader } from '../components/ui/Page'
import { EmptyState, ErrorState, LoadingState } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { api } from '../services/api'
import { Badge } from '../components/ui/Badge'

const CONCEPT_ICONS: Record<string, LucideIcon> = {
  process: Cpu,
  thread: Shuffle,
  ipc: Network,
  pipe: Network,
  queue: Layers,
  shared_memory: Share2,
  shm: MemoryStick,
  sync: Lock,
  lock: Lock,
  semaphore: Lock,
  scheduling: Shuffle,
  memory: MemoryStick,
}

function conceptIcon(id: string, name: string): LucideIcon {
  const key = id.toLowerCase()
  if (CONCEPT_ICONS[key]) return CONCEPT_ICONS[key]
  for (const [k, Icon] of Object.entries(CONCEPT_ICONS)) {
    if (key.includes(k) || name.toLowerCase().includes(k)) return Icon
  }
  return BookOpen
}

export function ConceptsPage() {
  const { data, error, loading, refetch } = useApi(() => api.getConcepts())

  return (
    <PageFade>
      <PageHeader
        title="OS Concepts"
        description={
          data?.title ??
          'Operating system viva concepts mapped to this multiprocessing IPC project.'
        }
      />

      {error ? (
        <div className="mb-4">
          <ErrorState message={error} onRetry={() => void refetch()} />
        </div>
      ) : null}

      {loading && !data ? (
        <LoadingState label="Loading concepts…" />
      ) : (data?.concepts ?? []).length === 0 ? (
        <EmptyState
          title="NO CONCEPTS LOADED"
          description="The backend /api/concepts endpoint returned an empty list."
          icon={BookOpen}
        />
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {(data?.concepts ?? []).map((c) => {
            const Icon = conceptIcon(c.id, c.name)
            return (
              <Card key={c.id} className="group hover:border-accent/30">
                <CardHeader>
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-accent/25 bg-accent-muted text-accent transition-colors group-hover:border-accent/45">
                      <Icon className="h-4 w-4" />
                    </div>
                    <Badge variant="secondary">{c.id}</Badge>
                  </div>
                  <CardTitle>{c.name}</CardTitle>
                  <CardDescription className="leading-relaxed">{c.summary}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
                    In this project
                  </p>
                  <p className="mt-1.5 text-sm leading-relaxed text-foreground/90">
                    {c.in_project}
                  </p>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </PageFade>
  )
}
