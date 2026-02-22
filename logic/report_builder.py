"""
report_builder.py — Edstellar LNA Platform
Builds the full 17-section HTML LNA report.
Pure logic — no Streamlit imports.
"""

import pandas as pd
import base64
import os
from datetime import datetime
from .charts import (
    bar_chart, multi_bar_chart, stacked_bar_chart, pie_chart,
    heatmap_chart, treemap_chart, scatter_quadrant, radar_chart,
    NAVY, BLUE, GOLD, GREEN, RED, PURPLE, TEAL, ORANGE, COLORS,
)
from .metrics import safe_div

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.27.0.min.js"


# ── HTML Helpers ──────────────────────────────────────────────────────────────

def kpi_tile(label, value, unit="", trend=None, color=NAVY, sub=""):
    trend_html = ""
    if trend == "up":   trend_html = '<span class="trend up">▲</span>'
    if trend == "down": trend_html = '<span class="trend down">▼</span>'
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f'''<div class="kpi-card" style="border-top:4px solid {color}">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}<span class="kpi-unit">{unit}</span>{trend_html}</div>
      {sub_html}</div>'''


def kpi_row(*tiles):
    return f'<div class="kpi-row">{"".join(tiles)}</div>'


def section_header(num, title, icon=""):
    return f'''<div class="section-header">
      <span class="sec-num">{num}</span>
      <span class="sec-icon">{icon}</span>
      <span class="sec-title">{title}</span></div>'''


def subsection(title):
    return f'<h3 class="subsec-title">{title}</h3>'


def insight_box(text, icon="💡"):
    return f'<div class="insight-box"><span class="insight-icon">{icon}</span><div>{text}</div></div>'


def table_html(df, max_rows=None, col_colors=None):
    if df is None or (hasattr(df, "empty") and df.empty):
        return "<p><em>No data available.</em></p>"
    if max_rows:
        df = df.head(max_rows)
    rows_html = ""
    for _, row in df.iterrows():
        cells = ""
        for col, val in zip(df.columns, row):
            style = ""
            if col_colors and col in col_colors:
                for kw, clr in col_colors[col].items():
                    if kw.lower() in str(val).lower():
                        style = f'style="color:{clr};font-weight:600"'
                        break
            cells += f"<td {style}>{val}</td>"
        rows_html += f"<tr>{cells}</tr>"
    headers = "".join(f"<th>{c}</th>" for c in df.columns)
    return f'<div class="table-wrap"><table><thead><tr>{headers}</tr></thead><tbody>{rows_html}</tbody></table></div>'


def plotly_embed(fig, caption=""):
    div = fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False})
    cap = f'<p class="chart-caption">{caption}</p>' if caption else ""
    return f'<div class="chart-wrap">{div}{cap}</div>'


def progress_bar(label, value, benchmark=None, color=NAVY):
    pct = min(float(value), 100)
    bench_html = f'<span class="bench-label">Benchmark: {benchmark}</span>' if benchmark else ""
    return f'''<div class="progress-row">
      <div class="progress-label">{label}</div>
      <div class="progress-bar-bg">
        <div class="progress-bar-fill" style="width:{pct}%;background:{color}"></div>
      </div>
      <div class="progress-value">{value:.1f}%</div>
      {bench_html}</div>'''


# ── CSS ───────────────────────────────────────────────────────────────────────

