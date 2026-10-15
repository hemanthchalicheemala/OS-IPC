import { Loader2, Radio, Send } from 'lucide-react'
import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { MessageInspector } from '../components/chat/MessageInspector'
import { MessageList } from '../components/chat/MessageList'
import { IpcVisualizer } from '../components/ipc/IpcVisualizer'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { Select, Textarea } from '../components/ui/Input'
import { PageFade, PageHeader } from '../components/ui/Page'
import { ErrorState } from '../components/ui/States'
import { useApi, usePolling } from '../hooks/useApi'
import { useRealtime } from '../hooks/useRealtime'
import { api } from '../services/api'
import { capitalize, cn, formatPercent } from '../lib/utils'
import type { ChatMessage, IpcMechanism, ProcessInfo, WorkerName } from '../types'

const WORKERS: WorkerName[] = ['alice', 'bob', 'charlie']
const MECHANISMS: IpcMechanism[] = ['pipe', 'queue', 'shared_memory']

const MECHANISM_LABEL: Record<IpcMechanism, string> = {
  pipe: 'Pipe',
  queue: 'Message Queue',
  shared_memory: 'Shared Memory',
}

export function ChatPage() {
  const { liveMessages, upsertMessage, setLiveMessages, connected } = useRealtime()
  const statusApi = useApi(() => api.getIpcStatus())
  const messagesApi = useApi(() => api.getMessages())
  const processesApi = usePolling(() => api.getProcesses(), 2500)
  const metricsApi = usePolling(() => api.getIpcMetrics(), 2500)

  const [sender, setSender] = useState<WorkerName>('alice')
  const [receiver, setReceiver] = useState<WorkerName>('bob')
  const [mechanism, setMechanism] = useState<IpcMechanism>('pipe')
  const [content, setContent] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<ChatMessage | null>(null)
  const [animTrigger, setAnimTrigger] = useState<ChatMessage | null>(null)

  useEffect(() => {
    const mech = statusApi.data?.mechanism
    if (mech === 'pipe' || mech === 'queue' || mech === 'shared_memory') {
      setMechanism(mech)
    }
  }, [statusApi.data?.mechanism])

  useEffect(() => {
    if (!messagesApi.data) return
    const merged = [...(messagesApi.data.messages ?? [])]
    setLiveMessages((prev) => {
      const map = new Map<string, ChatMessage>()
      for (const m of [...merged, ...prev]) map.set(m.id, { ...map.get(m.id), ...m })
      return Array.from(map.values()).sort((a, b) => {
        const ta = typeof a.timestamp === 'number' ? a.timestamp : 0
        const tb = typeof b.timestamp === 'number' ? b.timestamp : 0
        return tb - ta
      })
    })
  }, [messagesApi.data, setLiveMessages])

  const receivers = useMemo(() => WORKERS.filter((w) => w !== sender), [sender])

  useEffect(() => {
    if (receiver === sender) setReceiver(receivers[0] ?? 'bob')
  }, [sender, receiver, receivers])

  const workerProcesses = useMemo(() => {
    const list = processesApi.data?.processes ?? []
    return WORKERS.map((name) => list.find((p) => p.name.toLowerCase() === name)).filter(
      Boolean,
    ) as ProcessInfo[]
  }, [processesApi.data])

  const allProcesses = processesApi.data?.processes ?? []
  const mechMetrics = metricsApi.data?.per_mechanism?.[mechanism]

  async function onMechanismChange(next: IpcMechanism) {
    setMechanism(next)
    try {
      await api.setMechanism(next)
      void statusApi.refetch()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set mechanism')
    }
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!content.trim()) return
    setSending(true)
    setError(null)
    try {
      const res = await api.sendMessage({
        sender,
        receiver,
        content: content.trim(),
        mechanism,
      })
      upsertMessage(res.message)
      setAnimTrigger(res.message)
      setContent('')
      void messagesApi.refetch()
      void metricsApi.refetch()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Send failed')
    } finally {
      setSending(false)
    }
  }

  return (
    <PageFade>
      <PageHeader
        title="IPC Chat"
        description="Real process communication over Pipe, Message Queue, or Shared Memory."
        actions={
          <div className="flex items-center gap-2">
            <Badge variant={connected ? 'success' : 'danger'}>
              <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-current" />
              {connected ? 'SYSTEM ONLINE' : 'OFFLINE'}
            </Badge>
            <Badge variant="outline">{MECHANISM_LABEL[mechanism]}</Badge>
          </div>
        }
      />

      {error ? (
        <div className="mb-4">
          <ErrorState message={error} />
        </div>
      ) : null}

      <div className="mb-4 grid gap-4 xl:grid-cols-[220px_1fr]">
        <ProcessRail processes={workerProcesses} selected={[sender, receiver]} />

        <div className="grid min-w-0 gap-4 lg:grid-cols-[340px_1fr]">
          <Card className="border-border/80 bg-card/80">
            <CardHeader className="border-b border-border/50 bg-surface/30">
              <CardTitle>Compose Message</CardTitle>
              <CardDescription>Delivered by managed OS processes</CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              <form className="space-y-4" onSubmit={onSubmit}>
                <div className="grid grid-cols-2 gap-3">
                  <label className="space-y-1.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                    Sender
                    <Select
                      value={sender}
                      onChange={(e) => setSender(e.target.value as WorkerName)}
                      className="capitalize"
                    >
                      {WORKERS.map((w) => (
                        <option key={w} value={w}>
                          {capitalize(w)}
                        </option>
                      ))}
                    </Select>
                  </label>
                  <label className="space-y-1.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                    Receiver
                    <Select
                      value={receiver}
                      onChange={(e) => setReceiver(e.target.value as WorkerName)}
                      className="capitalize"
                    >
                      {receivers.map((w) => (
                        <option key={w} value={w}>
                          {capitalize(w)}
                        </option>
                      ))}
                    </Select>
                  </label>
                </div>

                <div className="space-y-2">
                  <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                    IPC Mechanism
                  </p>
                  <div className="grid grid-cols-1 gap-2">
                    {MECHANISMS.map((m) => (
                      <button
                        key={m}
                        type="button"
                        onClick={() => void onMechanismChange(m)}
                        className={cn(
                          'flex items-center justify-between rounded-lg border px-3 py-2.5 text-left text-sm transition-colors',
                          mechanism === m
                            ? 'border-accent/60 bg-accent-muted text-foreground'
                            : 'border-border bg-surface/40 text-muted-foreground hover:border-accent/30 hover:bg-surface-hover',
                        )}
                      >
                        <span className="font-medium">{MECHANISM_LABEL[m]}</span>
                        {mechanism === m ? (
                          <Badge variant="default" className="text-[10px]">
                            ACTIVE
                          </Badge>
                        ) : null}
                      </button>
                    ))}
                  </div>
                </div>

                <label className="block space-y-1.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
                  Message
                  <Textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    placeholder="Type a message for real IPC delivery…"
                    className="min-h-[100px]"
                  />
                </label>

                <Button
                  type="submit"
                  disabled={sending || !content.trim()}
                  className="w-full"
                  size="lg"
                >
                  {sending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                  {sending ? 'Transmitting…' : 'Send via IPC'}
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card className="flex min-h-[420px] flex-col border-border/80">
            <CardHeader className="border-b border-border/50 bg-surface/30">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <CardTitle>Live Communication</CardTitle>
                  <CardDescription>Click a message for full IPC inspection</CardDescription>
                </div>
                <Badge variant="secondary">{liveMessages.length} msgs</Badge>
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto pt-4">
              <MessageList messages={liveMessages} onSelect={setSelected} />
            </CardContent>
          </Card>
        </div>
      </div>

      <IpcVisualizer
        mechanism={mechanism}
        lastMessage={animTrigger ?? liveMessages[0] ?? null}
        processes={allProcesses}
        metrics={{
          latency_ms: mechMetrics?.latency_ms.avg,
          success: mechMetrics?.count_success,
          fail: mechMetrics?.count_fail,
        }}
      />

      <MessageInspector message={selected} open={!!selected} onClose={() => setSelected(null)} />
    </PageFade>
  )
}

