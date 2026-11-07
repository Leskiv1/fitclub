import { useCallback, useEffect, useState } from 'react';

// Loads data with a memoized loader (wrap it in useCallback with its own dependencies).
// `loading` is derived — true until the result belongs to the current loader and reload count —
// so the effect never sets state synchronously. Old data stays visible while new data loads.
export default function useApi(loader) {
  const [version, setVersion] = useState(0);
  const [result, setResult] = useState({ loader: null, version: -1, data: undefined, error: null });

  useEffect(() => {
    let active = true;
    loader().then(
      (data) => active && setResult({ loader, version, data, error: null }),
      (error) => active && setResult((prev) => ({ loader, version, data: prev.data, error })),
    );
    return () => {
      active = false;
    };
  }, [loader, version]);

  const reload = useCallback(() => setVersion((v) => v + 1), []);
  const loading = result.loader !== loader || result.version !== version;

  return { data: result.data, error: result.error, loading, reload };
}
