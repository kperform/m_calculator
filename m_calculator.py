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

Offline use:
  → Works fully without internet — type prev close manually, skip Fetch
  → If online, Fetch auto-fills the prev close field
  → Manual field is always visible and editable regardless

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
  .m-header .sub { font-size: 0.72rem; color: #8b949e; margin: 0; line-height: 1.5; }
  .m-header .badge {
    display: inline-block; background: #1f2d10; border: 1px solid #3fb950;
    color: #3fb950; font-size: 0.62rem; font-weight: 700; letter-spacing: .08em;
    padding: 2px 8px; border-radius: 20px; margin-top: 6px; text-transform: uppercase;
  }

  .card {
    background: #161b22; border: 1px solid #21262d;
    border-radius: 12px; padding: 16px; margin-bottom: 12px;
  }
  .card-title {
    font-size: 0.68rem; font-weight: 700; letter-spacing: .09em;
    text-transform: uppercase; color: #8b949e; margin-bottom: 12px;
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

  .big-block { text-align: center; padding: 16px 0 10px; }
  .big-block .lbl {
    font-size: 0.68rem; color: #8b949e; letter-spacing:.08em;
    text-transform: uppercase; margin-bottom: 5px;
  }
  .big-block .num  { font-size: 2.6rem; font-weight: 800; line-height: 1; }
  .big-block .unit { font-size: 0.78rem; color: #8b949e; margin-top: 3px; }

  .grid3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 12px; }
  .mini {
    background: #161b22; border: 1px solid #21262d;
    border-radius: 10px; padding: 11px 8px; text-align: center;
  }
  .mini .lbl { font-size: 0.60rem; color: #8b949e; text-transform: uppercase;
    letter-spacing:.06em; margin-bottom: 4px; }
  .mini .val { font-size: 1.05rem; font-weight: 700; }

  .alert { border-radius: 8px; padding: 10px 14px; font-size: 0.82rem;
    margin-bottom: 12px; line-height: 1.45; }
  .alert.warn  { background: #2d1f0a; border: 1px solid #e3b341; color: #e3b341; }
  .alert.ok    { background: #0a2d10; border: 1px solid #3fb950; color: #3fb950; }
  .alert.info  { background: #0a1f2d; border: 1px solid #58a6ff; color: #79c0ff; }
  .alert.error { background: #2d0a0a; border: 1px solid #f85149; color: #f85149; }

  .or-divider {
    display: flex; align-items: center; gap: 10px;
    margin: 6px 0 4px; color: #3d444d; font-size: 0.72rem;
  }
  .or-divider::before, .or-divider::after {
    content: ''; flex: 1; border-top: 1px solid #21262d;
  }

  .source-pill {
    display: inline-block; font-size: 0.62rem; font-weight: 700;
    letter-spacing: .06em; padding: 2px 8px; border-radius: 20px;
    text-transform: uppercase; margin-bottom: 4px;
  }
  .pill-live   { background: #0a2d10; border: 1px solid #3fb950; color: #3fb950; }
  .pill-manual { background: #2d1f0a; border: 1px solid #e3b341; color: #e3b341; }
  .pill-empty  { background: #161b22; border: 1px solid #30363d; color: #8b949e; }

  .section-label {
    font-size: 0.65rem; font-weight: 700; letter-spacing: .12em;
    text-transform: uppercase; color: #f0c040; margin: 16px 0 8px; padding-left: 2px;
  }

  [data-testid="stNumberInput"] input  { font-size: 1rem !important; }
  [data-testid="stNumberInput"] label,
  [data-testid="stTextInput"]   label  { font-size: 0.78rem !important; color: #8b949e !important; }
  [data-testid="stTextInput"] input {
    font-size: 1.1rem !important; font-weight: 700 !important; text-transform: uppercase;
  }
  [data-testid="stButton"] button {
    width: 100%; border-radius: 10px; font-size: 0.88rem; font-weight: 700; padding: 10px;
    background: #161b22; border: 1px solid #30363d; color: #79c0ff; margin-top: 2px;
  }
  [data-testid="stButton"] button:hover { background: #1c2330; border-color: #58a6ff; }
  footer, #MainMenu, header, [data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ── constants ────────────────────────────────────────────────────────────────
M_CAL_CAPITAL  = 1250.0
M_CAL_DISCOUNT = 0.02


# ── helpers ──────────────────────────────────────────────────────────────────
def fetch_prev_close(symbol: str):
    """Try yfinance. Returns (price, source, error)."""
    try:
        import yfinance as yf
        hist = yf.Ticker(symbol.upper()).history(period="5d")
        if hist.empty or len(hist) < 2:
            return None, None, "Not enough data — check the symbol."
        return float(hist["Close"].iloc[-2]), "live", None
    except ImportError:
        return None, None, "yfinance not installed. Run: pip install yfinance"
    except Exception as e:
        return None, None, str(e)[:120]


# ── session state ─────────────────────────────────────────────────────────────
for k, v in [("m_prev_close", 0.0), ("m_source", "empty"), ("m_msg", "")]:
    if k not in st.session_state:
        st.session_state[k] = v


# ── header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="m-header">
  <h1>M_Cal</h1>
  <span class="badge">M_CAL Strategy</span>
</div>
""", unsafe_allow_html=True)

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ M_Cal Settings")
    st.markdown("**Formulas from M_Calculator.xlsx:**")
    st.code(
        "Shares   = ROUNDDOWN(1250 / Entry, 0)\n"
        "CalPrice = Entry / 0.98  (= Prev Close)\n"
        "Target   = PrevClose × 0.98"
    )
    st.markdown("---")
    st.markdown(
        "**Offline mode** — skip Fetch entirely. "
        "Type the prev close directly into the field. "
        "All calculations run locally with no internet needed."
    )
    st.markdown("---")
    st.markdown("**Strategy Rules**")
    st.markdown("""

    """)


# ════════════════════════════════════════════════════════════════
# MODE TOGGLE
# ════════════════════════════════════════════════════════════════
st.markdown('<div class="section-label">Calculation Mode</div>', unsafe_allow_html=True)

mode = st.radio(
    "Choose what you want to enter:",
    options=["Mode A — I know the Prev Close → give me Entry Price & Shares",
             "Mode B — I know my Entry Price → give me Prev Close & Shares"],
    index=0,
    label_visibility="collapsed",
)
is_mode_a = mode.startswith("Mode A")

st.markdown('<div class="section-label">Trade Inputs</div>', unsafe_allow_html=True)

# ── Symbol (always shown) ─────────────────────────────────────────────────────
symbol = st.text_input("Stock Symbol", value="", placeholder="e.g. AAPL", max_chars=10)

# ── fetch button (online only — always optional) ──────────────────────────────
fetch_clicked = st.button("⬇  Auto-Fetch Prev Close  (skip this if offline)")

if fetch_clicked:
    sym = symbol.strip().upper()
    if not sym:
        st.session_state.m_msg = "error:Please enter a stock symbol first."
    else:
        with st.spinner(f"Fetching {sym}…"):
            price, source, err = fetch_prev_close(sym)
        if price:
            st.session_state.m_prev_close = round(price, 2)
            st.session_state.m_source     = "live"
            st.session_state.m_msg        = f"ok:✅ Fetched live prev close for {sym} — field pre-filled below."
        else:
            st.session_state.m_source = "manual"
            st.session_state.m_msg    = f"warn:⚠️ Fetch failed: {err} — Enter manually below."

if st.session_state.m_msg:
    kind, text = st.session_state.m_msg.split(":", 1)
    st.markdown(f'<div class="alert {kind}">{text}</div>', unsafe_allow_html=True)

st.markdown('<div class="or-divider">or type manually — works offline</div>', unsafe_allow_html=True)

# ── source pill ───────────────────────────────────────────────────────────────
src = st.session_state.m_source
pill_cls  = {"live": "pill-live", "manual": "pill-manual"}.get(src, "pill-empty")
pill_text = {"live": "🟢 Live — auto-filled", "manual": "🟡 Manual"}.get(src, "⬜ Waiting")
st.markdown(f'<span class="source-pill {pill_cls}">{pill_text}</span>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# MODE A — enter Prev Close → derive Entry + Shares
# ════════════════════════════════════════════════════════════════
if is_mode_a:

    prev_close_input = st.number_input(
        "Previous Day Close ($)",
        min_value=0.0,
        value=float(st.session_state.m_prev_close),
        step=0.01,
        format="%.2f",
        help="Auto-filled by Fetch when online. Type here directly when offline.",
    )
    if prev_close_input != st.session_state.m_prev_close:
        st.session_state.m_prev_close = prev_close_input
        if src != "live":
            st.session_state.m_source = "manual"

    prev_close = prev_close_input

    if prev_close > 0:
        # derived values
        ideal_entry  = prev_close * (1 - M_CAL_DISCOUNT)       # PrevClose × 0.98  ← entry target
        shares       = math.floor(M_CAL_CAPITAL / ideal_entry)  # ROUNDDOWN(1250 / ideal_entry, 0)
        capital_used = shares * ideal_entry

        sym_display = symbol.strip().upper() or "—"
        badge_cls   = "pill-live" if st.session_state.m_source == "live" else "pill-manual"
        badge_text  = "🟢 LIVE" if st.session_state.m_source == "live" else "🟡 MANUAL"

        st.markdown('<div class="section-label">M_Cal Results</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <span style="font-size:1.5rem;font-weight:800;color:#f0c040;letter-spacing:.04em;">{sym_display}</span>
            <span class="source-pill {badge_cls}">{badge_text}</span>
          </div>
          <div class="big-block">
            <div class="lbl">Shares to Buy</div>
            <div class="num green">{shares:,}</div>
            <div class="unit">@ ${ideal_entry:,.2f} entry &nbsp;·&nbsp; ${capital_used:,.2f} deployed</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="grid3">
          <div class="mini">
            <div class="lbl">Prev Close</div>
            <div class="val blue">${prev_close:,.2f}</div>
          </div>
          <div class="mini">
            <div class="lbl">Entry Target</div>
            <div class="val gold">${ideal_entry:,.2f}</div>
          </div>
          <div class="mini">
            <div class="lbl">Discount</div>
            <div class="val green">−2.00%</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="alert ok">
          ✅ Enter at <strong>${ideal_entry:,.2f}</strong> or below
          (2% discount from prev close of ${prev_close:,.2f}).
          Buy <strong>{shares:,} shares</strong> — deploying ${capital_used:,.2f} of $1,250.
        </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-label">Full Breakdown</div>', unsafe_allow_html=True)

        def render_card(title, rows):
            inner = "".join(
                f'<div class="res-row">'
                f'<span class="res-label">{lbl}</span>'
                f'<span class="res-value {cls}">{val}</span>'
                f'</div>'
                for lbl, val, cls in rows
            )
            st.markdown(
                f'<div class="card"><div class="card-title">{title}</div>{inner}</div>',
                unsafe_allow_html=True,
            )

        render_card("💰 Price Levels", [
            ("Prev Day Close",            f"${prev_close:,.2f}",   "blue"),
            ("Ideal Entry Price (−2%)",   f"${ideal_entry:,.2f}",  "gold"),
            ("M_Cal Cal Price (÷ 0.98)",  f"${prev_close:,.2f}",   ""),
        ])
        render_card("📐 Position Sizing (M_Cal)", [
            ("Shares  [ROUNDDOWN(1250 ÷ Entry, 0)]", f"{shares:,}",            "gold"),
            ("Capital Per Trade",                     f"${M_CAL_CAPITAL:,.0f}", ""),
            ("Capital Deployed",                      f"${capital_used:,.2f}",  "blue"),
            ("Unused Capital",                        f"${M_CAL_CAPITAL - capital_used:,.2f}", ""),
        ])

        with st.expander("📋 M_Cal Formula Reference", expanded=False):
            st.markdown(f"""
**Mode A — Know Prev Close, find Entry & Shares**
```
Ideal Entry = PrevClose × 0.98
            = {prev_close:.2f} × 0.98
            = {ideal_entry:.4f}

Shares = ROUNDDOWN(1250 / Ideal Entry, 0)
       = ROUNDDOWN(1250 / {ideal_entry:.2f}, 0)
       = {shares}
```
            """)

    else:
        st.markdown("""
        <div class="alert info">
          <strong>Mode A:</strong> Enter the previous day's close price above
          (or tap Fetch if online). M_Cal will calculate your ideal entry price
          and share count automatically.
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# MODE B — enter Entry Price → derive Prev Close + Shares
# ════════════════════════════════════════════════════════════════
else:

    entry_price = st.number_input(
        "Your Entry Price ($)",
        min_value=0.01,
        value=50.00,
        step=0.01,
        format="%.2f",
        help="Type the price you plan to enter at. M_Cal will back-calculate the implied prev close.",
    )

    if entry_price > 0:
        # derived values
        implied_prev  = entry_price / (1 - M_CAL_DISCOUNT)      # Entry / 0.98 ← col I
        shares        = math.floor(M_CAL_CAPITAL / entry_price)  # ROUNDDOWN(1250/entry,0)
        capital_used  = shares * entry_price

        # if a prev close was also fetched, validate entry against it
        fetched_prev  = st.session_state.m_prev_close
        has_fetched   = fetched_prev > 0
        if has_fetched:
            actual_ideal  = fetched_prev * (1 - M_CAL_DISCOUNT)
            entry_ok      = entry_price <= actual_ideal * 1.001
            discount_pct  = (fetched_prev - entry_price) / fetched_prev * 100
        else:
            entry_ok      = True
            discount_pct  = 2.0   # by definition when derived

        sym_display = symbol.strip().upper() or "—"
        badge_cls   = "pill-live" if st.session_state.m_source == "live" else "pill-manual"
        badge_text  = "🟢 LIVE" if st.session_state.m_source == "live" else "🟡 MANUAL"

        st.markdown('<div class="section-label">M_Cal Results</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <span style="font-size:1.5rem;font-weight:800;color:#f0c040;letter-spacing:.04em;">{sym_display}</span>
            <span class="source-pill {badge_cls}">{badge_text}</span>
          </div>
          <div class="big-block">
            <div class="lbl">Shares to Buy</div>
            <div class="num green">{shares:,}</div>
            <div class="unit">@ ${entry_price:,.2f} entry &nbsp;·&nbsp; ${capital_used:,.2f} deployed</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        disc_color = "green" if discount_pct >= 1.8 else "orange" if discount_pct >= 0 else "red"
        st.markdown(f"""
        <div class="grid3">
          <div class="mini">
            <div class="lbl">Implied Prev Close</div>
            <div class="val blue">${implied_prev:,.2f}</div>
          </div>
          <div class="mini">
            <div class="lbl">Your Entry</div>
            <div class="val gold">${entry_price:,.2f}</div>
          </div>
          <div class="mini">
            <div class="lbl">Discount</div>
            <div class="val {disc_color}">{discount_pct:+.2f}%</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # validation alert
        if has_fetched:
            if entry_ok:
                diff = actual_ideal - entry_price
                st.markdown(f"""
                <div class="alert ok">
                  ✅ Entry <strong>${entry_price:,.2f}</strong> is within the 2% threshold
                  of actual prev close (${fetched_prev:,.2f}). You are
                  <strong>${diff:,.2f} below</strong> the ideal entry of ${actual_ideal:,.2f}.
                </div>""", unsafe_allow_html=True)
            else:
                overshoot = entry_price - actual_ideal
                st.markdown(f"""
                <div class="alert warn">
                  ⚠️ Entry <strong>${entry_price:,.2f}</strong> exceeds the 2% discount target
                  of <strong>${actual_ideal:,.2f}</strong> (from actual prev close ${fetched_prev:,.2f})
                  by <strong>${overshoot:,.2f}</strong>.
                  Consider waiting for a pullback.
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="alert info">
              ℹ️ Implied Prev Close: <strong>${implied_prev:,.2f}</strong>
              (back-calculated as Entry ÷ 0.98).
              Tap Fetch if online to validate against the actual prev close.
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-label">Full Breakdown</div>', unsafe_allow_html=True)

        def render_card(title, rows):
            inner = "".join(
                f'<div class="res-row">'
                f'<span class="res-label">{lbl}</span>'
                f'<span class="res-value {cls}">{val}</span>'
                f'</div>'
                for lbl, val, cls in rows
            )
            st.markdown(
                f'<div class="card"><div class="card-title">{title}</div>{inner}</div>',
                unsafe_allow_html=True,
            )

        price_rows = [
            ("Your Entry Price",              f"${entry_price:,.2f}",  "gold"),
            ("Implied Prev Close (÷ 0.98)",   f"${implied_prev:,.2f}", "blue"),
        ]
        if has_fetched:
            price_rows += [
                ("Actual Prev Close (fetched)", f"${fetched_prev:,.2f}",          "blue"),
                ("Ideal Entry from Actual PC",  f"${fetched_prev*(1-M_CAL_DISCOUNT):,.2f}", "green" if entry_ok else "orange"),
                ("Discount to Actual PC",       f"{discount_pct:+.2f}%",           "green" if discount_pct >= 2.0 else "orange"),
            ]

        render_card("💰 Price Levels", price_rows)
        render_card("📐 Position Sizing (M_Cal)", [
            ("Shares  [ROUNDDOWN(1250 ÷ Entry, 0)]", f"{shares:,}",            "gold"),
            ("Capital Per Trade",                     f"${M_CAL_CAPITAL:,.0f}", ""),
            ("Capital Deployed",                      f"${capital_used:,.2f}",  "blue"),
            ("Unused Capital",                        f"${M_CAL_CAPITAL - capital_used:,.2f}", ""),
        ])

        with st.expander("📋 M_Cal Formula Reference", expanded=False):
            st.markdown(f"""
**Mode B — Know Entry Price, find Prev Close & Shares**
```
Implied Prev Close = Entry / 0.98
                   = {entry_price:.2f} / 0.98
                   = {implied_prev:.4f}

Shares = ROUNDDOWN(1250 / Entry, 0)
       = ROUNDDOWN(1250 / {entry_price:.2f}, 0)
       = {shares}
```
            """)

    else:
        st.markdown("""
        <div class="alert info">
          <strong>Mode B:</strong> Enter the price you plan to buy at above.
          M_Cal will back-calculate the implied previous day close and
          calculate your share count automatically.
        </div>
        """, unsafe_allow_html=True)


# ── footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:24px 0 8px;font-size:0.65rem;color:#3d444d;">
  M_Cal · Formulas from M_Calculator.xlsx (UST_M_CAL2026)<br>
  Shares = ROUNDDOWN(1250 / Entry, 0) · Target = PrevClose × 0.98<br>
  ✅ Works fully offline — all calculations are local
</div>
""", unsafe_allow_html=True)
