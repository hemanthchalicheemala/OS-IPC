import {
  Activity,
  Beaker,
  BookOpen,
  Brain,
  GitCompare,
  History,
  LayoutDashboard,
  MessageSquare,
  Network,
  Settings,
  Cpu,
  Menu,
  X,
} from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { cn } from '../../lib/utils'
import { ConnectionPill } from '../ui/Status'
import type { ConnectionState } from '../../hooks/useWebSocket'
import { Button } from '../ui/Button'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/chat', label: 'Chat', icon: MessageSquare },
  { to: '/processes', label: 'Processes', icon: Cpu },
  { to: '/ipc', label: 'IPC', icon: Network },
  { to: '/comparison', label: 'Comparison', icon: GitCompare },
  { to: '/ml', label: 'ML Analysis', icon: Brain },
  { to: '/experiments', label: 'Experiments', icon: Beaker },
  { to: '/history', label: 'History', icon: History },
  { to: '/concepts', label: 'Concepts', icon: BookOpen },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export function Sidebar({
  open,
  onClose,
  connectionState,
}: {
  open: boolean
  onClose: () => void
  connectionState: ConnectionState
}) {
  return (
    <>
      {open ? (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-black/55 backdrop-blur-[2px] lg:hidden"
          aria-label="Close sidebar"
          onClick={onClose}
        />
      ) : null}

      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-border bg-sidebar transition-transform duration-200 lg:static lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex items-start justify-between gap-2 border-b border-border px-4 py-5">
          <div className="min-w-0">
            <div className="flex items-center gap-3">
              <div className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-accent/30 bg-accent-muted text-accent shadow-[0_0_20px_rgba(34,211,238,0.15)]">
                <Activity className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold tracking-tight text-foreground">
                  IPC Control Center
                </p>
                <p className="text-[10px] leading-tight text-muted-foreground">
                  OS monitoring · live IPC
                </p>
              </div>
            </div>
          </div>
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="px-4 py-3">
          <ConnectionPill state={connectionState} />
        </div>

        <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 pb-4">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground',
                  isActive &&
                    'bg-accent-muted text-accent shadow-[inset_0_0_0_1px_rgba(34,211,238,0.2)] hover:bg-accent-muted hover:text-accent',
                )
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-border px-4 py-3">
          <p className="text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
            BTech OS Viva Demo
          </p>
        </div>
      </aside>
    </>
  )
}

export function MobileMenuButton({ onClick }: { onClick: () => void }) {
  return (
    <Button variant="outline" size="icon" className="lg:hidden" onClick={onClick}>
      <Menu className="h-4 w-4" />
    </Button>
  )
}
