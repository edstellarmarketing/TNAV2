"""
pages/4_LNI_Report.py — Edstellar LNA Platform
Page 4: LNI/TNI Report generation using LNA data + Strategy Profile.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.metrics     import compute_all_metrics
from logic.strategy    import apply_strategy_weights
from logic.lni_builder import build_lni_report

st.set_page_config(
    page_title="LNI/TNI Report — Edstellar",
    page_icon="📋",
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
    if "strategy_profile" in st.session_state:
        sp = st.session_state.strategy_profile
        st.info(f"🎯 {sp['version']} locked")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&family=DM+Serif+Display&display=swap');
html,[class*="css"]{font-family:'DM Sans',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
.page-banner{background:linear-gradient(135deg,#2E1760,#4A2AB8);border-radius:12px;padding:28px 36px;margin-bottom:28px;display:flex;align-items:center;gap:20px;}
.page-banner-title{font-family:'DM Serif Display',serif;font-size:26px;color:#fff;}
.page-banner-sub{font-size:13px;color:rgba(255,255,255,0.65);margin-top:4px;}
.kpi-chip{background:#F4F7FC;border-radius:8px;padding:10px 14px;border:1px solid #E8EDF5;}
.kpi-chip-label{font-size:10px;color:#6B7A99;text-transform:uppercase;letter-spacing:0.5px;}
.kpi-chip-value{font-size:20px;font-weight:800;color:#1B3A6B;}
.strategy-badge{background:linear-gradient(135deg,#0F4C2F,#1A7A50);border-radius:10px;padding:14px 20px;color:white;margin-bottom:16px;}
.sb-version{font-size:11px;color:rgba(255,255,255,0.5);margin-top:8px;}
.prereq-card{background:#fff;border-radius:10px;padding:20px 24px;border:1px solid #E8EDF5;box-shadow:0 2px 10px rgba(27,58,107,0.07);margin-bottom:12px;}
.prereq-done{border-left:5px solid #217346;}
.prereq-pending{border-left:5px solid #E67E22;}
</style>
""", unsafe_allow_html=True)

# ── Guards: check prerequisites ───────────────────────────────────────────────
data_loaded     = "lna_data" in st.session_state
metrics_ready   = "lna_metrics" in st.session_state
strategy_ready  = "strategy_profile" in st.session_state

st.markdown("""
<div class="page-banner">
    <div style="font-size:42px">📋</div>
    <div>
        <div class="page-banner-title">LNI / TNI Report</div>
        <div class="page-banner-sub">Strategy-aligned Learning & Training Needs Identification — combining LNA data with leadership priorities</div>
    </div>
</div>
""", unsafe_allow_html=True)

if not data_loaded or not strategy_ready:
    st.warning("⚠️ Prerequisites not complete. Complete the steps below before generating the LNI/TNI report.")

    col1, col2, col3 = st.columns(3)

    with col1:
        cls = "prereq-done" if data_loaded else "prereq-pending"
        icon = "✅" if data_loaded else "⏳"
        detail = f"{len(st.session_state.lna_data['active_emp'])} employees loaded" if data_loaded else "Upload your Employee Master Excel"
        st.markdown(f"""
        <div class="prereq-card {cls}">
            <div style="font-size:24px">{icon}</div>
            <div style="font-weight:700;color:#1B3A6B;margin:6px 0">Step 1: Upload Data</div>
            <div style="font-size:12px;color:#6B7A99">{detail}</div>
        </div>
        """, unsafe_allow_html=True)
        if not data_loaded:
            st.button("📂 Upload Data →", key="btn_upload", on_click=lambda: st.switch_page("pages/1_Upload.py"))

    with col2:
        cls = "prereq-done" if metrics_ready else "prereq-pending"
        icon = "✅" if metrics_ready else "⏳"
        detail = "LNA metrics computed" if metrics_ready else "Generate the LNA/TNA report first"
        st.markdown(f"""
        <div class="prereq-card {cls}">
            <div style="font-size:24px">{icon}</div>
            <div style="font-weight:700;color:#1B3A6B;margin:6px 0">Step 2: LNA Report</div>
            <div style="font-size:12px;color:#6B7A99">{detail}</div>
        </div>
        """, unsafe_allow_html=True)
        if data_loaded and not metrics_ready:
            if st.button("📊 Generate LNA Report →", key="btn_lna"):
                st.switch_page("pages/2_LNA_Report.py")

    with col3:
        cls = "prereq-done" if strategy_ready else "prereq-pending"
        icon = "✅" if strategy_ready else "⏳"
        if strategy_ready:
            sp = st.session_state.strategy_profile
            detail = f"{sp['version']} · confirmed by {sp['confirmed_by']}"
        else:
            detail = "Configure and lock leadership priorities"
        st.markdown(f"""
        <div class="prereq-card {cls}">
            <div style="font-size:24px">{icon}</div>
            <div style="font-weight:700;color:#1B3A6B;margin:6px 0">Step 3: Strategy Config</div>
            <div style="font-size:12px;color:#6B7A99">{detail}</div>
        </div>
        """, unsafe_allow_html=True)
        if not strategy_ready:
            if st.button("🎯 Configure Strategy →", key="btn_strategy", type="primary"):
                st.switch_page("pages/3_Strategy_Config.py")

    st.stop()

