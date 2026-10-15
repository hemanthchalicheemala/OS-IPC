import { AlertTriangle, Brain, Sparkles } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { Textarea } from '../components/ui/Input'
import { PageFade, PageHeader } from '../components/ui/Page'
import { EmptyState, ErrorState } from '../components/ui/States'
import { api } from '../services/api'
import { cn } from '../lib/utils'
import type { MlAnalyzeResponse } from '../types'

function isSpam(label: string) {
  return label.toLowerCase().includes('spam')
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(100, value * 100))
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">Confidence</span>
        <span className="font-medium tabular-nums text-foreground">{pct.toFixed(1)}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-accent transition-[width] duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

export function MlPage() {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [current, setCurrent] = useState<MlAnalyzeResponse | null>(null)
  const [recent, setRecent] = useState<MlAnalyzeResponse[]>([])

  async function onAnalyze(e: FormEvent) {
    e.preventDefault()
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.analyzeText(text.trim())
      setCurrent(res)
      setRecent((prev) => [res, ...prev].slice(0, 20))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const spam = current ? isSpam(current.classification.label) : false

  return (
    <PageFade>
      <PageHeader
        title="Message Analysis"
        description="Classify chat text and score sentiment with the backend TF-IDF + Logistic Regression model."
      />

      {error ? (
        <div className="mb-4">
          <ErrorState message={error} />
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-accent" />
              Analyze text
            </CardTitle>
            <CardDescription>
              Model: TF-IDF + Logistic Regression · POST /api/ml/analyze
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-3" onSubmit={onAnalyze}>
              <Textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="e.g. Congratulations! You won a FREE iPhone…"
                rows={7}
              />
              <Button type="submit" disabled={loading || !text.trim()} className="w-full">
                <Sparkles className="h-4 w-4" />
                {loading ? 'Analyzing…' : 'Run analysis'}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card
          className={cn(
            spam && 'border-danger/40 shadow-[0_0_0_1px_rgba(248,113,113,0.15)]',
          )}
        >
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {spam ? (
                <>
                  <AlertTriangle className="h-4 w-4 text-danger" />
                  Spam detected
                </>
              ) : (
                'Latest prediction'
              )}
            </CardTitle>
            <CardDescription>Classification · confidence · sentiment</CardDescription>
          </CardHeader>
          <CardContent>
            {!current ? (
              <EmptyState
                title="NO PREDICTION YET"
                description="Submit message text to see classification, confidence, and sentiment."
                icon={Brain}
              />
            ) : (
              <div className="space-y-5">
                <div className="flex flex-wrap gap-2">
                  <Badge variant={spam ? 'danger' : 'success'}>
                    {current.classification.label}
                  </Badge>
                  <Badge variant="outline">{current.sentiment.label}</Badge>
                  <Badge variant="secondary">TF-IDF + Logistic Regression</Badge>
                </div>

                <ConfidenceBar value={current.classification.confidence} />

                {current.sentiment.score != null || current.sentiment.polarity != null ? (
                  <div className="rounded-lg border border-border bg-muted/30 px-3 py-2.5 text-sm">
                    <p className="text-[10px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
                      Sentiment
                    </p>
                    <p className="mt-1 font-medium capitalize">{current.sentiment.label}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {current.sentiment.score != null
                        ? `score ${(current.sentiment.score * 100).toFixed(1)}%`
                        : null}
                      {current.sentiment.polarity != null
                        ? `${current.sentiment.score != null ? ' · ' : ''}polarity ${Number(current.sentiment.polarity).toFixed(3)}`
                        : null}
                    </p>
                  </div>
                ) : null}

                <p
                  className={cn(
                    'rounded-lg border p-3 text-sm leading-relaxed',
                    spam
                      ? 'border-danger/30 bg-danger/5 text-danger'
                      : 'border-border bg-muted/40 text-muted-foreground',
                  )}
                >
                  {current.text}
                </p>

                {current.classification.probabilities ? (
                  <div className="space-y-2">
                    <p className="text-[10px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
                      Class probabilities
                    </p>
                    {Object.entries(current.classification.probabilities).map(([label, p]) => (
                      <div key={label} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="capitalize">{label}</span>
                          <span className="tabular-nums text-muted-foreground">
                            {(p * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                          <div
                            className={cn(
                              'h-full rounded-full',
                              isSpam(label) ? 'bg-danger' : 'bg-success',
                            )}
                            style={{ width: `${Math.max(0, Math.min(100, p * 100))}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Recent predictions</CardTitle>
          <CardDescription>Session history (this browser tab)</CardDescription>
        </CardHeader>
        <CardContent>
          {recent.length === 0 ? (
            <EmptyState
              title="NO RECENT PREDICTIONS"
              description="Analyses from this session will appear here."
            />
          ) : (
            <div className="space-y-2">
              {recent.map((r, i) => {
                const rowSpam = isSpam(r.classification.label)
                return (
                  <div
                    key={`${r.text}-${i}`}
                    className={cn(
                      'flex flex-col gap-2 rounded-xl border px-3 py-3 sm:flex-row sm:items-center',
                      rowSpam ? 'border-danger/30 bg-danger/5' : 'border-border',
                    )}
                  >
                    <p className="line-clamp-2 flex-1 text-sm">{r.text}</p>
                    <div className="flex flex-wrap gap-1.5">
                      <Badge variant={rowSpam ? 'danger' : 'success'}>
                        {r.classification.label}
                      </Badge>
                      <Badge variant="secondary">
                        {(r.classification.confidence * 100).toFixed(0)}%
                      </Badge>
                      <Badge variant="outline">{r.sentiment.label}</Badge>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </PageFade>
  )
}
