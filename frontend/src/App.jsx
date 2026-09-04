import { useState, useEffect, useRef } from 'react';
import './index.css';
import {
  House, ChartBar, CurrencyDollar, Moon, Sun, CloudArrowUp, Lightning,
} from '@phosphor-icons/react';
import { api }         from './api.js';
import IposPage      from './pages/IposPage.jsx';
import IpoDetailPage from './pages/IpoDetailPage.jsx';
import CapitalPage   from './pages/CapitalPage.jsx';
import BacktestPage  from './pages/BacktestPage.jsx';
import LivePage      from './pages/LivePage.jsx';

const NAV = [
  { id: 'live',     label: 'Live IPOs',      Icon: Lightning      },
  { id: 'ipos',     label: 'IPO Universe',   Icon: House          },
  { id: 'capital',  label: 'Capital Planner', Icon: CurrencyDollar },
  { id: 'backtest', label: 'Backtest',        Icon: ChartBar       },
];

function useTheme() {
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem('ipo-theme') || 'dark'; }
    catch { return 'dark'; }
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem('ipo-theme', theme); } catch {}
  }, [theme]);

  function toggle() { setTheme(t => t === 'dark' ? 'light' : 'dark'); }
  return { theme, toggle };
}

/* ── Backend warm-up ──────────────────────────────────────── */
function useWarmup() {
  // 'pending' | 'warming' | 'ready' | 'timeout'
  const [status, setStatus] = useState('pending');
  const [elapsed, setElapsed] = useState(0);
  const intervalRef = useRef(null);
  const timerRef   = useRef(null);

  useEffect(() => {
    let attempts = 0;
    const MAX_WAIT = 40; // seconds before we give up

    async function ping() {
      try {
        const res = await api.health();
        if (res?.status === 'ok') {
          clearInterval(intervalRef.current);
          clearInterval(timerRef.current);
          setStatus('ready');
          return;
        }
      } catch { /* cold start — backend not yet awake */ }
      attempts++;
      if (attempts === 1) setStatus('warming'); // show overlay after first failure
    }

    // First ping immediately
    ping();
    // Retry every 3s
    intervalRef.current = setInterval(ping, 3000);
    // Elapsed counter every second
    timerRef.current = setInterval(() => {
      setElapsed(s => {
        if (s + 1 >= MAX_WAIT) {
          clearInterval(intervalRef.current);
          clearInterval(timerRef.current);
          setStatus('timeout');
        }
        return s + 1;
      });
    }, 1000);

    return () => {
      clearInterval(intervalRef.current);
      clearInterval(timerRef.current);
    };
  }, []);

  return { status, elapsed };
}

function WarmupOverlay({ status, elapsed }) {
  if (status === 'pending' || status === 'ready') return null;

  const isTimeout = status === 'timeout';

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      background: 'var(--bg-0)',
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      gap: 20,
      animation: 'fadeIn 0.3s ease',
    }}>
      {!isTimeout && (
        <div style={{
          width: 48, height: 48,
          border: '2px solid var(--border-1)',
          borderTopColor: 'var(--accent)',
          borderRadius: '50%',
          animation: 'spin 0.9s linear infinite',
        }} />
      )}
      {isTimeout && (
        <CloudArrowUp size={40} weight="thin" style={{ color: 'var(--text-2)' }} />
      )}

      <div style={{ textAlign: 'center' }}>
        <div style={{
          fontFamily: 'var(--font-sans)',
          fontWeight: 600,
          fontSize: 16,
          color: 'var(--text-0)',
          marginBottom: 6,
        }}>
          {isTimeout ? 'Backend unreachable' : 'Waking up backend…'}
        </div>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 12,
          color: 'var(--text-2)',
          maxWidth: 320,
          lineHeight: 1.7,
        }}>
          {isTimeout
            ? 'The server did not respond after 40s. Try refreshing or check back shortly.'
            : `Render free tier spins down after inactivity. Cold start takes ~20–30s. (${elapsed}s)`
          }
        </div>
        {isTimeout && (
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: 16,
              background: 'var(--accent)',
              color: '#fff',
              border: 'none',
              padding: '8px 20px',
              borderRadius: 'var(--r)',
              cursor: 'pointer',
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
            }}
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [page, setPage]             = useState('ipos');
  const [selectedIpo, setSelected]  = useState(null);
  const { theme, toggle }           = useTheme();
  const { status, elapsed }         = useWarmup();

  function navigate(p) { setPage(p); setSelected(null); }

  function renderPage() {
    if (page === 'ipo-detail' && selectedIpo) {
      return (
        <IpoDetailPage
          ipoId={selectedIpo}
          onBack={() => navigate('ipos')}
        />
      );
    }
    switch (page) {
      case 'live':     return <LivePage />;
      case 'ipos':     return <IposPage onSelectIpo={id => { setSelected(id); setPage('ipo-detail'); }} />;
      case 'capital':  return <CapitalPage />;
      case 'backtest': return <BacktestPage />;
      default:         return <LivePage />;
    }
  }

  const activeId = page === 'ipo-detail' ? 'ipos' : page;

  return (
    <div style={{ display: 'flex', minHeight: '100dvh' }}>
      <WarmupOverlay status={status} elapsed={elapsed} />
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-name">IPO Terminal</div>
          <div className="sidebar-brand-tag">RULE_ESTIMATE · v0.2.0</div>
        </div>

        <nav className="sidebar-nav">
          {NAV.map(({ id, label, Icon }) => (
            <button
              key={id}
              id={`nav-${id}`}
              className={`nav-item ${activeId === id ? 'active' : ''}`}
              onClick={() => navigate(id)}
            >
              <span className="nav-icon">
                <Icon size={15} weight={activeId === id ? 'fill' : 'regular'} />
              </span>
              {label}
            </button>
          ))}
        </nav>

        <div className="sidebar-meta">
          <div className="sidebar-meta-stat">318 IPOs · 2018–2024</div>
          <div style={{ marginTop: 2 }}>
            <span className="pos">●</span> 244 NSE verified
          </div>
          <div style={{ marginTop: 10, lineHeight: 1.7 }}>
            Live + historical data.<br />Not investment advice.
          </div>

          {/* Theme toggle */}
          <button
            id="theme-toggle"
            onClick={toggle}
            title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
            style={{
              marginTop: 14,
              display: 'flex',
              alignItems: 'center',
              gap: 7,
              background: 'var(--bg-3)',
              border: '1px solid var(--border-1)',
              color: 'var(--text-1)',
              padding: '6px 10px',
              borderRadius: 'var(--r-sm)',
              cursor: 'pointer',
              fontSize: 11,
              fontFamily: 'var(--font-mono)',
              width: '100%',
              transition: 'border-color var(--t), background var(--t)',
            }}
          >
            {theme === 'dark'
              ? <><Sun  size={13} weight="regular" /> Light mode</>
              : <><Moon size={13} weight="regular" /> Dark mode</>
            }
          </button>
        </div>
      </aside>

      <main className="main">
        {renderPage()}
      </main>
    </div>
  );
}
