# Research Index — IPO Listing-Gain Decision Engine

## Phase: Data Feasibility Sprint (complete)

### Documents produced

| Document | Purpose | Status |
|----------|---------|--------|
| [DATA-FEASIBILITY-REPORT.md](./DATA-FEASIBILITY-REPORT.md) | Full research findings; GO/NO-GO decision; recommended V1 dataset | Complete |
| [SOURCE-MATRIX.md](./SOURCE-MATRIX.md) | All data sources with access details, reliability, limitations | Complete |
| [DATA-COLLECTION-GUIDE.md](./DATA-COLLECTION-GUIDE.md) | Step-by-step instructions for gates G1–G7 with exact output formats | Complete |

### Key findings

1. **GO (conditional)** — the strategy can be honestly backtested with a reduced feature set
2. **Intraday subscription** — NOT available historically; remove from historical model
3. **Historical GMP** — NOT reliably available; exclude from historical backtest
4. **Universe size** — ~535 Mainboard IPOs 2018–2024; ~480 usable after quality filter
5. **Listing price** — use NSE/BSE Bhav Copy OPEN on Day 1 (pre-open equilibrium)
6. **Allotment** — SEBI formula is deterministic post-close; ML estimator only needed pre-close
7. **NII reform** — September 2022 split into sNII/bNII; `sebi_nii_regime` flag required
8. **T+3 reform** — December 2023 change from T+6; `timeline_regime` flag required

### Next milestone: Data Collection Sprint

Complete gates G1–G4 before writing any application code.

| Gate | Description | Blocking? |
|------|-------------|-----------|
| G1 | IPO universe list 2018–2024 | Yes — gates all other work |
| G2 | Listing prices from Bhav Copy | Yes — label for all models |
| G3 | Final subscription data | Yes — core feature |
| G4 | Base rate computation | Yes — validates strategy assumptions |
| G5 | Market data (Nifty/VIX) | Yes — before model training |
| G6 | Basis of allotment sample (50 IPOs) | Yes — before model training |
| G7 | PDF parsing prototype (10 IPOs) | Yes — before full fundamental extraction |

### Data directory structure (to be populated)

```
docs/research/
├── data/
│   ├── ipo_universe_raw.csv          (Gate G1 output)
│   ├── listing_prices_raw.csv        (Gate G2 output)
│   ├── subscription_final_raw.csv    (Gate G3 output)
│   ├── base_rate_analysis.md         (Gate G4 output)
│   ├── market_data.csv               (Gate G5 output)
│   ├── boa_sample_index.csv          (Gate G6 output)
│   └── boa_sample/                   (Gate G6 PDFs)
└── scratch/
    └── pdf_parser_test.py            (Gate G7 prototype)
```
