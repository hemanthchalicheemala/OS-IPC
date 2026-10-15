import { motion } from 'framer-motion'
import { capitalize, formatMs, formatTimestamp } from '../../lib/utils'
import type { ChatMessage } from '../../types'
import { Badge } from '../ui/Badge'
import { EmptyState } from '../ui/States'

export function MessageList({
  messages,
  onSelect,
}: {
  messages: ChatMessage[]
  onSelect?: (msg: ChatMessage) => void
}) {
  if (!messages.length) {
    return (
      <EmptyState
        title="NO ACTIVE COMMUNICATION"
        description="Compose a message on the left to observe real IPC traffic between processes."
      />
    )
  }

  return (
    <div className="space-y-3">
      {messages.map((msg, index) => {
        const status = msg.delivered
          ? 'DELIVERED'
          : msg.latency_ms != null
            ? 'SENT'
            : 'SENDING'
        return (
          <motion.button
            key={msg.id}
            type="button"
            layout
            initial={{ opacity: 0, y: 8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ delay: Math.min(index * 0.02, 0.12) }}
            onClick={() => onSelect?.(msg)}
            className="group flex w-full flex-col gap-2.5 rounded-xl border border-border/80 bg-surface/40 p-3.5 text-left transition-all hover:border-accent/40 hover:bg-surface-hover hover:shadow-[0_0_0_1px_var(--accent-muted)]"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-semibold tracking-tight">
                {capitalize(msg.sender)}
                <span className="mx-1.5 text-muted-foreground">→</span>
                {capitalize(msg.receiver)}
              </span>
              <Badge variant="secondary" className="uppercase tracking-wide">
                {msg.mechanism.replace('_', ' ')}
              </Badge>
              <Badge
                variant={
                  status === 'DELIVERED' ? 'success' : status === 'SENT' ? 'default' : 'warning'
                }
              >
                {status}
              </Badge>
              <span className="ml-auto font-mono text-[11px] text-muted-foreground">
                {formatTimestamp(msg.timestamp)}
              </span>
            </div>

            <div className="rounded-lg border border-border/50 bg-card/60 px-3 py-2.5">
              <p className="text-sm leading-relaxed text-foreground">{msg.content}</p>
            </div>

            <div className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-[11px] text-muted-foreground">
              <span>
                Latency <span className="text-foreground">{formatMs(msg.latency_ms)}</span>
              </span>
              <span>
                Size{' '}
                <span className="text-foreground">
                  {msg.size_bytes != null ? `${msg.size_bytes} B` : '—'}
                </span>
              </span>
              <span className="text-accent opacity-0 transition-opacity group-hover:opacity-100">
                Inspect →
              </span>
            </div>
          </motion.button>
        )
      })}
    </div>
  )
}
