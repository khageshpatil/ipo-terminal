import { useState } from 'react';
import { motion } from 'motion/react';
import { api } from '../api.js';
import { LoadingFill, Notice, RecPill, fmtInr } from '../components/shared.jsx';

export default function CapitalPage() {
  const [capital, setCapital]     = useState('');
  const [skipWatch, setSkipWatch] = useState(false);
  const [plan, setPlan]           = useState(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);

  async function run() {
    const amount = parseFloat(capital.replace(/,/g, ''));
    if (!amount || amount <= 0) { setError('Enter a valid amount'); return; }
    setLoading(true);
    setError(null);
    try {
      const result = await api.capitalRecommendation(amount, skipWatch);
      setPlan(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const rawCapital   = parseFloat(capital.replace(/,/g, '')) || 0;
  const deployed     = plan?.total_capital_deployed || 0;
  const remaining    = plan?.remaining_capital || 0;
  const totalProfit  = plan?.lines?.reduce((s, l) => s + (l.expected_profit || 0), 0) || 0;

  return (
    <div className="page">
      <div className="ph">
        <h1 className="ph-title">Capital Planner</h1>
        <p className="ph-sub">Allocate capital across current IPO opportunities</p>
      </div>

      <Notice text="Expected profit is RULE_ESTIMATE only. Allotment not guaranteed. Not investment advice." />

      {/* Input block */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
        className="surface"
        style={{ marginBottom: 20 }}
      >
        <div className="capital-input-block">
          <div className="input-stack">
            <label className="input-lbl">Available Capital (₹)</label>
            <input
              className="capital-field"
              type="text"
              placeholder="e.g. 50,000"
              value={capital}
              onChange={e => setCapital(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && run()}
            />
          </div>
          <div className="input-stack">
            <label className="input-lbl">Mode</label>
            <select
              className="mode-select"
              value={skipWatch ? 'apply-only' : 'all'}
              onChange={e => setSkipWatch(e.target.value === 'apply-only')}
            >
              <option value="all">APPLY + WATCH</option>
              <option value="apply-only">APPLY only</option>
            </select>
          </div>
          <button
            className="btn-run"
            onClick={run}
            disabled={loading || !capital}
            style={{ alignSelf: 'flex-end' }}
          >
            {loading ? 'Calculating…' : 'Plan →'}
          </button>
        </div>

        {error && (
          <div style={{ color: 'var(--red)', fontFamily: 'var(--font-mono)', fontSize: 12, marginTop: 4 }}>
            {error}
          </div>
        )}
      </motion.div>

      {loading && <LoadingFill />}

      {plan && !loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4 }}
        >
          {/* Summary row */}
          <div className="stat-grid stat-grid-4" style={{ marginBottom: 16 }}>
            <div className="stat-box">
              <div className="stat-box-label">Available</div>
              <div className="stat-box-value">{fmtInr(rawCapital)}</div>
            </div>
            <div className="stat-box">
              <div className="stat-box-label">Deployed</div>
              <div className="stat-box-value accent">{fmtInr(deployed)}</div>
            </div>
            <div className="stat-box">
              <div className="stat-box-label">Remaining</div>
              <div className="stat-box-value">{fmtInr(remaining)}</div>
            </div>
            <div className="stat-box">
              <div className="stat-box-label">Expected profit</div>
              <div className={`stat-box-value ${totalProfit > 0 ? 'green' : ''}`}>
                {totalProfit > 0 ? fmtInr(totalProfit) : '—'}
              </div>
              <div className="stat-box-sub">RULE_ESTIMATE</div>
            </div>
          </div>

          {plan.lines.length === 0 ? (
            <div className="surface">
              <div className="empty-fill" style={{ minHeight: 120 }}>
                {remaining < 14000
                  ? 'Capital too low for any application (min ~₹14,000 per application)'
                  : 'No investable IPOs under current strategy'}
              </div>
            </div>
          ) : (
            <div className="surface">
              <div className="surface-label">{plan.lines.length} Recommended Applications</div>
              <table className="alloc-table">
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Rec</th>
                    <th style={{ textAlign: 'right' }}>Lots</th>
                    <th style={{ textAlign: 'right' }}>Capital</th>
                    <th style={{ textAlign: 'right' }}>E[Profit]</th>
                    <th style={{ textAlign: 'right' }}>P(Allot)</th>
                    <th style={{ textAlign: 'right' }}>E[Return]</th>
                  </tr>
                </thead>
                <tbody>
                  {plan.lines.map((line, i) => (
                    <motion.tr
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.04, duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                    >
                      <td style={{ fontWeight: 600, color: 'var(--text-0)', maxWidth: 220 }}>
                        <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {line.company_name}
                        </div>
                      </td>
                      <td><RecPill rec={line.recommendation} /></td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                        {line.lots_to_apply}
                      </td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                        {fmtInr(line.capital_required)}
                      </td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--green)' }}>
                        {line.expected_profit ? fmtInr(line.expected_profit) : '—'}
                      </td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                        {line.allotment_probability
                          ? `${(line.allotment_probability * 100).toFixed(0)}%`
                          : '—'}
                      </td>
                      <td style={{
                        textAlign: 'right',
                        fontFamily: 'var(--font-mono)',
                        fontWeight: 700,
                        color: line.expected_return_pct > 0 ? 'var(--green)' : 'var(--red)',
                      }}>
                        {line.expected_return_pct != null
                          ? `${line.expected_return_pct > 0 ? '+' : ''}${line.expected_return_pct.toFixed(1)}%`
                          : '—'}
                      </td>
                    </motion.tr>
                  ))}
                </tbody>
              </table>

              <div className="alloc-footer">
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-2)' }}>
                  {plan.lines.length} applications · {fmtInr(deployed)} blocked
                </span>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-2)', marginBottom: 4 }}>
                    Expected total profit (RULE_ESTIMATE)
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 700, color: 'var(--green)' }}>
                    {totalProfit > 0 ? fmtInr(totalProfit) : '—'}
                  </div>
                </div>
              </div>
            </div>
          )}

          {plan.skipped?.length > 0 && (
            <div style={{ marginTop: 12, fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-3)' }}>
              {plan.skipped.length} IPOs skipped (insufficient capital or no data)
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
