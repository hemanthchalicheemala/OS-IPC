import type { ReactNode } from 'react'
import { capitalize, formatBytes, formatMs, formatTimestamp } from '../../lib/utils'
import type { ChatMessage } from '../../types'
import { Badge } from '../ui/Badge'
import { Drawer } from '../ui/Drawer'

export function MessageInspector({
  message,
  open,
  onClose,
}: {
  message: ChatMessage | null
  open: boolean
  onClose: () => void
}) {
  const status = message?.delivered
    ? 'DELIVERED'
    : message?.latency_ms != null
      ? 'SENT'
      : 'SENDING'

  return (
    <Drawer open={open && !!message} onClose={onClose} title="Message Inspector">
      {message ? (
        <div className="space-y-4 text-sm">
          <div className="rounded-xl border border-border bg-surface/50 p-3">
            <p className="text-xs uppercase tracking-wider text-muted-foreground">Route</p>
            <p className="mt-1 text-base font-semibold">
              {capitalize(message.sender)}
              <span className="mx-2 text-muted-foreground">→</span>
              {capitalize(message.receiver)}
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <Badge variant="default" className="uppercase">
                {message.mechanism.replace('_', ' ')}
              </Badge>
              <Badge
                variant={
                  status === 'DELIVERED' ? 'success' : status === 'SENT' ? 'default' : 'warning'
                }
              >
                {status}
              </Badge>
            </div>
          </div>

          <Field label="Message ID" value={<code className="font-mono text-xs">{message.id}</code>} />
          <Field label="Latency" value={formatMs(message.latency_ms)} />
          <Field label="Size" value={formatBytes(message.size_bytes)} />
          <Field label="Timestamp" value={formatTimestamp(message.timestamp)} />

          <div>
            <p className="mb-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Content
            </p>
            <pre className="whitespace-pre-wrap rounded-lg border border-border bg-muted/40 p-3 font-mono text-xs leading-relaxed">
              {message.content}
            </pre>
          </div>
        </div>
      ) : null}
    </Drawer>
  )
}

function Field({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border/60 pb-3">
      <span className="text-xs uppercase tracking-wider text-muted-foreground">{label}</span>
      <span className="text-right text-sm">{value}</span>
    </div>
  )
}
