import { AnimatePresence, motion } from 'framer-motion'
import { HardDrive, Lock, MemoryStick, Radio } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { capitalize, cn, formatMs, formatPercent } from '../../lib/utils'
import type { ChatMessage, ProcessInfo } from '../../types'
import { Badge } from '../ui/Badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card'

const MECHANISM_INFO: Record<
  string,
  { title: string; blurb: string; sync: string; sizeLabel: string }
> = {
  pipe: {
    title: 'Pipe',
    blurb:
      'A duplex byte stream between two endpoints. Each worker holds a Pipe to the broker, which forwards payloads to the peer.',
    sync: 'OS pipe buffers',
    sizeLabel: 'Stream channel',
  },
  queue: {
    title: 'Message Queue',
    blurb:
      'A synchronized producer–consumer channel. Workers enqueue to the broker; the broker delivers into receiver inboxes.',
    sync: 'Internal queue lock',
    sizeLabel: 'Bounded queue',
  },
  shared_memory: {
    title: 'Shared Memory',
    blurb:
      'Processes communicate through a mapped memory region. A Lock plus notify Queue prevent races and wake the peer on Windows.',
    sync: 'Lock + Notify Queue',
    sizeLabel: '64 KB region',
  },
}

type AnimPhase = 'idle' | 'send' | 'ipc' | 'recv' | 'done'

