import { useState, useMemo } from 'react';
import { motion }            from 'motion/react';
import { useIpos }           from '../hooks/useFetch.js';
import { GridSkeleton, ErrorFill, RecPill, QBadge, SubBar, fmtInr, fmtX } from '../components/shared.jsx';
import { api }               from '../api.js';

const YEARS    = [2024, 2023, 2022, 2021, 2020, 2019, 2018];
const PAGE_SZ  = 30;

export default function IposPage({ onSelectIpo }) {
  const [search, setSearch]                 = useState('');
  const [year, setYear]                     = useState('');
  const [shown, setShown]                   = useState(PAGE_SZ);
  const [analysisCache, setAnalysisCache]   = useState({});

  const { data: ipos, loading, error } = useIpos({
    search: search || undefined,
    year:   year   || undefined,
    limit: 318,
  });

  // Reset pagination on filter change
  function handleSearch(v) { setSearch(v); setShown(PAGE_SZ); }
  function handleYear(v)   { setYear(v);   setShown(PAGE_SZ); }

  async function prefetchAnalysis(id) {
    if (analysisCache[id]) return;
    try {
      const r = await api.analyseIpo(id);
      setAnalysisCache(p => ({ ...p, [id]: r }));
    } catch { /* noop */ }
  }

  const enriched = useMemo(() => {
    if (!ipos) return [];
    return ipos.map(ipo => ({ ...ipo, analysis: analysisCache[ipo.ipo_id] || null }));
  }, [ipos, analysisCache]);

  const visible  = enriched.slice(0, shown);
  const hasMore  = shown < enriched.length;
  const maxSub   = useMemo(
    () => Math.max(...enriched.map(r => r.subscription_total_x || 0), 100),
    [enriched],
  );

  if (loading) return (
    <div className="page">
      <div className="ph">
        <div className="skeleton" style={{ width: 160, height: 20, marginBottom: 8 }} />
        <div className="skeleton" style={{ width: 220, height: 11 }} />
      </div>
      <GridSkeleton n={9} />
    </div>
  );

  if (error) return <div className="page"><ErrorFill message={error} /></div>;

  const total = enriched.length;

  return (
    <div className="page">
      {/* Header — no eyebrow */}
      <div className="ph" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1 className="ph-title">IPO Universe</h1>
          <p className="ph-sub">{total} of 318 Mainboard IPOs · 2018–2024</p>
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-2)', textAlign: 'right', lineHeight: 1.9 }}>
          <div><span className="pos">●</span> 244 NSE Verified</div>
          <div><span style={{ color: 'var(--accent)' }}>●</span> 74 Aggregator</div>
        </div>
      </div>

      {/* Filters */}
      <div className="filter-bar">
        <input
          className="fi"
          placeholder="Search company or symbol"
          value={search}
          onChange={e => handleSearch(e.target.value)}
          style={{ width: 240 }}
        />
        <select className="fi" value={year} onChange={e => handleYear(e.target.value)}>
          <option value="">All years</option>
          {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
        </select>
        <span className="filter-count">{visible.length} / {total}</span>
      </div>

      {total === 0 && (
        <div className="empty-fill" style={{ marginTop: 40 }}>No IPOs match your filters</div>
      )}

      {/* Grid — only `shown` items rendered */}
      <div className="ipo-grid">
        {visible.map((ipo, i) => (
          <motion.div
            key={ipo.ipo_id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.28, delay: Math.min(i, 8) * 0.04, ease: [0.16, 1, 0.3, 1] }}
          >
            <IpoCard
              ipo={ipo}
              maxSub={maxSub}
              onHover={() => prefetchAnalysis(ipo.ipo_id)}
              onClick={() => onSelectIpo(ipo.ipo_id)}
            />
          </motion.div>
        ))}
      </div>

      {/* Load more */}
      {hasMore && (
        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <button
            onClick={() => setShown(s => s + PAGE_SZ)}
            style={{
              background: 'var(--bg-2)',
              border: '1px solid var(--border-1)',
              color: 'var(--text-1)',
              padding: '9px 20px',
              borderRadius: 'var(--r)',
              cursor: 'pointer',
              fontSize: 13,
              fontFamily: 'var(--font-mono)',
              transition: 'all var(--t)',
            }}
            onMouseEnter={e => e.target.style.borderColor = 'var(--accent)'}
            onMouseLeave={e => e.target.style.borderColor = 'var(--border-1)'}
          >
            Load {Math.min(PAGE_SZ, enriched.length - shown)} more
            <span style={{ color: 'var(--text-2)', marginLeft: 8 }}>
              ({enriched.length - shown} remaining)
            </span>
          </button>
        </div>
      )}
    </div>
  );
}

function IpoCard({ ipo, maxSub, onHover, onClick }) {
  const ret      = ipo.listing_return_pct;
  const rec      = ipo.analysis?.recommendation
    || (ret > 0 ? 'APPLY' : ret < 0 ? 'SKIP' : 'WATCH');
  const recClass = rec.toLowerCase();
  const retCls   = ret > 0 ? 'pos' : ret < 0 ? 'neg' : 'muted';

  return (
    <div
      className={`ipo-card ${recClass}`}
      onMouseEnter={onHover}
      onClick={onClick}
    >
      <div className="ic-head">
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="ic-name">{ipo.company_name}</div>
          <div className="ic-symbol">{ipo.nse_symbol} · {ipo.year}</div>
        </div>
        <RecPill rec={rec} />
      </div>

      {ipo.issue_price && (
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 17, fontWeight: 700, letterSpacing: '-0.03em' }}>
            {fmtInr(ipo.issue_price)}
          </span>
          {ipo.lot_size && (
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-2)' }}>
              {fmtInr(ipo.issue_price * ipo.lot_size)}/lot
            </span>
          )}
        </div>
      )}

      {(ipo.subscription_qib_x || ipo.subscription_nii_x || ipo.subscription_retail_x) && (
        <div className="sub-mini">
          {ipo.subscription_qib_x    != null && <SubBar label="QIB"    value={ipo.subscription_qib_x}    max={maxSub} colorClass="qib"    />}
          {ipo.subscription_nii_x    != null && <SubBar label="NII"    value={ipo.subscription_nii_x}    max={maxSub} colorClass="nii"    />}
          {ipo.subscription_retail_x != null && <SubBar label="Retail" value={ipo.subscription_retail_x} max={maxSub} colorClass="retail" />}
        </div>
      )}

      <div className="ic-foot">
        <div>
          <div className="ic-return-label">Listing return</div>
          <div className={`ic-return ${retCls}`}>
            {ret != null ? `${ret > 0 ? '+' : ''}${ret.toFixed(1)}%` : '—'}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-2)' }}>
            {fmtX(ipo.subscription_total_x)} total
          </div>
          <QBadge quality={ipo.listing_open_quality} />
        </div>
      </div>
    </div>
  );
}
