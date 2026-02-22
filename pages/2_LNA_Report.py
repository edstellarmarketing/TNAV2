"""
pages/2_LNA_Report.py — Edstellar LNA Platform
Page 2: LNA/TNA report generation with AI insights.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.metrics       import compute_all_metrics
from logic.report_builder import build_all_sections, assemble_html_report
from logic.ai_insights    import generate_all_insights, MODELS

st.set_page_config(
    page_title="LNA Report — Edstellar",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:serif;font-size:20px;color:white">EDSTELLAR</div>', unsafe_allow_html=True)
    st.caption("LNA · Intelligence Platform")
    st.divider()
    st.page_link("app.py",                     label="🏠 Home")
    st.page_link("pages/1_Upload.py",          label="📂 Upload Data")
    st.page_link("pages/2_LNA_Report.py",      label="📊 LNA / TNA Report")
    st.page_link("pages/3_Strategy_Config.py", label="🎯 Strategy Configuration")
    st.page_link("pages/4_LNI_Report.py",      label="📋 LNI / TNI Report")
    st.divider()
    if "lna_data" in st.session_state:
        d = st.session_state.lna_data
        st.success(f"✅ {d['company']}")
        st.caption(f"{len(d['active_emp'])} employees")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&family=DM+Serif+Display&display=swap');
html,[class*="css"]{font-family:'DM Sans',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
.page-banner{background:linear-gradient(135deg,#1B3A6B,#2E5BA8);border-radius:12px;padding:28px 36px;margin-bottom:28px;display:flex;align-items:center;gap:20px;}
.page-banner-title{font-family:'DM Serif Display',serif;font-size:26px;color:#fff;}
.page-banner-sub{font-size:13px;color:rgba(255,255,255,0.65);margin-top:4px;}
.config-card{background:#fff;border-radius:10px;padding:22px 26px;border:1px solid #E8EDF5;box-shadow:0 2px 10px rgba(27,58,107,0.07);margin-bottom:16px;}
.config-title{font-weight:700;font-size:15px;color:#1B3A6B;margin-bottom:14px;}
.kpi-strip{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0;}
.kpi-chip{background:#F4F7FC;border-radius:8px;padding:10px 14px;min-width:120px;border:1px solid #E8EDF5;}
.kpi-chip-label{font-size:10px;color:#6B7A99;text-transform:uppercase;letter-spacing:0.5px;}
.kpi-chip-value{font-size:20px;font-weight:800;color:#1B3A6B;}
.section-progress{background:#EBF0FA;border-radius:8px;padding:12px 16px;margin:6px 0;display:flex;justify-content:space-between;align-items:center;font-size:12px;}
</style>
""", unsafe_allow_html=True)

