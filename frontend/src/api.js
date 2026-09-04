/** API — uses relative URLs, proxied to FastAPI by Vite in dev */
const BASE = import.meta.env.VITE_API_URL || '';

async function apiFetch(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => apiFetch('/health'),

  listIpos: (params = {}) => {
    const q = new URLSearchParams();
    if (params.year) q.set('year', params.year);
    if (params.search) q.set('search', params.search);
    if (params.limit) q.set('limit', params.limit);
    if (params.offset) q.set('offset', params.offset);
    return apiFetch(`/ipos?${q}`);
  },

  getIpo: (id) => apiFetch(`/ipos/${id}`),

  analyseIpo: (id) => apiFetch(`/ipos/${id}/analysis`),

  capitalRecommendation: (availableCapital, skipWatch = false) =>
    apiFetch('/capital/recommendation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ available_capital: availableCapital, skip_watch: skipWatch }),
    }),

  backtestSummary: () => apiFetch('/backtests/summary'),

  backtestPerIpo: (params = {}) => {
    const q = new URLSearchParams();
    if (params.year) q.set('year', params.year);
    if (params.rec) q.set('rec', params.rec);
    if (params.limit) q.set('limit', params.limit || 318);
    return apiFetch(`/backtests/per-ipo?${q}`);
  },

  baseline: () => apiFetch('/backtests/baseline'),

  // ── Live IPO endpoints ──────────────────────────────────────────────────
  liveIpos: (status) => {
    const q = new URLSearchParams();
    if (status) q.set('status', status);
    return apiFetch(`/live/ipos?${q}`);
  },

  liveIpoAnalysis: (ipoId) => apiFetch(`/live/ipos/${ipoId}/analysis`),

  liveSnapshots: (ipoId, field) => {
    const q = new URLSearchParams();
    if (field) q.set('field', field);
    return apiFetch(`/live/ipos/${ipoId}/snapshots?${q}`);
  },

  triggerRefresh: () => apiFetch('/live/refresh', { method: 'POST' }),
};
