import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '../../lib/utils'

export function Card({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-xl border border-border bg-card text-card-foreground shadow-sm transition-colors',
        className,
      )}
      {...props}
    />
  )
}

export function CardHeader({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('flex flex-col gap-1 p-5 pb-3', className)} {...props} />
}

export function CardTitle({
  className,
  ...props
}: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn('text-sm font-semibold tracking-tight', className)} {...props} />
}

export function CardDescription({
  className,
  ...props
}: HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn('text-xs text-muted-foreground', className)} {...props} />
}

export function CardContent({
  className,
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('p-5 pt-0', className)} {...props} />
}

export function MetricCard({
  label,
  value,
  hint,
  icon,
  className,
}: {
  label: string
  value: ReactNode
  hint?: string
  icon?: ReactNode
  className?: string
}) {
  return (
    <Card
      className={cn(
        'group overflow-hidden border-border/80 bg-gradient-to-b from-card to-card/80',
        'hover:border-accent/30 hover:shadow-[0_0_0_1px_rgba(34,211,238,0.08)]',
        className,
      )}
    >
      <CardContent className="pt-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 space-y-1.5">
            <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
              {label}
            </p>
            <div className="truncate text-2xl font-semibold tabular-nums tracking-tight text-foreground">
              {value}
            </div>
            {hint ? (
              <p className="text-xs text-muted-foreground/90">{hint}</p>
            ) : null}
          </div>
          {icon ? (
            <div className="rounded-lg border border-accent/20 bg-accent-muted p-2.5 text-accent transition-colors group-hover:border-accent/40">
              {icon}
            </div>
          ) : null}
        </div>
      </CardContent>
    </Card>
  )
}
