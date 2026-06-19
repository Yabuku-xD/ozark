import { useCallback, useEffect, useState } from "react";

export function useApi(fetcher) {
  const [data, setData] = useState(undefined);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(
    async (...args) => {
      setLoading(true);
      setError(null);
      try {
        const result = await fetcher(...args);
        setData(result);
        return result;
      } catch (e) {
        setError(e);
        throw e;
      } finally {
        setLoading(false);
      }
    },
    [fetcher],
  );

  const reset = useCallback(() => {
    setData(undefined);
    setError(null);
    setLoading(false);
  }, []);

  return { data, error, loading, run, reset };
}

export function useAutoRefresh(fetcher, interval = 3000, deps = []) {
  const { data, error, loading, run, reset } = useApi(fetcher);

  useEffect(() => {
    let mounted = true;
    let id;

    const tick = async () => {
      if (!mounted) return;
      try {
        await run();
      } catch {
        // handled by hook
      }
    };

    tick();
    id = setInterval(tick, interval);
    return () => {
      mounted = false;
      clearInterval(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, error, loading, run, reset };
}
