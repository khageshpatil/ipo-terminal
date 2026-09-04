import { useState, useEffect, useCallback } from 'react';
import { api } from '../api.js';
import {
  ArrowClockwise, Lightning, Eye, X, CheckCircle,
  Warning, Clock, Spinner,
} from '@phosphor-icons/react';

// ── Helpers ──────────────────────────────────────────────────────────────────

const REC_CONFIG = {
  APPLY:  { color: 'var(--green)',  bg: 'rgba(34,197,94,0.1)',  label: 'APPLY'  },
  WATCH:  { color: 'var(--amber)',  bg: 'rgba(245,158,11,0.1)', label: 'WATCH'  },
  SKIP:   { color: 'var(--red)',    bg: 'rgba(239,68,68,0.1)',  label: 'SKIP'   },
};

const STATUS_COLOR = {
  OPEN:     'var(--green)',
  UPCOMING: 'var(--accent)',
  CLOSED:   'var(--text-2)',
  UNKNOWN:  'var(--text-3)',
};

const QUALITY_ICON = {
  FULL:    <CheckCircle size={12} weight="fill" style={{ color: 'var(--green)' }} />,
  PARTIAL: <Warning     size={12} weight="fill" style={{ color: 'var(--amber)' }} />,
  MINIMAL: <Warning     size={12} weight="fill" style={{ color: 'var(--red)'   }} />,
};

function fmt(v, decimals = 1) {
  if (v === null || v === undefined) return '—';
  return Number(v).toFixed(decimals);
}

function fmtDate(s) {
  if (!s) return '—';
  try {
    return new Date(s).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  } catch { return s; }
}

function fmtTS(s) {
  if (!s) return '—';
  try {
    return new Date(s).toLocaleString('en-IN', { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' });
  } catch { return s; }
}

// ── Sub-components ────────────────────────────────────────────────────────────

function SubBadge({ label, value }) {
  if (value === null || value === undefined) return (
    <span style={{ color: 'var(--text-3)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>—</span>
  );
  return (
    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-1)' }}>
      <span style={{ color: 'var(--text-3)', fontSize: 10 }}>{label} </span>
      {fmt(value)}x
    </span>
  );
}

function RecBadge({ rec }) {
  const cfg = REC_CONFIG[rec] || { color: 'var(--text-2)', bg: 'var(--bg-3)', label: rec || '—' };
  return (
    <span style={{
      background: cfg.bg,
      color: cfg.color,
      border: `1px solid ${cfg.color}33`,
      borderRadius: 'var(--r-sm)',
      padding: '2px 8px',
      fontSize: 11,
      fontFamily: 'var(--font-mono)',
      fontWeight: 600,
      letterSpacing: '0.04em',
    }}>
      {cfg.label}
    </span>
  );
}

function LiveCard({ ipo, onClick }) {
  const rec = ipo.recommendation;
  const cfg = REC_CONFIG[rec] || {};

  return (
    <div
      className={`ipo-card ${rec?.toLowerCase() || ''}`}
      onClick={() => onClick(ipo)}
      style={{ cursor: 'pointer' }}
    >
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontWeight: 600, fontSize: 14, color: 'var(--text-0)',
            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
          }}>
            {ipo.company_name}
          </div>
          {ipo.nse_symbol && (
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent)', marginTop: 2 }}>
              {ipo.nse_symbol}
            </div>
          )}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4 }}>
          <RecBadge rec={rec} />
          <span style={{
            fontSize: 10, fontFamily: 'var(--font-mono)',
            color: STATUS_COLOR[ipo.status] || 'var(--text-3)',
          }}>
            ● {ipo.status || 'UNKNOWN'}
          </span>
        </div>
      </div>

      {/* Dates */}
      <div style={{ display: 'flex', gap: 16, fontSize: 11, color: 'var(--text-2)', fontFamily: 'var(--font-mono)' }}>
        <span>Open {fmtDate(ipo.open_date)}</span>
        <span>Close {fmtDate(ipo.close_date)}</span>
      </div>

      {/* Price + lot */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontSize: 10, color: 'var(--text-3)', fontFamily: 'var(--font-mono)' }}>PRICE</div>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-0)', fontFamily: 'var(--font-mono)' }}>
            {ipo.price_band_low && ipo.price_band_high
              ? `₹${ipo.price_band_low}–${ipo.price_band_high}`
              : ipo.issue_price ? `₹${ipo.issue_price}` : '—'}
          </div>
        </div>
        {ipo.lot_size && (
          <div>
            <div style={{ fontSize: 10, color: 'var(--text-3)', fontFamily: 'var(--font-mono)' }}>LOT</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-0)', fontFamily: 'var(--font-mono)' }}>
              {ipo.lot_size}
            </div>
          </div>
        )}
        {ipo.issue_size_cr && (
          <div>
            <div style={{ fontSize: 10, color: 'var(--text-3)', fontFamily: 'var(--font-mono)' }}>SIZE</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-0)', fontFamily: 'var(--font-mono)' }}>
              ₹{Math.round(ipo.issue_size_cr)} Cr
            </div>
          </div>
        )}
      </div>

      {/* Subscription */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', borderTop: '1px solid var(--border-0)', paddingTop: 10 }}>
        <SubBadge label="QIB" value={ipo.subscription_qib_x} />
        <SubBadge label="NII" value={ipo.subscription_nii_x} />
        <SubBadge label="RET" value={ipo.subscription_retail_x} />
        <SubBadge label="TOT" value={ipo.subscription_total_x} />
      </div>

      {/* GMP + data quality */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {ipo.gmp_inr != null ? (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-2)' }}>
            GMP <span style={{ color: ipo.gmp_inr >= 0 ? 'var(--green)' : 'var(--red)' }}>
              {ipo.gmp_inr >= 0 ? '+' : ''}₹{ipo.gmp_inr}
            </span>
            {ipo.gmp_pct != null && <span style={{ color: 'var(--text-3)' }}> ({fmt(ipo.gmp_pct)}%)</span>}
            <span style={{ color: 'var(--text-3)', fontSize: 9 }}> [unofficial]</span>
          </span>
        ) : <span />}
        <span style={{ display: 'flex', alignItems: 'center', gap: 3, fontSize: 10, color: 'var(--text-3)', fontFamily: 'var(--font-mono)' }}>
          {QUALITY_ICON[ipo.data_quality]} {ipo.data_quality}
        </span>
      </div>
    </div>
  );
}

