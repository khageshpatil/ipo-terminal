import { useState } from 'react';
import { motion } from 'motion/react';
import { useBacktestSummary, useBacktestPerIpo, useBaseline } from '../hooks/useFetch.js';
import { LoadingFill, ErrorFill, Notice, RecPill, QBadge } from '../components/shared.jsx';

const YEARS = [2024, 2023, 2022, 2021, 2020, 2019, 2018];

export default function BacktestPage() {
  const { data: summary, loading: sl, error: se } = useBacktestSummary();
  const { data: baseline } = useBaseline();
  const [year, setYear] = useState('');
  const [rec,  setRec]  = useState('');

  const { data: perIpo, loading: pl } = useBacktestPerIpo({
    year:   year  || undefined,
    rec:    rec   || undefined,
    limit: 318,
  });

  if (sl) return <div className="page"><LoadingFill /></div>;
  if (se) return <div className="page"><ErrorFill message={se} /></div>;

  const strats  = summary?.strategies || [];
  const apply   = strats.find(s => s.strategy_name?.includes('Apply-Every'));
  const subOnly = strats.find(s => s.strategy_name?.includes('Sub-Only'));
  const ruleV1  = strats.find(s => s.strategy_name?.includes('Rule'));

  return (
    <div className="page">
      <div className="ph">
        <h1 className="ph-title">Backtest Results</h1>
        <p className="ph-sub">Three-strategy comparison · 318 Mainboard IPOs 2018–2024</p>
      </div>

      <Notice text={
        summary?.dataset_note ||
        'IN-SAMPLE. Subscription data observed ex-post. Not forward performance evidence.'
      } />

      {/* Base rate */}
      {baseline && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.16,1,0.3,1] }}
          className="surface"
          style={{ marginBottom: 16 }}
        >
          <div className="surface-label">Historical Base Rate</div>
          <div className="stat-grid stat-grid-4">
            <StatBox label="Total IPOs"            value={baseline.total_ipos}              sub="2018-2024 Mainboard" />
            <StatBox label="Positive listing rate" value={`${baseline.positive_rate_pct}%`} colorClass="green" sub={`${baseline.positive_listings} of ${baseline.usable_ipos}`} />
            <StatBox label="Mean return"           value={`+${baseline.mean_return_pct}%`}  colorClass="green" sub="per application" />
            <StatBox label="Median return"         value={`+${baseline.median_return_pct}%`} />
          </div>
          <div style={{ marginTop: 14, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-2)', display: 'flex', gap: 16 }}>
            <span><span className="pos">●</span> 244 NSE Verified</span>
            <span><span style={{ color: 'var(--accent)' }}>●</span> 74 Aggregator</span>
            <span>0 missing prices</span>
          </div>
        </motion.div>
      )}

      {/* Strategy comparison */}
      <div className="strategy-grid">
        <StratCard strategy={apply}   label="Apply-Every-IPO"   desc="Baseline — apply to all IPOs"    accent="var(--text-2)"  i={0} />
        <StratCard strategy={subOnly} label="Subscription-Only" desc="Apply if total sub >= 10x"       accent="var(--amber)"   i={1} />
        <StratCard strategy={ruleV1}  label="Rule-V1"           desc="Sub + market + structure filter" accent="var(--green)"   i={2} isWinner />
      </div>

      {/* Interpretation */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="surface"
        style={{ marginBottom: 16, borderColor: 'var(--amber-border)', background: 'var(--amber-bg)' }}
      >
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--amber)', marginBottom: 10 }}>
          Interpretation
        </div>
        <div style={{ fontSize: 12.5, color: 'var(--text-1)', lineHeight: 1.7 }}>
          Rule-V1 shows 100% hit rate because <strong>subscription data is observed ex-post</strong>.
          These figures show historical correlation, not predictive power.
          The strategy framework is sound — high subscription strongly correlates with positive listings in-sample.
          The real test is forward, live-data performance.
        </div>
      </motion.div>

      {/* Year breakdown */}
      {ruleV1?.yearly && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.15 }}
          className="surface"
          style={{ marginBottom: 16 }}
        >
          <div className="surface-label">Year Breakdown — Rule-V1 APPLY Decisions</div>
          <YearTable yearly={ruleV1.yearly} baselineYearly={baseline?.by_year} />
        </motion.div>
      )}

      {/* Per-IPO table */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.2 }}
        className="surface"
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div className="surface-label" style={{ margin: 0 }}>Per-IPO Records (Rule-V1)</div>
          <div style={{ display: 'flex', gap: 8 }}>
            <select className="fi" value={year} onChange={e => setYear(e.target.value)}>
              <option value="">All years</option>
              {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
            </select>
            <select className="fi" value={rec} onChange={e => setRec(e.target.value)}>
              <option value="">All decisions</option>
              <option value="APPLY">APPLY</option>
              <option value="SKIP">SKIP</option>
              <option value="WATCH">WATCH</option>
            </select>
          </div>
        </div>
        {pl ? <LoadingFill /> : <PerIpoTable records={perIpo || []} />}
      </motion.div>
    </div>
  );
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

