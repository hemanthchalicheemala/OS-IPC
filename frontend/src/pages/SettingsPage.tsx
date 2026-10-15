import { Moon, Sun, Wifi, Info, Server } from 'lucide-react'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { ConnectionPill } from '../components/ui/Status'
import { PageFade, PageHeader } from '../components/ui/Page'
import { useTheme } from '../hooks/useTheme'
import { useRealtime } from '../hooks/useRealtime'
import { useApi } from '../hooks/useApi'
import { api } from '../services/api'

export function SettingsPage() {
  const { theme, toggleTheme, isDark } = useTheme()
  const { connectionState, connected } = useRealtime()
  const statusApi = useApi(() => api.getIpcStatus())

  return (
    <PageFade>
      <PageHeader
        title="Settings"
        description="Appearance, backend connection, and project information for the IPC Control Center."
      />

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="hover:border-accent/25">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {isDark ? <Moon className="h-4 w-4 text-accent" /> : <Sun className="h-4 w-4 text-accent" />}
              Appearance
            </CardTitle>
            <CardDescription>Dark mode is the default for the viva demo</CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-medium">Theme</p>
              <p className="text-xs capitalize text-muted-foreground">{theme}</p>
            </div>
            <Button variant="outline" onClick={toggleTheme}>
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              Switch to {isDark ? 'light' : 'dark'}
            </Button>
          </CardContent>
        </Card>

        <Card className="hover:border-accent/25">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wifi className="h-4 w-4 text-accent" />
              Connection
            </CardTitle>
            <CardDescription>Backend at 127.0.0.1:8000 via Vite proxy</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between rounded-lg border border-border/70 bg-muted/20 px-3 py-2">
              <span className="text-sm text-muted-foreground">WebSocket</span>
              <ConnectionPill state={connectionState} />
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border/70 bg-muted/20 px-3 py-2">
              <span className="text-sm text-muted-foreground">REST</span>
              <Badge variant={statusApi.error ? 'danger' : statusApi.data ? 'success' : 'secondary'}>
                {statusApi.error ? 'unreachable' : statusApi.data ? 'ok' : 'checking…'}
              </Badge>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border/70 bg-muted/20 px-3 py-2">
              <span className="text-sm text-muted-foreground">IPC mechanism</span>
              <Badge variant="outline">{statusApi.data?.mechanism ?? '—'}</Badge>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-border/70 bg-muted/20 px-3 py-2">
              <span className="text-sm text-muted-foreground">Manager started</span>
              <Badge variant={statusApi.data?.started ? 'success' : 'secondary'}>
                {statusApi.data?.started ? 'yes' : 'no'}
              </Badge>
            </div>
            <Button variant="secondary" size="sm" onClick={() => void statusApi.refetch()}>
              <Server className="h-3.5 w-3.5" />
              Recheck
            </Button>
            {!connected ? (
              <p className="text-xs text-muted-foreground">
                Ensure the FastAPI backend is running, then reload this page.
              </p>
            ) : null}
          </CardContent>
        </Card>

        <Card className="md:col-span-2 hover:border-accent/25">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="h-4 w-4 text-accent" />
              About
            </CardTitle>
            <CardDescription>Intelligent IPC Chat Application · Control Center</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm leading-relaxed text-muted-foreground">
            <p>
              A BTech Operating Systems viva demo showing real multiprocessing IPC
              (Pipe, Queue, Shared Memory), process lifecycle, synchronization experiments,
              and lightweight ML classification over chat traffic.
            </p>
            <p>
              Frontend: React + TypeScript + Vite + Tailwind v4 · Backend: FastAPI ·
              Metrics and PIDs are read live — never fabricated in the UI.
            </p>
          </CardContent>
        </Card>
      </div>
    </PageFade>
  )
}
