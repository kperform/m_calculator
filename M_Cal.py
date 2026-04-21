"""
M_Cal — Trade Entry Calculator
================================


Column H (Shares):  =ROUNDDOWN(1250 / Entry, 0)
  → Fixed capital of $1,250 per position, rounded DOWN to whole shares

Column I (Cal Price):  =Entry / 0.98
  → Back-calculates previous day's close (since Entry = PrevClose × 0.98)
  → PrevClose = Entry / 0.98

Entry Validation:
  → Ideal entry = PrevClose × 0.98  (2% discount to prev close)
  → Alert if user's entry > ideal entry (chasing above the 2% threshold)

Usage:
  pip install streamlit yfinance
  streamlit run M_Cal.py
"""

import math
import streamlit as st

# ── page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="M_Cal",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── mobile-first CSS ─────────────────────────────────────────────────────────
st.markdown("""
<style>
  html, body, [data-testid="stAppViewContainer"] {
    background: #0d1117;
    color: #e6edf3;
    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }
  [data-testid="stAppViewContainer"] { padding: 0 !important; }

  .m-header {
    background: linear-gradient(135deg, #0f2027 0%, #0d1117 100%);
    border-bottom: 1px solid #21262d;
    padding: 20px 20px 14px;
    text-align: center;
    margin-bottom: 8px;
  }
  .m-header h1 {
    font-size: 1.6rem; font-weight: 800; letter-spacing: -0.01em;
    background: linear-gradient(90deg, #f0c040, #f7e08a);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0 0 3px;
  }
  .m-header .sub {
    font-size: 0.72rem; color: #8b949e; margin: 0;
    line-height: 1.5;
  }
  .m-header .badge {
    display: inline-block; background: #1f2d10; border: 1px solid #3fb950;
    color: #3fb950; font-size: 0.62rem; font-weight: 700; letter-spacing: .08em;
    padding: 2px 8px; border-radius: 20px; margin-top: 6px;
    text-transform: uppercase;
  }

  .card {
    background: #161b22; border: 1px solid #21262d;
    border-radius: 12px; padding: 16px; margin-bottom: 12px;
  }
  .card-title {
    font-size: 0.68rem; font-weight: 700; letter-spacing: .09em;
    text-transform: uppercase; color: #8b949e;
    margin-bottom: 12px;
  }

  .res-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 9px 0; border-bottom: 1px solid #21262d;
  }
  .res-row:last-child { border-bottom: none; }
  .res-label { font-size: 0.83rem; color: #8b949e; }
  .res-value { font-size: 0.95rem; font-weight: 700; color: #e6edf3; }
  .res-value.gold   { color: #f0c040; }
  .res-value.green  { color: #3fb950; }
  .res-value.red    { color: #f85149; }
  .res-value.blue   { color: #79c0ff; }
  .res-value.orange { color: #e3b341; }

  .big-block {
    text-align: center; padding: 16px 0 10px;
  }
  .big-block .lbl {
    font-size: 0.68rem; color: #8b949e; letter-spacing:.08em;
    text-transform: uppercase; margin-bottom: 5px;
  }
  .big-block .num {
    font-size: 2.6rem; font-weight: 800; line-height: 1;
  }
  .big-block .unit {
    font-size: 0.78rem; color: #8b949e; margin-top: 3px;
  }

  .grid3 {
    display: grid; grid-template-columns: 1fr 1fr 1fr;
    gap: 8px; margin-bottom: 12px;
  }
  .mini {
    background: #161b22; border: 1px solid #21262d;
    border-radius: 10px; padding: 11px 8px; text-align: center;
  }
  .mini .lbl { font-size: 0.60rem; color: #8b949e; text-transform: uppercase;
    letter-spacing:.06em; margin-bottom: 4px; }
  .mini .val { font-size: 1.05rem; font-weight: 700; }

  .alert { border-radius: 8px; padding: 10px 14px; font-size: 0.82rem; margin-bottom: 12px; line-height: 1.45; }
  .alert.warn  { background: #2d1f0a; border: 1px solid #e3b341; color: #e3b341; }
  .alert.ok    { background: #0a2d10; border: 1px solid #3fb950; color: #3fb950; }
  .alert.info  { background: #0a1f2d; border: 1px solid #58a6ff; color: #79c0ff; }
  .alert.error { background: #2d0a0a; border: 1px solid #f85149; color: #f85149; }

  .section-label {
    font-size: 0.65rem; font-weight: 700; letter-spacing: .12em;
    text-transform: uppercase; color: #f0c040;
    margin: 16px 0 8px; padding-left: 2px;
  }

  .fetch-badge {
    font-size: 0.65rem; padding: 2px 7px; border-radius: 20px;
    font-weight: 700; letter-spacing: .04em;
  }
  .fetch-live { background: #0a2d10; border: 1px solid #3fb950; color: #3fb950; }
  .fetch-manual { background: #2d1f0a; border: 1px solid #e3b341; color: #e3b341; }

  [data-testid="stNumberInput"] input { font-size: 1rem !important; }
  [data-testid="stNumberInput"] label,
  [data-testid="stTextInput"] label { font-size: 0.78rem !important; color: #8b949e !important; }
  [data-testid="stTextInput"] input {
    font-size: 1.1rem !important; font-weight: 700 !important;
    text-transform: uppercase;
  }
  [data-testid="stButton"] button {
    width: 100%; border-radius: 10px; font-size: 1rem;
    font-weight: 700; padding: 12px;
    background: linear-gradient(135deg, #b8860b, #f0c040);
    border: none; color: #0d1117; margin-top: 6px;
  }
  [data-testid="stButton"] button:hover {
    background: linear-gradient(135deg, #f0c040, #ffd700);
  }
  footer, #MainMenu, header, [data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ── helpers ──────────────────────────────────────────────────────────────────
def fetch_prev_close(symbol: str):
    """Fetch previous trading day's close via yfinance. Returns (price, error_msg)."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period="5d")
        if hist.empty or len(hist) < 2:
            return None, "Not enough history returned — check the symbol."
        prev_close = float(hist["Close"].iloc[-2])
        return prev_close, None
    except ImportError:
        return None, "yfinance not installed. Run: pip install yfinance"
    except Exception as e:
        return None, f"Fetch failed: {str(e)[:80]}"

M_CAL_CAPITAL = 1250.0   # Fixed capital per position (from spreadsheet col H)
M_CAL_DISCOUNT = 0.02    # 2% below prev close (from strategy header & col I logic)
M_CAL_ALERT_TOLERANCE = 0.001  # 0.1% tolerance band for "close enough" check


# ── header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="m-header">
  <h1>M_Cal</h1>
  <p class="sub">
    Russell 1000 · Stock &gt; 200D MA · Lowest 10 days<br>
    Enter 2% below prev close · Max 8 positions · $1,250/trade
  </p>
  <span class="badge">MRT Strategy</span>
</div>
""", unsafe_allow_html=True)

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ M_Cal Settings")
    st.markdown("**Formulas from M_Calculator.xlsx:**")
    st.code(
        "Shares  = ROUNDDOWN(1250 / Entry, 0)\n"
        "CalPrice = Entry / 0.98  (= Prev Close)\n"
        "Target   = PrevClose × 0.98"
    )
    st.markdown("---")
    st.markdown("**Strategy Rules**")
    st.markdown("""
- ✅ Stock must be > 200D MA
- ✅ Near lowest price of last 10 days
- ✅ Enter 2% below previous day close
- ✅ Exit when RSI-2d crosses above 50
- ⚠️ Max 8 open positions
- ⚠️ Max 12.5% capital per trade
    """)

# ── input section ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Trade Inputs</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    symbol = st.text_input("Stock Symbol", value="", placeholder="e.g. AAPL", max_chars=10)
with col2:
    entry_price = st.number_input(
        "Your Entry Price ($)", min_value=0.01, value=50.00, step=0.01, format="%.2f"
    )

fetch_clicked = st.button("⬇ Fetch Prev Close & Calculate")

# ── state: prev close ─────────────────────────────────────────────────────────
if "m_cal_prev_close" not in st.session_state:
    st.session_state.m_cal_prev_close = None
if "m_cal_fetch_source" not in st.session_state:
    st.session_state.m_cal_fetch_source = None
if "m_cal_fetch_error" not in st.session_state:
    st.session_state.m_cal_fetch_error = None
if "m_cal_symbol" not in st.session_state:
    st.session_state.m_cal_symbol = ""

if fetch_clicked:
    sym = symbol.strip().upper()
    if not sym:
        st.markdown('<div class="alert error">⚠️ Please enter a stock symbol first.</div>', unsafe_allow_html=True)
    else:
        with st.spinner(f"Fetching prev close for {sym}..."):
            price, err = fetch_prev_close(sym)
        if price:
            st.session_state.m_cal_prev_close = price
            st.session_state.m_cal_fetch_source = "live"
            st.session_state.m_cal_fetch_error = None
            st.session_state.m_cal_symbol = sym
        else:
            st.session_state.m_cal_prev_close = None
            st.session_state.m_cal_fetch_source = "failed"
            st.session_state.m_cal_fetch_error = err
            st.session_state.m_cal_symbol = sym

# ── manual fallback if fetch failed ──────────────────────────────────────────
fetch_error = st.session_state.m_cal_fetch_error
if fetch_error:
    st.markdown(f'<div class="alert warn">⚠️ Auto-fetch failed: {fetch_error}<br>Enter prev close manually below.</div>', unsafe_allow_html=True)
    manual_prev = st.number_input(
        "Previous Day Close (manual)", min_value=0.01,
        value=round(entry_price / 0.98, 2), step=0.01, format="%.2f"
    )
    st.session_state.m_cal_prev_close = manual_prev
    st.session_state.m_cal_fetch_source = "manual"

# ── results ───────────────────────────────────────────────────────────────────
prev_close = st.session_state.m_cal_prev_close
fetch_source = st.session_state.m_cal_fetch_source
display_symbol = st.session_state.m_cal_symbol or symbol.strip().upper()

if prev_close and prev_close > 0 and entry_price > 0:

    # ── Core M_Cal calculations (matching spreadsheet exactly) ──
    ideal_entry   = prev_close * (1 - M_CAL_DISCOUNT)          # PrevClose × 0.98
    cal_price     = entry_price / (1 - M_CAL_DISCOUNT)         # col I: Entry / 0.98
    shares        = math.floor(M_CAL_CAPITAL / entry_price)     # col H: ROUNDDOWN(1250/Entry, 0)
    capital_used  = shares * entry_price                        # col J: Shares × Entry
    discount_pct  = (prev_close - entry_price) / prev_close * 100
    entry_ok      = entry_price <= ideal_entry * (1 + M_CAL_ALERT_TOLERANCE)
    tp1           = entry_price * 2                             # TP1 from col L: Entry × 2
    tp2           = entry_price * 2.7                           # TP2 from col M: Entry × 2.7

    # ── source badge ──
    badge_cls  = "fetch-live" if fetch_source == "live" else "fetch-manual"
    badge_text = "🟢 LIVE" if fetch_source == "live" else "🟡 MANUAL"

    # ── symbol + shares highlight ──
    sym_display = display_symbol if display_symbol else "—"
    st.markdown(f"""
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <span style="font-size:1.5rem;font-weight:800;color:#f0c040;letter-spacing:.04em;">{sym_display}</span>
        <span class="fetch-badge {badge_cls}">{badge_text}</span>
      </div>
      <div class="big-block">
        <div class="lbl">Shares to Buy</div>
        <div class="num green">{shares:,}</div>
        <div class="unit">@ ${entry_price:,.2f} entry · ${capital_used:,.2f} deployed</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── mini stats ──
    st.markdown(f"""
    <div class="grid3">
      <div class="mini">
        <div class="lbl">Prev Close</div>
        <div class="val blue">${prev_close:,.2f}</div>
      </div>
      <div class="mini">
        <div class="lbl">Ideal Entry</div>
        <div class="val gold">${ideal_entry:,.2f}</div>
      </div>
      <div class="mini">
        <div class="lbl">Discount</div>
        <div class="val {'green' if discount_pct >= 1.5 else 'orange' if discount_pct >= 0 else 'red'}">{discount_pct:+.2f}%</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── entry validation alert ──
    if entry_ok:
        diff = ideal_entry - entry_price
        st.markdown(f"""
        <div class="alert ok">
          ✅ Entry <strong>${entry_price:,.2f}</strong> is at or below the 2% discount target
          (${ideal_entry:,.2f}). You're <strong>${diff:,.2f} below</strong> the threshold — valid M_Cal entry.
        </div>""", unsafe_allow_html=True)
    else:
        overshoot = entry_price - ideal_entry
        st.markdown(f"""
        <div class="alert warn">
          ⚠️ Entry <strong>${entry_price:,.2f}</strong> exceeds the 2% discount target of
          <strong>${ideal_entry:,.2f}</strong> by <strong>${overshoot:,.2f}</strong>.
          You are chasing above the M_Cal threshold — consider waiting for a pullback.
        </div>""", unsafe_allow_html=True)

    # ── full breakdown ──
    st.markdown('<div class="section-label">M_Cal Full Breakdown</div>', unsafe_allow_html=True)

    def res_rows(rows_data):
        inner = "".join(
            f'<div class="res-row">'
            f'<span class="res-label">{lbl}</span>'
            f'<span class="res-value {cls}">{val}</span>'
            f'</div>'
            for lbl, val, cls in rows_data
        )
        return inner

    price_rows = [
        ("Prev Day Close",          f"${prev_close:,.2f}",    "blue"),
        ("Ideal Entry (−2%)",       f"${ideal_entry:,.2f}",   "gold"),
        ("Your Entry",              f"${entry_price:,.2f}",   "green" if entry_ok else "orange"),
        ("M_Cal Cal Price (÷0.98)", f"${cal_price:,.2f}",     ""),
        ("Discount to Prev Close",  f"{discount_pct:+.2f}%",  "green" if discount_pct >= 2.0 else "orange"),
    ]

    sizing_rows = [
        ("Shares (ROUNDDOWN)",      f"{shares:,}",            "gold"),
        ("Capital Per Trade",       f"${M_CAL_CAPITAL:,.0f}", ""),
        ("Capital Deployed",        f"${capital_used:,.2f}",  "blue"),
        ("Unused Capital",          f"${M_CAL_CAPITAL - capital_used:,.2f}", ""),
    ]

    st.markdown(f"""
    <div class="card">
      <div class="card-title">💰 Price Levels</div>
      {res_rows(price_rows)}
    </div>
    <div class="card">
      <div class="card-title">📐 Position Sizing (M_Cal)</div>
      {res_rows(sizing_rows)}
    </div>
    """, unsafe_allow_html=True)

    # ── formula expander ──
    with st.expander("📋 M_Cal Formula Reference", expanded=False):
        st.markdown(f"""
**Shares** (col H — M_Calculator.xlsx)
```
Shares = ROUNDDOWN(1250 / Entry, 0)
       = ROUNDDOWN(1250 / {entry_price:.2f}, 0)
       = {shares}
```

**Cal Price** (col I — M_Calculator.xlsx)
```
CalPrice = Entry / 0.98
         = {entry_price:.2f} / 0.98
         = {cal_price:.4f}   ← implied prev close
```

**Ideal Entry Target**
```
Ideal Entry = PrevClose × 0.98
            = {prev_close:.2f} × 0.98
            = {ideal_entry:.4f}
```

**Validation**
```
Your Entry ({entry_price:.2f}) {'≤' if entry_ok else '>'} Ideal Entry ({ideal_entry:.2f})
→ {'✅ VALID — within M_Cal threshold' if entry_ok else '⚠️ ALERT — exceeds M_Cal threshold'}
```

**Strategy (from M_Calculator.xlsx row 1)**
```
MRT: Stock > 200D MA · Lowest 10 days
     Enter 2% below prev day close
     Exit: RSI-2d above 50
     Max 8 positions · 12.5% allocation
```
        """)

elif not prev_close:
    # No data yet — show prompt
    st.markdown("""
    <div class="alert info">
      👆 Enter a stock symbol and your intended entry price, then tap
      <strong>Fetch Prev Close & Calculate</strong> to run the M_Cal analysis.
      <br><br>
      M_Cal will fetch the previous day's close price, verify your 2% discount,
      and calculate your share count using the formula from M_Calculator.xlsx.
    </div>
    """, unsafe_allow_html=True)

# ── footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:24px 0 8px;font-size:0.65rem;color:#3d444d;">
  M_Cal · Formulas extracted from M_Calculator.xlsx (UST_MRT2026)<br>
  Shares = ROUNDDOWN(1250 / Entry, 0) · Target = PrevClose × 0.98
</div>
""", unsafe_allow_html=True)
