import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type Dispatch,
  type SetStateAction,
} from 'react'

interface UseApiOptions<T> {
  immediate?: boolean
  initialData?: T | null
  deps?: unknown[]
}

interface UseApiResult<T> {
  data: T | null
  error: string | null
  loading: boolean
  refetch: () => Promise<T | null>
  setData: Dispatch<SetStateAction<T | null>>
}

export function useApi<T>(
  fetcher: () => Promise<T>,
  options: UseApiOptions<T> = {},
): UseApiResult<T> {
  const { immediate = true, initialData = null, deps = [] } = options
  const [data, setData] = useState<T | null>(initialData)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(immediate)
  const fetcherRef = useRef(fetcher)

  useEffect(() => {
    fetcherRef.current = fetcher
  }, [fetcher])

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetcherRef.current()
      setData(result)
      return result
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Request failed'
      setError(message)
      return null
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    if (!immediate) return
    void refetch()
  }, [immediate, refetch])

  return { data, error, loading, refetch, setData }
}

export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs: number,
  enabled = true,
) {
  const api = useApi(fetcher, { immediate: enabled })

  useEffect(() => {
    if (!enabled || intervalMs <= 0) return
    const id = window.setInterval(() => {
      void api.refetch()
    }, intervalMs)
    return () => window.clearInterval(id)
  }, [enabled, intervalMs, api.refetch])

  return api
}