function ProcessRail({
  processes,
  selected,
}: {
  processes: ProcessInfo[]
  selected: string[]
}) {
  return (
    <Card className="h-fit border-border/80 bg-surface/20">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <Radio className="h-4 w-4 text-accent" />
          <CardTitle>Processes</CardTitle>
        </div>
        <CardDescription>Live managed workers</CardDescription>
      </CardHeader>
      <CardContent className="space-y-2 pt-2">
        {WORKERS.map((name) => {
          const p = processes.find((x) => x.name.toLowerCase() === name)
          const running = String(p?.status ?? '').toLowerCase() === 'running'
          const isSelected = selected.includes(name)
          return (
            <div
              key={name}
              className={cn(
                'rounded-lg border px-3 py-2.5 transition-colors',
                isSelected
                  ? 'border-accent/40 bg-accent-muted/50'
                  : 'border-border/70 bg-card/50',
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-semibold capitalize">{name}</span>
                <span
                  className={cn(
                    'inline-flex items-center gap-1 text-[10px] font-medium uppercase',
                    running ? 'text-success' : 'text-muted-foreground',
                  )}
                >
                  <span
                    className={cn(
                      'h-1.5 w-1.5 rounded-full',
                      running ? 'bg-success animate-pulse-dot' : 'bg-muted-foreground',
                    )}
                  />
                  {running ? 'RUNNING' : 'STOPPED'}
                </span>
              </div>
              <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                PID {p?.pid ?? '—'}
              </p>
              <div className="mt-1.5 flex gap-3 text-[10px] text-muted-foreground">
                <span>CPU {formatPercent(p?.stats?.cpu_percent)}</span>
                <span>
                  {p?.stats?.memory_rss_mb != null
                    ? `${p.stats.memory_rss_mb.toFixed(0)} MB`
                    : '—'}
                </span>
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
