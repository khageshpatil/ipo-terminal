import { motion } from 'motion/react';
import { useIpoAnalysis } from '../hooks/useFetch.js';
import {
  LoadingFill, ErrorFill, RecPill, QBadge, Notice, Surface, BackBtn,
  fmtInr, fmtX, fmtPct, ReturnText
} from '../components/shared.jsx';

const FADE = {
  hidden: { opacity: 0, y: 12 },
  visible: i => ({
    opacity: 1, y: 0,
    transition: { duration: 0.38, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] },
  }),
};

function FadeIn({ i = 0, children, style }) {
  return (
    <motion.div
      custom={i}
      variants={FADE}
      initial="hidden"
      animate="visible"
      style={style}
    >
      {children}
    </motion.div>
  );
}

export default function IpoDetailPage({ ipoId, onBack }) {
  const { data: ipo, loading, error } = useIpoAnalysis(ipoId);

  if (loading) return <div className="page"><LoadingFill /></div>;
  if (error)   return <div className="page"><ErrorFill message={error} /></div>;
  if (!ipo)    return null;

  const recClass = ipo.recommendation?.toLowerCase();
  const ret = ipo.listing_return_pct;

  return (
    <div className="page">
      {/* Header */}
      <FadeIn i={0}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14, marginBottom: 22 }}>
          <BackBtn onClick={onBack} />
          <div>
            <h1 className="ph-title">{ipo.company_name}</h1>
            <p className="ph-sub">
              {ipo.nse_symbol}
              {ipo.listing_date ? ` · Listed ${ipo.listing_date}` : ''}
              {' '}· <QBadge quality={ipo.listing_open_quality} />
            </p>
          </div>
        </div>
      </FadeIn>

      <Notice text="All estimates are RULE_ESTIMATE — rule-based priors, not statistically validated predictions." />

      <div className="detail-layout">
        {/* ── Main column ── */}
        <div className="detail-col">
          {/* Decision hero */}
          <FadeIn i={1}>
            <div className={`decision-hero ${recClass}`}>
              <div className="decision-rec-row">
                <div>
                  <div className={`decision-rec-text ${recClass}`}>
                    {rec_display(ipo.recommendation)}
                  </div>
                  <div style={{ marginTop: 8 }}>
                    <span className="decision-confidence">{ipo.confidence}</span>
                  </div>
                </div>

                {ret != null && (
                  <div className="decision-actual-return">
                    <div className="decision-actual-label">Actual listing return</div>
                    <div
                      className="decision-actual-value"
                      style={{ color: ret > 0 ? 'var(--green)' : 'var(--red)' }}
                    >
                      {ret > 0 ? '+' : ''}{ret.toFixed(2)}%
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-2)', marginTop: 4 }}>
                      Open {fmtInr(ipo.listing_open_price)} vs Issue {fmtInr(ipo.issue_price)}
                    </div>
                  </div>
                )}
              </div>

              {/* Economics */}
              <div className="stat-grid stat-grid-4" style={{ marginBottom: 20 }}>
                <StatBox
                  label="P(positive listing)"
                  value={ipo.p_positive != null ? `${(ipo.p_positive * 100).toFixed(0)}%` : '—'}
                  colorClass={ipo.p_positive > 0.65 ? 'green' : ipo.p_positive > 0.5 ? 'amber' : 'red'}
                  sub="RULE_ESTIMATE"
                />
                <StatBox
                  label="Expected return"
                  value={ipo.expected_return_pct != null ? fmtPct(ipo.expected_return_pct, true) : '—'}
                  colorClass={ipo.expected_return_pct > 0 ? 'green' : 'red'}
                  sub="RULE_ESTIMATE"
                />
                <StatBox
                  label="P(allotment)"
                  value={ipo.p_allotment != null ? `${(ipo.p_allotment * 100).toFixed(0)}%` : '—'}
                  sub="per application"
                />
                <StatBox
                  label="E[profit/app]"
                  value={ipo.expected_profit_per_application != null ? fmtInr(ipo.expected_profit_per_application) : '—'}
                  colorClass={ipo.expected_profit_per_application > 0 ? 'green' : ''}
                  sub="RULE_ESTIMATE"
                />
              </div>

              {/* Reasons */}
              {ipo.reason_lines?.length > 0 && (
                <div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-2)', marginBottom: 8 }}>
                    Signal drivers
                  </div>
                  <div className="reason-list">
                    {ipo.reason_lines.map((r, i) => (
                      <div key={i} className="reason-row">
                        <span className="reason-icon" style={{ fontSize: 12 }}>›</span>
                        <span>{r}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </FadeIn>

          {/* Subscription */}
          <FadeIn i={2}>
            <Surface label="Subscription">
              {ipo.subscription_total_x ? (
                <SubVis ipo={ipo} />
              ) : (
                <span style={{ color: 'var(--text-2)', fontSize: 12 }}>No subscription data</span>
              )}
            </Surface>
          </FadeIn>

          {/* Market context */}
          <FadeIn i={3}>
            <Surface label="Market Context">
              {ipo.market_regime ? (
                <div className="stat-grid stat-grid-4">
                  <StatBox
                    label="Regime"
                    value={ipo.market_regime}
                    colorClass={ipo.market_regime === 'BULL' ? 'green' : ipo.market_regime === 'BEAR' ? 'red' : ''}
                  />
                  <StatBox
                    label="India VIX"
                    value={ipo.market_india_vix_close?.toFixed(1) ?? '—'}
                    colorClass={ipo.market_india_vix_close > 25 ? 'red' : 'green'}
                  />
                  <StatBox
                    label="Nifty 20D"
                    value={ipo.market_nifty_return_20d != null
                      ? fmtPct(ipo.market_nifty_return_20d * 100, true) : '—'}
                    colorClass={ipo.market_nifty_return_20d > 0 ? 'green' : 'red'}
                  />
                  <StatBox
                    label="Nifty 5D"
                    value={ipo.market_nifty_return_5d != null
                      ? fmtPct(ipo.market_nifty_return_5d * 100, true) : '—'}
                    colorClass={ipo.market_nifty_return_5d > 0 ? 'green' : 'red'}
                  />
                </div>
              ) : (
                <span style={{ color: 'var(--text-2)', fontSize: 12 }}>
                  Market features not available (close date missing from data source).
                </span>
              )}
            </Surface>
          </FadeIn>
        </div>

        {/* ── Sidebar column ── */}
        <div className="detail-col">
          <FadeIn i={2}>
            <Surface label="Issue Details">
              <IssueTable ipo={ipo} />
            </Surface>
          </FadeIn>

          <FadeIn i={3}>
            <Surface label="Data Quality">
              <RiskTable ipo={ipo} />
            </Surface>
          </FadeIn>
        </div>
      </div>
    </div>
  );
}

function rec_display(rec) {
  return {
    APPLY: '● APPLY',
    SKIP:  '○ SKIP',
    WATCH: '◐ WATCH',
  }[rec] || rec;
}

function StatBox({ label, value, colorClass = '', sub }) {
  return (
    <div className="stat-box">
      <div className="stat-box-label">{label}</div>
      <div className={`stat-box-value ${colorClass}`}>{value}</div>
      {sub && <div className="stat-box-sub">{sub}</div>}
    </div>
  );
}

function SubVis({ ipo }) {
  const rows = [
    { label: 'QIB',    value: ipo.subscription_qib_x,    color: '#6366f1' },
    { label: 'NII',    value: ipo.subscription_nii_x,    color: '#a78bfa' },
    { label: 'Retail', value: ipo.subscription_retail_x, color: '#34d399' },
    { label: 'Total',  value: ipo.subscription_total_x,  color: 'var(--text-2)' },
  ].filter(r => r.value != null);

  const max = Math.max(...rows.map(r => r.value), 1);

  return (
    <div className="sub-vis">
      {rows.map(({ label, value, color }) => (
        <div key={label} className="sub-vis-row">
          <span className="sub-vis-label">{label}</span>
          <div className="sub-vis-track">
            <div
              className="sub-vis-fill"
              style={{ width: `${Math.min((value / max) * 100, 100)}%`, background: color }}
            />
          </div>
          <span className="sub-vis-value" style={{ color }}>{value.toFixed(1)}x</span>
        </div>
      ))}
    </div>
  );
}

function IssueTable({ ipo }) {
  const rows = [
    { label: 'Issue price',   value: fmtInr(ipo.issue_price) },
    { label: 'Lot size',      value: ipo.lot_size ? `${ipo.lot_size} shares` : '—' },
    { label: 'Capital / lot', value: ipo.capital_required_per_lot ? fmtInr(ipo.capital_required_per_lot) : fmtInr(ipo.issue_price) + '*' },
    { label: 'Issue size',    value: ipo.issue_size_cr ? `₹${Number(ipo.issue_size_cr).toLocaleString('en-IN')} Cr` : '—' },
    { label: 'OFS',           value: ipo.ofs_cr ? `₹${Number(ipo.ofs_cr).toLocaleString('en-IN')} Cr` : '—' },
    { label: 'OFS ratio',     value: ipo.ofs_pct != null ? `${(ipo.ofs_pct * 100).toFixed(0)}%` : '—' },
  ];

  return (
    <table className="kv-table">
      <tbody>
        {rows.map(({ label, value }) => (
          <tr key={label}>
            <td className="kv-lbl">{label}</td>
            <td className="kv-val">{value}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function RiskTable({ ipo }) {
  const rows = [
    { label: 'Price data',   value: <QBadge quality={ipo.listing_open_quality} />, warn: ipo.listing_open_quality !== 'PRIMARY_VERIFIED' },
    { label: 'Market data',  value: ipo.market_regime ? 'Available' : 'Unavailable', warn: !ipo.market_regime },
    { label: 'GMP',          value: 'Excluded from model', warn: true },
    { label: 'Intraday sub', value: 'Excluded from model', warn: true },
    { label: 'Basis',        value: ipo.confidence },
  ];

  return (
    <table className="kv-table">
      <tbody>
        {rows.map(({ label, value, warn }) => (
          <tr key={label}>
            <td className="kv-lbl">{label}</td>
            <td className="kv-val" style={{ color: warn ? 'var(--amber)' : undefined }}>
              {typeof value === 'string' ? value : value}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
