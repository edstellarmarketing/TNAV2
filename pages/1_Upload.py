"""
pages/1_Upload.py — Edstellar LNA Platform
Page 1: File upload and sheet validation.
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic.data_loader import (
    validate_file, load_all_data,
    REQUIRED_SHEETS, SHEET_DESCRIPTIONS,
)

st.set_page_config(
    page_title="Upload Data — Edstellar LNA",
    page_icon="📂",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Shared sidebar ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:serif;font-size:20px;font-weight:400;color:white">EDSTELLAR</div>', unsafe_allow_html=True)
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
        st.caption(f"{len(d['active_emp'])} employees loaded")

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700;800&family=DM+Serif+Display&display=swap');
html,[class*="css"]{font-family:'DM Sans',sans-serif;}
#MainMenu,footer,header{visibility:hidden;}
.page-banner{background:linear-gradient(135deg,#1B3A6B,#2E5BA8);border-radius:12px;padding:28px 36px;margin-bottom:28px;display:flex;align-items:center;gap:20px;}
.page-banner-title{font-family:'DM Serif Display',serif;font-size:26px;color:#fff;}
.page-banner-sub{font-size:13px;color:rgba(255,255,255,0.65);margin-top:4px;}
.sheet-row{display:flex;align-items:flex-start;gap:12px;padding:10px 14px;border-radius:8px;margin-bottom:6px;}
.sheet-row.ok{background:#F0FBF4;border:1px solid #C3E6CB;}
.sheet-row.missing{background:#FFF3F3;border:1px solid #F5C6CB;}
.sheet-name{font-weight:700;font-size:13px;color:#1B3A6B;min-width:200px;}
.sheet-desc{font-size:12px;color:#6B7A99;}
.sheet-icon{font-size:16px;flex-shrink:0;margin-top:2px;}
.summary-card{background:#fff;border-radius:10px;padding:20px 24px;box-shadow:0 2px 12px rgba(27,58,107,0.09);border:1px solid #E8EDF5;border-top:4px solid #1B3A6B;text-align:center;}
.summary-num{font-size:32px;font-weight:800;color:#1B3A6B;}
.summary-lbl{font-size:11px;color:#6B7A99;text-transform:uppercase;letter-spacing:0.6px;margin-top:4px;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-banner">
    <div style="font-size:42px">📂</div>
    <div>
        <div class="page-banner-title">Upload Employee Master Data</div>
        <div class="page-banner-sub">Upload your Edstellar Employee Master Excel file — all 17 sheets are validated automatically</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Upload widget ─────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Drop your Employee Master Excel file here",
    type=["xlsx", "xlsm"],
    help="Must be the full Employee Master .xlsx file — not individual CSV sheets",
    label_visibility="collapsed",
)

if uploaded is None:
    # Show expected sheets guide
    st.markdown("### Required Sheets")
    st.info("Upload your Employee Master Excel file to begin. The file must contain all 17 sheets listed below.")

    col1, col2 = st.columns(2)
    half = len(REQUIRED_SHEETS) // 2
    for i, sheet in enumerate(REQUIRED_SHEETS):
        col = col1 if i < half else col2
        with col:
            desc = SHEET_DESCRIPTIONS.get(sheet, "")
            st.markdown(f"""
            <div class="sheet-row ok" style="background:#F4F7FC;border-color:#C3D0E8;">
                <div class="sheet-icon">📋</div>
                <div>
                    <div class="sheet-name">{sheet}</div>
                    <div class="sheet-desc">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    st.stop()

# ── Validate uploaded file ────────────────────────────────────────────────────
with st.spinner("Validating file structure..."):
    validation = validate_file(uploaded)

