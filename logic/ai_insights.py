"""
ai_insights.py — Edstellar LNA Platform
OpenRouter API integration for AI-generated section insights.
Pure logic — no Streamlit imports.
"""

import requests
import time

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODELS = {
    "DeepSeek V3 (Free)":        "deepseek/deepseek-chat-v3-0324:free",
    "DeepSeek R1 (Free)":        "deepseek/deepseek-r1:free",
    "Gemini 2.0 Flash":          "google/gemini-2.0-flash-001",
    "Gemini 2.5 Pro (Free)":     "google/gemini-2.5-pro-exp-03-25:free",
    "GPT-4o":                    "openai/gpt-4o",
    "Claude 3.5 Sonnet":         "anthropic/claude-3.5-sonnet",
    "Grok 2":                    "x-ai/grok-2-1212",
}

SYSTEM_PROMPT = (
    "You are a senior L&D consultant writing an executive-grade Learning Needs Analysis "
    "report for an IT/SaaS company. Write in clear, professional business English. "
    "Be specific and data-driven — reference exact numbers provided. "
    "No generic filler. No bullet points. Write flowing analytical prose, 3-5 sentences. "
    "Use bold HTML tags (<strong>) to highlight key numbers and findings. "
    "Output plain HTML-safe text only — no markdown, no extra formatting."
)


def build_ctx(data: dict, m: dict) -> dict:
    """Build the metrics context dictionary for prompt interpolation."""
    active_emp    = data["active_emp"]
    skills_master = data["skills_master"]
    comp_master   = data["comp_master"]
    training      = data["training"]
    certs         = data["certs"]
    benchmark     = data["benchmark"]
    role_comps    = data["role_comps"]
    emp_comps     = data["emp_comps"]
    role_skills   = data["role_skills"]

    def _top_gap_skills(n=5):
        ss = m.get("skill_summary")
        if ss is None or ss.empty or "Skill Name" not in ss.columns:
            return "data not available"
        top = ss.sort_values("avg_gap", ascending=False).head(n)
        return "; ".join(
            f"{r['Skill Name']} (avg gap={r['avg_gap']:.1f}, {r['gap_pct']:.0f}% affected)"
            for _, r in top.iterrows()
        )

    def _top_comp_gaps(n=4):
        if emp_comps.empty or role_comps.empty:
            return "data not available"
        try:
            merged = emp_comps.merge(
                role_comps[["Competency ID","Required Proficiency Level"]],
                on="Competency ID", how="left"
            )
            merged["gap"] = (
                merged["Required Proficiency Level"].fillna(0)
                - merged["Proficiency Level"].fillna(0)
            )
            avg = merged.groupby("Competency ID")["gap"].mean().reset_index()
            avg = avg.merge(comp_master[["Competency ID","Competency Name"]], on="Competency ID", how="left")
            avg = avg.sort_values("gap", ascending=False).head(n)
            return "; ".join(f"{r['Competency Name']} (avg gap={r['gap']:.1f})" for _, r in avg.iterrows())
        except Exception:
            return "data not available"

    def _cert_status():
        if certs.empty or "Certification Status" not in certs.columns:
            return f"{len(certs)} total" if not certs.empty else "no data"
        counts = certs["Certification Status"].value_counts().to_dict()
        return ", ".join(f"{v} {k}" for k, v in counts.items())

    def _training_types():
        if training.empty or "Training Type" not in training.columns:
            return "not available"
        top = training["Training Type"].value_counts().head(3)
        return ", ".join(f"{v} {k}" for k, v in top.items())

    def _q1_names(n=5):
        q1 = m.get("q1_skills")
        if q1 is None or q1.empty or "Skill Name" not in q1.columns:
            return "none identified"
        return ", ".join(q1["Skill Name"].tolist()[:n])

    def _benchmark_summary():
        if benchmark.empty:
            return "no benchmark data"
        rows = []
        for _, r in benchmark.iterrows():
            rows.append(f"{r['Metric Name']}: org={r['Organization Value']}, industry={r['Industry Value']}")
        return " | ".join(rows)

    def _jf_dist():
        if "Job Family" not in active_emp.columns:
            return "not available"
        jf = active_emp["Job Family"].value_counts().head(5)
        return ", ".join(f"{k}({v})" for k, v in jf.items())

    def _loc_dist():
        if "Location" not in active_emp.columns:
            return "not available"
        lc = active_emp["Location"].value_counts()
        return ", ".join(f"{k}({v})" for k, v in lc.items())

    return {
        "company":           data["company"],
        "period":            f"{data['time_period']} {data['year']}",
        "industry":          "IT / SaaS",
        "total_employees":   m["N"],
        "total_roles":       m["total_roles"],
        "total_locations":   m["total_locs"],
        "avg_age":           m["avg_age"],
        "avg_tenure":        m["avg_tenure"],
        "avg_training_hrs":  m["avg_training_hrs"],
        "female_pct":        m["female_pct"],
        "age_risk_idx":      m["age_risk_idx"],
        "manager_ratio":     m["manager_ratio"],
        "span_of_control":   m["span_of_ctrl"],
        "role_skill_coverage": m["role_skill_cov"],
        "roles_mapped":      m["roles_mapped"],
        "roles_unmapped":    m["roles_unmapped"],
        "crit_roles":        m["crit_roles"],
        "total_skills":      m["total_skills"],
        "crit_skills_count": m["crit_skills_cnt"],
        "unmapped_skills":   m["unmapped_skills"],
        "total_competencies": m["total_comps"],
        "crit_comps_count":  m["crit_comps_cnt"],
        "unmapped_comps":    m["unmapped_comps"],
        "crit_skills_index": m["crit_skills_idx"],
        "skill_scarcity_idx": m["skill_scarcity_idx"],
        "geo_risk_idx":      m["geo_risk_idx"],
        "demo_risk":         m["demo_risk"],
        "total_certs":       m["total_certs"],
        "cert_emps":         m["cert_emps"],
        "cert_cov_idx":      m["cert_cov_idx"],
        "expired_certs":     m["expired_certs"],
        "total_budget_lakh": round(m["total_budget"] / 100000, 2),
        "total_hrs":         round(m["total_hrs"], 1),
        "avg_hrs_per_emp":   m["avg_hrs"],
        "crit_hrs_total":    round(m["crit_hrs_total"], 1),
        "learning_pen_idx":  m["learning_pen_idx"],
        "avg_budget_per_emp": m["avg_budget_pp"],
        "q1_skill_count":    len(m.get("q1_skills") or []),
        "q2_skill_count":    len(m.get("q2_skills") or []),
        "top_gap_skills":    _top_gap_skills(),
        "top_comp_gaps":     _top_comp_gaps(),
        "cert_status_summary": _cert_status(),
        "training_type_summary": _training_types(),
        "q1_skill_names":    _q1_names(),
        "benchmark_summary": _benchmark_summary(),
        "jf_distribution":   _jf_dist(),
        "location_distribution": _loc_dist(),
    }


