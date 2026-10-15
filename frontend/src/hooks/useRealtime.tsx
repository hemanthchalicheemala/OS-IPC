import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from 'react'
import { useWebSocket, type ConnectionState } from '../hooks/useWebSocket'
import type { ChatMessage, WsEvent } from '../types'

interface RealtimeContextValue {
  connectionState: ConnectionState
  connected: boolean
  events: WsEvent[]
  lastEvent: WsEvent | null
  liveMessages: ChatMessage[]
  clearEvents: () => void
  upsertMessage: (msg: ChatMessage) => void
  setLiveMessages: Dispatch<SetStateAction<ChatMessage[]>>
}

const RealtimeContext = createContext<RealtimeContextValue | null>(null)

function extractMessage(event: WsEvent): ChatMessage | null {
  const data = event.data ?? {}
  const msg = (data.message ?? data) as Partial<ChatMessage>
  if (!msg || typeof msg !== 'object') return null
  if (!msg.id || !msg.sender || !msg.receiver || msg.content == null) return null
  return {
    id: String(msg.id),
    sender: String(msg.sender),
    receiver: String(msg.receiver),
    content: String(msg.content),
    mechanism: String(msg.mechanism ?? 'unknown'),
    timestamp: (msg.timestamp as number | string | undefined) ?? event.timestamp,
    size_bytes: msg.size_bytes,
    latency_ms: msg.latency_ms ?? null,
    delivered: msg.delivered,
  }
}

export function RealtimeProvider({ children }: { children: ReactNode }) {
  const [liveMessages, setLiveMessages] = useState<ChatMessage[]>([])

  const onEvent = useCallback((event: WsEvent) => {
    if (
      event.type === 'message_queued' ||
      event.type === 'message_sent' ||
      event.type === 'message_received' ||
      event.type === 'message_failed'
    ) {
      const msg = extractMessage(event)
      if (!msg) return
      setLiveMessages((prev) => {
        const idx = prev.findIndex((m) => m.id === msg.id)
        if (idx >= 0) {
          const next = [...prev]
          next[idx] = { ...next[idx], ...msg }
          return next
        }
        return [msg, ...prev].slice(0, 200)
      })
    }
  }, [])

  const { connectionState, connected, events, lastEvent, clearEvents } = useWebSocket({
    onEvent,
  })

  const upsertMessage = useCallback((msg: ChatMessage) => {
    setLiveMessages((prev) => {
      const idx = prev.findIndex((m) => m.id === msg.id)
      if (idx >= 0) {
        const next = [...prev]
        next[idx] = { ...next[idx], ...msg }
        return next
      }
      return [msg, ...prev].slice(0, 200)
    })
  }, [])

  const value = useMemo(
    () => ({
      connectionState,
      connected,
      events,
      lastEvent,
      liveMessages,
      clearEvents,
      upsertMessage,
      setLiveMessages,
    }),
    [
      connectionState,
      connected,
      events,
      lastEvent,
      liveMessages,
      clearEvents,
      upsertMessage,
    ],
  )

  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>
}

export function useRealtime() {
  const ctx = useContext(RealtimeContext)
  if (!ctx) throw new Error('useRealtime must be used within RealtimeProvider')
  return ctx
}