function StratCard({ strategy, label, desc, accent, i, isWinner }) {
  if (!strategy) return null;
  const ap  = strategy.applied || {};
  const hit = ap.hit_rate_pct;
  const mn  = ap.mean_pct;

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] }}
      className={`strategy-card ${isWinner ? 'winner' : ''}`}
    >
      <div className="sc-label" style={{ color: accent }}>{label}</div>
      <div style={{ fontSize: 11, color: 'var(--text-2)', marginBottom: 14, fontFamily: 'var(--font-mono)' }}>{desc}</div>

      <div
        className="sc-hitrate"
        style={{ color: hit >= 80 ? 'var(--green)' : hit >= 60 ? 'var(--amber)' : 'var(--red)' }}
      >
        {hit != null ? `${hit}%` : '—'}
      </div>
      <div className="sc-hitrate-lbl">hit rate on APPLY decisions</div>

      <div className="sc-row">
        <span className="sc-row-label">APPLY / SKIP / WATCH</span>
        <span className="sc-row-val">{strategy.n_apply} / {strategy.n_skip} / {strategy.n_watch}</span>
      </div>
      <div className="sc-row">
        <span className="sc-row-label">Apply rate</span>
        <span className="sc-row-val">{strategy.apply_rate_pct}%</span>
      </div>
      <div className="sc-row">
        <span className="sc-row-label">Mean return</span>
        <span className="sc-row-val" style={{ color: mn > 0 ? 'var(--green)' : 'var(--red)' }}>
          {mn != null ? `${mn > 0 ? '+' : ''}${mn.toFixed(1)}%` : '—'}
        </span>
      </div>
      <div className="sc-row">
        <span className="sc-row-label">Median</span>
        <span className="sc-row-val">
          {ap.median_pct != null ? `${ap.median_pct > 0 ? '+' : ''}${ap.median_pct.toFixed(1)}%` : '—'}
        </span>
      </div>
      <div className="sc-row">
        <span className="sc-row-label">Best / Worst</span>
        <span className="sc-row-val" style={{ fontSize: 11 }}>
          {ap.max_gain_pct != null ? `+${ap.max_gain_pct.toFixed(0)}%` : '—'}
          {' / '}
          {ap.max_loss_pct != null ? `${ap.max_loss_pct.toFixed(0)}%` : '—'}
        </span>
      </div>
    </motion.div>
  );
}

function YearTable({ yearly, baselineYearly }) {
  const years = Object.keys(yearly).map(Number).sort();
  return (
    <table className="dt">
      <thead>
        <tr>
          <th>Year</th>
          <th style={{ textAlign: 'right' }}>Applied</th>
          <th style={{ textAlign: 'right' }}>Hit rate</th>
          <th style={{ textAlign: 'right' }}>Mean return</th>
          <th style={{ textAlign: 'right' }}>Median</th>
          <th style={{ textAlign: 'right' }}>Baseline</th>
          <th style={{ textAlign: 'right' }}>Advantage</th>
        </tr>
      </thead>
      <tbody>
        {years.map(y => {
          const yr  = yearly[y] || {};
          const bl  = baselineYearly?.[y] || {};
          const adv = yr.hit_rate_pct != null && bl.positive_rate_pct != null
            ? yr.hit_rate_pct - bl.positive_rate_pct : null;
          return (
            <tr key={y}>
              <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-0)', fontWeight: 700 }}>{y}</td>
              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{yr.n}</td>
              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: yr.hit_rate_pct >= 80 ? 'var(--green)' : 'var(--amber)' }}>
                {yr.hit_rate_pct != null ? `${yr.hit_rate_pct}%` : '—'}
              </td>
              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: yr.mean_pct > 0 ? 'var(--green)' : 'var(--red)' }}>
                {yr.mean_pct != null ? `${yr.mean_pct > 0 ? '+' : ''}${yr.mean_pct.toFixed(1)}%` : '—'}
              </td>
              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                {yr.median_pct != null ? `${yr.median_pct > 0 ? '+' : ''}${yr.median_pct.toFixed(1)}%` : '—'}
              </td>
              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--text-2)' }}>
                {bl.positive_rate_pct != null ? `${bl.positive_rate_pct}%` : '—'}
              </td>
              <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 700, color: adv > 0 ? 'var(--green)' : adv < 0 ? 'var(--red)' : 'var(--text-2)' }}>
                {adv != null ? `${adv > 0 ? '+' : ''}${adv.toFixed(1)}pp` : '—'}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function PerIpoTable({ records }) {
  if (!records.length) return <div className="empty-fill">No records match filters</div>;
  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="dt">
        <thead>
          <tr>
            <th>Company</th>
            <th>Symbol</th>
            <th style={{ textAlign: 'right' }}>Year</th>
            <th>Decision</th>
            <th style={{ textAlign: 'right' }}>Total Sub</th>
            <th style={{ textAlign: 'right' }}>Listing Return</th>
            <th style={{ textAlign: 'right' }}>Outcome</th>
            <th>Price Quality</th>
          </tr>
        </thead>
        <tbody>
          {records.map((r, i) => {
            const ret = r.return_pct;
            return (
              <tr key={i}>
                <td style={{ color: 'var(--text-0)', fontWeight: 500, maxWidth: 200 }}>
                  <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 200 }}>
                    {r.company}
                  </div>
                </td>
                <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>{r.nse_symbol}</td>
                <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{r.year}</td>
                <td><RecPill rec={r.rec} /></td>
                <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                  {r.subscription_total_x != null ? `${r.subscription_total_x.toFixed(1)}x` : '—'}
                </td>
                <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 700, color: ret > 0 ? 'var(--green)' : ret < 0 ? 'var(--red)' : 'var(--text-2)' }}>
                  {ret != null ? `${ret > 0 ? '+' : ''}${ret.toFixed(2)}%` : '—'}
                </td>
                <td style={{ textAlign: 'right' }}>
                  {r.positive === true  && <span style={{ color: 'var(--green)',  fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700 }}>+ve</span>}
                  {r.positive === false && <span style={{ color: 'var(--red)',    fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700 }}>-ve</span>}
                  {r.positive == null   && <span style={{ color: 'var(--text-2)' }}>—</span>}
                </td>
                <td><QBadge quality={r.listing_open_quality} /></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