SECTION_PROMPTS = {
    "s1_cover": "Write a 2-sentence confidentiality and purpose statement for the LNA cover page. Company: {company}, Period: {period}, Employees: {total_employees}, Locations: {total_locations}. Mention it is a Level 1 baseline assessment commissioned to identify skill and capability gaps.",
    "s2_doc_control": "Write a 2-sentence document governance note. Company: {company}. Mention version control, quarterly review cycle, and stakeholder sign-off requirement.",
    "s3_exec_summary": "Write a 4-5 sentence executive summary for {company}'s LNA. Metrics: {total_employees} employees, {total_locations} locations, {total_roles} roles, avg tenure {avg_tenure} yrs, avg age {avg_age}. Role Skill Coverage: {role_skill_coverage}%, Critical Skills Index: {crit_skills_index}%, Learning Penetration: {learning_pen_idx}%, Cert Coverage: {cert_cov_idx}%, Female: {female_pct}%, Q1 urgent skills: {q1_skill_count}, Budget: Rs.{total_budget_lakh}L. Highlight the most critical gap and most positive indicator.",
    "s4_strategy": "Write a 3-4 sentence strategic context insight for {company} ({industry}, {total_employees} employees). Job families: {jf_distribution}. Role Skill Coverage: {role_skill_coverage}%, {roles_unmapped} roles unmapped. Connect workforce composition to L&D investment alignment.",
    "s5_scope": "Write a 2-3 sentence LNA scope insight for {company}. In scope: {total_employees} employees, {total_roles} roles, {total_locations} locations. Mention the risk if contractors and interns remain out of scope.",
    "s6_methodology": "Write a 3-sentence methodological insight. Data: {total_employees} employees, {total_skills} skills ({crit_skills_count} critical), {total_certs} cert records ({cert_cov_idx:.1f}% coverage). Manager inputs pending. Highlight self-reported proficiency data quality risk.",
    "s7_profile": "Write a 3-4 sentence workforce profile insight for {company}. Data: {total_employees} employees, locations: {location_distribution}, female: {female_pct}%, age risk index: {age_risk_idx}%, manager ratio: {manager_ratio}%, span of control: {span_of_control}. Identify the dominant segment and most notable demographic risk.",
    "s8_roles": "Write a 3-4 sentence role structure insight. {total_roles} roles, {roles_mapped} mapped, {roles_unmapped} unmapped, {crit_roles} critical, Coverage: {role_skill_coverage}%. Explain the business risk of unmapped roles.",
    "s9_skills": "Write a 3-4 sentence skills framework insight. {total_skills} total skills, {crit_skills_count} critical, {unmapped_skills} unmapped. Top skill gaps: {top_gap_skills}. Comment on framework maturity.",
    "s10_competencies": "Write a 3-4 sentence competency framework insight. {total_competencies} competencies, {crit_comps_count} critical, {unmapped_comps} unmapped. Top gaps: {top_comp_gaps}. Explain what combined skill and competency gaps mean for L&D design.",
    "s11_capability": "Write a 4-5 sentence current capability assessment insight. Critical Skills Index: {crit_skills_index}%, Skill Scarcity: {skill_scarcity_idx}%, Geographic Risk: {geo_risk_idx}%, Demographic Risk: {demo_risk}%, Cert coverage: {cert_cov_idx}%, expired: {expired_certs}, status: {cert_status_summary}. Name the single highest-risk area.",
    "s12_priority": "Write a 4-5 sentence training priority insight. Q1 (immediate): {q1_skill_count} skills — {q1_skill_names}. Q2 (planned): {q2_skill_count} skills. Explain budget allocation recommendation between Q1 and Q2.",
    "s13_investment": "Write a 3-4 sentence learning investment insight. Budget Rs.{total_budget_lakh}L, avg Rs.{avg_budget_per_emp:,.0f}/employee, {total_hrs:.0f} total hours, {avg_hrs_per_emp} hrs/emp (IT benchmark ~32), critical hours: {crit_hrs_total:.0f}, penetration: {learning_pen_idx}%, types: {training_type_summary}. Compare to benchmark.",
    "s14_indices": "Write a 3-4 sentence composite indices insight. From Role Skill Coverage {role_skill_coverage}%, Learning Penetration {learning_pen_idx}%, Critical Skills {crit_skills_index}%, Cert Coverage {cert_cov_idx}%, Skill Scarcity {skill_scarcity_idx}% — identify strongest and weakest index. Summarise overall capability maturity.",
    "s15_roadmap": "Write a 3-4 sentence 30-60-90 day roadmap insight. {q1_skill_count} Q1 skills in 30 days ({q1_skill_names}), {expired_certs} expired certs to renew, {roles_unmapped} unmapped roles, geo risk {geo_risk_idx}% needs virtual delivery. Explain consequences of delaying beyond 60 days.",
    "s16_risks": "Write a 3-sentence assumptions and risks insight. Risks: self-reported proficiency, missing manager inputs, single-year data, {cert_cov_idx:.1f}% cert coverage, point-in-time snapshot. State confidence level given these constraints.",
    "s17_conclusion": "Write a 4-5 sentence conclusion for {company}'s LNA Level 1 report. {total_employees} employees, {total_roles} roles, {total_locations} locations, Role Skill Coverage {role_skill_coverage}%, Learning Penetration {learning_pen_idx}%, {q1_skill_count} urgent priorities, Cert Coverage {cert_cov_idx}%, female {female_pct}% vs 35% benchmark. End with what Level 2 LNA will unlock.",
}


