import { Database, History, RefreshCw } from 'lucide-react'
import { useState } from 'react'
import { MessageInspector } from '../components/chat/MessageInspector'
import { MessageList } from '../components/chat/MessageList'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { PageFade, PageHeader } from '../components/ui/Page'
import { EmptyState, ErrorState, LoadingState } from '../components/ui/States'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { useApi } from '../hooks/useApi'
import { api } from '../services/api'
import type { ChatMessage } from '../types'

export function HistoryPage() {
  const { data, error, loading, refetch } = useApi(() => api.getMessages())
  const [selected, setSelected] = useState<ChatMessage | null>(null)

  const live = data?.messages ?? []
  const persisted = data?.persisted ?? []

  return (
    <PageFade>
      <PageHeader
        title="Message History"
        description="In-memory ring buffer and persisted SQLite history from the API — select a message to inspect."
        actions={
          <Button variant="outline" size="sm" onClick={() => void refetch()}>
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
        }
      />

      {error ? (
        <div className="mb-4">
          <ErrorState message={error} onRetry={() => void refetch()} />
        </div>
      ) : null}

      {loading && !data ? (
        <LoadingState label="Loading message history…" />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between gap-2">
                <CardTitle className="flex items-center gap-2">
                  <History className="h-4 w-4 text-accent" />
                  Live messages
                </CardTitle>
                <Badge variant="secondary">{live.length}</Badge>
              </div>
              <CardDescription>In-memory buffer from the running backend</CardDescription>
            </CardHeader>
            <CardContent>
              {live.length === 0 ? (
                <EmptyState
                  title="NO ACTIVE COMMUNICATION"
                  description="Send messages from Chat to populate the live ring buffer."
                  icon={History}
                />
              ) : (
                <MessageList messages={live} onSelect={setSelected} />
              )}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between gap-2">
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-accent" />
                  Persisted messages
                </CardTitle>
                <Badge variant="secondary">{persisted.length}</Badge>
              </div>
              <CardDescription>SQLite-backed history</CardDescription>
            </CardHeader>
            <CardContent>
              {persisted.length === 0 ? (
                <EmptyState
                  title="NO PERSISTED MESSAGES"
                  description="Delivered traffic is stored in SQLite and listed here."
                  icon={Database}
                />
              ) : (
                <MessageList messages={persisted} onSelect={setSelected} />
              )}
            </CardContent>
          </Card>
        </div>
      )}

      <MessageInspector
        message={selected}
        open={!!selected}
        onClose={() => setSelected(null)}
      />
    </PageFade>
  )
}