REPORT_CSS = """
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=DM+Serif+Display&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'DM Sans',Arial,sans-serif;font-size:13px;color:#2C2C2C;background:#F4F6FB;line-height:1.55}
.report-wrapper{max-width:1200px;margin:0 auto;background:#fff;box-shadow:0 2px 24px rgba(27,58,107,.10)}
.report-header{background:linear-gradient(135deg,#1B3A6B 0%,#2E5BA8 60%,#4472C4 100%);padding:36px 48px;display:flex;justify-content:space-between;align-items:center}
.report-header-left .brand{font-size:22px;font-weight:800;color:#fff;letter-spacing:1px;font-family:'DM Serif Display',serif}
.report-header-left .tagline{font-size:12px;color:rgba(255,255,255,.75);margin-top:4px}
.report-header-right{text-align:right;color:rgba(255,255,255,.85);font-size:12px;line-height:1.8}
.toc{background:#EBF0FA;padding:28px 48px;border-bottom:3px solid #1B3A6B}
.toc h2{color:#1B3A6B;font-size:15px;margin-bottom:14px}
.toc-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px 24px}
.toc-item{display:flex;align-items:center;gap:8px;padding:4px 0;color:#1B3A6B;font-size:12px;text-decoration:none}
.toc-item:hover{color:#4472C4}
.toc-num{background:#1B3A6B;color:#fff;border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;flex-shrink:0}
.section{padding:36px 48px 28px;border-bottom:1px solid #E8EDF5}
.section:nth-child(odd){background:#fff}
.section:nth-child(even){background:#FAFBFD}
.section-header{display:flex;align-items:center;gap:12px;background:linear-gradient(90deg,#1B3A6B 0%,#2E5BA8 100%);color:#fff;padding:14px 20px;border-radius:6px;margin-bottom:24px}
.sec-num{background:#F4A024;color:#1B3A6B;font-weight:800;font-size:15px;width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.sec-icon{font-size:18px}
.sec-title{font-size:16px;font-weight:700;letter-spacing:.3px}
.subsec-title{font-size:13px;font-weight:700;color:#1B3A6B;border-left:4px solid #F4A024;padding:4px 0 4px 12px;margin:20px 0 12px}
.kpi-row{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:20px}
.kpi-card{flex:1;min-width:120px;background:#fff;border-radius:8px;padding:14px 16px;box-shadow:0 2px 8px rgba(27,58,107,.09);border-top:4px solid #1B3A6B}
.kpi-label{font-size:10px;color:#6B7A99;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}
.kpi-value{font-size:24px;font-weight:800;color:#1B3A6B;line-height:1}
.kpi-unit{font-size:12px;font-weight:400;color:#6B7A99;margin-left:2px}
.kpi-sub{font-size:10px;color:#6B7A99;margin-top:4px}
.trend{font-size:14px;margin-left:4px}
.trend.up{color:#217346}
.trend.down{color:#C0392B}
.chart-wrap{background:#fff;border-radius:8px;padding:12px;margin:14px 0;box-shadow:0 1px 6px rgba(27,58,107,.07);border:1px solid #E8EDF5}
.chart-caption{font-size:11px;color:#6B7A99;text-align:center;margin-top:6px;font-style:italic}
.chart-grid-2{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:14px 0}
.table-wrap{overflow-x:auto;margin:12px 0}
table{width:100%;border-collapse:collapse;font-size:12px}
thead tr{background:#1B3A6B}
th{color:#fff;padding:10px 12px;text-align:left;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,.15)}
td{padding:9px 12px;border-bottom:1px solid #EEF1F8;vertical-align:top}
tbody tr:nth-child(even) td{background:#F4F7FC}
tbody tr:hover td{background:#EBF0FA}
.insight-box{display:flex;gap:12px;align-items:flex-start;background:linear-gradient(135deg,#EBF0FA 0%,#F4F7FC 100%);border:1px solid #C3D0E8;border-left:5px solid #1B3A6B;border-radius:6px;padding:14px 16px;margin:16px 0;font-size:12.5px;line-height:1.65}
.insight-icon{font-size:18px;flex-shrink:0;margin-top:2px}
.cover-block{text-align:center;padding:40px 20px 20px;background:linear-gradient(160deg,#EBF0FA 0%,#FFFFFF 100%);border-radius:8px;border:1px solid #C3D0E8;margin:10px 0 20px}
.cover-logo{font-size:56px;margin-bottom:16px}
.cover-title{font-size:26px;font-weight:800;color:#1B3A6B;margin-bottom:8px;font-family:'DM Serif Display',serif}
.cover-subtitle{font-size:14px;color:#4472C4;margin-bottom:12px;font-style:italic}
.cover-company{font-size:20px;font-weight:700;color:#F4A024;margin-bottom:24px}
.cover-meta-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;max-width:600px;margin:0 auto}
.cover-meta-item{background:#fff;border-radius:6px;padding:12px;box-shadow:0 1px 6px rgba(27,58,107,.1)}
.cmk{display:block;font-size:10px;color:#6B7A99;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}
.cmv{display:block;font-size:14px;font-weight:700;color:#1B3A6B}
.composite-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:16px 0}
.composite-card{background:#fff;border-radius:8px;padding:14px 16px;box-shadow:0 1px 8px rgba(27,58,107,.08)}
.composite-name{font-size:11px;color:#6B7A99;margin-bottom:6px}
.composite-val{font-size:28px;font-weight:800;line-height:1}
.composite-unit{font-size:13px;font-weight:400}
.composite-delta{font-size:11px;margin-top:4px;font-weight:600}
.composite-bench{font-size:10px;color:#9BA8B8;margin-top:2px}
.progress-row{display:flex;align-items:center;gap:10px;margin:6px 0}
.progress-label{width:220px;font-size:11px;color:#2C2C2C;flex-shrink:0}
.progress-bar-bg{flex:1;height:8px;background:#E8EDF5;border-radius:4px;overflow:hidden}
.progress-bar-fill{height:100%;border-radius:4px}
.progress-value{width:50px;font-size:11px;font-weight:700;color:#1B3A6B;text-align:right}
.bench-label{font-size:10px;color:#9BA8B8;width:90px;flex-shrink:0}
.obj-list{padding-left:20px}
.obj-list li{margin:7px 0;font-size:13px}
.next-steps{padding-left:20px}
.next-steps li{margin:8px 0;font-size:13px}
.strategic-overview table th{background:#2E5BA8}
.report-footer{background:#1B3A6B;color:rgba(255,255,255,.7);padding:20px 48px;text-align:center;font-size:11px;display:flex;justify-content:space-between;align-items:center}
.report-footer .footer-brand{color:#F4A024;font-weight:700}
@media(max-width:768px){.section{padding:20px 16px}.report-header{flex-direction:column;gap:12px;text-align:center}.toc-grid{grid-template-columns:1fr}.chart-grid-2{grid-template-columns:1fr}.composite-grid{grid-template-columns:1fr 1fr}.cover-meta-grid{grid-template-columns:1fr}}
@media print{.section{page-break-inside:avoid}body{background:#fff}.report-wrapper{box-shadow:none}}
"""


# ── Section Builders ──────────────────────────────────────────────────────────

