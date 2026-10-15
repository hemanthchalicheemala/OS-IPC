import { useCallback, useEffect, useRef, useState } from 'react'
import { getWsUrl } from '../services/api'
import type { WsEvent } from '../types'

export type ConnectionState = 'connecting' | 'connected' | 'disconnected'

interface UseWebSocketOptions {
  onEvent?: (event: WsEvent) => void
  enabled?: boolean
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const { onEvent, enabled = true } = options
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected')
  const [lastEvent, setLastEvent] = useState<WsEvent | null>(null)
  const [events, setEvents] = useState<WsEvent[]>([])
  const onEventRef = useRef(onEvent)
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef(0)
  const timerRef = useRef<number | null>(null)

  useEffect(() => {
    onEventRef.current = onEvent
  }, [onEvent])

  const pushEvent = useCallback((event: WsEvent) => {
    setLastEvent(event)
    setEvents((prev) => [event, ...prev].slice(0, 200))
    onEventRef.current?.(event)
  }, [])

  useEffect(() => {
    if (!enabled) {
      setConnectionState('disconnected')
      return
    }

    let closed = false

    const connect = () => {
      if (closed) return
      setConnectionState('connecting')
      const ws = new WebSocket(getWsUrl())
      wsRef.current = ws

      ws.onopen = () => {
        retryRef.current = 0
        setConnectionState('connected')
      }

      ws.onmessage = (msg) => {
        try {
          const parsed = JSON.parse(msg.data as string) as WsEvent
          if (parsed.type === 'ping') {
            ws.send('ping')
            return
          }
          if (parsed.type === 'pong') return
          pushEvent(parsed)
        } catch {
          /* ignore malformed */
        }
      }

      ws.onclose = () => {
        setConnectionState('disconnected')
        wsRef.current = null
        if (closed) return
        const delay = Math.min(8000, 500 + retryRef.current * 1000)
        retryRef.current += 1
        timerRef.current = window.setTimeout(connect, delay)
      }

      ws.onerror = () => {
        ws.close()
      }
    }

    connect()

    return () => {
      closed = true
      if (timerRef.current != null) window.clearTimeout(timerRef.current)
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [enabled, pushEvent])

  const clearEvents = useCallback(() => setEvents([]), [])

  return {
    connectionState,
    connected: connectionState === 'connected',
    lastEvent,
    events,
    clearEvents,
  }
}
