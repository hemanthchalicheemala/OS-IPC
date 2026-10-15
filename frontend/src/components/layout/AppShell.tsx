import { useState, type ReactNode } from 'react'
import { Outlet } from 'react-router-dom'
import { useRealtime } from '../../hooks/useRealtime'
import { MobileMenuButton, Sidebar } from './Sidebar'
import { ConnectionPill } from '../ui/Status'

export function AppShell({ children }: { children?: ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { connectionState } = useRealtime()

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        connectionState={connectionState}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-border bg-background/80 px-4 py-3 backdrop-blur-md lg:px-6">
          <div className="flex items-center gap-3">
            <MobileMenuButton onClick={() => setSidebarOpen(true)} />
            <div className="lg:hidden">
              <p className="text-sm font-semibold tracking-tight">IPC Control Center</p>
              <p className="text-[10px] text-muted-foreground">Live OS monitoring</p>
            </div>
          </div>
          <ConnectionPill state={connectionState} />
        </header>
        <main className="flex-1 overflow-x-hidden px-4 py-5 lg:px-6 lg:py-6">
          {children ?? <Outlet />}
        </main>
      </div>
    </div>
  )
}
