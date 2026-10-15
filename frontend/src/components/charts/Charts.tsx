import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { MetricPoint } from '../../types'

const ACCENT = '#22d3ee'
const MUTED = '#71717a'
const SUCCESS = '#4ade80'
const WARNING = '#facc15'

const tooltipStyle = {
  backgroundColor: 'var(--card)',
  border: '1px solid var(--border)',
  borderRadius: 10,
  fontSize: 12,
  boxShadow: '0 8px 24px rgba(0,0,0,0.35)',
}

export function SystemTrendsChart({ data }: { data: MetricPoint[] }) {
  if (!data.length) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        Waiting for live metrics…
      </div>
    )
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" strokeOpacity={0.7} />
          <XAxis dataKey="time" tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} />
          <YAxis tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} />
          <Tooltip contentStyle={tooltipStyle} />
          <Legend />
          <Line type="monotone" dataKey="cpu" name="CPU %" stroke={ACCENT} strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="memory" name="RAM %" stroke={MUTED} strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="msgsPerSec" name="Msgs/s" stroke={SUCCESS} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function LatencyAreaChart({ data }: { data: MetricPoint[] }) {
  if (!data.length) {
    return (
      <div className="flex h-56 items-center justify-center text-sm text-muted-foreground">
        No latency samples yet
      </div>
    )
  }

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="latFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={ACCENT} stopOpacity={0.4} />
              <stop offset="100%" stopColor={ACCENT} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" strokeOpacity={0.7} />
          <XAxis dataKey="time" tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} />
          <YAxis tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} />
          <Tooltip contentStyle={tooltipStyle} />
          <Area
            type="monotone"
            dataKey="latency"
            name="Latency (ms)"
            stroke={ACCENT}
            fill="url(#latFill)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export function MechanismCompareChart({
  data,
}: {
  data: { mechanism: string; avg_ms: number | null; min_ms?: number | null; max_ms?: number | null }[]
}) {
  if (!data.length) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
        Run the latency comparison to populate this chart
      </div>
    )
  }

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" strokeOpacity={0.7} />
          <XAxis dataKey="mechanism" tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} />
          <YAxis tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }} unit=" ms" />
          <Tooltip contentStyle={tooltipStyle} />
          <Legend />
          <Bar dataKey="avg_ms" name="Avg ms" fill={ACCENT} radius={[6, 6, 0, 0]} />
          <Bar dataKey="min_ms" name="Min ms" fill={SUCCESS} radius={[6, 6, 0, 0]} />
          <Bar dataKey="max_ms" name="Max ms" fill={WARNING} radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