export function IpcVisualizer({
  mechanism,
  lastMessage,
  processes = [],
  metrics,
}: {
  mechanism: string
  lastMessage: ChatMessage | null
  processes?: ProcessInfo[]
  metrics?: {
    latency_ms?: number | null
    success?: number
    fail?: number
  }
}) {
  const [packet, setPacket] = useState<ChatMessage | null>(null)
  const [phase, setPhase] = useState<AnimPhase>('idle')

  const info = MECHANISM_INFO[mechanism] ?? {
    title: capitalize(mechanism || 'IPC'),
    blurb: 'Select a mechanism to inspect how chat traffic is routed.',
    sync: '—',
    sizeLabel: '—',
  }

  useEffect(() => {
    if (!lastMessage) return
    setPacket(lastMessage)
    setPhase('send')
    const t1 = window.setTimeout(() => setPhase('ipc'), 450)
    const t2 = window.setTimeout(() => setPhase('recv'), 1100)
    const t3 = window.setTimeout(() => setPhase('done'), 1700)
    const t4 = window.setTimeout(() => {
      setPhase('idle')
      setPacket(null)
    }, 2800)
    return () => {
      window.clearTimeout(t1)
      window.clearTimeout(t2)
      window.clearTimeout(t3)
      window.clearTimeout(t4)
    }
  }, [lastMessage?.id])

  const byName = useMemo(() => {
    const map = new Map<string, ProcessInfo>()
    for (const p of processes) map.set(p.name.toLowerCase(), p)
    return map
  }, [processes])

  const senderName = (packet?.sender ?? 'alice').toLowerCase()
  const receiverName = (packet?.receiver ?? 'bob').toLowerCase()
  const sender = byName.get(senderName)
  const receiver = byName.get(receiverName)
  const active = phase !== 'idle'

  const packetY =
    phase === 'send' ? '18%' : phase === 'ipc' ? '48%' : phase === 'recv' || phase === 'done' ? '78%' : '18%'

  return (
    <Card className="overflow-hidden">
      <CardHeader className="border-b border-border/60 bg-surface/40">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="text-base">IPC Path Visualizer</CardTitle>
            <CardDescription className="mt-1">
              {active && packet
                ? `Live: ${capitalize(packet.sender)} → ${info.title} → ${capitalize(packet.receiver)}`
                : 'Idle — waiting for real IPC traffic'}
            </CardDescription>
          </div>
          <Badge variant={active ? 'default' : 'outline'}>
            {active ? 'TRANSMITTING' : 'IDLE'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-5">
        <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
          <div className="relative overflow-hidden rounded-xl border border-border bg-[radial-gradient(ellipse_at_top,_var(--accent-muted),_transparent_55%)] px-4 py-8 sm:px-8">
            <div className="relative mx-auto flex max-w-md flex-col items-center gap-0">
              <ProcessNode
                name={senderName}
                pid={sender?.pid}
                status={sender?.status}
                cpu={sender?.stats?.cpu_percent}
                mem={sender?.stats?.memory_rss_mb}
                lit={phase === 'send' || phase === 'done'}
              />

              <PathSegment active={phase === 'send' || phase === 'ipc'} />

              <MechanismNode
                title={info.title}
                sizeLabel={info.sizeLabel}
                sync={info.sync}
                lit={phase === 'ipc' || phase === 'done'}
                lockState={phase === 'ipc' ? 'HELD' : 'FREE'}
              />

              <PathSegment active={phase === 'ipc' || phase === 'recv' || phase === 'done'} />

              <ProcessNode
                name={receiverName}
                pid={receiver?.pid}
                status={receiver?.status}
                cpu={receiver?.stats?.cpu_percent}
                mem={receiver?.stats?.memory_rss_mb}
                lit={phase === 'recv' || phase === 'done'}
              />

              <AnimatePresence>
                {packet && phase !== 'idle' ? (
                  <motion.div
                    key={packet.id}
                    className="pointer-events-none absolute left-1/2 z-10 -translate-x-1/2"
                    initial={{ top: '12%', opacity: 0, scale: 0.9 }}
                    animate={{ top: packetY, opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.55, ease: 'easeInOut' }}
                  >
                    <div className="flex max-w-[200px] items-center gap-2 rounded-full border border-accent/50 bg-card/95 px-3 py-1.5 shadow-[0_0_24px_rgba(34,211,238,0.25)] backdrop-blur">
                      <span className="h-2 w-2 shrink-0 rounded-full bg-accent animate-pulse-dot" />
                      <span className="truncate font-mono text-[11px] text-accent">
                        {packet.content}
                      </span>
                    </div>
                  </motion.div>
                ) : null}
              </AnimatePresence>
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded-xl border border-border bg-surface/50 p-4">
              <div className="mb-3 flex items-center gap-2">
                <Radio className="h-4 w-4 text-accent" />
                <p className="text-sm font-semibold">{info.title}</p>
              </div>
              <dl className="space-y-2.5 text-xs">
                <Row label="Status" value={active ? 'ACTIVE' : 'READY'} />
                <Row label="Channel" value={info.sizeLabel} />
                <Row label="Synchronization" value={info.sync} />
                <Row
                  label="Last latency"
                  value={formatMs(packet?.latency_ms ?? metrics?.latency_ms)}
                />
                <Row label="Success" value={String(metrics?.success ?? '—')} />
                <Row label="Failures" value={String(metrics?.fail ?? '—')} />
              </dl>
              <p className="mt-4 border-t border-border/70 pt-3 text-[12px] leading-relaxed text-muted-foreground">
                {info.blurb}
              </p>
            </div>

            {packet ? (
              <div className="rounded-xl border border-success/30 bg-success-muted/40 p-4 text-xs">
                <p className="mb-2 font-semibold text-success">Last transmission</p>
                <p className="text-muted-foreground">
                  {capitalize(packet.sender)} → {capitalize(packet.receiver)}
                </p>
                <p className="mt-1 font-mono text-foreground">{packet.content}</p>
                <div className="mt-2 flex flex-wrap gap-2 text-muted-foreground">
                  <span>{formatMs(packet.latency_ms)}</span>
                  {packet.size_bytes != null ? <span>· {packet.size_bytes} B</span> : null}
                  <span>· {packet.delivered ? 'DELIVERED' : 'IN FLIGHT'}</span>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-mono text-[11px] text-foreground">{value}</dd>
    </div>
  )
}

function PathSegment({ active }: { active?: boolean }) {
  return (
    <div className="flex h-10 w-px flex-col items-center justify-center">
      <div
        className={cn(
          'h-full w-px',
          active ? 'bg-accent shadow-[0_0_8px_var(--accent)]' : 'bg-border',
        )}
      />
    </div>
  )
}

function ProcessNode({
  name,
  pid,
  status,
  cpu,
  mem,
  lit,
}: {
  name: string
  pid?: number | null
  status?: string
  cpu?: number
  mem?: number
  lit?: boolean
}) {
  const running = String(status ?? '').toLowerCase() === 'running'
  return (
    <motion.div
      animate={{
        borderColor: lit ? 'var(--accent)' : 'var(--border)',
        boxShadow: lit ? '0 0 0 1px var(--accent-muted), 0 0 28px rgba(34,211,238,0.15)' : 'none',
      }}
      className="w-full max-w-xs rounded-xl border bg-card/90 px-4 py-3 backdrop-blur"
    >
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-semibold uppercase tracking-wide">{name}</p>
        <span
          className={cn(
            'inline-flex items-center gap-1.5 text-[10px] font-medium uppercase',
            running ? 'text-success' : 'text-muted-foreground',
          )}
        >
          <span
            className={cn(
              'h-1.5 w-1.5 rounded-full',
              running ? 'bg-success animate-pulse-dot' : 'bg-muted-foreground',
            )}
          />
          {running ? 'RUNNING' : String(status || 'UNKNOWN').toUpperCase()}
        </span>
      </div>
      <p className="mt-1 font-mono text-[11px] text-muted-foreground">
        PID {pid ?? '—'}
      </p>
      <div className="mt-2 flex gap-3 text-[10px] text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <HardDrive className="h-3 w-3" />
          {formatPercent(cpu)}
        </span>
        <span className="inline-flex items-center gap-1">
          <MemoryStick className="h-3 w-3" />
          {mem != null ? `${mem.toFixed(1)} MB` : '—'}
        </span>
      </div>
    </motion.div>
  )
}

function MechanismNode({
  title,
  sizeLabel,
  sync,
  lit,
  lockState,
}: {
  title: string
  sizeLabel: string
  sync: string
  lit?: boolean
  lockState: string
}) {
  return (
    <motion.div
      animate={{
        borderColor: lit ? 'var(--accent)' : 'var(--border)',
        backgroundColor: lit ? 'var(--accent-muted)' : 'var(--card)',
      }}
      className="w-full max-w-xs rounded-xl border px-4 py-3"
    >
      <div className="flex items-center gap-2">
        <Lock className={cn('h-4 w-4', lit ? 'text-accent' : 'text-muted-foreground')} />
        <p className="text-sm font-semibold uppercase tracking-wide">{title}</p>
      </div>
      <dl className="mt-2 grid grid-cols-2 gap-2 text-[10px]">
        <div>
          <dt className="text-muted-foreground">Channel</dt>
          <dd className="font-mono text-foreground">{sizeLabel}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Lock</dt>
          <dd className={cn('font-mono', lockState === 'HELD' ? 'text-warning' : 'text-success')}>
            {lockState}
          </dd>
        </div>
        <div className="col-span-2">
          <dt className="text-muted-foreground">Sync</dt>
          <dd className="font-mono text-foreground">{sync}</dd>
        </div>
      </dl>
    </motion.div>
  )
}
