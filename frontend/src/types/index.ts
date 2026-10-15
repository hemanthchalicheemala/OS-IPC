export type ProcessStatus = 'running' | 'stopped' | 'crashed' | string

export type IpcMechanism = 'pipe' | 'queue' | 'shared_memory'

export interface ProcessStats {
  pid?: number
  name?: string
  status?: string
  cpu_percent?: number
  memory_rss?: number
  memory_rss_mb?: number
  num_threads?: number
  create_time?: number
}

export interface ProcessInfo {
  name: string
  pid: number | null
  status: ProcessStatus
  stats?: ProcessStats | null
}

export interface ChatMessage {
  id: string
  sender: string
  receiver: string
  content: string
  mechanism: string
  timestamp?: number | string | null
  size_bytes?: number
  latency_ms?: number | null
  delivered?: boolean
  t_send_start?: number | null
  t_send_end?: number | null
}

export interface LatencyStats {
  min: number | null
  max: number | null
  avg: number | null
  samples: number
}

export interface MechanismMetrics {
  count_success: number
  count_fail: number
  total_bytes: number
  latency_ms: LatencyStats
}

export interface IpcMetrics {
  per_mechanism: Record<string, MechanismMetrics>
  msgs_per_sec: number
  total_success: number
  total_fail: number
}

export interface IpcStatus {
  mechanism: IpcMechanism | string
  started: boolean
  processes: ProcessInfo[]
  shm_name?: string | null
}

export interface SystemStats {
  processes: Record<string, ProcessStats>
  system: {
    cpu_percent: number
    cpu_count: number
    memory_total: number
    memory_available: number
    memory_percent: number
  }
  mechanism?: string
  ipc_metrics?: IpcMetrics
  anomalies?: Record<string, AnomalyResult>
}

export interface AnomalyResult {
  score?: number
  is_anomaly?: boolean
  [key: string]: unknown
}

export interface ExperimentInfo {
  id: string
  title: string
  description: string
}

export interface ExperimentResult {
  run_id?: string
  experiment_id: string
  title: string
  success: boolean
  error?: string | null
  elapsed_ms?: number
  result?: Record<string, unknown>
  timestamp?: number
}

export interface PersistedExperimentResult {
  id: number
  experiment_id: string
  title: string
  success: boolean
  result: ExperimentResult | Record<string, unknown>
  created_at?: string | null
}

export interface ClassificationResult {
  label: string
  confidence: number
  probabilities?: Record<string, number>
}

export interface SentimentResult {
  label: string
  score?: number
  polarity?: number
  [key: string]: unknown
}

export interface MlAnalyzeResponse {
  ok: boolean
  text: string
  classification: ClassificationResult
  sentiment: SentimentResult
}

export interface OsConcept {
  id: string
  name: string
  summary: string
  in_project: string
}

export interface ConceptsResponse {
  title: string
  concepts: OsConcept[]
}

export interface LogEntry {
  id?: number
  level: string
  source: string
  message: string
  created_at?: string | null
}

export interface WsEvent {
  id?: string
  type: string
  process?: string | null
  message_id?: string | null
  timestamp?: number
  data?: Record<string, unknown>
}

export interface MetricPoint {
  time: string
  cpu: number
  memory: number
  latency: number
  msgsPerSec: number
}

export type WorkerName = 'alice' | 'bob' | 'charlie'