if not validation["valid"]:
    st.error(f"❌ **Validation failed** — {len(validation['sheets_missing'])} required sheets are missing.")

    col1, col2 = st.columns(2)
    for i, sheet in enumerate(REQUIRED_SHEETS):
        status = validation["sheet_status"].get(sheet, {})
        col = col1 if i % 2 == 0 else col2
        with col:
            if status.get("status") == "ok":
                st.markdown(f"""
                <div class="sheet-row ok">
                    <div class="sheet-icon">✅</div>
                    <div>
                        <div class="sheet-name">{sheet}</div>
                        <div class="sheet-desc">{status.get('rows',0)} rows · {SHEET_DESCRIPTIONS.get(sheet,'')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="sheet-row missing">
                    <div class="sheet-icon">❌</div>
                    <div>
                        <div class="sheet-name">{sheet}</div>
                        <div class="sheet-desc" style="color:#C0392B">Sheet not found — {SHEET_DESCRIPTIONS.get(sheet,'')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    st.stop()

# ── All sheets present — show validation success ──────────────────────────────
st.success(f"✅ All {len(REQUIRED_SHEETS)} required sheets found and validated")

# Sheet summary grid
col1, col2 = st.columns(2)
for i, sheet in enumerate(REQUIRED_SHEETS):
    status = validation["sheet_status"].get(sheet, {})
    col = col1 if i % 2 == 0 else col2
    with col:
        rows = status.get("rows", 0)
        st.markdown(f"""
        <div class="sheet-row ok">
            <div class="sheet-icon">✅</div>
            <div>
                <div class="sheet-name">{sheet}</div>
                <div class="sheet-desc">{rows} rows · {SHEET_DESCRIPTIONS.get(sheet,'')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ── Load all data ─────────────────────────────────────────────────────────────
with st.spinner("Loading all sheets into session..."):
    uploaded.seek(0)
    data = load_all_data(uploaded)
    st.session_state.lna_data = data
    # Clear downstream session state on new upload
    for key in ["lna_metrics", "lna_html", "lna_insights", "strategy_profile", "lni_html"]:
        if key in st.session_state:
            del st.session_state[key]

# ── Data summary ──────────────────────────────────────────────────────────────
st.markdown("### Data Summary")

active_emp = data["active_emp"]
training   = data["training"]
certs      = data["certs"]
skills_m   = data["skills_master"]

c1, c2, c3, c4, c5, c6 = st.columns(6)
metrics_summary = [
    (c1, len(active_emp),                                      "Active Employees"),
    (c2, active_emp["Job Role"].nunique() if "Job Role" in active_emp.columns else "—", "Job Roles"),
    (c3, active_emp["Location"].nunique() if "Location" in active_emp.columns else "—", "Locations"),
    (c4, len(skills_m),                                        "Skills Defined"),
    (c5, len(training) if not training.empty else 0,          "Training Records"),
    (c6, len(certs) if not certs.empty else 0,                "Cert Records"),
]
for col, val, label in metrics_summary:
    with col:
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-num">{val}</div>
            <div class="summary-lbl">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Company metadata
colA, colB = st.columns(2)
with colA:
    st.markdown("**File Details**")
    st.write(f"🏢 **Company:** {data['company']}")
    st.write(f"📅 **Period:** {data['time_period']} {data['year']}")
    st.write(f"📆 **Report Date:** {data['report_date']}")

with colB:
    st.markdown("**Workforce Snapshot**")
    if "Gender" in active_emp.columns:
        female = (active_emp["Gender"] == "Female").sum()
        st.write(f"👩 **Female employees:** {female} ({female/max(len(active_emp),1)*100:.1f}%)")
    if "Tenure (Years)" in active_emp.columns:
        st.write(f"⏱️ **Avg Tenure:** {active_emp['Tenure (Years)'].mean():.1f} years")
    if "Age" in active_emp.columns:
        st.write(f"🎂 **Avg Age:** {active_emp['Age'].mean():.1f} years")

st.markdown("---")

# ── Proceed button ─────────────────────────────────────────────────────────────
st.markdown("### Ready to Generate Your LNA Report")
st.markdown("""
<div style="background:#F0FBF4;border:1px solid #C3E6CB;border-radius:8px;padding:14px 18px;font-size:13px;margin-bottom:16px;">
    ✅ Data loaded and validated. Click below to proceed to the <strong>LNA / TNA Report</strong> page where you can configure AI insights and generate your full report.
</div>
""", unsafe_allow_html=True)

if st.button("📊 Proceed to LNA Report →", type="primary", use_container_width=True):
    st.switch_page("pages/2_LNA_Report.py")