def build_all_sections(data: dict, m: dict, ai_insights: dict = None) -> list:
    """
    Build all 17 HTML sections.
    data    — from data_loader.load_all_data()
    m       — from metrics.compute_all_metrics()
    ai_insights — optional dict from ai_insights module
    Returns list of 17 HTML strings.
    """
    ai = ai_insights or {}
    sections = []

    COMPANY     = data["company"]
    TIME_PERIOD = data["time_period"]
    YEAR        = data["year"]
    REPORT_DATE = data["report_date"]
    active_emp  = data["active_emp"]
    skills_master = data["skills_master"]
    role_skills   = data["role_skills"]
    emp_skills    = data["emp_skills"]
    comp_master   = data["comp_master"]
    role_comps    = data["role_comps"]
    emp_comps     = data["emp_comps"]
    training      = data["training"]
    certs         = data["certs"]
    benchmark     = data["benchmark"]
    emp_projects  = data["emp_projects"]

    N = m["N"]

    # ── S1 — COVER PAGE ──────────────────────────────────────────────────────
    s = section_header(1, "Cover Page", "🏢")
    s += f'''<div class="cover-block">
  <div class="cover-logo">📊</div>
  <div class="cover-title">Learning Needs Analysis (LNA)</div>
  <div class="cover-subtitle">Level 1: Workforce and Organisation Baseline</div>
  <div class="cover-company">{COMPANY}</div>
  <div class="cover-meta-grid">
    <div class="cover-meta-item"><span class="cmk">Time Period</span><span class="cmv">{TIME_PERIOD} {YEAR}</span></div>
    <div class="cover-meta-item"><span class="cmk">Report Date</span><span class="cmv">{REPORT_DATE}</span></div>
    <div class="cover-meta-item"><span class="cmk">Prepared By</span><span class="cmv">Edstellar</span></div>
    <div class="cover-meta-item"><span class="cmk">Confidentiality</span><span class="cmv">Confidential</span></div>
    <div class="cover-meta-item"><span class="cmk">Version</span><span class="cmv">v1.0</span></div>
    <div class="cover-meta-item"><span class="cmk">Employees in Scope</span><span class="cmv">{N}</span></div>
  </div></div>'''
    s += insight_box(ai.get("s1_cover", f"This Level 1 LNA for <strong>{COMPANY}</strong> covers <strong>{N}</strong> employees across <strong>{m['total_locs']}</strong> locations for <strong>{TIME_PERIOD} {YEAR}</strong>. This is a confidential baseline assessment prepared by Edstellar."), "🏢")
    sections.append(s)

    # ── S2 — DOCUMENT CONTROL ────────────────────────────────────────────────
    s = section_header(2, "Document Control & Governance", "📋")
    s += subsection("Version History")
    vdf = pd.DataFrame([
        ["v1.0", REPORT_DATE, "Initial Draft — LNA Level 1 Baseline", "Edstellar", "Pending", "Pending"],
        ["v1.1", "—", "Post-review updates", "Edstellar", "—", "—"],
        ["v2.0", "—", "Final approved version", "Edstellar", "—", "—"],
    ], columns=["Version","Date","Description","Author","Reviewed By","Approved By"])
    s += table_html(vdf)
    s += subsection("Reviewers & Approvers")
    adf = pd.DataFrame([
        ["Head of L&D", COMPANY, "Content Review", "Pending"],
        ["CHRO", COMPANY, "Strategic Approval", "Pending"],
        ["Business Unit Heads", COMPANY, "Section Validation", "Pending"],
    ], columns=["Role","Organisation","Responsibility","Status"])
    s += table_html(adf)
    s += insight_box(ai.get("s2_doc_control", f"This document follows version control governance. All revisions require Head of L&D review and CHRO approval before distribution. Quarterly refresh is recommended."), "📋")
    sections.append(s)

    # ── S3 — EXECUTIVE SUMMARY ───────────────────────────────────────────────
    s = section_header(3, "Executive Summary", "📌")
    s += insight_box(ai.get("s3_exec_summary",
        f"<strong>{COMPANY}</strong> has <strong>{N}</strong> active employees across <strong>{m['total_locs']}</strong> locations. "
        f"Role Skill Coverage: <strong>{m['role_skill_cov']:.1f}%</strong>, Critical Skills Index: <strong>{m['crit_skills_idx']:.1f}%</strong>, "
        f"Learning Penetration: <strong>{m['learning_pen_idx']:.1f}%</strong>. "
        f"<strong>{len(m['q1_skills'])}</strong> skills require immediate high-urgency intervention."), "📄")

    s += kpi_row(
        kpi_tile("Role Skill Coverage", f"{m['role_skill_cov']:.1f}", "%", color=GREEN if m['role_skill_cov'] >= 80 else ORANGE),
        kpi_tile("Critical Skills Index", f"{m['crit_skills_idx']:.1f}", "%", color=GREEN if m['crit_skills_idx'] >= 75 else RED),
        kpi_tile("Manager Ratio", f"{m['manager_ratio']:.1f}", "%", color=BLUE),
        kpi_tile("Female Representation", f"{m['female_pct']:.1f}", "%", color=PURPLE),
        kpi_tile("Learning Penetration", f"{m['learning_pen_idx']:.1f}", "%", color=GREEN if m['learning_pen_idx'] >= 85 else ORANGE),
        kpi_tile("Training Intensity", f"{m['training_intensity']:.1f}", "hrs", color=TEAL),
        kpi_tile("Certification Coverage", f"{m['cert_cov_idx']:.1f}", "%", color=GREEN if m['cert_cov_idx'] >= 50 else ORANGE),
    )

    s += subsection("Strategic Overview")
    q1_cnt = len(m["q1_skills"])
    s += f'''<table><thead><tr><th>Dimension</th><th>Current State</th><th>Gap / Risk</th><th>Strategic Implication</th></tr></thead><tbody>
      <tr><td><strong>Skill Coverage</strong></td><td>{m['role_skill_cov']:.1f}% roles mapped</td><td>{100-m['role_skill_cov']:.1f}% unmapped</td><td>Immediate framework completion needed</td></tr>
      <tr><td><strong>Critical Skills</strong></td><td>{m['crit_skills_idx']:.1f}% meet thresholds</td><td>{q1_cnt} Q1 skills</td><td>Prioritise urgent training interventions</td></tr>
      <tr><td><strong>Training Investment</strong></td><td>₹{m['total_budget']:,.0f} budget</td><td>Avg {m['avg_hrs']:.1f} hrs/employee</td><td>Benchmark alignment needed</td></tr>
      <tr><td><strong>Certifications</strong></td><td>{m['cert_cov_idx']:.1f}% certified</td><td>{m['expired_certs']} expired</td><td>Renewal drive required</td></tr>
      <tr><td><strong>Diversity</strong></td><td>{m['female_pct']:.1f}% female</td><td>Industry benchmark ~35%</td><td>Inclusive development focus</td></tr>
    </tbody></table>'''

    s += subsection("Top 5 Findings")
    top_skill = m["q1_skills"]["Skill Name"].iloc[0] if not m["q1_skills"].empty and "Skill Name" in m["q1_skills"].columns else "Key technical skill"
    findings = pd.DataFrame([
        [1, "Critical Skill Gaps", f"{q1_cnt} skills in High Impact/High Urgency quadrant. '{top_skill}' shows highest avg gap."],
        [2, "Certification Gap", f"Only {m['cert_cov_idx']:.1f}% employees certified. {m['expired_certs']} certifications expired."],
        [3, "Gender Diversity", f"Female representation {m['female_pct']:.1f}% vs ~35% industry benchmark."],
        [4, "Training Distribution", f"Training hours uneven across levels. L1/L2 receive fewer hours than senior employees."],
        [5, "Geographic Risk", f"Geographic Risk Exposure Index: {m['geo_risk_idx']:.1f}% — locations with critical skill gaps >30%."],
    ], columns=["#", "Finding", "Detail"])
    s += table_html(findings)

    s += subsection("Top 5 Recommendations")
    recs = pd.DataFrame([
        [1, "Q1 Critical Skill Programmes", f"Deploy ILT/blended for {q1_cnt} Q1 skills. Target 80% coverage within 30 days.", "High", "30 Days"],
        [2, "Certification Renewal Campaign", f"Address {m['expired_certs']} expired certs. Target 60%+ coverage.", "High", "60 Days"],
        [3, "Structured L1/L2 Onboarding", "90-day learning paths for junior employees.", "High", "60 Days"],
        [4, "Geographic Capability Equalisation", "Virtual programmes for under-served locations.", "Medium", "90 Days"],
        [5, "Diversity Development Pathways", "Mentoring and leadership tracks for female employees.", "Medium", "90 Days"],
    ], columns=["#", "Recommendation", "Detail", "Priority", "Timeline"])
    s += table_html(recs, col_colors={"Priority": {"High": RED, "Medium": ORANGE, "Low": GREEN}})
    sections.append(s)

    # ── S4 — BUSINESS & STRATEGIC CONTEXT ────────────────────────────────────
    s = section_header(4, "Business & Strategic Context", "🎯")
    s += subsection("Strategy-to-Skills Mapping")
    jf_goal_map = {
        "Engineering":   ("Scale Engineering Velocity", "DevOps & Cloud Migration", "Programming, Cloud & DevOps"),
        "Sales":         ("Drive Revenue Growth", "Sales Enablement & CRM", "Sales & Customer Skills"),
        "Product":       ("Accelerate Product Innovation", "Product-Led Growth", "Product & UX Skills"),
        "Data":          ("Enable Data-Driven Decisions", "Analytics & AI Adoption", "Data & Analytics"),
        "HR":            ("Build Talent & Culture", "People Development", "People & Leadership"),
        "Finance":       ("Improve Financial Controls", "FinTech & Compliance", "Finance & Risk"),
        "Operations":    ("Optimise Operations", "Process Excellence", "Operations & Quality"),
        "Customer":      ("Enhance Customer Experience", "Service Excellence", "Customer Skills"),
    }
    auto_goals = []
    if "Job Family" in active_emp.columns:
        for jf, cnt in active_emp["Job Family"].value_counts().head(6).items():
            goal_data = jf_goal_map.get(str(jf), (f"Strengthen {jf} Capability", f"{jf} Transformation", "Functional Skills"))
            auto_goals.append([goal_data[0], goal_data[1], "High" if cnt > N*0.15 else "Medium", goal_data[2], "Leadership & Collaboration"])
    if auto_goals:
        gdf = pd.DataFrame(auto_goals, columns=["Business Goal","Transformation Initiative","Priority","Skill Category","Competency Category"])
        s += table_html(gdf, col_colors={"Priority": {"High": RED, "Medium": ORANGE}})
    s += insight_box(ai.get("s4_strategy", f"The skills framework covers <strong>{m['role_skill_cov']:.1f}%</strong> of roles. Completing skill mapping for the remaining <strong>{m['roles_unmapped']}</strong> roles is a prerequisite for full L&D strategic alignment."), "🎯")
    sections.append(s)

    # ── S5 — SCOPE & OBJECTIVES ──────────────────────────────────────────────
    s = section_header(5, "Scope & Objectives of LNA", "🔍")
    s += subsection("LNA Objectives")
    objectives = [
        "Establish a comprehensive capability baseline across all active employees",
        "Identify critical skill and competency gaps relative to role requirements",
        "Quantify training investment demand and learning penetration",
        "Prioritise training interventions using the Impact × Urgency quadrant model",
        "Produce a data-driven 30-60-90 day roadmap for L&D action",
        "Create measurable indices to track capability improvement over time",
    ]
    s += "<ol class='obj-list'>" + "".join(f"<li>{o}</li>" for o in objectives) + "</ol>"
    s += subsection("Scope")
    scope_df = pd.DataFrame([
        ["Active Employees", str(N), "Included"],
        ["Job Roles", str(m["total_roles"]), "Included"],
        ["Locations", str(m["total_locs"]), "Included"],
        ["Contractors / Consultants", "Variable", "Excluded"],
        ["Board Members", "—", "Excluded"],
        ["Interns", "—", "Excluded"],
    ], columns=["Segment","Count","Status"])
    s += table_html(scope_df, col_colors={"Status": {"Included": GREEN, "Excluded": ORANGE}})
    s += insight_box(ai.get("s5_scope", f"This LNA covers <strong>{N}</strong> active employees across <strong>{m['total_roles']}</strong> roles and <strong>{m['total_locs']}</strong> locations. Contractors and interns are excluded — including them in the next cycle would provide a complete extended workforce picture."), "🔍")
    sections.append(s)

    # ── S6 — METHODOLOGY & DATA SOURCES ─────────────────────────────────────
    s = section_header(6, "Methodology & Data Sources", "🔬")
    sources = pd.DataFrame([
        ["Employee Master",        "HR System",            str(N),                         "✅ Complete"],
        ["Skills Framework",       "L&D Platform",         str(m["total_skills"]),          "✅ Complete"],
        ["Role-Skill Mapping",     "L&D Platform",         f"{m['roles_mapped']} roles",    "✅ Complete" if m["roles_unmapped"] == 0 else "⚠️ Partial"],
        ["Employee Skill Records", "Self-Assessment",      f"{len(data['emp_skills'])}",    "✅ Complete"],
        ["Competency Framework",   "HR System",            str(m["total_comps"]),           "✅ Complete"],
        ["Training Records",       "LMS",                  f"{len(training)} records",       "✅ Complete" if not training.empty else "⚠️ Missing"],
        ["Certifications",         "Cert Registry",        str(m["total_certs"]),           "✅ Complete"],
        ["Manager Assessments",    "Manager Survey",       "—",                             "⚠️ Pending"],
        ["360 Feedback",           "Performance System",   "—",                             "⚠️ Pending"],
        ["Industry Benchmarks",    "Edstellar Benchmarks", f"{len(benchmark)} metrics",     "✅ Complete" if not benchmark.empty else "⚠️ Missing"],
    ], columns=["Data Source","Origin","Volume","Status"])
    s += table_html(sources, col_colors={"Status": {"✅": GREEN, "⚠️": ORANGE}})
    s += insight_box(ai.get("s6_methodology", f"Data covers <strong>{m['total_skills']}</strong> skills, <strong>{m['total_certs']}</strong> certifications, and training records for <strong>{N}</strong> employees. Manager assessments are pending — self-reported proficiency data may overstate actual capability levels."), "🔬")
    sections.append(s)

    # ── S7 — PARTICIPANT PROFILE ──────────────────────────────────────────────
    s = section_header(7, "Participant Profile", "👥")
    s += kpi_row(
        kpi_tile("Total Employees", N, color=NAVY),
        kpi_tile("Total Roles", m["total_roles"], color=BLUE),
        kpi_tile("Locations", m["total_locs"], color=TEAL),
        kpi_tile("Avg Tenure", m["avg_tenure"], "yrs", color=GREEN),
        kpi_tile("Avg Training Hrs", m["avg_training_hrs"], "hrs", color=ORANGE),
        kpi_tile("Manager Ratio", f"{m['manager_ratio']:.1f}", "%", color=PURPLE),
        kpi_tile("Span of Control", m["span_of_ctrl"], color=BLUE),
        kpi_tile("Age Risk Index", f"{m['age_risk_idx']:.1f}", "%", color=GREEN if m["age_risk_idx"] < 15 else RED),
        kpi_tile("Level Distribution", f"{m['ldi']:.1f}", "%", color=TEAL),
    )
    if "Gender" in active_emp.columns:
        gc = active_emp["Gender"].value_counts()
        fig_g = pie_chart(gc.index.tolist(), gc.values.tolist(), "Employees by Gender")
        if "Age" in active_emp.columns:
            bins = [20,25,30,35,40,45,50,55,60]
            age_labels = [f"{b}-{bins[i+1]}" for i, b in enumerate(bins[:-1])]
            age_counts = pd.cut(active_emp["Age"], bins=bins, labels=age_labels).value_counts().sort_index()
            fig_age = bar_chart(age_labels, age_counts.values.tolist(), "Employees by Age Band", "Age Band", "Headcount", BLUE)
            s += f'<div class="chart-grid-2">{plotly_embed(fig_g, "Gender distribution")}{plotly_embed(fig_age, "Age band distribution")}</div>'
        else:
            s += plotly_embed(fig_g, "Gender distribution")
    if "Tenure (Years)" in active_emp.columns:
        tb = [0,1,2,3,5,8,15]; tl = ["<1yr","1-2yr","2-3yr","3-5yr","5-8yr","8+yr"]
        tc = pd.cut(active_emp["Tenure (Years)"], bins=tb, labels=tl).value_counts().sort_index()
        fig_ten = bar_chart(tl, tc.values.tolist(), "Headcount by Tenure Band", "Tenure", "Headcount", TEAL)
        if "Location" in active_emp.columns:
            lc = active_emp["Location"].value_counts()
            fig_loc = bar_chart(lc.index.tolist(), lc.values.tolist(), "Headcount by Location", "Location", "Employees", GOLD)
            s += f'<div class="chart-grid-2">{plotly_embed(fig_ten, "Tenure distribution")}{plotly_embed(fig_loc, "Location distribution")}</div>'
        else:
            s += plotly_embed(fig_ten, "Tenure distribution")
    if "Job Family" in active_emp.columns:
        jf_c = active_emp["Job Family"].value_counts().reset_index()
        jf_c.columns = ["Job Family","Count"]
        labels = [COMPANY] + jf_c["Job Family"].tolist()
        parents = [""] + [COMPANY]*len(jf_c)
        values = [jf_c["Count"].sum()] + jf_c["Count"].tolist()
        s += plotly_embed(treemap_chart(labels, parents, values, "Job Families — Headcount Distribution"), "Job family composition")
    s += insight_box(ai.get("s7_profile", f"Workforce of <strong>{N}</strong> employees. Avg age <strong>{m['avg_age']}</strong>, avg tenure <strong>{m['avg_tenure']} yrs</strong>. Female representation <strong>{m['female_pct']:.1f}%</strong> vs 35% industry benchmark. Age Risk Index <strong>{m['age_risk_idx']:.1f}%</strong>."), "💡")
    sections.append(s)

    # ── S8 — ROLE-BASED CONTEXT ───────────────────────────────────────────────
    s = section_header(8, "Role-Based Context", "🏗️")
    s += kpi_row(
        kpi_tile("Total Roles", m["total_roles"], color=NAVY),
        kpi_tile("Critical Roles", m["crit_roles"], color=RED),
        kpi_tile("Roles Mapped", m["roles_mapped"], color=GREEN),
        kpi_tile("Roles Unmapped", m["roles_unmapped"], color=ORANGE),
        kpi_tile("Role Density", m["role_density"], color=BLUE),
        kpi_tile("Role Saturation", f"{m['role_sat_idx']:.1f}", "%", color=ORANGE if m["role_sat_idx"] > 20 else GREEN),
        kpi_tile("Role Skill Coverage", f"{m['role_skill_cov']:.1f}", "%", color=GREEN if m["role_skill_cov"] >= 80 else RED),
    )
    if not role_skills.empty and not skills_master.empty and "Skill Category" in skills_master.columns:
        rs_m = role_skills.merge(skills_master[["Skill ID","Skill Category"]], on="Skill ID", how="left")
        pivot = rs_m.groupby(["Job Role","Skill Category"])["Required Proficiency Level"].mean().unstack(fill_value=0).round(1)
        if not pivot.empty and pivot.shape[0] > 1 and pivot.shape[1] > 1:
            s += plotly_embed(heatmap_chart(pivot.values.tolist(), pivot.columns.tolist(), pivot.index.tolist(),
                "Role × Skill Category — Avg Required Proficiency", max(400, len(pivot)*30+100)),
                "Proficiency depth required per role × skill category")
    if "Job Role" in active_emp.columns:
        rh = active_emp["Job Role"].value_counts().reset_index()
        rh.columns = ["Job Role","Headcount"]
        s += plotly_embed(bar_chart(rh["Job Role"].tolist(), rh["Headcount"].tolist(), "Headcount by Role",
            orientation="h", height=max(380, len(rh)*22+60)), "Role headcount — identifies concentration risk")
    s += insight_box(ai.get("s8_roles", f"<strong>{m['crit_roles']}</strong> critical roles identified. <strong>{m['roles_unmapped']}</strong> roles unmapped to skills — limiting gap analysis accuracy. Role Saturation Index: <strong>{m['role_sat_idx']:.1f}%</strong>."), "💡")
    sections.append(s)

    # ── S9 — SKILLS FRAMEWORK ────────────────────────────────────────────────
    s = section_header(9, "Skills Framework", "🛠️")
    s += kpi_row(
        kpi_tile("Total Skills", m["total_skills"], color=NAVY),
        kpi_tile("Critical Skills", m["crit_skills_cnt"], color=RED),
        kpi_tile("Skills Mapped", m["skills_in_roles"], color=GREEN),
        kpi_tile("Unmapped Skills", m["unmapped_skills"], color=ORANGE),
        kpi_tile("Roles with Skills", m["roles_mapped"], color=BLUE),
    )
    if not skills_master.empty and "Skill Category" in skills_master.columns:
        sc = skills_master["Skill Category"].value_counts()
        s += plotly_embed(bar_chart(sc.index.tolist(), sc.values.tolist(), "Skills by Category", "Category", "Count", NAVY), "Skill category distribution")
    if not emp_skills.empty and "Proficiency Level" in emp_skills.columns:
        pl = emp_skills["Proficiency Level"].value_counts().sort_index()
        s += plotly_embed(bar_chart([f"Level {l}" for l in pl.index], pl.values.tolist(),
            "Employee Skill Proficiency Distribution", "Level", "Records", BLUE), "Majority cluster at levels 2-3 — developing stage")
    if not skills_master.empty and "Is Critical Skill (Y/N)" in skills_master.columns and "Skill Category" in skills_master.columns:
        sm_cat = skills_master.groupby(["Skill Category","Is Critical Skill (Y/N)"]).size().unstack(fill_value=0)
        if "Y" in sm_cat.columns and "N" in sm_cat.columns:
            s += plotly_embed(stacked_bar_chart(sm_cat.index.tolist(),
                {"Critical": sm_cat["Y"].tolist(), "Non-Critical": sm_cat["N"].tolist()},
                "Critical vs Non-Critical Skills by Category"), "Critical skill concentration by category")
    s += insight_box(ai.get("s9_skills", f"<strong>{m['total_skills']}</strong> skills, <strong>{m['crit_skills_cnt']}</strong> critical. <strong>{m['unmapped_skills']}</strong> skills unmapped to roles. Proficiency data shows workforce in developing stage."), "💡")
    sections.append(s)

    # ── S10 — COMPETENCIES FRAMEWORK ─────────────────────────────────────────
    s = section_header(10, "Competencies Framework", "🧠")
    s += kpi_row(
        kpi_tile("Total Competencies", m["total_comps"], color=NAVY),
        kpi_tile("Critical Competencies", m["crit_comps_cnt"], color=RED),
        kpi_tile("Competencies Mapped", m["comps_mapped"], color=GREEN),
        kpi_tile("Unmapped", m["unmapped_comps"], color=ORANGE),
        kpi_tile("Roles Mapped", role_comps["Job Role"].nunique() if not role_comps.empty and "Job Role" in role_comps.columns else 0, color=BLUE),
    )
    if not comp_master.empty and "Competency Category" in comp_master.columns:
        cc = comp_master["Competency Category"].value_counts()
        s += plotly_embed(bar_chart(cc.index.tolist(), cc.values.tolist(), "Competencies by Category", "Category", "Count", PURPLE), "Competency category spread")
    if not emp_comps.empty and "Proficiency Level" in emp_comps.columns:
        cp = emp_comps["Proficiency Level"].value_counts().sort_index()
        s += plotly_embed(bar_chart([f"Level {l}" for l in cp.index], cp.values.tolist(),
            "Competency Proficiency Distribution", "Level", "Records", PURPLE), "Employee competency proficiency levels")
    s += insight_box(ai.get("s10_competencies", f"<strong>{m['total_comps']}</strong> competencies, <strong>{m['crit_comps_cnt']}</strong> critical. <strong>{m['unmapped_comps']}</strong> not yet mapped to roles. Competency coaching needed for behavioural and cognitive gaps."), "💡")
    sections.append(s)

    # ── S11 — CURRENT CAPABILITY ASSESSMENT ──────────────────────────────────
    s = section_header(11, "Current Capability Assessment", "📊")
    s += kpi_row(
        kpi_tile("Critical Skills Index", f"{m['crit_skills_idx']:.1f}", "%", color=GREEN if m["crit_skills_idx"] >= 75 else RED),
        kpi_tile("Skill Scarcity Index", f"{m['skill_scarcity_idx']:.1f}", "%", color=RED if m["skill_scarcity_idx"] > 20 else GREEN),
        kpi_tile("Total Certs", m["total_certs"], color=BLUE),
        kpi_tile("Certified Employees", m["cert_emps"], color=GREEN),
        kpi_tile("Expired Certs", m["expired_certs"], color=ORANGE if m["expired_certs"] > 0 else GREEN),
        kpi_tile("Geographic Risk", f"{m['geo_risk_idx']:.1f}", "%", color=RED if m["geo_risk_idx"] > 25 else ORANGE),
        kpi_tile("Demographic Risk", f"{m['demo_risk']:.1f}", "%", color=RED if m["demo_risk"] > 20 else GREEN),
        kpi_tile("Cert Coverage", f"{m['cert_cov_idx']:.1f}", "%", color=GREEN if m["cert_cov_idx"] >= 50 else ORANGE),
    )
    gap_df = m["gap_df"]
    if not gap_df.empty and "Gap Severity" in gap_df.columns:
        sev = gap_df.groupby(["Is Critical Skill","Gap Severity"]).size().unstack(fill_value=0)
        if not sev.empty:
            s += plotly_embed(stacked_bar_chart(
                sev.index.tolist(),
                {col: sev[col].tolist() for col in sev.columns if col in sev.columns},
                "Gap Severity by Skill Criticality"), "High severity gaps on critical skills require immediate action")
    s += insight_box(ai.get("s11_capability", f"Critical Skills Index: <strong>{m['crit_skills_idx']:.1f}%</strong>. Skill Scarcity: <strong>{m['skill_scarcity_idx']:.1f}%</strong>. Geographic Risk: <strong>{m['geo_risk_idx']:.1f}%</strong>. <strong>{m['expired_certs']}</strong> expired certifications require urgent renewal."), "💡")
    sections.append(s)

    # ── S12 — PRIORITY TRAINING NEEDS ────────────────────────────────────────
    s = section_header(12, "Priority Training Needs", "🎯")
    q1 = m["q1_skills"]; q2 = m["q2_skills"]
    s += kpi_row(
        kpi_tile("Q1 — High Impact / High Urgency", len(q1), color=RED),
        kpi_tile("Q2 — High Impact / Low Urgency", len(q2), color=ORANGE),
        kpi_tile("Q3 — Low Impact / High Urgency", len(m["q3_skills"]), color=BLUE),
        kpi_tile("Q4 — Low Impact / Low Urgency", len(m["q4_skills"]), color="#AAAAAA"),
    )
    skill_sum = m["skill_summary"]
    if not skill_sum.empty and "Quadrant" in skill_sum.columns:
        s += plotly_embed(scatter_quadrant(skill_sum, "Priority Training Quadrant Analysis"), "Bubble size = employees affected. Red = immediate action required.")
    if not q1.empty:
        s += subsection("Q1 Priority Skills — Immediate Action Required")
        q1_disp = q1[["Skill Name","Skill Category","avg_gap","gap_pct","emp_with_gap"]].copy() if "Skill Name" in q1.columns else q1.head(10)
        q1_disp.columns = ["Skill","Category","Avg Gap","% Employees","# Affected"] if "Skill Name" in q1.columns else q1_disp.columns
        s += table_html(q1_disp.round(1), max_rows=10)
    s += insight_box(ai.get("s12_priority", f"<strong>{len(q1)}</strong> Q1 skills require immediate intervention. <strong>{len(q2)}</strong> Q2 skills for planned delivery. Q1 skills should receive first budget allocation."), "💡")
    sections.append(s)

    # ── S13 — LEARNING INVESTMENT & DEMAND ───────────────────────────────────
    s = section_header(13, "Learning Investment & Demand", "💰")
    s += kpi_row(
        kpi_tile("Total Budget", f"₹{m['total_budget']/100000:.1f}L", color=NAVY),
        kpi_tile("Budget/Employee", f"₹{m['avg_budget_pp']:,.0f}", color=BLUE),
        kpi_tile("Total Hours", f"{m['total_hrs']:.0f}", "hrs", color=TEAL),
        kpi_tile("Avg Hrs/Employee", m["avg_hrs"], "hrs", color=GREEN if m["avg_hrs"] >= 30 else ORANGE),
        kpi_tile("Critical Skill Hrs", f"{m['crit_hrs_total']:.0f}", "hrs", color=RED),
        kpi_tile("Learning Penetration", f"{m['learning_pen_idx']:.1f}", "%", color=GREEN if m["learning_pen_idx"] >= 85 else ORANGE),
        kpi_tile("Training Intensity", f"{m['training_intensity']:.1f}", "hrs/emp", color=TEAL),
    )
    if not training.empty:
        if "Training Type" in training.columns and "Training Hours" in training.columns:
            tt = training.groupby("Training Type")["Training Hours"].sum().reset_index()
            s += plotly_embed(pie_chart(tt["Training Type"].tolist(), tt["Training Hours"].tolist(), "Training Hours by Type"), "Training delivery type breakdown")
        if "Job Family" in training.columns and "Training Hours" in training.columns:
            jf_hrs = training.groupby("Job Family")["Training Hours"].sum().sort_values(ascending=False)
            s += plotly_embed(bar_chart(jf_hrs.index.tolist(), jf_hrs.values.tolist(), "Training Hours by Job Family", "Job Family", "Hours", GOLD), "Training hour distribution by job family")
    s += insight_box(ai.get("s13_investment", f"Total investment: <strong>₹{m['total_budget']/100000:.1f}L</strong> across <strong>{m['total_hrs']:.0f}</strong> hours. Avg <strong>{m['avg_hrs']}</strong> hrs/employee ({'meets' if m['avg_hrs'] >= 30 else 'below'} the ~32 hr IT benchmark). Learning penetration: <strong>{m['learning_pen_idx']:.1f}%</strong>."), "💡")
    sections.append(s)

    # ── S14 — COMPOSITE INDICES ───────────────────────────────────────────────
    s = section_header(14, "Composite Indices", "📈")
    composite = m["composite"]
    cards_html = ""
    for idx_name, (val, threshold, direction) in composite.items():
        if direction == "higher":
            delta = val - threshold
            status_color = GREEN if val >= threshold else (ORANGE if val >= threshold * 0.75 else RED)
            delta_label = f"{'▲' if delta >= 0 else '▼'} {abs(delta):.1f}% vs target"
        elif direction == "lower":
            delta = threshold - val
            status_color = GREEN if val <= threshold else (ORANGE if val <= threshold * 1.3 else RED)
            delta_label = f"{'✅' if val <= threshold else '⚠️'} target ≤{threshold}%"
        else:
            status_color = BLUE
            delta_label = f"Contextual — target ~{threshold}"
        cards_html += f'''<div class="composite-card" style="border-left:5px solid {status_color}">
          <div class="composite-name">{idx_name}</div>
          <div class="composite-val" style="color:{status_color}">{val:.1f}<span class="composite-unit">{"%" if isinstance(val, float) else ""}</span></div>
          <div class="composite-delta" style="color:{status_color}">{delta_label}</div>
          <div class="composite-bench">Target: {threshold}%</div></div>'''
    s += f'<div class="composite-grid">{cards_html}</div>'

    # Radar chart
    radar_keys = ["Role Skill Coverage Index","Learning Penetration Index","Critical Skills Index",
                  "Certification Coverage Index","Training Intensity Index","Level Distribution Index"]
    r_labels = [k.replace(" Index","").replace(" Risk Index","") for k in radar_keys if k in composite]
    r_org    = [composite[k][0] for k in radar_keys if k in composite]
    r_target = [composite[k][1] for k in radar_keys if k in composite]
    if r_labels:
        s += plotly_embed(radar_chart(r_labels, r_org, r_target), "Blue = organisation actuals; Gold = target thresholds")
    s += insight_box(ai.get("s14_indices", f"Strongest: Role Skill Coverage <strong>{m['role_skill_cov']:.1f}%</strong>, Learning Penetration <strong>{m['learning_pen_idx']:.1f}%</strong>. Most critical: Cert Coverage <strong>{m['cert_cov_idx']:.1f}%</strong>, Skill Scarcity <strong>{m['skill_scarcity_idx']:.1f}%</strong>."), "📈")
    sections.append(s)

    # ── S15 — 30-60-90 DAY ROADMAP ───────────────────────────────────────────
    s = section_header(15, "30-60-90 Day Roadmap", "🗓️")
    q1_list = q1["Skill Name"].tolist()[:5] if not q1.empty and "Skill Name" in q1.columns else ["Key Skill 1","Key Skill 2"]
    roadmap = [
        ("Days 1–30 🔴", f"Launch ILT for Q1 critical skills: {', '.join(q1_list[:3])}", "Q1 Quadrant", "L&D Team", "ILT/Bootcamp", "↑ Critical Skills Index"),
        ("Days 1–30 🔴", f"Certification renewal — {m['expired_certs']} expired certs", "Cert Coverage Index", "L&D + HR", "Self-Paced + Exam Prep", "↑ Cert Coverage"),
        ("Days 1–30 🔴", "Complete skill mapping for unmapped roles", f"{m['roles_unmapped']} roles unmapped", "HR + BU Heads", "Workshop", "↑ Role Skill Coverage"),
        ("Days 1–30 🔴", "Structured onboarding path for L1/L2 employees", "Level Distribution Index", "L&D", "Blended", "↑ Learning Penetration"),
        ("Days 31–60 🟠", f"Q2 skill programmes: {', '.join(q1_list[3:5])}", "Q2 Quadrant", "L&D Team", "Online + Mentoring", "↑ Critical Skills Index"),
        ("Days 31–60 🟠", "Competency coaching for L3/L4 managers", "Competency gap at mid-senior level", "People Managers", "Coaching", "↑ Competency Index"),
        ("Days 31–60 🟠", "Virtual programmes for geographic risk locations", f"Geo Risk: {m['geo_risk_idx']:.1f}%", "L&D + Regional Heads", "Virtual ILT", "↓ Geographic Risk"),
        ("Days 31–60 🟠", "D&I learning pathway and mentoring circles", f"Female: {m['female_pct']:.1f}% vs 35%", "HR + CHRO", "Workshop + Mentoring", "↑ Diversity Index"),
        ("Days 61–90 🔵", "Career development and succession plans for critical roles", "Age Risk — succession pipeline", "HR + Leadership", "IDP + Coaching", "↓ Age Risk"),
        ("Days 61–90 🔵", "Integrate LNA into annual performance cycle", "Systemic learning culture", "CHRO", "Policy + System", "Sustained improvement"),
        ("Days 61–90 🔵", "Commission Level 2 LNA (individual IDPs)", "Foundation established by L1 LNA", "L&D + HR", "Assessment + IDP", "Personalised learning plans"),
    ]
    rdf = pd.DataFrame(roadmap, columns=["Phase","Action","Priority Basis","Owner","Format","KPI Impact"])
    s += table_html(rdf, col_colors={"Phase": {"1–30": RED, "31–60": ORANGE, "61–90": BLUE}})
    s += insight_box(ai.get("s15_roadmap", f"30-day priorities: <strong>{len(q1)}</strong> Q1 skills and <strong>{m['expired_certs']}</strong> expired certifications. Delays beyond 60 days risk compounding skill scarcity as project dependencies on critical skills grow."), "🗓️")
    sections.append(s)

    # ── S16 — ASSUMPTIONS & RISKS ─────────────────────────────────────────────
    s = section_header(16, "Assumptions & Risks", "⚠️")
    risks = pd.DataFrame([
        ["Data Completeness",    "Medium", "Proficiency data is self-assessed — calibration with manager validation recommended."],
        ["Certification Recency","Medium", "Certs without expiry dates assumed active — some may be practically outdated."],
        ["Point-in-Time Snapshot","Low",   "LNA reflects data at report date. Quarterly refresh recommended."],
        ["Manager Input Missing", "High",  "Manager assessments not incorporated — may understate behavioural gaps."],
        ["Business Goals",       "Medium", "Business goals derived from workforce patterns — client validation needed."],
        ["Single-Year Training",  "Low",   "Training data covers one year. Multi-year trends would provide stronger signal."],
        ["Out-of-scope Roles",   "Low",    "Board, interns, contractors excluded — future inclusion recommended."],
        ["Attrition Impact",     "Medium", "Exited employees may have held critical skills — untracked capability loss."],
    ], columns=["Area","Risk Level","Detail"])
    s += table_html(risks, col_colors={"Risk Level": {"High": RED, "Medium": ORANGE, "Low": GREEN}})
    s += insight_box(ai.get("s16_risks", f"Primary risk: self-reported proficiency without manager calibration. With <strong>{m['cert_cov_idx']:.1f}%</strong> certification coverage and a single-year training snapshot, findings should be treated as directional until validated."), "⚠️")
    sections.append(s)

    # ── S17 — CONCLUSION ─────────────────────────────────────────────────────
    s = section_header(17, "Conclusion", "🏁")
    q1_c = len(q1)
    s += insight_box(ai.get("s17_conclusion",
        f"<strong>{COMPANY}</strong> has completed its first Level 1 LNA covering <strong>{N}</strong> employees across "
        f"<strong>{m['total_locs']}</strong> locations and <strong>{m['total_roles']}</strong> roles. "
        f"Role Skill Coverage <strong>{m['role_skill_cov']:.0f}%</strong> and Learning Penetration <strong>{m['learning_pen_idx']:.0f}%</strong> "
        f"are positive foundations, but <strong>{q1_c}</strong> critical skills require immediate action. "
        f"The 30-60-90 day roadmap provides a clear prioritised path. "
        f"Level 2 LNA (individual IDPs) should follow the 90-day cycle."), "📝")

    s += subsection("Summary Scorecard")
    scorecard = []
    for idx_name, (val, threshold, direction) in list(composite.items())[:8]:
        if direction == "higher":
            status = "✅ On Track" if val >= threshold else ("⚠️ At Risk" if val >= threshold * 0.75 else "❌ Below Target")
        elif direction == "lower":
            status = "✅ On Track" if val <= threshold else ("⚠️ At Risk" if val <= threshold * 1.3 else "❌ Below Target")
        else:
            status = "ℹ️ Contextual"
        scorecard.append([idx_name, f"{val:.1f}%", f"{threshold}%", status])
    sc_df = pd.DataFrame(scorecard, columns=["Index","Current","Target","Status"])
    s += table_html(sc_df, col_colors={"Status": {"✅": GREEN, "⚠️": ORANGE, "❌": RED}})

    s += subsection("Next Steps")
    next_steps = [
        f"Present this LNA to {COMPANY} leadership for review and approval (Week 1)",
        "Conduct stakeholder workshop to validate findings and assign ownership (Week 2)",
        "Convert 30-60-90 Roadmap into a formal L&D project plan with budget (Week 2–3)",
        "Begin vendor and programme sourcing for Q1 training interventions (Week 3)",
        "Set 30-day checkpoint to review roadmap progress (Day 30)",
        "Initiate Level 2 LNA — individual-level gap assessment and IDPs (Month 4)",
        "Schedule next LNA refresh cycle for next quarter",
    ]
    s += "<ol class='next-steps'>" + "".join(f"<li>{ns}</li>" for ns in next_steps) + "</ol>"
    sections.append(s)

    return sections


