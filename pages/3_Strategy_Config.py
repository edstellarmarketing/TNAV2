"""
pages/3_Strategy_Config.py — Edstellar LNA Platform
Page 3: Leadership Talent Strategy Configuration.
Interactive configuration of priorities that govern LNI/TNI generation.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.strategy import (
    build_strategy_profile,
    detect_conflicts,
    CULTURAL_OPTIONS,
    SKILL_DIMENSIONS,
    EMPLOYEE_SEGMENTS,
    TIME_HORIZONS,
)

st.set_page_config(
    page_title="Strategy Configuration — Edstellar LNA",
    page_icon="🎯",
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
        st.info(f"🎯 Strategy {sp['version']} locked")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&family=DM+Serif+Display&display=swap');
html,[class*="css"]{font-family:'DM Sans',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
.page-banner{background:linear-gradient(135deg,#0F4C2F,#1A7A50);border-radius:12px;padding:28px 36px;margin-bottom:28px;display:flex;align-items:center;gap:20px;}
.page-banner-title{font-family:'DM Serif Display',serif;font-size:26px;color:#fff;}
.page-banner-sub{font-size:13px;color:rgba(255,255,255,0.65);margin-top:4px;}
.section-card{background:#fff;border-radius:12px;padding:24px 28px;margin-bottom:20px;border:1px solid #E8EDF5;box-shadow:0 2px 10px rgba(27,58,107,0.07);}
.section-card-title{font-size:16px;font-weight:700;color:#1B3A6B;margin-bottom:4px;}
.section-card-sub{font-size:12px;color:#9BA8B8;margin-bottom:18px;}
.lna-context{background:#F4F7FC;border:1px solid #C3D0E8;border-left:5px solid #1B3A6B;border-radius:8px;padding:12px 16px;font-size:12px;color:#2D3748;margin-bottom:14px;}
.lna-context strong{color:#1B3A6B;}
.conflict-warn{background:#FFF8E1;border:1px solid #FFE082;border-left:5px solid #F4A024;border-radius:8px;padding:12px 16px;font-size:12px;margin:8px 0;}
.conflict-crit{background:#FFEBEE;border:1px solid #F5C6CB;border-left:5px solid #C0392B;border-radius:8px;padding:12px 16px;font-size:12px;margin:8px 0;}
.confirm-box{background:linear-gradient(135deg,#0F2447,#1B3A6B);border-radius:12px;padding:24px 28px;margin-top:24px;color:white;}
.confirm-title{font-size:18px;font-weight:700;margin-bottom:8px;}
.confirm-sub{font-size:12px;color:rgba(255,255,255,0.65);margin-bottom:18px;}
.strategy-preview{background:rgba(255,255,255,0.1);border-radius:8px;padding:14px 18px;font-size:13px;line-height:1.6;color:rgba(255,255,255,0.9);margin-bottom:16px;}
.locked-banner{background:#E8F5E9;border:2px solid #217346;border-radius:10px;padding:18px 22px;margin-bottom:20px;}
.locked-title{font-weight:700;color:#217346;font-size:15px;margin-bottom:4px;}
.locked-sub{font-size:12px;color:#388E3C;}
</style>
""", unsafe_allow_html=True)

