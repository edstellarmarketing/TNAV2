"""
metrics.py — Edstellar LNA Platform
All KPI and composite index computation.
Pure logic — no Streamlit imports.
"""

import pandas as pd
import numpy as np


def safe_div(a, b, pct=False, decimals=1):
    if b == 0:
        return 0
    val = a / b
    return round(val * 100, decimals) if pct else round(val, decimals)


def compute_all_metrics(data: dict) -> dict:
    """
    Takes the data dict from data_loader.load_all_data()
    Returns a flat metrics dict with all computed KPIs, indices, and dataframes.
    """
    active_emp   = data["active_emp"]
    emp          = data["emp"]
    skills_master= data["skills_master"]
    role_skills  = data["role_skills"]
    emp_skills   = data["emp_skills"]
    comp_master  = data["comp_master"]
    role_comps   = data["role_comps"]
    emp_comps    = data["emp_comps"]
    training     = data["training"]
    certs        = data["certs"]
    benchmark    = data["benchmark"]

    N = len(active_emp)
    m = {}  # metrics output dict

    # ── BENCHMARK LOOKUP ─────────────────────────────────────────────────────
    def bench_val(keyword):
        if benchmark.empty:
            return None
        match = benchmark[
            benchmark["Metric Name"].str.lower().str.contains(keyword.lower(), na=False)
        ]
        if not match.empty:
            return {
                "org": match.iloc[0]["Organization Value"],
                "ind": match.iloc[0]["Industry Value"],
            }
        return None

    # ── 1. PARTICIPANT PROFILE ────────────────────────────────────────────────
    m["N"]           = N
    m["total_emp"]   = N
    m["total_roles"] = active_emp["Job Role"].nunique() if "Job Role" in active_emp.columns else 0
    m["total_locs"]  = active_emp["Location"].nunique() if "Location" in active_emp.columns else 0
    m["avg_tenure"]  = round(active_emp["Tenure (Years)"].mean(), 1) if "Tenure (Years)" in active_emp.columns else 0
    m["avg_age"]     = round(active_emp["Age"].mean(), 1) if "Age" in active_emp.columns else 0

    mgr_ids      = active_emp["Manager ID"].dropna().unique() if "Manager ID" in active_emp.columns else []
    n_managers   = len([mid for mid in mgr_ids if mid in active_emp["Employee ID"].values]) if "Employee ID" in active_emp.columns else 0
    m["n_managers"]    = n_managers
    m["manager_ratio"] = safe_div(n_managers, N, pct=True)
    m["span_of_ctrl"]  = round(N / max(n_managers, 1), 1)

    m["avg_training_hrs"] = (
        round(training["Training Hours"].mean(), 1)
        if not training.empty and "Training Hours" in training.columns else 0
    )
    m["age_risk_idx"] = (
        safe_div(len(active_emp[active_emp["Age"] >= 50]), N, pct=True)
        if "Age" in active_emp.columns else 0
    )

    # Level Distribution Index
    if "Level" in active_emp.columns:
        level_counts = active_emp["Level"].value_counts()
        n_levels = len(level_counts)
        ldi = round(100 - (level_counts.std() / max(level_counts.mean(), 1)) * 100 / n_levels, 1)
        m["ldi"] = max(0, min(100, ldi))
    else:
        m["ldi"] = 0

    m["female_pct"] = safe_div(
        len(active_emp[active_emp["Gender"] == "Female"]) if "Gender" in active_emp.columns else 0,
        N, pct=True
    )
    m["gender_div_risk"] = round(abs(50 - m["female_pct"]), 1)

    # ── 2. ROLE-BASED KPIs ───────────────────────────────────────────────────
    all_roles = active_emp["Job Role"].unique() if "Job Role" in active_emp.columns else []
    m["all_roles"]     = all_roles
    m["roles_mapped"]  = role_skills["Job Role"].nunique() if not role_skills.empty and "Job Role" in role_skills.columns else 0
    m["roles_unmapped"]= len(all_roles) - m["roles_mapped"]
    m["role_density"]  = round(N / max(len(all_roles), 1), 1)

    crit_skill_ids = (
        skills_master[skills_master["Is Critical Skill (Y/N)"] == "Y"]["Skill ID"].tolist()
        if not skills_master.empty else []
    )
    m["crit_skill_ids"] = crit_skill_ids
    m["crit_roles"]     = (
        role_skills[role_skills["Skill ID"].isin(crit_skill_ids)]["Job Role"].nunique()
        if not role_skills.empty else 0
    )
    m["role_skill_cov"] = safe_div(m["roles_mapped"], max(len(all_roles), 1), pct=True)

    if "Job Role" in active_emp.columns:
        role_hc = active_emp["Job Role"].value_counts()
        threshold = role_hc.mean() + role_hc.std()
        m["role_sat_idx"] = safe_div((role_hc > threshold).sum(), len(all_roles), pct=True)
    else:
        m["role_sat_idx"] = 0

    # ── 3. SKILLS KPIs ───────────────────────────────────────────────────────
    m["total_skills"]    = len(skills_master) if not skills_master.empty else 0
    m["crit_skills_cnt"] = len(crit_skill_ids)
    m["skills_in_roles"] = role_skills["Skill ID"].nunique() if not role_skills.empty else 0
    m["unmapped_skills"] = m["total_skills"] - m["skills_in_roles"]

    # ── 4. COMPETENCY KPIs ───────────────────────────────────────────────────
    m["total_comps"]  = len(comp_master) if not comp_master.empty else 0
    crit_comp_ids = (
        comp_master[comp_master["Is Critical Capability"] == "Y"]["Competency ID"].tolist()
        if not comp_master.empty else []
    )
    m["crit_comp_ids"]  = crit_comp_ids
    m["crit_comps_cnt"] = len(crit_comp_ids)
    m["comps_mapped"]   = role_comps["Competency ID"].nunique() if not role_comps.empty else 0
    m["unmapped_comps"] = m["total_comps"] - m["comps_mapped"]

    # ── 5. GAP ANALYSIS ──────────────────────────────────────────────────────
    if not emp_skills.empty and not role_skills.empty and "Job Role" in active_emp.columns:
        cols = [c for c in ["Employee ID", "Job Role", "Location", "Business Unit", "Age"] if c in active_emp.columns]
        emp_role = active_emp[cols].copy()
        rs_cols  = [c for c in ["Job Role","Skill ID","Required Proficiency Level","Is Critical Skill"] if c in role_skills.columns]
        emp_role_skills = emp_role.merge(role_skills[rs_cols], on="Job Role")
        gap_df = emp_role_skills.merge(
            emp_skills[["Employee ID","Skill ID","Proficiency Level"]].rename(
                columns={"Proficiency Level": "Actual Proficiency"}
            ),
            on=["Employee ID","Skill ID"], how="left"
        )
        gap_df["Actual Proficiency"] = gap_df["Actual Proficiency"].fillna(0)
        gap_df["Gap"] = gap_df["Required Proficiency Level"] - gap_df["Actual Proficiency"]
        gap_df["Has Gap"] = gap_df["Gap"] > 0
        gap_df["Gap Severity"] = gap_df["Gap"].apply(
            lambda g: "High" if g >= 2 else ("Medium" if g == 1 else ("No Gap" if g == 0 else "Over-skilled"))
        )
        m["gap_df"] = gap_df
    else:
        m["gap_df"] = pd.DataFrame()

    gap_df = m["gap_df"]

    # Critical Skills Index, Scarcity, Geographic Risk, Demographic Risk
    if not gap_df.empty:
        crit_gap = gap_df[gap_df["Is Critical Skill"] == "Y"]
        emps_meet = crit_gap[crit_gap["Gap"] <= 0]["Employee ID"].nunique()
        m["crit_skills_idx"] = safe_div(emps_meet, N, pct=True)

        skill_gap_pct = gap_df.groupby("Skill ID")["Has Gap"].mean() * 100
        scarce = (skill_gap_pct > 40).sum()
        m["skill_scarcity_idx"] = safe_div(scarce, max(m["total_skills"], 1), pct=True)

        if "Location" in gap_df.columns:
            geo_crit = gap_df[gap_df["Is Critical Skill"] == "Y"]
            loc_gap_pct = geo_crit.groupby("Location")["Has Gap"].mean() * 100
            m["geo_risk_idx"] = safe_div((loc_gap_pct > 30).sum(), max(m["total_locs"], 1), pct=True)
        else:
            m["geo_risk_idx"] = 0

        if "Age" in gap_df.columns:
            old_emps = gap_df[gap_df["Age"] >= 50]
            m["demo_risk"] = safe_div(
                old_emps[old_emps["Has Gap"] & (old_emps["Is Critical Skill"] == "Y")]["Employee ID"].nunique(),
                max(old_emps["Employee ID"].nunique(), 1), pct=True
            )
        else:
            m["demo_risk"] = 0
    else:
        m["crit_skills_idx"] = m["skill_scarcity_idx"] = m["geo_risk_idx"] = m["demo_risk"] = 0

    # ── 6. CERTIFICATION KPIs ────────────────────────────────────────────────
    if not certs.empty:
        m["total_certs"]  = len(certs)
        m["unique_certs"] = certs["Certification Name"].nunique() if "Certification Name" in certs.columns else 0
        m["cert_emps"]    = certs["Employee ID"].nunique() if "Employee ID" in certs.columns else 0
        m["cert_cov_idx"] = safe_div(m["cert_emps"], N, pct=True)
        if "Certification Status" in certs.columns:
            active_c = certs[certs["Certification Status"].str.lower().str.contains("active", na=False)]
            m["expired_certs"] = len(certs) - len(active_c)
        else:
            m["expired_certs"] = 0
    else:
        m["total_certs"] = m["unique_certs"] = m["cert_emps"] = m["expired_certs"] = 0
        m["cert_cov_idx"] = 0

    # ── 7. TRAINING / LEARNING KPIs ──────────────────────────────────────────
    if not training.empty:
        budget_col = next((c for c in training.columns if "budget" in c.lower()), None)
        m["total_budget"] = training[budget_col].sum() if budget_col else 0
        m["total_hrs"]    = training["Training Hours"].sum() if "Training Hours" in training.columns else 0
        m["avg_hrs"]      = round(m["total_hrs"] / max(N, 1), 1)
        crit_hrs_col = next((c for c in training.columns if "critical" in c.lower()), None)
        m["crit_hrs_total"] = training[crit_hrs_col].sum() if crit_hrs_col else 0
        if "Training Hours" in training.columns and "Employee ID" in training.columns:
            trained_emps = training[training["Training Hours"] > 0]["Employee ID"].nunique()
        else:
            trained_emps = 0
        m["learning_pen_idx"]   = safe_div(trained_emps, N, pct=True)
        m["training_intensity"] = round(m["total_hrs"] / max(N, 1), 1)
        m["avg_budget_pp"]      = round(m["total_budget"] / max(N, 1), 0)
    else:
        m["total_budget"] = m["total_hrs"] = m["avg_hrs"] = m["crit_hrs_total"] = 0
        m["learning_pen_idx"] = m["training_intensity"] = m["avg_budget_pp"] = 0

    # ── 8. COMPOSITE INDICES ─────────────────────────────────────────────────
    m["composite"] = {
        "Role Skill Coverage Index":      (m["role_skill_cov"],      80,  "higher"),
        "Role Density Index":             (m["role_density"],          5,  "context"),
        "Level Distribution Index":       (m["ldi"],                  70,  "higher"),
        "Span of Control Index":          (m["span_of_ctrl"],          8,  "context"),
        "Manager Ratio Index":            (m["manager_ratio"],        20,  "context"),
        "Age Risk Index":                 (m["age_risk_idx"],         15,  "lower"),
        "Gender Diversity Risk Index":    (m["gender_div_risk"],      15,  "lower"),
        "Role Saturation Index":          (m["role_sat_idx"],         20,  "lower"),
        "Geographic Risk Exposure Index": (m["geo_risk_idx"],         25,  "lower"),
        "Demographic Skill Gap":          (m["demo_risk"],            20,  "lower"),
        "Learning Penetration Index":     (m["learning_pen_idx"],     85,  "higher"),
        "Training Intensity Index":       (m["training_intensity"],   30,  "higher"),
        "Certification Coverage Index":   (m["cert_cov_idx"],         50,  "higher"),
        "Skill Scarcity Index":           (m["skill_scarcity_idx"],   20,  "lower"),
        "Critical Skills Index":          (m["crit_skills_idx"],      75,  "higher"),
    }

    # ── 9. QUADRANT ANALYSIS ─────────────────────────────────────────────────
    if not gap_df.empty:
        skill_summary = gap_df.groupby(["Skill ID", "Is Critical Skill"]).agg(
            avg_gap      =("Gap", "mean"),
            emp_with_gap =("Has Gap", "sum"),
            total_emp    =("Employee ID", "nunique"),
        ).reset_index()
        skill_summary["gap_pct"] = skill_summary["emp_with_gap"] / skill_summary["total_emp"] * 100
        if not skills_master.empty:
            skill_summary = skill_summary.merge(
                skills_master[["Skill ID", "Skill Name", "Skill Category"]], on="Skill ID", how="left"
            )

        def quadrant(row):
            hi = row["Is Critical Skill"] == "Y"
            hu = row["avg_gap"] >= 1.5 or row["gap_pct"] >= 40
            if hi and hu:   return "Q1 — High Impact / High Urgency"
            if hi and not hu: return "Q2 — High Impact / Low Urgency"
            if not hi and hu: return "Q3 — Low Impact / High Urgency"
            return "Q4 — Low Impact / Low Urgency"

        skill_summary["Quadrant"] = skill_summary.apply(quadrant, axis=1)
        m["skill_summary"] = skill_summary
        m["q1_skills"] = skill_summary[skill_summary["Quadrant"].str.startswith("Q1")].sort_values("avg_gap", ascending=False)
        m["q2_skills"] = skill_summary[skill_summary["Quadrant"].str.startswith("Q2")]
        m["q3_skills"] = skill_summary[skill_summary["Quadrant"].str.startswith("Q3")]
        m["q4_skills"] = skill_summary[skill_summary["Quadrant"].str.startswith("Q4")]
    else:
        m["skill_summary"] = m["q1_skills"] = m["q2_skills"] = m["q3_skills"] = m["q4_skills"] = pd.DataFrame()

    return m