# ── Full HTML Assembly ────────────────────────────────────────────────────────

def assemble_html_report(data: dict, sections: list) -> str:
    """Assemble all 17 sections into a complete self-contained HTML document."""
    COMPANY     = data["company"]
    TIME_PERIOD = data["time_period"]
    YEAR        = data["year"]
    REPORT_DATE = data["report_date"]

    section_meta = [
        ("1","Cover Page","🏢"), ("2","Document Control & Governance","📋"),
        ("3","Executive Summary","📌"), ("4","Business & Strategic Context","🎯"),
        ("5","Scope & Objectives","🔍"), ("6","Methodology & Data Sources","🔬"),
        ("7","Participant Profile","👥"), ("8","Role-Based Context","🏗️"),
        ("9","Skills Framework","🛠️"), ("10","Competencies Framework","🧠"),
        ("11","Current Capability Assessment","📊"), ("12","Priority Training Needs","🎯"),
        ("13","Learning Investment & Demand","💰"), ("14","Composite Indices","📈"),
        ("15","30-60-90 Day Roadmap","🗓️"), ("16","Assumptions & Risks","⚠️"),
        ("17","Conclusion","🏁"),
    ]
    toc_items = "\n".join(
        f'<a class="toc-item" href="#sec{n}"><div class="toc-num">{n}</div>{icon} {title}</a>'
        for n, title, icon in section_meta
    )
    sections_body = "\n".join(
        f'<div class="section" id="sec{i+1}">{html}</div>'
        for i, html in enumerate(sections)
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LNA Level 1 — {COMPANY} — {TIME_PERIOD} {YEAR}</title>
  <script src="{PLOTLY_CDN}"></script>
  <style>{REPORT_CSS}</style>
</head>
<body>
<div class="report-wrapper">
  <div class="report-header">
    <div class="report-header-left">
      <div class="brand">EDSTELLAR</div>
      <div class="tagline">Learning Needs Analysis — Level 1 Report</div>
    </div>
    <div class="report-header-right">
      <div><strong style="color:#F4A024">{COMPANY}</strong></div>
      <div>Period: {TIME_PERIOD} {YEAR}</div>
      <div>Date: {REPORT_DATE}</div>
      <div>Classification: Confidential</div>
    </div>
  </div>
  <div class="toc">
    <h2>📑 Table of Contents</h2>
    <div class="toc-grid">{toc_items}</div>
  </div>
  {sections_body}
  <div class="report-footer">
    <div>© 2025 <span class="footer-brand">Edstellar</span> — All rights reserved.</div>
    <div>{COMPANY} · LNA Level 1 · {TIME_PERIOD} {YEAR}</div>
    <div>Generated: {REPORT_DATE}</div>
  </div>
</div>
</body>
</html>"""
