import { useState, useEffect } from 'react';
import './index.css';
import {
  House, ChartBar, CurrencyDollar, Moon, Sun,
} from '@phosphor-icons/react';
import IposPage      from './pages/IposPage.jsx';
import IpoDetailPage from './pages/IpoDetailPage.jsx';
import CapitalPage   from './pages/CapitalPage.jsx';
import BacktestPage  from './pages/BacktestPage.jsx';

const NAV = [
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

export default function App() {
  const [page, setPage]             = useState('ipos');
  const [selectedIpo, setSelected]  = useState(null);
  const { theme, toggle }           = useTheme();

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
      case 'ipos':     return <IposPage onSelectIpo={id => { setSelected(id); setPage('ipo-detail'); }} />;
      case 'capital':  return <CapitalPage />;
      case 'backtest': return <BacktestPage />;
      default:         return <IposPage onSelectIpo={id => { setSelected(id); setPage('ipo-detail'); }} />;
    }
  }

  const activeId = page === 'ipo-detail' ? 'ipos' : page;

  return (
    <div style={{ display: 'flex', minHeight: '100dvh' }}>
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
            Historical data only.<br />Not investment advice.
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