# ── All prerequisites met ─────────────────────────────────────────────────────
data    = st.session_state.lna_data
m       = st.session_state.lna_metrics
profile = st.session_state.strategy_profile

# Strategy badge
st.markdown(f"""
<div class="strategy-badge">
    <div style="font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:rgba(255,255,255,0.6);margin-bottom:8px">
        🎯 Strategy Configuration Applied
    </div>
    <div style="font-size:13px;line-height:1.6;color:rgba(255,255,255,0.9)">{profile['strategic_summary']}</div>
    <div class="sb-version">{profile['version']} · Confirmed by {profile['confirmed_by']} · {profile['created_display']} · {profile['time_horizon']}</div>
</div>
""", unsafe_allow_html=True)

# KPI strip
q1 = m.get("q1_skills", None)
q1_count = len(q1) if q1 is not None and not (hasattr(q1, "empty") and q1.empty) else 0

kpi_items = [
    ("Employees",            m["N"],                         ""),
    ("Q1 Priority Skills",   q1_count,                       ""),
    ("Role Skill Coverage",  f"{m['role_skill_cov']:.1f}",   "%"),
    ("Critical Skills Idx",  f"{m['crit_skills_idx']:.1f}",  "%"),
    ("Learning Penetration", f"{m['learning_pen_idx']:.1f}", "%"),
    ("Strategy Version",     profile["version"],             ""),
    ("Time Horizon",         profile["time_horizon"].split("(")[0].strip(), ""),
    ("Segments",             len(profile.get("employee_segments", [])) or "All", ""),
]

