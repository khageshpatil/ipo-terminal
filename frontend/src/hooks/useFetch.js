import { useState, useEffect } from 'react';
import { api } from '../api.js';

/** Generic data fetcher hook */
export function useFetch(fn, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fn().then(d => { if (!cancelled) { setData(d); setLoading(false); } })
        .catch(e => { if (!cancelled) { setError(e.message); setLoading(false); } });
    return () => { cancelled = true; };
  }, deps);

  return { data, loading, error };
}

export function useIpos(params = {}) {
  return useFetch(
    () => api.listIpos(params),
    [params.year, params.search, params.limit, params.offset]
  );
}

export function useIpoAnalysis(id) {
  return useFetch(() => api.analyseIpo(id), [id]);
}

export function useBacktestSummary() {
  return useFetch(() => api.backtestSummary(), []);
}

export function useBacktestPerIpo(params = {}) {
  return useFetch(() => api.backtestPerIpo(params), [params.year, params.rec]);
}

export function useBaseline() {
  return useFetch(() => api.baseline(), []);
}