function DetailPanel({ ipo, onClose }) {
  const [analysis, setAnalysis] = useState(null);
  const [snapshots, setSnapshots] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.liveIpoAnalysis(ipo.ipo_id).catch(() => null),
      api.liveSnapshots(ipo.ipo_id, 'subscription_total_x').catch(() => null),
    ]).then(([a, s]) => {
      setAnalysis(a);
      setSnapshots(s);
      setLoading(false);
    });
  }, [ipo.ipo_id]);

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 200,
      background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 24,
      animation: 'fadeIn 0.2s ease',
    }} onClick={onClose}>
      <div style={{
        background: 'var(--bg-1)', border: '1px solid var(--border-1)',
        borderRadius: 'var(--r-lg)', maxWidth: 560, width: '100%',
        maxHeight: '85vh', overflowY: 'auto',
        padding: 24,
      }} onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-0)' }}>
              {ipo.company_name}
            </div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-3)', marginTop: 4 }}>
              {ipo.ipo_id} · {ipo.source}
            </div>
          </div>
          <button onClick={onClose} style={{
            background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-2)', padding: 4,
          }}>
            <X size={18} />
          </button>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--text-2)' }}>
            <Spinner size={24} style={{ animation: 'spin 0.9s linear infinite' }} />
          </div>
        ) : analysis ? (
          <>
            {/* Decision */}
            <div style={{
              background: 'var(--bg-2)', borderRadius: 'var(--r)', padding: 16, marginBottom: 16,
              border: '1px solid var(--border-0)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <RecBadge rec={analysis.recommendation} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-3)' }}>
                  {analysis.confidence}
                </span>
              </div>
              {analysis.p_positive != null && (
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--text-2)', marginBottom: 4 }}>
                  P(positive listing): <strong style={{ color: 'var(--text-0)' }}>{fmt(analysis.p_positive * 100, 0)}%</strong>
                  {analysis.expected_return_pct != null && (
                    <> · Expected return: <strong style={{ color: 'var(--text-0)' }}>{fmt(analysis.expected_return_pct)}%</strong></>
                  )}
                </div>
              )}
              <ul style={{ margin: 0, padding: '0 0 0 16px' }}>
                {(analysis.reason_lines || []).map((line, i) => (
                  <li key={i} style={{ fontSize: 12, color: 'var(--text-2)', marginTop: 3, fontFamily: 'var(--font-mono)' }}>
                    {line}
                  </li>
                ))}
              </ul>
            </div>

            {/* Missing fields */}
            {analysis.missing_fields?.length > 0 && (
              <div style={{
                fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--amber)',
                background: 'rgba(245,158,11,0.08)', borderRadius: 'var(--r-sm)', padding: '6px 10px',
                marginBottom: 12,
              }}>
                Missing: {analysis.missing_fields.join(', ')}
              </div>
            )}

            {/* Subscription time series */}
            {snapshots?.observations?.length > 0 && (
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-3)', fontFamily: 'var(--font-mono)', marginBottom: 8 }}>
                  TOTAL SUBSCRIPTION — TIME SERIES
                </div>
                {snapshots.observations.slice(-10).map((obs, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between',
                    padding: '4px 0', borderBottom: '1px solid var(--border-0)',
                    fontFamily: 'var(--font-mono)', fontSize: 11,
                  }}>
                    <span style={{ color: 'var(--text-3)' }}>{fmtTS(obs.observed_at)}</span>
                    <span style={{ color: obs.value != null ? 'var(--text-0)' : 'var(--text-3)' }}>
                      {obs.value != null ? `${fmt(obs.value)}x` : '—'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <div style={{ color: 'var(--text-3)', fontSize: 13 }}>Analysis unavailable.</div>
        )}
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function LivePage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [selected, setSelected] = useState(null);

  const load = useCallback(async () => {
    try {
      const res = await api.liveIpos(statusFilter || undefined);
      setData(res);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => { load(); }, [load]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await api.triggerRefresh();
      // Wait briefly then reload
      await new Promise(r => setTimeout(r, 3000));
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setRefreshing(false);
    }
  };

  const ipos = data?.ipos || [];
  const byStatus = {
    OPEN: ipos.filter(i => i.status === 'OPEN'),
    UPCOMING: ipos.filter(i => i.status === 'UPCOMING'),
    CLOSED: ipos.filter(i => i.status === 'CLOSED'),
    OTHER: ipos.filter(i => !['OPEN', 'UPCOMING', 'CLOSED'].includes(i.status)),
  };

  return (
    <div style={{ padding: '28px 24px', maxWidth: 1100, margin: '0 auto' }}>
      {selected && <DetailPanel ipo={selected} onClose={() => setSelected(null)} />}

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-0)', margin: 0 }}>
            <Lightning size={20} weight="fill" style={{ color: 'var(--accent)', marginRight: 8 }} />
            Live IPOs
          </h1>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-3)', marginTop: 4 }}>
            {data?.last_refreshed
              ? `Last refreshed ${fmtTS(data.last_refreshed)} · Source: Chittorgarh`
              : 'Fetching live data…'}
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--amber)', marginTop: 2 }}>
            ⚠ All recommendations are RULE_ESTIMATE — not a validated model prediction
          </div>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            background: 'var(--accent)', color: '#fff', border: 'none',
            padding: '8px 14px', borderRadius: 'var(--r)', cursor: refreshing ? 'not-allowed' : 'pointer',
            fontSize: 12, fontFamily: 'var(--font-mono)', opacity: refreshing ? 0.7 : 1,
          }}
        >
          <ArrowClockwise size={14} style={{ animation: refreshing ? 'spin 0.9s linear infinite' : 'none' }} />
          {refreshing ? 'Refreshing…' : 'Refresh Now'}
        </button>
      </div>

      {/* Status filter */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        {['', 'OPEN', 'UPCOMING', 'CLOSED'].map(s => (
          <button key={s} onClick={() => setStatusFilter(s)} style={{
            padding: '5px 12px', borderRadius: 'var(--r-sm)',
            border: '1px solid var(--border-1)',
            background: statusFilter === s ? 'var(--accent)' : 'var(--bg-2)',
            color: statusFilter === s ? '#fff' : 'var(--text-2)',
            cursor: 'pointer', fontSize: 11, fontFamily: 'var(--font-mono)',
          }}>
            {s || 'ALL'} {s && `(${byStatus[s]?.length ?? 0})`}
          </button>
        ))}
        <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-3)', alignSelf: 'center' }}>
          {ipos.length} IPOs tracked
        </span>
      </div>

      {/* Content */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: 80, color: 'var(--text-2)' }}>
          <div style={{
            width: 40, height: 40, borderRadius: '50%',
            border: '2px solid var(--border-1)', borderTopColor: 'var(--accent)',
            animation: 'spin 0.9s linear infinite', margin: '0 auto 16px',
          }} />
          Loading live IPO data…
        </div>
      ) : error ? (
        <div style={{
          background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
          borderRadius: 'var(--r)', padding: 20, color: 'var(--red)', fontFamily: 'var(--font-mono)', fontSize: 13,
        }}>
          {error}<br />
          <span style={{ fontSize: 11, color: 'var(--text-3)' }}>
            Try clicking "Refresh Now" — the backend may need a moment to fetch live data.
          </span>
        </div>
      ) : ipos.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: 80,
          color: 'var(--text-3)', fontFamily: 'var(--font-mono)', fontSize: 13,
        }}>
          <Clock size={32} style={{ marginBottom: 12 }} />
          <div>No live IPO data yet.</div>
          <div style={{ fontSize: 11, marginTop: 8 }}>
            Click "Refresh Now" to fetch current IPOs from Chittorgarh.
          </div>
        </div>
      ) : (
        <>
          {/* OPEN section — most important */}
          {byStatus.OPEN.length > 0 && !statusFilter && (
            <div style={{ marginBottom: 28 }}>
              <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--green)', marginBottom: 12, letterSpacing: '0.08em' }}>
                ● OPEN NOW ({byStatus.OPEN.length})
              </div>
              <div className="ipo-grid">
                {byStatus.OPEN.map(ipo => <LiveCard key={ipo.ipo_id} ipo={ipo} onClick={setSelected} />)}
              </div>
            </div>
          )}

          {/* UPCOMING */}
          {byStatus.UPCOMING.length > 0 && !statusFilter && (
            <div style={{ marginBottom: 28 }}>
              <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--accent)', marginBottom: 12, letterSpacing: '0.08em' }}>
                ◦ UPCOMING ({byStatus.UPCOMING.length})
              </div>
              <div className="ipo-grid">
                {byStatus.UPCOMING.map(ipo => <LiveCard key={ipo.ipo_id} ipo={ipo} onClick={setSelected} />)}
              </div>
            </div>
          )}

          {/* Filtered view */}
          {statusFilter && (
            <div className="ipo-grid">
              {ipos.map(ipo => <LiveCard key={ipo.ipo_id} ipo={ipo} onClick={setSelected} />)}
            </div>
          )}

          {/* CLOSED (collapsed) */}
          {!statusFilter && byStatus.CLOSED.length > 0 && (
            <div style={{ marginBottom: 28 }}>
              <div style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--text-3)', marginBottom: 12, letterSpacing: '0.08em' }}>
                ✓ RECENTLY CLOSED ({byStatus.CLOSED.length})
              </div>
              <div className="ipo-grid">
                {byStatus.CLOSED.map(ipo => <LiveCard key={ipo.ipo_id} ipo={ipo} onClick={setSelected} />)}
              </div>
            </div>
          )}
        </>
      )}

      {/* Data note */}
      <div style={{
        marginTop: 40, padding: 12, borderRadius: 'var(--r-sm)',
        background: 'var(--bg-2)', border: '1px solid var(--border-0)',
        fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)', lineHeight: 1.8,
      }}>
        Source: Chittorgarh · RULE_ESTIMATE strategy (not ML) · GMP is unofficial grey market data ·
        Each refresh appends timestamped observations to the prospective training dataset
      </div>
    </div>
  );
}