cols = st.columns(len(kpi_items))
for col, (label, val, unit) in zip(cols, kpi_items):
    with col:
        st.markdown(f"""
        <div class="kpi-chip">
            <div class="kpi-chip-label">{label}</div>
            <div class="kpi-chip-value">{val}<span style="font-size:12px;color:#9BA8B8">{unit}</span></div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ── Generate button ───────────────────────────────────────────────────────────
already_built = "lni_html" in st.session_state

col_btn, col_regen = st.columns([3, 1])
with col_btn:
    generate_clicked = st.button(
        "⚡ Generate LNI/TNI Report" if not already_built else "🔄 Regenerate LNI/TNI Report",
        type="primary",
        use_container_width=True,
    )
with col_regen:
    if already_built:
        if st.button("🎯 Update Strategy →", use_container_width=True):
            st.switch_page("pages/3_Strategy_Config.py")

if generate_clicked:
    with st.spinner("Applying strategy weights to LNA data..."):
        weighted_m = apply_strategy_weights(m, profile)

    with st.spinner("Building 10-section LNI/TNI report..."):
        lni_html = build_lni_report(data, weighted_m, profile)
        st.session_state.lni_html = lni_html

    conflicts = profile.get("conflicts", [])
    conflict_note = f" · {len(conflicts)} strategic override(s) recorded" if conflicts else ""
    st.success(f"✅ LNI/TNI Report generated · {len(lni_html)//1024} KB · 10 sections · Strategy {profile['version']}{conflict_note}")
    st.balloons()

# ── Download and preview ──────────────────────────────────────────────────────
if "lni_html" in st.session_state:
    lni_html = st.session_state.lni_html

    st.markdown("---")
    st.markdown("### Report Actions")

    filename = (
        f"LNI_TNI_{data['company'].replace(' ','_')}"
        f"_{data['time_period']}_{data['year'].replace('-','_')}"
        f"_{profile['version']}.html"
    )

    col_dl1, col_dl2, col_back = st.columns([2, 2, 1])

    with col_dl1:
        st.download_button(
            "⬇️ Download LNI/TNI Report (HTML)",
            data=lni_html.encode("utf-8"),
            file_name=filename,
            mime="text/html",
            use_container_width=True,
            type="primary",
        )

    with col_dl2:
        # Also offer LNA download if it exists
        if "lna_html" in st.session_state:
            lna_filename = (
                f"LNA_Level1_{data['company'].replace(' ','_')}"
                f"_{data['time_period']}_{data['year'].replace('-','_')}.html"
            )
            st.download_button(
                "⬇️ Download LNA Report (HTML)",
                data=st.session_state.lna_html.encode("utf-8"),
                file_name=lna_filename,
                mime="text/html",
                use_container_width=True,
            )

    with col_back:
        if st.button("🎯 Edit Strategy", use_container_width=True):
            st.switch_page("pages/3_Strategy_Config.py")

    # ── Report preview ─────────────────────────────────────────────────────────
    st.markdown("---")

    # Conflict warnings summary above preview
    conflicts = profile.get("conflicts", [])
    if conflicts:
        with st.expander(f"⚠️ {len(conflicts)} Strategic Override(s) in This Report", expanded=False):
            for c in conflicts:
                sev = c.get("severity","info")
                bg = "#FFEBEE" if sev=="critical" else ("#FFF8E1" if sev=="warning" else "#E3F2FD")
                j = profile.get("justifications",{}).get(c.get("dimension",""),"")
                j_html = f"<br><em>Justification: {j}</em>" if j else ""
                st.markdown(f"""
                <div style="background:{bg};border-radius:6px;padding:10px 14px;margin:6px 0;font-size:12px">
                    <strong>{c['dimension']}</strong><br>{c['message']}{j_html}
                </div>
                """, unsafe_allow_html=True)

    st.markdown("### LNI/TNI Report Preview")
    st.caption("Full 10-section strategy-aligned report — scroll to explore")
    st.components.v1.html(lni_html, height=1000, scrolling=True)

    # ── Section summary outside preview ───────────────────────────────────────
    st.markdown("---")
    st.markdown("### Sections in This Report")

    section_names = [
        ("1", "Strategic Intent Summary",       "Leadership configuration that governs this report"),
        ("2", "Priority Training Needs",        "Strategy-weighted skills from LNA quadrant analysis"),
        ("3", "Segment-Level Recommendations",  "Training design per employee segment"),
        ("4", "Business Unit Focus",            "Scope amplification for priority areas"),
        ("5", "Learning Programme Design",      "Format, delivery mode, and design guidance"),
        ("6", "Learning Investment Plan",       "Budget allocation by segment weight"),
        ("7", "30-60-90 Day Roadmap",          "Execution plan for the time horizon selected"),
        ("8", "Composite Indices & Metrics",    "LNA baseline targets and improvement goals"),
        ("9", "Risk & Override Register",       "Execution risks and strategic override documentation"),
        ("10","Measurement & Next Steps",       "How to measure success and trigger Level 2 LNA"),
    ]

    c1, c2 = st.columns(2)
    for i, (num, title, desc) in enumerate(section_names):
        col = c1 if i % 2 == 0 else c2
        with col:
            st.markdown(f"""
            <div style="display:flex;gap:10px;padding:10px 12px;background:#fff;border-radius:8px;
                        border:1px solid #E8EDF5;margin-bottom:8px;align-items:center">
                <div style="background:#2E1760;color:white;width:28px;height:28px;border-radius:50%;
                            display:flex;align-items:center;justify-content:center;
                            font-weight:800;font-size:12px;flex-shrink:0">{num}</div>
                <div>
                    <div style="font-weight:700;font-size:13px;color:#1B3A6B">{title}</div>
                    <div style="font-size:11px;color:#9BA8B8">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
