import { useEffect, useRef, useState } from 'react';

/**
 * Generic polling hook.
 *
 * @param fetchFn  A **stable** function (wrap with `useCallback`) that returns
 *                 a promise resolving to data of type `T`.
 * @param intervalMs  Polling interval in milliseconds.
 * @returns `{ data, loading, error, refetch }`
 */
export function usePolling<T>(
  fetchFn: () => Promise<T>,
  intervalMs: number,
): {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
} {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Keep a ref to the latest fetchFn so the interval never captures a stale closure.
  const fetchRef = useRef(fetchFn);
  fetchRef.current = fetchFn;

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const execute = async () => {
    try {
      const result = await fetchRef.current();
      setData(result);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    execute();

    // Set up interval
    intervalRef.current = setInterval(execute, intervalMs);

    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
      }
    };
    // Re-run only when intervalMs changes. fetchRef ensures the latest fetchFn
    // is always used without needing it in the dependency array.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs]);

  const refetch = async () => {
    setLoading(true);
    await execute();
  };

  return { data, loading, error, refetch };
}