# ── Guard: require data ───────────────────────────────────────────────────────
if "lna_data" not in st.session_state:
    st.markdown("""
    <div class="page-banner">
        <div style="font-size:42px">📊</div>
        <div>
            <div class="page-banner-title">LNA / TNA Report</div>
            <div class="page-banner-sub">Upload your data first to generate the report</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.warning("⚠️ No data loaded. Please upload your Employee Master file first.")
    if st.button("📂 Go to Upload →", type="primary"):
        st.switch_page("pages/1_Upload.py")
    st.stop()

data = st.session_state.lna_data

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-banner">
    <div style="font-size:42px">📊</div>
    <div>
        <div class="page-banner-title">LNA / TNA Report</div>
        <div class="page-banner-sub">{data['company']} · {data['time_period']} {data['year']} · {len(data['active_emp'])} employees</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Compute metrics (cached in session) ───────────────────────────────────────
if "lna_metrics" not in st.session_state:
    with st.spinner("Computing all metrics and indices..."):
        st.session_state.lna_metrics = compute_all_metrics(data)

m = st.session_state.lna_metrics

# ── KPI snapshot strip ────────────────────────────────────────────────────────
st.markdown("### Key Metrics Snapshot")
kpi_items = [
    ("Employees",          m["N"],                        ""),
    ("Roles",              m["total_roles"],              ""),
    ("Locations",          m["total_locs"],               ""),
    ("Role Skill Coverage",f"{m['role_skill_cov']:.1f}", "%"),
    ("Critical Skills Idx",f"{m['crit_skills_idx']:.1f}","%"),
    ("Learning Penetration",f"{m['learning_pen_idx']:.1f}","%"),
    ("Cert Coverage",      f"{m['cert_cov_idx']:.1f}",   "%"),
    ("Q1 Urgent Skills",   len(m["q1_skills"]),           ""),
]
cols = st.columns(len(kpi_items))
for col, (label, val, unit) in zip(cols, kpi_items):
    with col:
        st.markdown(f"""
        <div class="kpi-chip">
            <div class="kpi-chip-label">{label}</div>
            <div class="kpi-chip-value">{val}<span style="font-size:13px;font-weight:400;color:#9BA8B8">{unit}</span></div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ── AI Configuration ──────────────────────────────────────────────────────────
st.markdown("### AI Insight Configuration")
st.markdown("""
<div style="background:#F4F7FC;border:1px solid #C3D0E8;border-left:5px solid #1B3A6B;border-radius:8px;padding:14px 18px;font-size:13px;margin-bottom:16px;">
    AI insights generate a professional narrative paragraph for each of the 17 report sections,
    referencing your actual data. <strong>Completely optional</strong> — skip to use data-driven fallback text.
    Get a free API key at <a href="https://openrouter.ai/keys" target="_blank">openrouter.ai/keys</a>.
</div>
""", unsafe_allow_html=True)

col_ai1, col_ai2 = st.columns([1, 1])
with col_ai1:
    st.markdown('<div class="config-card"><div class="config-title">🔑 API Key</div>', unsafe_allow_html=True)
    api_key = st.text_input(
        "OpenRouter API Key",
        type="password",
        placeholder="sk-or-v1-...",
        help="Entered securely — not stored anywhere in the app",
        label_visibility="collapsed",
    )
    st.caption("Leave blank to use data-driven fallback (no API required)")
    st.markdown('</div>', unsafe_allow_html=True)

with col_ai2:
    st.markdown('<div class="config-card"><div class="config-title">🤖 Select Model</div>', unsafe_allow_html=True)
    model_name = st.selectbox(
        "Model",
        options=list(MODELS.keys()),
        index=0,
        label_visibility="collapsed",
    )
    model_id = MODELS[model_name]
    cost_map = {
        "DeepSeek V3 (Free)": "Free · fast · strong quality",
        "DeepSeek R1 (Free)": "Free · reasoning model",
        "Gemini 2.0 Flash":   "~$0.005/report · very fast",
        "Gemini 2.5 Pro (Free)": "Free · high quality",
        "GPT-4o":             "~$0.05/report · highest quality prose",
        "Claude 3.5 Sonnet":  "~$0.04/report · best structured output",
        "Grok 2":             "~$0.02/report · strong business context",
    }
    st.caption(cost_map.get(model_name, ""))
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")

# ── Generate button ───────────────────────────────────────────────────────────
already_built = "lna_html" in st.session_state

col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
with col_btn1:
    generate_clicked = st.button(
        "⚡ Generate LNA Report" if not already_built else "🔄 Regenerate LNA Report",
        type="primary",
        use_container_width=True,
    )
with col_btn2:
    skip_ai = st.checkbox("Skip AI — use data-driven text", value=not bool(api_key))

if generate_clicked:
    # ── Step 1: AI Insights ───────────────────────────────────────────────────
    st.markdown("### Generating Report...")

    use_api_key = api_key if (api_key and not skip_ai) else ""
    use_model   = model_id if (api_key and not skip_ai) else ""

    progress_bar  = st.progress(0)
    status_text   = st.empty()
    section_log   = st.empty()
    log_lines     = []

    def on_progress(key, idx, total, status):
        pct = idx / total
        progress_bar.progress(pct)
        icon = "🤖" if status == "ai" else "📊"
        label = key.replace("_"," ").upper()
        log_lines.append(f"{icon} [{idx:02d}/{total}] {label}")
        status_text.markdown(f"**{icon} Processing section {idx} of {total}:** `{label}`")
        section_log.markdown(
            "<br>".join(f'<span style="font-size:11px;color:#6B7A99">{l}</span>' for l in log_lines[-5:]),
            unsafe_allow_html=True
        )

    with st.spinner(""):
        insights = generate_all_insights(
            data, m,
            api_key  = use_api_key,
            model_id = use_model,
            progress_callback = on_progress,
        )
        st.session_state.lna_insights = insights

    progress_bar.progress(1.0)
    mode_label = f"🤖 AI — {model_name}" if use_api_key else "📊 Data-driven fallback"
    status_text.success(f"✅ All 17 insights ready · Mode: {mode_label}")

    # ── Step 2: Build sections ────────────────────────────────────────────────
    with st.spinner("Building 17 report sections..."):
        sections = build_all_sections(data, m, insights)

    # ── Step 3: Assemble HTML ─────────────────────────────────────────────────
    with st.spinner("Assembling full HTML document..."):
        html_doc = assemble_html_report(data, sections)
        st.session_state.lna_html = html_doc

    st.success(f"✅ LNA Report generated · {len(html_doc)//1024} KB · 17 sections · 15 composite indices")
    st.balloons()

# ── Show report preview and download ─────────────────────────────────────────
if "lna_html" in st.session_state:
    html_doc = st.session_state.lna_html

    st.markdown("---")
    st.markdown("### Report Actions")

    col_dl, col_prev, col_next = st.columns([2, 1, 2])

    with col_dl:
        filename = (
            f"LNA_Level1_{data['company'].replace(' ','_')}"
            f"_{data['time_period']}_{data['year'].replace('-','_')}.html"
        )
        st.download_button(
            label="⬇️ Download LNA Report (HTML)",
            data=html_doc.encode("utf-8"),
            file_name=filename,
            mime="text/html",
            use_container_width=True,
            type="primary",
        )

    with col_next:
        if st.button("🎯 Proceed to Strategy Configuration →", use_container_width=True):
            st.switch_page("pages/3_Strategy_Config.py")

    # ── Inline preview ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Report Preview")
    st.caption("Full interactive report — scroll to explore all 17 sections")

    st.components.v1.html(html_doc, height=900, scrolling=True)

    st.markdown("---")
    st.markdown("### Composite Indices Summary")

    composite = m["composite"]
    c1, c2, c3 = st.columns(3)
    for i, (name, (val, threshold, direction)) in enumerate(composite.items()):
        col = [c1, c2, c3][i % 3]
        with col:
            if direction == "higher":
                ok = val >= threshold
                delta = val - threshold
                color = "#217346" if ok else ("#E67E22" if val >= threshold * 0.75 else "#C0392B")
                status = "✅" if ok else ("⚠️" if val >= threshold * 0.75 else "❌")
            elif direction == "lower":
                ok = val <= threshold
                delta = -(val - threshold)
                color = "#217346" if ok else ("#E67E22" if val <= threshold * 1.3 else "#C0392B")
                status = "✅" if ok else ("⚠️" if val <= threshold * 1.3 else "❌")
            else:
                color = "#1B3A6B"; status = "ℹ️"; delta = 0

            st.markdown(f"""
            <div style="background:#fff;border-radius:8px;padding:12px 16px;
                        border:1px solid #E8EDF5;border-left:5px solid {color};margin-bottom:10px;">
                <div style="font-size:10px;color:#6B7A99;text-transform:uppercase;letter-spacing:0.5px">{name}</div>
                <div style="font-size:22px;font-weight:800;color:{color}">{val:.1f}%</div>
                <div style="font-size:11px;color:#9BA8B8">{status} Target: {threshold}%</div>
            </div>
            """, unsafe_allow_html=True)
