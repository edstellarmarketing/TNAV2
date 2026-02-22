"""
logic/strategy.py — Edstellar LNA Platform
Strategy Configuration logic — pure Python, no Streamlit.
Builds STRATEGY_PROFILE from UI selections and applies weights to LNA data.
"""

from datetime import datetime
import uuid

# ── Configuration Options ─────────────────────────────────────────────────────

CULTURAL_OPTIONS = [
    "Execution Excellence",
    "Leadership Depth",
    "Innovation & Experimentation",
    "Customer Centricity",
    "Collaboration & Cross-Functional Working",
    "Accountability & Ownership",
    "Agility & Change Readiness",
    "Risk & Compliance Discipline",
]

SKILL_DIMENSIONS = [
    "Technical / Functional Skills",
    "Leadership & People Skills",
    "Behavioral & Cultural Skills",
    "Digital / Future Skills",
    "Compliance & Risk Skills",
]

EMPLOYEE_SEGMENTS = [
    "Entry / Graduate Talent",
    "Individual Contributors",
    "First-Time Managers",
    "Mid-Level Managers",
    "Senior Leaders",
    "High Potentials",
    "Critical Role Holders",
]

TIME_HORIZONS = [
    "Immediate (0–3 months)",
    "Short-term (3–6 months)",
    "Medium-term (6–12 months)",
    "Long-term (12–24 months)",
]

# Training format bias per segment — flows into LNI/TNI recommendations
SEGMENT_FORMAT_BIAS = {
    "Entry / Graduate Talent":     {"format": "Structured cohort programmes", "delivery": "ILT + eLearning", "budget_weight": 1.0},
    "Individual Contributors":     {"format": "Skill-based modules",           "delivery": "Blended",          "budget_weight": 1.0},
    "First-Time Managers":         {"format": "Blended + coaching",            "delivery": "Blended + 1:1",    "budget_weight": 1.3},
    "Mid-Level Managers":          {"format": "Leadership programmes",         "delivery": "ILT + peer groups", "budget_weight": 1.4},
    "Senior Leaders":              {"format": "Peer learning + external",      "delivery": "External + exec",  "budget_weight": 1.8},
    "High Potentials":             {"format": "Experiential + stretch",        "delivery": "Project-based",    "budget_weight": 1.6},
    "Critical Role Holders":       {"format": "ILT + certification paths",     "delivery": "ILT + exam prep",  "budget_weight": 1.5},
}

# Roadmap horizon logic
HORIZON_CONFIG = {
    "Immediate (0–3 months)":    {"days": 90,  "quadrants": ["Q1"],         "budget_release": "100% now",     "format_bias": "ILT / Bootcamp"},
    "Short-term (3–6 months)":   {"days": 180, "quadrants": ["Q1", "Q2"],  "budget_release": "Phased",       "format_bias": "Blended"},
    "Medium-term (6–12 months)": {"days": 365, "quadrants": ["Q1","Q2","Q3"],"budget_release": "Structured", "format_bias": "Full mix"},
    "Long-term (12–24 months)":  {"days": 730, "quadrants": ["Q1","Q2","Q3","Q4"],"budget_release": "Annual", "format_bias": "Academy build"},
}


# ── Conflict Detection ────────────────────────────────────────────────────────

def detect_conflicts(slider_values: dict, m: dict) -> list:
    """
    Detect conflicts between leadership intent (sliders) and LNA data signals.
    Returns list of conflict dicts with severity: 'info', 'warning', 'critical'
    """
    conflicts = []

    # Map skill dimensions to relevant LNA metrics
    # We use a heuristic — in a real system these would be direct category-level gap %
    dimension_gap_proxy = {
        "Technical / Functional Skills": m.get("role_skill_cov", 100),          # inverted
        "Leadership & People Skills":    m.get("manager_ratio", 20),
        "Behavioral & Cultural Skills":  100 - m.get("crit_skills_idx", 75),     # gap proxy
        "Digital / Future Skills":       m.get("skill_scarcity_idx", 0),
        "Compliance & Risk Skills":      m.get("cert_cov_idx", 50),
    }

    # For Technical/Digital — lower coverage = higher gap
    gap_estimates = {
        "Technical / Functional Skills": round(100 - m.get("role_skill_cov", 100), 1),
        "Leadership & People Skills":    round(100 - min(m.get("manager_ratio", 20) * 4, 100), 1),
        "Behavioral & Cultural Skills":  round(100 - m.get("crit_skills_idx", 75), 1),
        "Digital / Future Skills":       round(m.get("skill_scarcity_idx", 0), 1),
        "Compliance & Risk Skills":      round(100 - m.get("cert_cov_idx", 50), 1),
    }

    for dim, slider_val in slider_values.items():
        gap_pct = gap_estimates.get(dim, 0)

        if slider_val < 0 and gap_pct > 60:
            severity = "critical" if slider_val <= -2 else "warning"
            conflicts.append({
                "dimension":  dim,
                "slider_val": slider_val,
                "gap_pct":    gap_pct,
                "severity":   severity,
                "message":    (
                    f"{dim} is deprioritised at {slider_val:+d} despite an estimated "
                    f"{gap_pct:.0f}% gap in the LNA data. This is a strategic override "
                    f"and will be flagged in the LNI/TNI report."
                ),
                "requires_justification": severity == "critical",
            })
        elif slider_val < 0 and gap_pct > 30:
            conflicts.append({
                "dimension":  dim,
                "slider_val": slider_val,
                "gap_pct":    gap_pct,
                "severity":   "info",
                "message":    (
                    f"{dim} is deprioritised at {slider_val:+d}. "
                    f"The LNA shows a moderate {gap_pct:.0f}% estimated gap — "
                    f"note this as an intentional deferral."
                ),
                "requires_justification": False,
            })

    return conflicts


