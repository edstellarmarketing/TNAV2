"""
logic/lni_builder.py — Edstellar LNA Platform
LNI/TNI report builder — combines LNA output + Strategy Profile.
Pure logic — no Streamlit dependencies.
"""

import json
from datetime import datetime


NAVY  = "#1B3A6B"
TEAL  = "#0F7B6C"
AMBER = "#E67E22"
RED   = "#C0392B"
GREEN = "#217346"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700;800&family=DM+Serif+Display&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'DM Sans', sans-serif; background: #F0F3F8; color: #1A1A2E; font-size: 14px; line-height: 1.65; }
.report-wrap { max-width: 1200px; margin: 0 auto; padding: 32px 24px 80px; }

/* Header */
.report-header { background: linear-gradient(135deg, #0F2447 0%, #1B3A6B 60%, #2E5BA8 100%);
    border-radius: 16px; padding: 36px 48px; margin-bottom: 32px; color: white; }
.rh-badge { font-size: 10px; letter-spacing: 2px; text-transform: uppercase;
    background: rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 20px;
    display: inline-block; margin-bottom: 12px; }
.rh-title { font-family: 'DM Serif Display', serif; font-size: 34px; line-height: 1.2; margin-bottom: 8px; }
.rh-sub { font-size: 13px; color: rgba(255,255,255,0.65); }
.rh-meta { display: flex; gap: 24px; margin-top: 20px; flex-wrap: wrap; }
.rh-meta-item { font-size: 11px; color: rgba(255,255,255,0.55); }
.rh-meta-item strong { color: rgba(255,255,255,0.9); font-size: 13px; display: block; }

/* Strategy banner */
.strategy-banner { background: linear-gradient(135deg, #0F4C2F, #1A7A50);
    border-radius: 12px; padding: 20px 28px; margin-bottom: 28px; color: white; }
.sb-label { font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase;
    color: rgba(255,255,255,0.6); margin-bottom: 8px; }
.sb-text { font-size: 13px; line-height: 1.6; color: rgba(255,255,255,0.9); }
.sb-version { font-size: 11px; color: rgba(255,255,255,0.5); margin-top: 10px; }

/* Section cards */
.lni-section { background: white; border-radius: 12px; padding: 28px 32px;
    margin-bottom: 20px; box-shadow: 0 2px 12px rgba(27,58,107,0.07);
    border: 1px solid #E8EDF5; border-left: 6px solid #1B3A6B; }
.lni-section-header { display: flex; align-items: center; gap: 14px; margin-bottom: 20px; }
.lni-section-num { background: #1B3A6B; color: white; width: 36px; height: 36px;
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 14px; flex-shrink: 0; }
.lni-section-title { font-size: 17px; font-weight: 700; color: #1B3A6B; }
.lni-section-sub { font-size: 11px; color: #9BA8B8; margin-top: 2px; }

/* Two-column compare */
.compare-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 16px 0; }
.compare-col { border-radius: 8px; padding: 16px 18px; }
.compare-col.lna { background: #F4F7FC; border: 1px solid #C3D0E8; }
.compare-col.lni { background: #F0FBF4; border: 1px solid #C3E6CB; }
.compare-label { font-size: 10px; font-weight: 700; letter-spacing: 1px;
    text-transform: uppercase; margin-bottom: 10px; }
.compare-col.lna .compare-label { color: #1B3A6B; }
.compare-col.lni .compare-label { color: #217346; }
.compare-col p { font-size: 13px; line-height: 1.6; color: #2D3748; margin-bottom: 8px; }

/* Priority cards */
.priority-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; margin: 14px 0; }
.priority-card { background: #fff; border-radius: 8px; padding: 14px 16px;
    border: 1px solid #E8EDF5; border-top: 4px solid #1B3A6B; }
.pc-q { font-size: 10px; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase; color: #9BA8B8; }
.pc-name { font-weight: 700; color: #1B3A6B; font-size: 14px; margin: 4px 0; }
.pc-gap { font-size: 12px; color: #6B7A99; }
.pc-tag { display: inline-block; padding: 2px 8px; border-radius: 20px;
    font-size: 10px; font-weight: 600; margin-top: 8px; }
.tag-red    { background: #FFEBEE; color: #C0392B; }
.tag-orange { background: #FFF3E0; color: #E67E22; }
.tag-green  { background: #E8F5E9; color: #217346; }
.tag-blue   { background: #E3F2FD; color: #1B3A6B; }

/* Segment cards */
.segment-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px; margin: 14px 0; }
.segment-card { background: white; border-radius: 10px; padding: 18px 20px;
    border: 1px solid #E8EDF5; border-top: 4px solid #4472C4; }
.sc-name { font-weight: 700; color: #1B3A6B; font-size: 14px; margin-bottom: 12px; }
.sc-row { display: flex; gap: 8px; margin-bottom: 6px; align-items: flex-start; }
.sc-label { font-size: 10px; color: #9BA8B8; text-transform: uppercase; letter-spacing: 0.5px; min-width: 70px; flex-shrink: 0; padding-top: 2px; }
.sc-value { font-size: 12px; color: #2D3748; font-weight: 600; }

/* Roadmap */
.roadmap-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px; margin: 14px 0; }
.rm-card { border-radius: 10px; padding: 18px 20px; }
.rm-card.d30 { background: #FFEBEE; border: 1px solid #F5C6CB; border-top: 5px solid #C0392B; }
.rm-card.d60 { background: #FFF3E0; border: 1px solid #FFE082; border-top: 5px solid #E67E22; }
.rm-card.d90 { background: #E8F5E9; border: 1px solid #C3E6CB; border-top: 5px solid #217346; }
.rm-period { font-weight: 800; font-size: 13px; margin-bottom: 10px; }
.rm-card.d30 .rm-period { color: #C0392B; }
.rm-card.d60 .rm-period { color: #E67E22; }
.rm-card.d90 .rm-period { color: #217346; }
.rm-item { font-size: 12px; color: #2D3748; margin-bottom: 6px; padding-left: 14px; position: relative; }
.rm-item::before { content: "→"; position: absolute; left: 0; color: #9BA8B8; }

/* Conflict box */
.conflict-box { border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-size: 12px; }
.conflict-box.critical { background: #FFEBEE; border: 1px solid #F5C6CB; border-left: 5px solid #C0392B; }
.conflict-box.warning  { background: #FFF8E1; border: 1px solid #FFE082; border-left: 5px solid #F4A024; }
.conflict-box.info     { background: #E3F2FD; border: 1px solid #BBDEFB; border-left: 5px solid #1B3A6B; }
.conflict-title { font-weight: 700; margin-bottom: 4px; }

/* Index table */
.index-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.index-table th { background: #F4F7FC; color: #1B3A6B; font-weight: 700; font-size: 11px;
    text-transform: uppercase; letter-spacing: 0.5px; padding: 10px 14px; text-align: left; }
.index-table td { padding: 10px 14px; border-bottom: 1px solid #F0F3F8; }
.index-table tr:hover td { background: #FAFBFF; }

/* Footer */
.report-footer { text-align: center; padding: 32px; color: #9BA8B8; font-size: 11px; margin-top: 40px; }
</style>
"""


def _skill_list_html(skills_df, n=8):
    """Render top N skills as priority cards."""
    if skills_df is None or (hasattr(skills_df, "empty") and skills_df.empty):
        return "<p style='color:#9BA8B8;font-size:13px'>No skill data available.</p>"

    rows = skills_df.head(n).to_dict("records")
    cards = []
    for r in rows:
        name    = r.get("Skill Name", r.get("Skill ID", "Unknown"))
        gap     = r.get("avg_gap", 0)
        gap_pct = r.get("gap_pct", 0)
        crit    = r.get("Is Critical Skill", "N") == "Y"
        quad    = r.get("Quadrant", "")
        q_short = quad.split("—")[0].strip() if "—" in quad else quad

        tag_cls = "tag-red" if crit and gap >= 2 else ("tag-orange" if crit else "tag-blue")
        tag_lbl = "Critical" if crit else "Standard"

        cards.append(f"""
        <div class="priority-card">
            <div class="pc-q">{q_short}</div>
            <div class="pc-name">{name}</div>
            <div class="pc-gap">Avg gap: {gap:.1f} · {gap_pct:.0f}% employees affected</div>
            <span class="pc-tag {tag_cls}">{tag_lbl}</span>
        </div>""")

    return f'<div class="priority-grid">{"".join(cards)}</div>'


def _segment_cards_html(segment_config: dict) -> str:
    if not segment_config:
        return "<p style='color:#9BA8B8;font-size:13px'>No segments selected.</p>"

    colors = ["#4472C4", "#1B3A6B", "#217346", "#E67E22", "#8E44AD", "#2E86AB", "#C0392B"]
    cards = []
    for i, (seg, cfg) in enumerate(segment_config.items()):
        color = colors[i % len(colors)]
        bw = cfg.get("budget_weight", 1.0)
        cards.append(f"""
        <div class="segment-card" style="border-top-color:{color}">
            <div class="sc-name">{seg}</div>
            <div class="sc-row">
                <div class="sc-label">Format</div>
                <div class="sc-value">{cfg.get('format','—')}</div>
            </div>
            <div class="sc-row">
                <div class="sc-label">Delivery</div>
                <div class="sc-value">{cfg.get('delivery','—')}</div>
            </div>
            <div class="sc-row">
                <div class="sc-label">Budget wt.</div>
                <div class="sc-value">{bw:.1f}x relative allocation</div>
            </div>
        </div>""")

    return f'<div class="segment-grid">{"".join(cards)}</div>'


def _conflicts_html(conflicts: list, justifications: dict = None) -> str:
    if not conflicts:
        return "<p style='color:#217346;font-size:13px'>✅ No strategic overrides detected. Leadership intent aligns with LNA data signals.</p>"

    html = []
    for c in conflicts:
        sev = c.get("severity", "info")
        dim = c.get("dimension", "")
        msg = c.get("message", "")
        j   = (justifications or {}).get(dim, "")
        j_html = f'<div style="margin-top:8px;font-style:italic;color:#555">Justification: {j}</div>' if j else ""
        html.append(f"""
        <div class="conflict-box {sev}">
            <div class="conflict-title">⚠️ {dim}</div>
            <div>{msg}</div>
            {j_html}
        </div>""")

    return "".join(html)


def _roadmap_html(m: dict, profile: dict) -> str:
    q1 = m.get("q1_skills", None)
    q1_names = []
    if q1 is not None and not (hasattr(q1, "empty") and q1.empty):
        q1_names = q1["Skill Name"].tolist()[:5] if "Skill Name" in q1.columns else []

    expired_certs = m.get("expired_certs", 0)
    geo_risk      = m.get("geo_risk_idx", 0)
    roles_unmapped = m.get("roles_unmapped", 0)
    horizon       = profile.get("time_horizon", "Short-term (3–6 months)")
    segments      = list(profile.get("segment_config", {}).keys())[:2]

    # 30-day items
    d30 = [f"Launch training for {s}" for s in (q1_names[:3] or ["priority skills"])]
    if expired_certs > 0:
        d30.append(f"Renew {expired_certs} expired certifications")

    # 60-day items
    d60 = []
    if roles_unmapped > 0:
        d60.append(f"Map {roles_unmapped} unmapped roles to skills framework")
    if geo_risk > 30:
        d60.append("Deploy virtual delivery for high geographic risk locations")
    d60.append("Launch competency coaching for selected segments")
    if segments:
        d60.append(f"Initiate {segments[0]} development programme")

    # 90-day items
    d90 = [
        "Conduct mid-cycle progress review vs LNA indices",
        "Adjust Q2 skill delivery plan based on Q1 outcomes",
        "Prepare LNA Level 2 assessment scope",
    ]
    if len(segments) > 1:
        d90.append(f"Expand programme to {segments[1]} cohort")

    def items(lst):
        return "".join(f'<div class="rm-item">{item}</div>' for item in lst)

    return f"""
    <div class="roadmap-grid">
        <div class="rm-card d30">
            <div class="rm-period">🔴 Days 1–30 — Immediate</div>
            {items(d30)}
        </div>
        <div class="rm-card d60">
            <div class="rm-period">🟡 Days 31–60 — Structural</div>
            {items(d60)}
        </div>
        <div class="rm-card d90">
            <div class="rm-period">🟢 Days 61–90 — Scale</div>
            {items(d90)}
        </div>
    </div>"""


def _index_table_html(m: dict, profile: dict) -> str:
    composite   = m.get("composite", {})
    skill_weights = profile.get("skill_weights", {})

    rows = []
    for name, (val, threshold, direction) in composite.items():
        if direction == "higher":
            status = "✅ On target" if val >= threshold else ("⚠️ Below" if val >= threshold * 0.75 else "❌ Critical")
            color  = GREEN if val >= threshold else (AMBER if val >= threshold * 0.75 else RED)
        elif direction == "lower":
            status = "✅ On target" if val <= threshold else ("⚠️ Elevated" if val <= threshold * 1.3 else "❌ High Risk")
            color  = GREEN if val <= threshold else (AMBER if val <= threshold * 1.3 else RED)
        else:
            status = "ℹ️ Context"; color = NAVY

        rows.append(f"""
        <tr>
            <td style="font-weight:600">{name}</td>
            <td style="font-weight:800;color:{color}">{val:.1f}%</td>
            <td style="color:#9BA8B8">{threshold}%</td>
            <td style="color:{color}">{status}</td>
        </tr>""")

    return f"""
    <table class="index-table">
        <thead>
            <tr>
                <th>Index</th>
                <th>Current</th>
                <th>Target</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>{"".join(rows)}</tbody>
    </table>"""


# ── Main Report Builder ───────────────────────────────────────────────────────

def build_lni_report(data: dict, m: dict, profile: dict, ai_insights: dict = None) -> str:
    """
    Build the complete LNI/TNI HTML report.
    Combines LNA output (m) with Strategy Profile (profile).
    """
    company    = data.get("company", "Organisation")
    period     = f"{data.get('time_period','')} {data.get('year','')}".strip()
    n          = m.get("N", 0)
    locs       = m.get("total_locs", 0)
    roles      = m.get("total_roles", 0)
    q1         = m.get("q1_skills", None)
    q1_count   = len(q1) if q1 is not None and not (hasattr(q1,"empty") and q1.empty) else 0
    q2         = m.get("q2_skills", None)
    q2_count   = len(q2) if q2 is not None and not (hasattr(q2,"empty") and q2.empty) else 0

    strategy   = profile.get("strategic_summary", "Strategy configuration applied.")
    version    = profile.get("version", "v1.0")
    confirmed  = profile.get("confirmed_by", "Not specified")
    conf_date  = profile.get("created_display", datetime.now().strftime("%d %b %Y"))
    horizon    = profile.get("time_horizon", "Short-term (3–6 months)")
    conflicts  = profile.get("conflicts", [])
    justifs    = profile.get("justifications", {})
    seg_config = profile.get("segment_config", {})
    cult_prio  = profile.get("cultural_priorities", [])
    org_focus  = profile.get("org_focus", [])

    # KPI metrics for header
    rsc  = m.get("role_skill_cov", 0)
    csi  = m.get("crit_skills_idx", 0)
    lpi  = m.get("learning_pen_idx", 0)
    cci  = m.get("cert_cov_idx", 0)
    budget = m.get("total_budget", 0)
    budget_l = round(budget / 100000, 1) if budget else 0

    # Cultural priorities as tags
    cult_tags = "".join(
        f'<span style="background:rgba(255,255,255,0.15);padding:3px 10px;border-radius:20px;'
        f'font-size:11px;margin:3px 3px 0 0;display:inline-block">{c}</span>'
        for c in cult_prio
    ) if cult_prio else '<span style="color:rgba(255,255,255,0.5)">None specified</span>'

    # AI insight helper
    def ai(key, fallback=""):
        return (ai_insights or {}).get(key, fallback)

    sections = []

    # ── S1: Strategic Intent Summary ─────────────────────────────────────────
    conflict_critical = [c for c in conflicts if c.get("severity") == "critical"]
    conf_flag = f"""
    <div class="conflict-box critical">
        <div class="conflict-title">⚠️ {len(conflict_critical)} Strategic Override(s) Recorded</div>
        <div>Leadership intent conflicts with LNA data signals in {len(conflict_critical)} dimension(s). See Section 9 for details.</div>
    </div>""" if conflict_critical else ""

    sections.append(f"""
    <div class="lni-section">
        <div class="lni-section-header">
            <div class="lni-section-num">1</div>
            <div>
                <div class="lni-section-title">Strategic Intent Summary</div>
                <div class="lni-section-sub">Leadership configuration that governs this LNI/TNI</div>
            </div>
        </div>
        <div style="background:#F0FBF4;border:1px solid #C3E6CB;border-radius:8px;padding:14px 18px;margin-bottom:16px;font-size:13px;line-height:1.65">
            {strategy}
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px">
            <div style="background:#F4F7FC;border-radius:8px;padding:12px 16px">
                <div style="font-size:10px;color:#9BA8B8;text-transform:uppercase;margin-bottom:4px">Cultural Focus</div>
                <div style="font-size:12px;color:#1B3A6B;font-weight:600">{', '.join(cult_prio) or '—'}</div>
            </div>
            <div style="background:#F4F7FC;border-radius:8px;padding:12px 16px">
                <div style="font-size:10px;color:#9BA8B8;text-transform:uppercase;margin-bottom:4px">Org Focus Areas</div>
                <div style="font-size:12px;color:#1B3A6B;font-weight:600">{', '.join(org_focus) or 'All BUs'}</div>
            </div>
            <div style="background:#F4F7FC;border-radius:8px;padding:12px 16px">
                <div style="font-size:10px;color:#9BA8B8;text-transform:uppercase;margin-bottom:4px">Time Horizon</div>
                <div style="font-size:12px;color:#1B3A6B;font-weight:600">{horizon}</div>
            </div>
        </div>
        {conf_flag}
        <p style="font-size:11px;color:#9BA8B8">Confirmed by: {confirmed} · {conf_date} · {version}</p>
    </div>""")

    # ── S2: Priority Training Needs ───────────────────────────────────────────
    sections.append(f"""
    <div class="lni-section" style="border-left-color:#C0392B">
        <div class="lni-section-header">
            <div class="lni-section-num" style="background:#C0392B">2</div>
            <div>
                <div class="lni-section-title">Priority Training Needs</div>
                <div class="lni-section-sub">Strategy-weighted skill priorities from the LNA quadrant analysis</div>
            </div>
        </div>
        <div class="compare-grid">
            <div class="compare-col lna">
                <div class="compare-label">📊 LNA Baseline</div>
                <p><strong>{q1_count}</strong> skills in Q1 (High Impact / High Urgency)</p>
                <p><strong>{q2_count}</strong> skills in Q2 (High Impact / Lower Urgency)</p>
                <p>Role Skill Coverage: <strong>{rsc:.1f}%</strong> · Critical Skills Index: <strong>{csi:.1f}%</strong></p>
            </div>
            <div class="compare-col lni">
                <div class="compare-label">🎯 LNI/TNI Recommendation</div>
                <p>Focus <strong>Q1 skills first</strong> per {horizon} horizon configuration.</p>
                <p>Skill weights applied from strategy sliders — dimensions with higher weights are elevated in priority order.</p>
                <p>Segments: <strong>{', '.join(seg_config.keys()) or 'All employees'}</strong></p>
            </div>
        </div>
        <h4 style="color:#1B3A6B;margin:18px 0 10px;font-size:13px">Q1 — Immediate Priority Skills</h4>
        {_skill_list_html(q1, n=8)}
        {f'<h4 style="color:#4472C4;margin:18px 0 10px;font-size:13px">Q2 — Planned Skills</h4>{_skill_list_html(q2, n=6)}' if q2_count > 0 else ''}
    </div>""")

    # ── S3: Segment-Level Recommendations ─────────────────────────────────────
    sections.append(f"""
    <div class="lni-section" style="border-left-color:#4472C4">
        <div class="lni-section-header">
            <div class="lni-section-num" style="background:#4472C4">3</div>
            <div>
                <div class="lni-section-title">Segment-Level Recommendations</div>
                <div class="lni-section-sub">Training design per employee segment — format, delivery, and budget allocation</div>
            </div>
        </div>
        <div class="compare-grid">
            <div class="compare-col lna">
                <div class="compare-label">📊 LNA Context</div>
                <p><strong>{n}</strong> total employees · avg age <strong>{m.get('avg_age',0)}</strong> · avg tenure <strong>{m.get('avg_tenure',0)}</strong> yrs</p>
                <p>Learning Penetration: <strong>{lpi:.1f}%</strong> (benchmark: 85%)</p>
                <p>Avg training: <strong>{m.get('avg_hrs',0)}</strong> hrs/employee (benchmark: 32 hrs)</p>
            </div>
            <div class="compare-col lni">
                <div class="compare-label">🎯 Strategy Selection</div>
                <p><strong>{len(seg_config)}</strong> priority segment(s) selected for focused investment.</p>
                <p>Budget weight multipliers applied — higher-weight segments receive proportionally greater allocation.</p>
            </div>
        </div>
        {_segment_cards_html(seg_config)}
        {f'<div class="conflict-box info"><div class="conflict-title">ℹ️ Segments not selected</div><div>Employees outside the priority segments above will continue standard training programmes. They are not excluded — priority is determined by budget and schedule sequencing.</div></div>' if seg_config else ''}
    </div>""")

    # ── S4: Business Unit / Department Breakdown ───────────────────────────────
    bu_focus_html = ""
    if org_focus:
        tags = "".join(
            f'<span style="background:#EBF0FA;border:1px solid #C3D0E8;border-radius:20px;'
            f'padding:4px 12px;font-size:12px;font-weight:600;color:#1B3A6B;margin:3px">{b}</span>'
            for b in org_focus
        )
        bu_focus_html = f'<div style="margin:14px 0">{tags}</div>'
    else:
        bu_focus_html = '<p style="color:#9BA8B8;font-size:13px">All business units treated equally — no scope amplification applied.</p>'

    sections.append(f"""
    <div class="lni-section" style="border-left-color:#217346">
        <div class="lni-section-header">
            <div class="lni-section-num" style="background:#217346">4</div>
            <div>
                <div class="lni-section-title">Business Unit & Department Focus</div>
                <div class="lni-section-sub">Scope amplification — prioritised areas receive elevated recommendation weight</div>
            </div>
        </div>
        <div class="compare-col lna" style="margin-bottom:16px">
            <div class="compare-label">📊 LNA Scope</div>
            <p>{n} employees · {roles} roles · {locs} locations</p>
        </div>
        <div class="compare-col lni" style="margin-bottom:16px">
            <div class="compare-label">🎯 Priority Focus Areas</div>
            <p>Recommendations for the selected BUs/departments are sequenced first in the roadmap and receive proportionally higher training budget allocation.</p>
        </div>
        {bu_focus_html}
    </div>""")

    # ── S5: Learning Programme Design ─────────────────────────────────────────
    horizon_cfg = profile.get("horizon_config", {})
    budget_release = horizon_cfg.get("budget_release", "Phased")
    format_bias    = horizon_cfg.get("format_bias", "Blended")
    active_q       = horizon_cfg.get("quadrants", ["Q1"])

    sections.append(f"""
    <div class="lni-section" style="border-left-color:#8E44AD">
        <div class="lni-section-header">
            <div class="lni-section-num" style="background:#8E44AD">5</div>
            <div>
                <div class="lni-section-title">Learning Programme Design</div>
                <div class="lni-section-sub">Format, delivery mode, and design principles per priority area</div>
            </div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:18px">
            <div style="background:#F9F0FF;border:1px solid #E1BEE7;border-radius:8px;padding:14px 16px">
                <div style="font-size:10px;color:#8E44AD;font-weight:700;text-transform:uppercase;margin-bottom:6px">Active Quadrants</div>
                <div style="font-size:14px;font-weight:700;color:#1B3A6B">{', '.join(active_q)}</div>
            </div>
            <div style="background:#F9F0FF;border:1px solid #E1BEE7;border-radius:8px;padding:14px 16px">
                <div style="font-size:10px;color:#8E44AD;font-weight:700;text-transform:uppercase;margin-bottom:6px">Format Bias</div>
                <div style="font-size:14px;font-weight:700;color:#1B3A6B">{format_bias}</div>
            </div>
            <div style="background:#F9F0FF;border:1px solid #E1BEE7;border-radius:8px;padding:14px 16px">
                <div style="font-size:10px;color:#8E44AD;font-weight:700;text-transform:uppercase;margin-bottom:6px">Budget Release</div>
                <div style="font-size:14px;font-weight:700;color:#1B3A6B">{budget_release}</div>
            </div>
        </div>
        <div class="compare-grid">
            <div class="compare-col lna">
                <div class="compare-label">📊 LNA Training Data</div>
                <p>Total hours: <strong>{m.get('total_hrs',0):.0f}</strong> · Avg: <strong>{m.get('avg_hrs',0)}</strong> hrs/emp</p>
                <p>Training types: <strong>{data.get('training',__import__('pandas').DataFrame()).get('Training Type',__import__('pandas').Series()).value_counts().head(2).to_dict() if not data.get('training',__import__('pandas').DataFrame()).empty else 'N/A'}</strong></p>
                <p>Budget: <strong>Rs.{budget_l:.1f}L</strong> · Avg: <strong>Rs.{m.get('avg_budget_pp',0):,.0f}</strong>/emp</p>
            </div>
            <div class="compare-col lni">
                <div class="compare-label">🎯 LNI/TNI Design Guidance</div>
                <p>Q1 skills → <strong>ILT / instructor-led</strong> for maximum knowledge transfer speed.</p>
                <p>Segment-specific formats applied — see Section 3 for per-segment delivery modes.</p>
                <p>Geographic risk locations ({m.get('geo_risk_idx',0):.0f}% exposure) require <strong>virtual delivery</strong> options.</p>
            </div>
        </div>
    </div>""")

    # ── S6: Learning Investment Plan ──────────────────────────────────────────
    total_bw = sum(cfg.get("budget_weight", 1.0) for cfg in seg_config.values()) or 1
    investment_rows = ""
    for seg, cfg in seg_config.items():
        bw = cfg.get("budget_weight", 1.0)
        pct = round(bw / total_bw * 100)
        investment_rows += f"""
        <tr>
            <td style="font-weight:600">{seg}</td>
            <td>{bw:.1f}x</td>
            <td>
                <div style="background:#E8EDF5;border-radius:4px;height:10px;width:100%;overflow:hidden">
                    <div style="background:#1B3A6B;height:10px;width:{pct}%;border-radius:4px"></div>
                </div>
            </td>
            <td style="color:#1B3A6B;font-weight:700">~{pct}%</td>
        </tr>"""

    if not investment_rows:
        investment_rows = '<tr><td colspan="4" style="color:#9BA8B8;text-align:center">No specific segments selected — equal allocation across all employees</td></tr>'

    sections.append(f"""
    <div class="lni-section" style="border-left-color:#E67E22">
        <div class="lni-section-header">
            <div class="lni-section-num" style="background:#E67E22">6</div>
            <div>
                <div class="lni-section-title">Learning Investment Plan</div>
                <div class="lni-section-sub">Budget allocation logic based on segment weights and strategy priorities</div>
            </div>
        </div>
        <div class="compare-grid" style="margin-bottom:18px">
            <div class="compare-col lna">
                <div class="compare-label">📊 LNA Baseline Budget</div>
                <p>Total: <strong>Rs.{budget_l:.1f}L</strong></p>
                <p>Per employee: <strong>Rs.{m.get('avg_budget_pp',0):,.0f}</strong></p>
                <p>Training hours: <strong>{m.get('total_hrs',0):.0f}</strong> total · <strong>{m.get('avg_hrs',0)}</strong> avg/emp</p>
                <p>Critical skills hours: <strong>{m.get('crit_hrs_total',0):.0f}</strong></p>
            </div>
            <div class="compare-col lni">
                <div class="compare-label">🎯 Strategy-Adjusted Allocation</div>
                <p>Budget weighted by segment priority. Higher-weight segments receive proportionally more of the training budget in planning.</p>
                <p>Budget release mode: <strong>{budget_release}</strong></p>
                <p>Recommend allocating <strong>60–70%</strong> to Q1 critical skills in the first {horizon_cfg.get('days',90)} days.</p>
            </div>
        </div>
        <h4 style="font-size:13px;color:#1B3A6B;margin-bottom:10px">Segment Budget Weight Allocation</h4>
        <table class="index-table">
            <thead><tr><th>Segment</th><th>Weight</th><th>Relative Allocation</th><th>Est. Share</th></tr></thead>
            <tbody>{investment_rows}</tbody>
        </table>
    </div>""")

    # ── S7: 30-60-90 Day Execution Roadmap ────────────────────────────────────
    sections.append(f"""
    <div class="lni-section" style="border-left-color:#C0392B">
        <div class="lni-section-header">
            <div class="lni-section-num" style="background:#C0392B">7</div>
            <div>
                <div class="lni-section-title">30-60-90 Day Execution Roadmap</div>
                <div class="lni-section-sub">Priority actions configured for {horizon} horizon · {budget_release} budget release</div>
            </div>
        </div>
        {_roadmap_html(m, profile)}
    </div>""")

    # ── S8: Composite Indices vs Strategy ─────────────────────────────────────
    sections.append(f"""
    <div class="lni-section" style="border-left-color:#1B3A6B">
        <div class="lni-section-header">
            <div class="lni-section-num">8</div>
            <div>
                <div class="lni-section-title">Composite Indices & Success Metrics</div>
                <div class="lni-section-sub">LNA baseline indices — targets to improve via LNI/TNI interventions</div>
            </div>
        </div>
        <div style="margin-bottom:16px;font-size:13px;color:#2D3748;line-height:1.65">
            The following 15 composite indices were measured in the LNA. The LNI/TNI interventions
            are designed to move the critical indices toward their targets within the
            <strong>{horizon}</strong> timeframe.
        </div>
        {_index_table_html(m, profile)}
    </div>""")

    # ── S9: Risk & Conflict Register ──────────────────────────────────────────
    sections.append(f"""
    <div class="lni-section" style="border-left-color:#E67E22">
        <div class="lni-section-header">
            <div class="lni-section-num" style="background:#E67E22">9</div>
            <div>
                <div class="lni-section-title">Risk & Strategic Override Register</div>
                <div class="lni-section-sub">Execution risks, data quality flags, and leadership intent overrides</div>
            </div>
        </div>
        <h4 style="font-size:13px;color:#1B3A6B;margin-bottom:10px">Strategic Overrides</h4>
        {_conflicts_html(conflicts, justifs)}
        <h4 style="font-size:13px;color:#1B3A6B;margin:18px 0 10px">Execution Risk Flags</h4>
        <div class="conflict-box warning">
            <div class="conflict-title">⚠️ Self-Reported Proficiency Data</div>
            <div>Proficiency scores are self-assessed. Without manager calibration, individual scores may overstate actual capability levels. Manager input collection is recommended as a priority follow-up.</div>
        </div>
        <div class="conflict-box info">
            <div class="conflict-title">ℹ️ Certification Coverage at {cci:.1f}%</div>
            <div>Certification records cover {m.get('cert_emps',0)} of {n} employees. {m.get('expired_certs',0)} expired certifications require renewal as a quick win.</div>
        </div>
        {'<div class="conflict-box warning"><div class="conflict-title">⚠️ Geographic Delivery Risk</div><div>Geographic Risk Index at ' + str(m.get("geo_risk_idx",0)) + '% — locations with critical skill gaps above 30% threshold require virtual delivery planning.</div></div>' if m.get("geo_risk_idx",0) > 30 else ''}
    </div>""")

    # ── S10: Measurement & Next Steps ─────────────────────────────────────────
    sections.append(f"""
    <div class="lni-section" style="border-left-color:#217346">
        <div class="lni-section-header">
            <div class="lni-section-num" style="background:#217346">10</div>
            <div>
                <div class="lni-section-title">Measurement & Next Steps</div>
                <div class="lni-section-sub">How to measure LNI/TNI success and when to trigger Level 2 LNA</div>
            </div>
        </div>
        <div class="compare-grid">
            <div class="compare-col lna">
                <div class="compare-label">📊 Baseline Targets from LNA</div>
                <p>Role Skill Coverage: <strong>{rsc:.1f}%</strong> → target <strong>80%+</strong></p>
                <p>Critical Skills Index: <strong>{csi:.1f}%</strong> → target <strong>75%+</strong></p>
                <p>Learning Penetration: <strong>{lpi:.1f}%</strong> → target <strong>85%+</strong></p>
                <p>Cert Coverage: <strong>{cci:.1f}%</strong> → target <strong>50%+</strong></p>
            </div>
            <div class="compare-col lni">
                <div class="compare-label">🎯 Recommended Measurement Cadence</div>
                <p><strong>30 days:</strong> Q1 training enrolment rate and completion rate.</p>
                <p><strong>60 days:</strong> Mid-cycle proficiency re-assessment for Q1 skills.</p>
                <p><strong>90 days:</strong> Index re-measurement vs LNA baseline — generate delta report.</p>
                <p><strong>After 90 days:</strong> Trigger Level 2 LNA for individual IDP generation.</p>
            </div>
        </div>
        <div style="background:#F0FBF4;border:1px solid #C3E6CB;border-radius:8px;padding:16px 20px;margin-top:16px">
            <strong>Level 2 LNA Trigger Criteria:</strong> When Q1 skill training is &gt;70% complete, 
            Critical Skills Index improves by 5+ points, or {horizon_cfg.get('days',90)} days elapse — 
            whichever comes first. Level 2 will generate employee-level IDPs using this LNI/TNI as the baseline.
        </div>
    </div>""")

    # ── Assemble full document ─────────────────────────────────────────────────
    sections_html = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LNI/TNI Report — {company}</title>
{CSS}
</head>
<body>
<div class="report-wrap">

    <div class="report-header">
        <div class="rh-badge">LNI / TNI Report · Level 1</div>
        <div class="rh-title">Learning Needs Identification &<br>Training Needs Identification</div>
        <div class="rh-sub">{company} · {period}</div>
        <div class="rh-meta">
            <div class="rh-meta-item"><strong>{n}</strong>Employees</div>
            <div class="rh-meta-item"><strong>{roles}</strong>Roles</div>
            <div class="rh-meta-item"><strong>{locs}</strong>Locations</div>
            <div class="rh-meta-item"><strong>{q1_count}</strong>Q1 Priority Skills</div>
            <div class="rh-meta-item"><strong>{version}</strong>Strategy Version</div>
            <div class="rh-meta-item"><strong>{conf_date}</strong>Generated</div>
        </div>
    </div>

    <div class="strategy-banner">
        <div class="sb-label">🎯 Strategic Configuration Applied</div>
        <div class="sb-text">{strategy}</div>
        <div class="sb-version">Strategy {version} · Confirmed by {confirmed} · {conf_date} · {horizon}</div>
    </div>

    {sections_html}

    <div class="report-footer">
        <p>Edstellar LNA Intelligence Platform · LNI/TNI Level 1 Report · {version} · Generated {conf_date}</p>
        <p style="margin-top:4px">This report is confidential and intended for authorised HR and business leadership only.</p>
    </div>

</div>
</body>
</html>"""