# ── Guard: require LNA data ───────────────────────────────────────────────────
if "lna_data" not in st.session_state:
    st.markdown("""
    <div class="page-banner">
        <div style="font-size:42px">🎯</div>
        <div>
            <div class="page-banner-title">Strategy Configuration</div>
            <div class="page-banner-sub">Upload your data and generate the LNA report first</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.warning("⚠️ No data loaded. Complete Steps 1 and 2 before configuring strategy.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📂 Upload Data →", use_container_width=True):
            st.switch_page("pages/1_Upload.py")
    with col2:
        if st.button("📊 Generate LNA Report →", use_container_width=True):
            st.switch_page("pages/2_LNA_Report.py")
    st.stop()

data = st.session_state.lna_data
m    = st.session_state.get("lna_metrics", {})

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-banner">
    <div style="font-size:42px">🎯</div>
    <div>
        <div class="page-banner-title">Talent & Capability Strategy Configuration</div>
        <div class="page-banner-sub">{data['company']} · {data['time_period']} {data['year']} · Configure leadership priorities for LNI/TNI generation</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Already locked — show read-only view ────────────────────────────────────
if "strategy_profile" in st.session_state and not st.session_state.get("strategy_editing", False):
    sp = st.session_state.strategy_profile

    st.markdown(f"""
    <div class="locked-banner">
        <div class="locked-title">✅ Strategy Configuration Locked — {sp['version']}</div>
        <div class="locked-sub">Confirmed by {sp['confirmed_by']} · {sp['created_display']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.info(f"**Strategic Context Summary:** {sp['strategic_summary']}")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("✏️ Edit Configuration", use_container_width=True):
            st.session_state.strategy_editing = True
            st.rerun()
    with col2:
        # Download config as HTML
        config_html = _build_config_html(sp, data, m)
        st.download_button(
            "⬇️ Download Config Summary",
            data=config_html.encode("utf-8"),
            file_name=f"Strategy_Config_{sp['version']}_{data['company'].replace(' ','_')}.html",
            mime="text/html",
            use_container_width=True,
        )
    with col3:
        if st.button("📋 Proceed to LNI/TNI Report →", type="primary", use_container_width=True):
            st.switch_page("pages/4_LNI_Report.py")

    # Preview summary
    st.markdown("---")
    st.markdown("### Configuration Summary")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Cultural Priorities**")
        for p in sp["cultural_priorities"]:
            st.markdown(f"• {p}")
        st.markdown("**Employee Segments**")
        for s in sp["employee_segments"]:
            st.markdown(f"• {s}")
    with c2:
        st.markdown("**Skill Emphasis Weights**")
        for dim, val in sp["skill_sliders"].items():
            bar = "▓" * abs(val) if val != 0 else "○"
            sign = "+" if val > 0 else ("–" if val < 0 else "")
            color = "🟢" if val > 0 else ("🔴" if val < 0 else "⚪")
            st.markdown(f"{color} {dim}: **{sign}{abs(val) if val != 0 else '0'}** {bar}")
        st.markdown(f"**Time Horizon:** {sp['time_horizon']}")
        st.markdown(f"**Org Focus:** {', '.join(sp['org_focus']) or 'All BUs'}")

    st.stop()


# ── Helper: build config HTML download ────────────────────────────────────────
def _build_config_html(sp: dict, data: dict, m: dict) -> str:
    """Generate a shareable HTML summary of the confirmed strategy configuration."""
    conflicts_html = ""
    for c in sp.get("conflicts", []):
        sev = c.get("severity", "info")
        bg  = "#FFEBEE" if sev == "critical" else ("#FFF8E1" if sev == "warning" else "#E3F2FD")
        border = "#C0392B" if sev == "critical" else ("#F4A024" if sev == "warning" else "#1B3A6B")
        j = sp.get("justifications", {}).get(c.get("dimension", ""), "")
        j_html = f'<p style="font-style:italic;margin-top:6px;color:#555">Justification: {j}</p>' if j else ""
        conflicts_html += f"""
        <div style="background:{bg};border-left:5px solid {border};border-radius:6px;padding:12px 16px;margin:8px 0;font-size:12px">
            <strong>{c.get('dimension','')}</strong><br>{c.get('message','')}
            {j_html}
        </div>"""

    sliders_html = ""
    for dim, val in sp["skill_sliders"].items():
        pct = (val + 3) / 6 * 100
        color = "#217346" if val > 0 else ("#C0392B" if val < 0 else "#9BA8B8")
        sign = "+" if val > 0 else ""
        sliders_html += f"""
        <div style="margin-bottom:12px">
            <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">
                <span style="font-weight:600">{dim}</span>
                <span style="font-weight:800;color:{color}">{sign}{val}</span>
            </div>
            <div style="background:#E8EDF5;border-radius:4px;height:8px">
                <div style="background:{color};width:{pct}%;height:8px;border-radius:4px"></div>
            </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Strategy Configuration — {data['company']}</title>
<style>
body{{font-family:'Segoe UI',sans-serif;background:#F0F3F8;color:#1A1A2E;margin:0;padding:24px}}
.wrap{{max-width:900px;margin:0 auto}}
.header{{background:linear-gradient(135deg,#0F4C2F,#1A7A50);border-radius:12px;padding:28px 36px;color:white;margin-bottom:24px}}
.h-title{{font-size:26px;font-weight:800;margin-bottom:6px}}
.h-sub{{font-size:13px;opacity:.7}}
.h-meta{{display:flex;gap:24px;margin-top:16px;flex-wrap:wrap}}
.h-meta-item{{font-size:11px;opacity:.6}}
.h-meta-item strong{{font-size:13px;opacity:1;display:block}}
.card{{background:white;border-radius:10px;padding:22px 26px;margin-bottom:16px;border:1px solid #E8EDF5}}
.card-title{{font-size:14px;font-weight:700;color:#1B3A6B;margin-bottom:14px;padding-bottom:8px;border-bottom:2px solid #E8EDF5}}
.pill{{display:inline-block;background:#EBF0FA;border:1px solid #C3D0E8;border-radius:20px;padding:4px 12px;font-size:12px;font-weight:600;color:#1B3A6B;margin:3px}}
.summary{{background:#F0FBF4;border:1px solid #C3E6CB;border-left:5px solid #217346;border-radius:8px;padding:14px 18px;font-size:13px;line-height:1.65}}
.footer{{text-align:center;color:#9BA8B8;font-size:11px;padding:24px;margin-top:16px}}
.draft-watermark{{background:#FFF8E1;border:2px solid #FFE082;border-radius:8px;padding:12px 18px;text-align:center;font-size:13px;font-weight:700;color:#E67E22;margin-bottom:20px}}
</style>
</head>
<body>
<div class="wrap">
    <div class="header">
        <div class="h-title">Talent & Capability Strategy Configuration</div>
        <div class="h-sub">{data['company']} · {data['time_period']} {data['year']}</div>
        <div class="h-meta">
            <div class="h-meta-item"><strong>{sp['version']}</strong>Version</div>
            <div class="h-meta-item"><strong>{sp['created_display']}</strong>Confirmed</div>
            <div class="h-meta-item"><strong>{sp['confirmed_by']}</strong>Confirmed By</div>
            <div class="h-meta-item"><strong>{sp['confirmed_role'] or '—'}</strong>Role</div>
            <div class="h-meta-item"><strong>{sp['time_horizon'].split('(')[0].strip()}</strong>Horizon</div>
        </div>
    </div>

    <div class="card">
        <div class="card-title">🎯 Strategic Context Summary</div>
        <div class="summary">{sp['strategic_summary']}</div>
    </div>

    <div class="card">
        <div class="card-title">🌟 Cultural & Behavioural Priorities</div>
        {"".join(f'<span class="pill">{p}</span>' for p in sp['cultural_priorities']) or '<span style="color:#9BA8B8">None selected</span>'}
    </div>

    <div class="card">
        <div class="card-title">⚖️ Skills & Competency Emphasis</div>
        {sliders_html}
    </div>

    <div class="card">
        <div class="card-title">🏢 Organisational Focus Areas</div>
        {"".join(f'<span class="pill">{o}</span>' for o in sp['org_focus']) or '<span style="color:#9BA8B8">All business units</span>'}
    </div>

    <div class="card">
        <div class="card-title">👥 Employee Segment Priorities</div>
        {"".join(f'<span class="pill">{s}</span>' for s in sp['employee_segments']) or '<span style="color:#9BA8B8">All employees</span>'}
    </div>

    <div class="card">
        <div class="card-title">⏱️ Time Horizon</div>
        <strong>{sp['time_horizon']}</strong>
    </div>

    {'<div class="card"><div class="card-title">⚠️ Strategic Overrides Recorded</div>' + conflicts_html + '</div>' if sp.get('conflicts') else ''}

    <div class="footer">
        Edstellar LNA Intelligence Platform · Strategy Configuration {sp['version']} · {sp['created_display']}<br>
        This document is confidential and intended for authorised HR and leadership review only.
        <br><br>
        <strong style="color:#217346">✅ CONFIRMED</strong> — This configuration is locked and has been used to generate the LNI/TNI report.
    </div>
</div>
</body>
</html>"""


# ── Configuration Form ────────────────────────────────────────────────────────

st.markdown("""
<div style="background:#FFF8E1;border:1px solid #FFE082;border-left:5px solid #F4A024;border-radius:8px;padding:14px 18px;font-size:13px;margin-bottom:24px">
    <strong>How this works:</strong> Configure your strategic priorities below. These selections
    will be applied as weighting signals when generating the LNI/TNI report — adjusting which
    skills, segments, and areas are prioritised relative to the raw LNA data.
    <strong>Conflicts between your intent and the LNA data will be flagged in real time.</strong>
</div>
""", unsafe_allow_html=True)

# LNA context strip (auto-populated from session)
if m:
    st.markdown(f"""
    <div class="lna-context">
        <strong>📊 Configuring against LNA baseline:</strong>
        {m.get('N',0)} employees · {m.get('total_roles',0)} roles · {m.get('total_locs',0)} locations ·
        Role Skill Coverage <strong>{m.get('role_skill_cov',0):.1f}%</strong> ·
        Critical Skills Index <strong>{m.get('crit_skills_idx',0):.1f}%</strong> ·
        Q1 Urgent Skills <strong>{len(m.get('q1_skills',[])) if m.get('q1_skills') is not None else 0}</strong> ·
        Learning Penetration <strong>{m.get('learning_pen_idx',0):.1f}%</strong>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ── SECTION 1: Cultural Direction ─────────────────────────────────────────────
st.markdown("""
<div class="section-card">
    <div class="section-card-title">🌟 Section 1 — Culture & Behavioural Direction</div>
    <div class="section-card-sub">Select up to 5 cultural attributes to reinforce through talent development this cycle</div>
</div>
""", unsafe_allow_html=True)

cultural_selected = st.multiselect(
    "Cultural priorities (max 5 recommended)",
    options=CULTURAL_OPTIONS,
    default=st.session_state.get("draft_cultural", []),
    max_selections=5,
    help="These become behavioral competency amplification signals in the LNI/TNI",
    label_visibility="collapsed",
)
st.session_state.draft_cultural = cultural_selected

if cultural_selected:
    st.success(f"✅ {len(cultural_selected)} priorities selected: {', '.join(cultural_selected)}")
else:
    st.caption("No cultural priorities selected — balanced baseline will be applied")

st.markdown("---")

# ── SECTION 2: Skill Emphasis Sliders ────────────────────────────────────────
st.markdown("""
<div class="section-card">
    <div class="section-card-title">⚖️ Section 2 — Skills & Competency Emphasis</div>
    <div class="section-card-sub">Adjust emphasis relative to what the LNA data shows. +3 = highest emphasis · 0 = maintain baseline · –3 = deprioritise for this cycle</div>
</div>
""", unsafe_allow_html=True)

# Get default values from any existing draft
draft_sliders = st.session_state.get("draft_sliders", {dim: 0 for dim in SKILL_DIMENSIONS})

skill_sliders = {}
conflict_candidates = []

# LNA context for each dimension
lna_context = {
    "Technical / Functional Skills":  f"Role Skill Coverage: {m.get('role_skill_cov',0):.1f}%",
    "Leadership & People Skills":     f"Manager ratio: {m.get('manager_ratio',0):.1f}% · Span of control: {m.get('span_of_ctrl',0):.1f}",
    "Behavioral & Cultural Skills":   f"Critical Skills Index: {m.get('crit_skills_idx',0):.1f}%",
    "Digital / Future Skills":        f"Skill Scarcity Index: {m.get('skill_scarcity_idx',0):.1f}%",
    "Compliance & Risk Skills":       f"Cert Coverage: {m.get('cert_cov_idx',0):.1f}% · Expired certs: {m.get('expired_certs',0)}",
} if m else {}

for dim in SKILL_DIMENSIONS:
    col_label, col_slider, col_value = st.columns([3, 4, 1])

    with col_label:
        st.markdown(f"**{dim}**")
        if dim in lna_context:
            st.caption(f"📊 {lna_context[dim]}")

    with col_slider:
        val = st.slider(
            dim,
            min_value=-3,
            max_value=3,
            value=draft_sliders.get(dim, 0),
            step=1,
            label_visibility="collapsed",
            key=f"slider_{dim}",
        )
        skill_sliders[dim] = val

    with col_value:
        sign = "+" if val > 0 else ""
        color = "#217346" if val > 0 else ("#C0392B" if val < 0 else "#9BA8B8")
        st.markdown(f'<div style="font-size:22px;font-weight:800;color:{color};text-align:center;padding-top:8px">{sign}{val}</div>', unsafe_allow_html=True)

st.session_state.draft_sliders = skill_sliders

# Real-time conflict detection
if m:
    conflicts = detect_conflicts(skill_sliders, m)
    for c in conflicts:
        sev = c.get("severity", "info")
        cls = "conflict-crit" if sev == "critical" else "conflict-warn"
        st.markdown(f'<div class="{cls}"><strong>{c["dimension"]}</strong><br>{c["message"]}</div>', unsafe_allow_html=True)
else:
    conflicts = []

st.markdown("---")

# ── SECTION 3: Organisational Focus ───────────────────────────────────────────
st.markdown("""
<div class="section-card">
    <div class="section-card-title">🏢 Section 3 — Organisational Focus Areas</div>
    <div class="section-card-sub">Which parts of the organisation require greater capability investment this cycle?</div>
</div>
""", unsafe_allow_html=True)

# Auto-detect BUs and departments from data
bu_options = []
dept_options = []
if not data["active_emp"].empty:
    if "Business Unit" in data["active_emp"].columns:
        bu_options = sorted(data["active_emp"]["Business Unit"].dropna().unique().tolist())
    if "Department" in data["active_emp"].columns:
        dept_options = sorted(data["active_emp"]["Department"].dropna().unique().tolist())

all_org_options = (
    [f"BU: {bu}" for bu in bu_options] +
    [f"Dept: {d}" for d in dept_options] +
    ["Strategic Programme: Digital Transformation",
     "Strategic Programme: Leadership Pipeline",
     "Strategic Programme: Compliance Uplift"]
)

if all_org_options:
    org_focus = st.multiselect(
        "Select business units, departments, or strategic programmes",
        options=all_org_options,
        default=st.session_state.get("draft_org_focus", []),
        label_visibility="collapsed",
        help="Selected areas will receive elevated priority and budget weight in LNI/TNI",
    )
else:
    st.info("Business Unit and Department data not detected in your Excel. You can type custom focus areas below.")
    org_focus_text = st.text_input(
        "Enter focus areas (comma-separated)",
        value=", ".join(st.session_state.get("draft_org_focus", [])),
    )
    org_focus = [x.strip() for x in org_focus_text.split(",") if x.strip()]

st.session_state.draft_org_focus = org_focus

if org_focus:
    st.success(f"✅ {len(org_focus)} focus area(s): {', '.join(org_focus)}")
else:
    st.caption("No specific focus areas selected — all business units treated equally")

st.markdown("---")

# ── SECTION 4: Employee Segments ──────────────────────────────────────────────
st.markdown("""
<div class="section-card">
    <div class="section-card-title">👥 Section 4 — Employee Segment Prioritisation</div>
    <div class="section-card-sub">Which employee segments should receive greater development focus? Each selection determines training format and budget allocation in the LNI/TNI.</div>
</div>
""", unsafe_allow_html=True)

# Show segment descriptions inline
segment_info = {
    "Entry / Graduate Talent":  "→ Structured cohort programmes · ILT + eLearning",
    "Individual Contributors":  "→ Skill-based modules · Blended",
    "First-Time Managers":      "→ Blended + coaching · 1.3x budget weight",
    "Mid-Level Managers":       "→ Leadership programmes · 1.4x budget weight",
    "Senior Leaders":           "→ Peer learning + external exposure · 1.8x budget weight",
    "High Potentials":          "→ Experiential + stretch assignments · 1.6x budget weight",
    "Critical Role Holders":    "→ ILT + certification paths · 1.5x budget weight",
}

employee_segments = st.multiselect(
    "Priority employee segments",
    options=EMPLOYEE_SEGMENTS,
    default=st.session_state.get("draft_segments", []),
    label_visibility="collapsed",
    help="Select segments that should receive disproportionate L&D investment this cycle",
)
st.session_state.draft_segments = employee_segments

if employee_segments:
    for seg in employee_segments:
        st.caption(f"✅ **{seg}**: {segment_info.get(seg,'')}")
else:
    st.caption("No segments selected — equal treatment across all employees")

st.markdown("---")

# ── SECTION 5: Time Horizon ───────────────────────────────────────────────────
st.markdown("""
<div class="section-card">
    <div class="section-card-title">⏱️ Section 5 — Time Horizon & Urgency</div>
    <div class="section-card-sub">This selection determines how the LNI/TNI roadmap is compressed or expanded, which quadrants are active, and the budget release mode.</div>
</div>
""", unsafe_allow_html=True)

# Show horizon implications
horizon_implications = {
    "Immediate (0–3 months)":    "Q1 skills only · ILT/Bootcamp format · 100% budget now · 90-day roadmap",
    "Short-term (3–6 months)":   "Q1 + Q2 skills · Blended delivery · Phased budget · 180-day roadmap",
    "Medium-term (6–12 months)": "Q1 + Q2 + Q3 skills · Full format mix · Structured budget · 365-day roadmap",
    "Long-term (12–24 months)":  "Full capability framework · Academy build · Annual budget cycle · 730-day roadmap",
}

default_horizon_idx = TIME_HORIZONS.index(st.session_state.get("draft_horizon", TIME_HORIZONS[1]))

time_horizon = st.radio(
    "Time horizon",
    options=TIME_HORIZONS,
    index=default_horizon_idx,
    label_visibility="collapsed",
    horizontal=True,
)
st.session_state.draft_horizon = time_horizon

st.info(f"**{time_horizon}:** {horizon_implications.get(time_horizon,'')}")

st.markdown("---")

# ── MANDATORY JUSTIFICATIONS for critical conflicts ───────────────────────────
justifications = {}
critical_conflicts = [c for c in conflicts if c.get("requires_justification")]

if critical_conflicts:
    st.markdown("### ⚠️ Justification Required for Critical Overrides")
    st.markdown("""
    <div class="conflict-crit">
        The following dimensions are significantly deprioritised despite critical LNA gaps.
        A justification note is required before you can confirm the configuration.
    </div>
    """, unsafe_allow_html=True)

    for c in critical_conflicts:
        dim = c["dimension"]
        j = st.text_area(
            f"Justification — {dim}",
            placeholder=f"Explain why {dim} is deprioritised despite {c['gap_pct']:.0f}% LNA gap...",
            key=f"justification_{dim}",
            height=80,
        )
        justifications[dim] = j

    all_justified = all(justifications.get(c["dimension"], "").strip() for c in critical_conflicts)
    if not all_justified:
        st.warning("⚠️ All critical overrides must have a justification note before you can confirm.")
else:
    all_justified = True

st.markdown("---")

# ── CONFIRMATION STEP ─────────────────────────────────────────────────────────
st.markdown("""
<div class="confirm-box">
    <div class="confirm-title">🔒 Confirm & Lock Configuration</div>
    <div class="confirm-sub">Once confirmed, this configuration will be versioned and used to generate the LNI/TNI report.
    You can edit and re-confirm to create a new version at any time.</div>
""", unsafe_allow_html=True)

# Live preview of strategic context summary
if cultural_selected or any(v != 0 for v in skill_sliders.values()) or employee_segments or org_focus:
    preview_profile = build_strategy_profile(
        cultural_priorities=cultural_selected,
        skill_sliders=skill_sliders,
        org_focus=org_focus,
        employee_segments=employee_segments,
        time_horizon=time_horizon,
        conflicts=conflicts,
    )
    st.markdown(f"""
    <div class="strategy-preview">
        <strong style="color:rgba(255,255,255,0.6);font-size:10px;letter-spacing:1px;text-transform:uppercase">
            Strategic Context Summary Preview
        </strong><br><br>
        {preview_profile['strategic_summary']}
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

col_name, col_role = st.columns(2)
with col_name:
    confirmed_by = st.text_input(
        "Confirmed by (Name)",
        placeholder="e.g. Priya Sharma",
        help="Optional — adds attribution to the configuration record",
        value=st.session_state.get("draft_confirmed_by", ""),
    )
    st.session_state.draft_confirmed_by = confirmed_by

with col_role:
    confirmed_role = st.text_input(
        "Role / Title",
        placeholder="e.g. Chief Human Resources Officer",
        value=st.session_state.get("draft_confirmed_role", ""),
    )
    st.session_state.draft_confirmed_role = confirmed_role

st.markdown("<br>", unsafe_allow_html=True)

existing_version = st.session_state.get("strategy_profile", {}).get("version")

confirm_disabled = not all_justified
confirm_clicked  = st.button(
    "✅ Confirm & Lock Configuration →",
    type="primary",
    use_container_width=True,
    disabled=confirm_disabled,
)

if confirm_disabled:
    st.caption("⚠️ Resolve all required justifications above before confirming.")

if confirm_clicked:
    profile = build_strategy_profile(
        cultural_priorities=cultural_selected,
        skill_sliders=skill_sliders,
        org_focus=org_focus,
        employee_segments=employee_segments,
        time_horizon=time_horizon,
        confirmed_by=confirmed_by,
        confirmed_role=confirmed_role,
        conflicts=conflicts,
        justifications=justifications,
        existing_version=existing_version,
    )
    st.session_state.strategy_profile  = profile
    st.session_state.strategy_editing  = False
    # Clear any existing LNI report so it regenerates
    if "lni_html" in st.session_state:
        del st.session_state.lni_html

    st.success(f"✅ Configuration locked as **{profile['version']}** · {profile['created_display']}")
    st.balloons()
    st.info("Navigate to **LNI / TNI Report** to generate your strategy-aligned report.")

    col_dl, col_next = st.columns(2)
    with col_dl:
        config_html = _build_config_html(profile, data, m)
        st.download_button(
            "⬇️ Download Configuration Summary",
            data=config_html.encode("utf-8"),
            file_name=f"Strategy_Config_{profile['version']}_{data['company'].replace(' ','_')}.html",
            mime="text/html",
            use_container_width=True,
        )
    with col_next:
        if st.button("📋 Generate LNI/TNI Report →", type="primary", use_container_width=True):
            st.switch_page("pages/4_LNI_Report.py")