# ── Strategy Profile Builder ──────────────────────────────────────────────────

def build_strategy_profile(
    cultural_priorities: list,
    skill_sliders: dict,
    org_focus: list,
    employee_segments: list,
    time_horizon: str,
    confirmed_by: str = "",
    confirmed_role: str = "",
    conflicts: list = None,
    justifications: dict = None,
    existing_version: str = None,
) -> dict:
    """
    Build the Leadership Talent Strategy Profile from UI selections.
    Returns structured dict consumed by LNI/TNI generator.
    """
    now = datetime.now()

    # Version increment
    if existing_version:
        try:
            major, minor = existing_version.lstrip("v").split(".")
            version = f"v{major}.{int(minor)+1}"
        except Exception:
            version = "v1.1"
    else:
        version = "v1.0"

    # Skill category multipliers from sliders (–3 to +3 → 0.1x to 4.0x)
    def slider_to_multiplier(val):
        mapping = {-3: 0.1, -2: 0.3, -1: 0.6, 0: 1.0, 1: 1.5, 2: 2.0, 3: 3.0}
        return mapping.get(val, 1.0)

    skill_weights = {dim: slider_to_multiplier(val) for dim, val in skill_sliders.items()}

    # Segment weights and format preferences
    segment_config = {}
    for seg in employee_segments:
        cfg = SEGMENT_FORMAT_BIAS.get(seg, {})
        segment_config[seg] = {
            "format":         cfg.get("format", "Blended"),
            "delivery":       cfg.get("delivery", "Blended"),
            "budget_weight":  cfg.get("budget_weight", 1.0),
        }

    # Time horizon config
    horizon_cfg = HORIZON_CONFIG.get(time_horizon, HORIZON_CONFIG["Short-term (3–6 months)"])

    # Strategic context summary — auto-generated
    cultural_str  = " and ".join(cultural_priorities[:3]) if cultural_priorities else "balanced priorities"
    segment_str   = ", ".join(employee_segments[:3]) if employee_segments else "all segments"
    focus_str     = ", ".join(org_focus[:3]) if org_focus else "all business units"
    horizon_short = time_horizon.split("(")[0].strip()

    # Identify amplified and deprioritised dimensions
    amplified    = [d for d, v in skill_sliders.items() if v >= 2]
    deprioritised = [d for d, v in skill_sliders.items() if v <= -2]

    amp_str  = f" {', '.join(amplified)} {'are' if len(amplified) > 1 else 'is'} amplified above data baseline." if amplified else ""
    dep_str  = f" Note: {', '.join(deprioritised)} {'are' if len(deprioritised) > 1 else 'is'} deprioritised as a strategic override." if deprioritised else ""

    strategic_summary = (
        f"This LNI/TNI is generated with a strategic emphasis on {cultural_str}, "
        f"prioritising {segment_str} across {focus_str}, "
        f"with a {horizon_short} focus.{amp_str}{dep_str}"
    )

    return {
        # Identity
        "version":           version,
        "version_id":        f"{version}-{uuid.uuid4().hex[:6].upper()}",
        "created_at":        now.isoformat(),
        "created_display":   now.strftime("%d %b %Y %H:%M"),
        "confirmed_by":      confirmed_by or "Not specified",
        "confirmed_role":    confirmed_role or "Not specified",

        # Selections
        "cultural_priorities":  cultural_priorities,
        "skill_sliders":        skill_sliders,
        "skill_weights":        skill_weights,
        "org_focus":            org_focus,
        "employee_segments":    employee_segments,
        "segment_config":       segment_config,
        "time_horizon":         time_horizon,
        "horizon_config":       horizon_cfg,

        # Derived
        "strategic_summary":    strategic_summary,
        "conflicts":            conflicts or [],
        "justifications":       justifications or {},
        "amplified_dimensions": amplified,
        "deprioritised_dimensions": deprioritised,
    }


# ── Weight Application ────────────────────────────────────────────────────────

def apply_strategy_weights(m: dict, profile: dict) -> dict:
    """
    Apply strategy profile weights to LNA metrics.
    Returns enriched metrics dict for LNI/TNI generation.
    """
    weighted = dict(m)  # copy
    q1 = m.get("q1_skills", None)
    q2 = m.get("q2_skills", None)
    skill_summary = m.get("skill_summary", None)

    # Re-score skills using strategy weights
    # In this simplified version we surface priority signals cleanly
    horizon_cfg = profile.get("horizon_config", {})
    active_quadrants = horizon_cfg.get("quadrants", ["Q1"])

    weighted["active_quadrants"]   = active_quadrants
    weighted["horizon_config"]     = horizon_cfg
    weighted["strategic_summary"]  = profile.get("strategic_summary", "")
    weighted["strategy_version"]   = profile.get("version", "v1.0")
    weighted["strategy_created"]   = profile.get("created_display", "")
    weighted["strategy_confirmed_by"] = profile.get("confirmed_by", "Not specified")

    # Focus segments with their delivery preferences
    weighted["priority_segments"]  = profile.get("segment_config", {})
    weighted["org_focus"]          = profile.get("org_focus", [])
    weighted["cultural_priorities"] = profile.get("cultural_priorities", [])
    weighted["skill_weights"]      = profile.get("skill_weights", {})
    weighted["conflicts"]          = profile.get("conflicts", [])

    return weighted
