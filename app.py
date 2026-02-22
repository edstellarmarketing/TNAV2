"""
app.py — Edstellar LNA Platform
Main Streamlit entry point.
"""

import streamlit as st

st.set_page_config(
    page_title="Edstellar — LNA Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS injected once at app level ─────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=DM+Serif+Display&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F2447 0%, #1B3A6B 60%, #2E5BA8 100%);
    border-right: none;
}
section[data-testid="stSidebar"] * {
    color: rgba(255,255,255,0.88) !important;
}
section[data-testid="stSidebar"] .stRadio label {
    color: rgba(255,255,255,0.88) !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.15) !important;
}
.sidebar-brand {
    font-family: 'DM Serif Display', serif;
    font-size: 22px;
    font-weight: 400;
    color: #ffffff !important;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
}
.sidebar-tagline {
    font-size: 11px;
    color: rgba(255,255,255,0.55) !important;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 20px;
}
.nav-status {
    font-size: 11px;
    padding: 6px 12px;
    border-radius: 20px;
    display: inline-block;
    margin-top: 4px;
}
.nav-status.ready   { background: rgba(33,115,70,0.35); color: #7DFFB3 !important; }
.nav-status.pending { background: rgba(244,160,36,0.25); color: #F4C87A !important; }
.nav-status.locked  { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.4) !important; }

/* ── Page header banner ── */
.page-banner {
    background: linear-gradient(135deg, #1B3A6B 0%, #2E5BA8 100%);
    border-radius: 12px;
    padding: 28px 36px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    gap: 20px;
}
.page-banner-icon { font-size: 42px; }
.page-banner-title {
    font-family: 'DM Serif Display', serif;
    font-size: 26px;
    color: #ffffff;
    line-height: 1.2;
}
.page-banner-sub {
    font-size: 13px;
    color: rgba(255,255,255,0.65);
    margin-top: 4px;
}

/* ── Metric cards ── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 14px;
    margin: 16px 0;
}
.metric-card {
    background: white;
    border-radius: 10px;
    padding: 16px 18px;
    box-shadow: 0 2px 12px rgba(27,58,107,0.09);
    border-top: 4px solid #1B3A6B;
    border: 1px solid #E8EDF5;
    border-top: 4px solid #1B3A6B;
}
.metric-label {
    font-size: 10px;
    color: #6B7A99;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 6px;
    font-weight: 600;
}
.metric-value {
    font-size: 26px;
    font-weight: 800;
    color: #1B3A6B;
    line-height: 1;
}
.metric-unit {
    font-size: 13px;
    font-weight: 400;
    color: #9BA8B8;
    margin-left: 2px;
}

/* ── Status pills ── */
.pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
}
.pill-green  { background: #E8F5E9; color: #217346; }
.pill-orange { background: #FFF3E0; color: #E67E22; }
.pill-red    { background: #FFEBEE; color: #C0392B; }
.pill-blue   { background: #E3F2FD; color: #1B3A6B; }

/* ── Info boxes ── */
.info-box {
    background: linear-gradient(135deg, #EBF0FA, #F4F7FC);
    border: 1px solid #C3D0E8;
    border-left: 5px solid #1B3A6B;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 14px 0;
    font-size: 13px;
    line-height: 1.65;
}
.warn-box {
    background: #FFF8E1;
    border: 1px solid #FFE082;
    border-left: 5px solid #F4A024;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 12px 0;
    font-size: 13px;
}

/* ── Section divider ── */
.section-divider {
    border: none;
    border-top: 2px solid #E8EDF5;
    margin: 28px 0;
}

/* ── Hide Streamlit chrome ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-brand">EDSTELLAR</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tagline">LNA · Intelligence Platform</div>', unsafe_allow_html=True)
    st.divider()

    # Navigation status indicators
    data_loaded     = "lna_data" in st.session_state
    report_built    = "lna_html" in st.session_state
    strategy_done   = "strategy_profile" in st.session_state

    def nav_status(ready, label_ready, label_pending):
        cls = "ready" if ready else "pending"
        label = label_ready if ready else label_pending
        return f'<span class="nav-status {cls}">{label}</span>'

    st.markdown("**Navigation**")
    st.page_link("app.py",                          label="🏠 Home")
    st.page_link("pages/1_Upload.py",               label="📂 Upload Data")
    st.page_link("pages/2_LNA_Report.py",           label="📊 LNA / TNA Report")
    st.page_link("pages/3_Strategy_Config.py",      label="🎯 Strategy Configuration")
    st.page_link("pages/4_LNI_Report.py",           label="📋 LNI / TNI Report")

    st.divider()

    # Session state status
    st.markdown("**Session Status**")
    st.markdown(nav_status(data_loaded, "✅ Data loaded", "⏳ No data"), unsafe_allow_html=True)
    st.markdown(nav_status(report_built, "✅ LNA generated", "⏳ Not generated"), unsafe_allow_html=True)
    st.markdown(nav_status(strategy_done, "✅ Strategy locked", "⏳ Not configured"), unsafe_allow_html=True)

    if data_loaded:
        st.divider()
        d = st.session_state.lna_data
        st.markdown(f"**{d['company']}**")
        st.caption(f"{d['time_period']} {d['year']} · {len(d['active_emp'])} employees")

    st.divider()
    st.caption("Powered by Edstellar · v1.0")

# ── Home page content ─────────────────────────────────────────────────────────
st.markdown("""
<div class="page-banner">
    <div class="page-banner-icon">📊</div>
    <div>
        <div class="page-banner-title">Edstellar LNA Intelligence Platform</div>
        <div class="page-banner-sub">Learning Needs Analysis · Strategy Configuration · LNI/TNI Generation</div>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="metric-card" style="border-top-color:#1B3A6B">
        <div class="metric-label">Step 1</div>
        <div style="font-size:32px;margin:8px 0">📂</div>
        <div style="font-weight:700;color:#1B3A6B;font-size:15px;margin-bottom:6px">Upload Data</div>
        <div style="font-size:12px;color:#6B7A99;line-height:1.5">Upload your Employee Master Excel file. The platform validates all 17 required sheets automatically.</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card" style="border-top-color:#4472C4">
        <div class="metric-label">Step 2</div>
        <div style="font-size:32px;margin:8px 0">📊</div>
        <div style="font-weight:700;color:#1B3A6B;font-size:15px;margin-bottom:6px">LNA / TNA Report</div>
        <div style="font-size:12px;color:#6B7A99;line-height:1.5">Generate your full 17-section LNA report with 15 composite indices, gap analysis, and AI-powered insights.</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card" style="border-top-color:#F4A024">
        <div class="metric-label">Step 3 → 4</div>
        <div style="font-size:32px;margin:8px 0">🎯</div>
        <div style="font-weight:700;color:#1B3A6B;font-size:15px;margin-bottom:6px">Strategy → LNI/TNI</div>
        <div style="font-size:12px;color:#6B7A99;line-height:1.5">Configure leadership priorities, then generate your strategy-aligned LNI/TNI action report.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
    <strong>How to use this platform:</strong><br>
    Navigate using the sidebar. Start with <strong>Upload Data</strong>, then proceed in order.
    Each step builds on the previous — data flows automatically between pages via your session.
    All reports can be downloaded as standalone HTML files.
</div>
""", unsafe_allow_html=True)

# Quick start button
if not ("lna_data" in st.session_state):
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📂 Get Started — Upload Your Data →", type="primary", use_container_width=True):
        st.switch_page("pages/1_Upload.py")
else:
    st.success(f"✅ Data loaded: **{st.session_state.lna_data['company']}** · {len(st.session_state.lna_data['active_emp'])} employees")
    if st.button("📊 Go to LNA Report →", type="primary", use_container_width=True):
        st.switch_page("pages/2_LNA_Report.py")