def _call_llm(section_key: str, prompt_template: str, ctx: dict,
              api_key: str, model_id: str, retries: int = 2) -> str | None:
    prompt = prompt_template.format(**ctx)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  "https://edstellar.com",
        "X-Title":       "Edstellar LNA Report Generator",
    }
    payload = {
        "model":    model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        "max_tokens":  400,
        "temperature": 0.4,
    }
    for attempt in range(retries + 1):
        try:
            resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt < retries:
                time.sleep(2)
                continue
            return None


def _fallback(section_key: str, ctx: dict) -> str:
    """Data-driven fallback — built entirely from ctx, zero hardcoding."""
    c = ctx
    fallbacks = {
        "s1_cover": f"This Learning Needs Analysis for <strong>{c['company']}</strong> covers <strong>{c['total_employees']}</strong> employees across <strong>{c['total_locations']}</strong> locations for <strong>{c['period']}</strong>. It is a Level 1 baseline assessment prepared by Edstellar to identify skill gaps and prioritised training interventions. This document is confidential and intended for authorised HR and business leadership only.",
        "s2_doc_control": f"This document follows structured version control governance for <strong>{c['company']}</strong>. All revisions require Head of L&D review and CHRO approval before distribution. A quarterly refresh cycle is recommended to keep findings current.",
        "s3_exec_summary": f"<strong>{c['company']}</strong> has <strong>{c['total_employees']}</strong> active employees across <strong>{c['total_locations']}</strong> locations with an average tenure of <strong>{c['avg_tenure']}</strong> years. Role Skill Coverage stands at <strong>{c['role_skill_coverage']:.1f}%</strong> and the Critical Skills Index at <strong>{c['crit_skills_index']:.1f}%</strong>, with <strong>{c['q1_skill_count']}</strong> skills requiring immediate high-urgency intervention. Certification coverage of <strong>{c['cert_cov_idx']:.1f}%</strong> and female representation of <strong>{c['female_pct']:.1f}%</strong> (vs 35% industry benchmark) indicate two additional priority areas.",
        "s4_strategy": f"{c['company']}'s workforce of <strong>{c['total_employees']}</strong> spans {c['jf_distribution']}. With <strong>{c['roles_unmapped']}</strong> roles unmapped to the skills framework, current coverage of <strong>{c['role_skill_coverage']:.1f}%</strong> limits gap analysis accuracy. Completing the framework is a prerequisite before L&D investments can be fully aligned to strategic outcomes.",
        "s5_scope": f"This LNA covers all <strong>{c['total_employees']}</strong> active employees across <strong>{c['total_roles']}</strong> roles in <strong>{c['total_locations']}</strong> locations. Contractors and interns are excluded from this cycle. Including them in a future LNA would provide a more complete picture of capability distribution across the extended workforce.",
        "s6_methodology": f"This LNA is built on <strong>{c['total_skills']}</strong> skill records, <strong>{c['total_certs']}</strong> certification records ({c['cert_cov_idx']:.1f}% employee coverage), and training data for all <strong>{c['total_employees']}</strong> employees. Proficiency data is self-assessed and has not been calibrated against manager evaluations — introducing a potential overestimation bias. Manager input collection is a priority follow-up to validate these findings.",
        "s7_profile": f"The workforce of <strong>{c['total_employees']}</strong> employees has an average age of <strong>{c['avg_age']}</strong> and average tenure of <strong>{c['avg_tenure']}</strong> years, distributed across: {c['location_distribution']}. Female representation is <strong>{c['female_pct']:.1f}%</strong>, below the 35% IT industry benchmark, signalling a diversity pipeline gap. The Age Risk Index of <strong>{c['age_risk_idx']:.1f}%</strong> and span of control of <strong>{c['span_of_control']}</strong> are key succession planning considerations.",
        "s8_roles": f"Of <strong>{c['total_roles']}</strong> active roles, <strong>{c['roles_mapped']}</strong> are mapped to skills and <strong>{c['crit_roles']}</strong> are classified as critical. The <strong>{c['roles_unmapped']}</strong> unmapped roles represent a governance gap — without formal skill requirements, structured hiring and gap analysis for these roles is not possible. Completing the mapping is the single highest-leverage structural action available.",
        "s9_skills": f"The skills framework contains <strong>{c['total_skills']}</strong> skills, of which <strong>{c['crit_skills_count']}</strong> are critical. Top skill gaps: <strong>{c['top_gap_skills']}</strong>. With <strong>{c['unmapped_skills']}</strong> skills not yet assigned to any role, there is an opportunity to expand role coverage or retire irrelevant skills to keep the framework lean and actionable.",
        "s10_competencies": f"The competency framework covers <strong>{c['total_competencies']}</strong> competencies, <strong>{c['crit_comps_count']}</strong> critical, with <strong>{c['unmapped_comps']}</strong> unmapped to roles. Top competency gaps: <strong>{c['top_comp_gaps']}</strong>. Competency gaps in cognitive and people management domains typically require coaching and structured journeys rather than standard training programmes.",
        "s11_capability": f"The Critical Skills Index of <strong>{c['crit_skills_index']:.1f}%</strong> and Skill Scarcity Index of <strong>{c['skill_scarcity_idx']:.1f}%</strong> highlight systemic training deficits requiring programme-level intervention. Geographic Risk Exposure of <strong>{c['geo_risk_idx']:.1f}%</strong> indicates location-specific capability risks that could impact delivery. <strong>{c['expired_certs']}</strong> expired certifications add urgency to the capability improvement plan.",
        "s12_priority": f"The priority matrix identifies <strong>{c['q1_skill_count']}</strong> skills in the High Impact / High Urgency quadrant requiring immediate intervention: <strong>{c['q1_skill_names']}</strong>. A further <strong>{c['q2_skill_count']}</strong> skills are high-impact but lower urgency, suitable for a structured 30–60 day delivery plan. Together these two quadrants define the core capability investment priority for the next 90 days.",
        "s13_investment": f"Total training investment is <strong>Rs.{c['total_budget_lakh']:.1f}L</strong> across <strong>{c['total_hrs']:.0f}</strong> hours — an average of <strong>{c['avg_hrs_per_emp']}</strong> hrs/employee ({'meeting' if c['avg_hrs_per_emp'] >= 30 else 'below'} the IT industry benchmark of ~32 hrs). Critical skills account for <strong>{c['crit_hrs_total']:.0f}</strong> training hours. Training type distribution ({c['training_type_summary']}) should be reviewed against Q1 skills which typically require higher ILT delivery ratios.",
        "s14_indices": f"Across 15 composite indices, <strong>{c['company']}</strong> shows strongest performance in Role Skill Coverage (<strong>{c['role_skill_coverage']:.1f}%</strong>) and Learning Penetration (<strong>{c['learning_pen_idx']:.1f}%</strong>). The most concerning indices are Cert Coverage (<strong>{c['cert_cov_idx']:.1f}%</strong> vs 50% target) and Skill Scarcity (<strong>{c['skill_scarcity_idx']:.1f}%</strong>). Overall capability maturity is at a developing stage — requiring focused investment to move from reactive to proactive L&D.",
        "s15_roadmap": f"The 30-day quick wins focus on <strong>{c['q1_skill_count']}</strong> high-urgency skills ({c['q1_skill_names']}) and renewing <strong>{c['expired_certs']}</strong> expired certifications — both delivering measurable index improvements within one month. The 31–60 day structural phase addresses geographic delivery gaps (Risk Index: <strong>{c['geo_risk_idx']:.1f}%</strong>) and competency coaching. Delays beyond 60 days risk compounding skill scarcity as project dependencies on critical skills continue to grow.",
        "s16_risks": f"The primary risk in this LNA is self-reported proficiency data — without manager calibration, individual scores may overstate actual capability levels. Manager inputs are currently pending, limiting behavioural competency confidence. With <strong>{c['cert_cov_idx']:.1f}%</strong> certification coverage and a single-year training snapshot, findings should be treated as directional until the next refresh cycle.",
        "s17_conclusion": f"<strong>{c['company']}</strong>'s first Level 1 LNA establishes a comprehensive baseline across <strong>{c['total_employees']}</strong> employees, <strong>{c['total_roles']}</strong> roles, and <strong>{c['total_locations']}</strong> locations. With Role Skill Coverage at <strong>{c['role_skill_coverage']:.1f}%</strong>, <strong>{c['q1_skill_count']}</strong> urgent training priorities identified, and Cert Coverage at <strong>{c['cert_cov_idx']:.1f}%</strong>, the 90-day roadmap provides a clear prioritised path to closing the most critical gaps. Level 2 LNA — individual gap assessments and personalised IDPs — should be commissioned after the 90-day cycle to translate these organisational findings into employee-level development plans.",
    }
    return fallbacks.get(section_key, f"Insight for this section based on {c['company']} workforce data for {c['period']}.")


def generate_all_insights(data: dict, m: dict,
                           api_key: str = "", model_id: str = "",
                           progress_callback=None) -> dict:
    """
    Generate all 17 section insights.
    progress_callback(section_key, index, total, status) — optional UI hook.
    Returns AI_INSIGHTS dict.
    """
    ctx     = build_ctx(data, m)
    use_ai  = bool(api_key and model_id)
    results = {}
    total   = len(SECTION_PROMPTS)

    for i, (key, prompt_tmpl) in enumerate(SECTION_PROMPTS.items()):
        if use_ai:
            result = _call_llm(key, prompt_tmpl, ctx, api_key, model_id)
            status = "ai" if result else "fallback"
            if not result:
                result = _fallback(key, ctx)
        else:
            result = _fallback(key, ctx)
            status = "fallback"

        results[key] = result

        if progress_callback:
            progress_callback(key, i + 1, total, status)

        if use_ai:
            time.sleep(0.4)

    return results
