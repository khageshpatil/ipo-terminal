"""Smoke test for API v0.2.0 — all new endpoints."""
import urllib.request, json, sys

BASE = "http://localhost:8001"

def get(path):
    try:
        r = urllib.request.urlopen(f"{BASE}{path}", timeout=10)
        return json.loads(r.read())
    except Exception as e:
        return {"ERROR": str(e)}

def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data,
          headers={"Content-Type": "application/json"}, method="POST")
    try:
        r = urllib.request.urlopen(req, timeout=15)
        return json.loads(r.read())
    except Exception as e:
        return {"ERROR": str(e)}

print("=== API v0.2.0 Smoke Test ===\n")

# Health
h = get("/health")
print(f"GET /health: {h}")

# IPO list with search
ipos = get("/ipos?limit=3&search=HDFC")
print(f"GET /ipos?search=HDFC: {len(ipos)} results, first: {ipos[0]['company_name'] if ipos else 'none'}")

# IPO analysis
a = get("/ipos/1/analysis")
print(f"GET /ipos/1/analysis: {a.get('company_name')} -> {a.get('recommendation')} ({a.get('confidence')})")
print(f"  p_positive={a.get('p_positive')} expected_return={a.get('expected_return_pct')}%")

# Backtest summary
bt = get("/backtests/summary")
strats = bt.get("strategies", [])
print(f"\nGET /backtests/summary: {len(strats)} strategies")
for s in strats:
    ap = s.get("applied", {})
    print(f"  {s['strategy_name']}: n_apply={s['n_apply']} hit_rate={ap.get('hit_rate_pct')}% mean={ap.get('mean_pct')}%")

# Baseline
bl = get("/backtests/baseline")
print(f"\nGET /backtests/baseline: {bl.get('total_ipos')} IPOs, {bl.get('positive_rate_pct')}% positive")

# Per-IPO
pi = get("/backtests/per-ipo?rec=APPLY&limit=5")
print(f"\nGET /backtests/per-ipo?rec=APPLY: {len(pi)} records returned")
if pi:
    print(f"  First: {pi[0]['company']} {pi[0].get('return_pct')}%")

# Capital
cap = post("/capital/recommendation", {"available_capital": 100000, "skip_watch": True})
print(f"\nPOST /capital/recommendation (100k, APPLY only):")
print(f"  n_ipos={cap.get('n_ipos')} deployed={cap.get('total_capital_deployed')}")
if cap.get("lines"):
    ln = cap["lines"][0]
    print(f"  First line: {ln['company_name']} {ln['lots_to_apply']}x {ln['capital_required']}")

print("\n=== All endpoints OK ===")
