import type {
  ChatMessage,
  ConceptsResponse,
  ExperimentInfo,
  ExperimentResult,
  IpcMechanism,
  IpcMetrics,
  IpcStatus,
  LogEntry,
  MlAnalyzeResponse,
  PersistedExperimentResult,
  ProcessInfo,
  SystemStats,
} from '../types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = (await res.json()) as { detail?: string | unknown }
      if (typeof body.detail === 'string') detail = body.detail
      else if (body.detail != null) detail = JSON.stringify(body.detail)
    } catch {
      /* ignore parse errors */
    }
    throw new Error(detail || `Request failed (${res.status})`)
  }

  return res.json() as Promise<T>
}

export const api = {
  getProcesses: () =>
    request<{ processes: ProcessInfo[]; managed: string[] }>('/api/processes'),

  startProcess: (name: string) =>
    request<{ ok: boolean; process: ProcessInfo }>(`/api/processes/${name}/start`, {
      method: 'POST',
    }),

  stopProcess: (name: string) =>
    request<{ ok: boolean; process: ProcessInfo }>(`/api/processes/${name}/stop`, {
      method: 'POST',
    }),

  restartProcess: (name: string) =>
    request<{ ok: boolean; process: ProcessInfo }>(`/api/processes/${name}/restart`, {
      method: 'POST',
    }),

  sendMessage: (body: {
    sender: string
    receiver: string
    content: string
    mechanism?: string
  }) =>
    request<{ ok: boolean; message: ChatMessage }>('/api/messages/send', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  getMessages: () =>
    request<{ messages: ChatMessage[]; persisted: ChatMessage[] }>('/api/messages'),

  getMessage: (id: string) =>
    request<{ message: ChatMessage }>(`/api/messages/${id}`),

  getIpcStatus: () => request<IpcStatus>('/api/ipc/status'),

  getIpcMetrics: () => request<IpcMetrics>('/api/ipc/metrics'),

  setMechanism: (mechanism: IpcMechanism) =>
    request<{ ok: boolean; mechanism: string; allowed: string[] }>('/api/ipc/mechanism', {
      method: 'POST',
      body: JSON.stringify({ mechanism }),
    }),

  getExperiments: () =>
    request<{ experiments: ExperimentInfo[] }>('/api/experiments'),

  runExperiment: (experiment_id: string) =>
    request<{ ok: boolean; result: ExperimentResult }>('/api/experiments/run', {
      method: 'POST',
      body: JSON.stringify({ experiment_id }),
    }),

  getExperimentResults: () =>
    request<{ results: ExperimentResult[]; persisted: PersistedExperimentResult[] }>(
      '/api/experiments/results',
    ),

  analyzeText: (text: string) =>
    request<MlAnalyzeResponse>('/api/ml/analyze', {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),

  getSystemStats: () => request<SystemStats>('/api/system/stats'),

  getLogs: (limit = 100) =>
    request<{ logs: LogEntry[]; persisted: LogEntry[] }>(`/api/logs?limit=${limit}`),

  getConcepts: () => request<ConceptsResponse>('/api/concepts'),
}

export function getWsUrl(): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws`
}
