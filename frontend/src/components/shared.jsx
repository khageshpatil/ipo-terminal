/**
 * Shared components — v2 (design-taste-frontend applied)
 * Uses: Phosphor icons, motion/react whileInView reveals
 */
import { House, ChartBar, CurrencyDollar, TrendUp, ArrowLeft,
         Warning, CheckCircle, XCircle, Circle, CaretRight } from '@phosphor-icons/react';

// ── Loading skeleton ────────────────────────────────────────
export function IpoCardSkeleton() {
  return (
    <div className="ipo-card-skeleton">
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <div className="skeleton" style={{ width: 140, height: 14, marginBottom: 8 }} />
          <div className="skeleton" style={{ width: 70, height: 10 }} />
        </div>
        <div className="skeleton" style={{ width: 60, height: 22, borderRadius: 999 }} />
      </div>
      <div>
        <div className="skeleton" style={{ width: 80, height: 22, marginBottom: 6 }} />
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {[0,1,2].map(i => (
          <div key={i} style={{ display: 'grid', gridTemplateColumns: '40px 1fr 44px', gap: 8, alignItems: 'center' }}>
            <div className="skeleton" style={{ height: 10 }} />
            <div className="skeleton" style={{ height: 3 }} />
            <div className="skeleton" style={{ height: 10 }} />
          </div>
        ))}
      </div>
      <div style={{ paddingTop: 10, borderTop: '1px solid var(--border-0)', display: 'flex', justifyContent: 'space-between' }}>
        <div className="skeleton" style={{ width: 70, height: 20 }} />
        <div className="skeleton" style={{ width: 50, height: 10 }} />
      </div>
    </div>
  );
}

export function GridSkeleton({ n = 6 }) {
  return (
    <div className="ipo-grid">
      {Array.from({ length: n }).map((_, i) => <IpoCardSkeleton key={i} />)}
    </div>
  );
}

// ── Loading / error / empty ──────────────────────────────────
export function LoadingFill() {
  return (
    <div className="loading-fill">
      <div className="loading-ring" />
      <span>Loading…</span>
    </div>
  );
}

export function ErrorFill({ message }) {
  return (
    <div className="loading-fill">
      <XCircle size={32} color="var(--red)" weight="fill" />
      <span style={{ color: 'var(--red)' }}>{message || 'Failed to load'}</span>
    </div>
  );
}

export function EmptyFill({ message }) {
  return (
    <div className="empty-fill">{message || 'No data'}</div>
  );
}

// ── Recommendation pill ──────────────────────────────────────
const REC_ICON = {
  APPLY: <CheckCircle size={12} weight="fill" />,
  SKIP:  <XCircle    size={12} weight="fill" />,
  WATCH: <Circle     size={12} weight="fill" />,
};

export function RecPill({ rec }) {
  const cls = {
    APPLY: 'rec-pill rec-apply',
    SKIP:  'rec-pill rec-skip',
    WATCH: 'rec-pill rec-watch',
  }[rec] || 'rec-pill';

  return (
    <span className={cls}>
      {REC_ICON[rec]}
      {rec}
    </span>
  );
}

// ── Quality badge ────────────────────────────────────────────
export function QBadge({ quality }) {
  const cls = {
    PRIMARY_VERIFIED:   'q-badge q-primary',
    SECONDARY_VERIFIED: 'q-badge q-secondary',
    MISSING:            'q-badge q-missing',
  }[quality] || 'q-badge q-missing';

  const label = {
    PRIMARY_VERIFIED:   'NSE',
    SECONDARY_VERIFIED: 'Aggregator',
    MISSING:            'Missing',
  }[quality] || quality;

  return <span className={cls}>{label}</span>;
}

// ── Formatters ───────────────────────────────────────────────
export function fmtInr(n) {
  if (n == null) return '—';
  return '₹' + Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 });
}

export function fmtX(n) {
  if (n == null) return '—';
  return n.toFixed(1) + 'x';
}

export function fmtPct(n, showSign = false) {
  if (n == null) return '—';
  const sign = showSign && n > 0 ? '+' : '';
  return `${sign}${n.toFixed(2)}%`;
}

export function ReturnText({ pct, size }) {
  if (pct == null) return <span style={{ color: 'var(--text-2)' }}>—</span>;
  const cls = pct > 0 ? 'pos' : pct < 0 ? 'neg' : 'muted';
  const sign = pct > 0 ? '+' : '';
  return (
    <span className={`mono ${cls}`} style={size ? { fontSize: size } : {}}>
      {sign}{pct.toFixed(2)}%
    </span>
  );
}

// ── Warning notice ───────────────────────────────────────────
export function Notice({ text }) {
  return (
    <div className="notice notice-warn">
      <Warning size={14} weight="fill" className="notice-icon" />
      <span>{text}</span>
    </div>
  );
}

// ── Section surface ──────────────────────────────────────────
export function Surface({ label, children, style }) {
  return (
    <div className="surface" style={style}>
      {label && <div className="surface-label">{label}</div>}
      {children}
    </div>
  );
}

// ── Subscription bar row ─────────────────────────────────────
export function SubBar({ label, value, max, colorClass }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div className="sub-row">
      <span className="sub-lbl">{label}</span>
      <div className="sub-track">
        <div className={`sub-fill ${colorClass}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="sub-val">{fmtX(value)}</span>
    </div>
  );
}

// ── Back button ──────────────────────────────────────────────
export function BackBtn({ onClick }) {
  return (
    <button className="btn-back" onClick={onClick}>
      <ArrowLeft size={13} />
      Back
    </button>
  );
}

// ── Phosphor icon exports for nav ────────────────────────────
export { House, ChartBar, CurrencyDollar, TrendUp, CaretRight };
