"""
data_loader.py — Edstellar LNA Platform
Handles all Excel ingestion and sheet validation.
Pure logic — no Streamlit imports.
"""

import pandas as pd
from datetime import datetime

REQUIRED_SHEETS = [
    "CoverPage", "Employees", "Employee Attrition", "Skills Master",
    "Role Skills", "Employee Skills", "Competency Master",
    "Role-Competency Mapping", "Employee Competencies", "Training",
    "Certifications", "Projects", "Project Skills", "Project Competencies",
    "Employee Projects", "Employee Tools", "Org_Industry_Benchmark",
]

SHEET_DESCRIPTIONS = {
    "CoverPage":               "Company name, report period, metadata",
    "Employees":               "Employee master data — roles, locations, tenure, age",
    "Employee Attrition":      "Employees who exited during the period",
    "Skills Master":           "Skills framework — names, categories, criticality",
    "Role Skills":             "Role → skill mapping with required proficiency levels",
    "Employee Skills":         "Individual employee skill proficiency records",
    "Competency Master":       "Competency framework — names, categories, criticality",
    "Role-Competency Mapping": "Role → competency mapping",
    "Employee Competencies":   "Individual employee competency proficiency records",
    "Training":                "Training hours, budget, type, job family",
    "Certifications":          "Employee certifications with status and expiry",
    "Projects":                "Active and upcoming projects",
    "Project Skills":          "Skill dependencies per project",
    "Project Competencies":    "Competency dependencies per project",
    "Employee Projects":       "Employee → project assignments",
    "Employee Tools":          "Tools used by employees",
    "Org_Industry_Benchmark":  "Benchmark metrics — org vs industry comparisons",
}


def load_sheet(xl: pd.ExcelFile, name: str, **kwargs) -> pd.DataFrame:
    """Safely load a sheet — returns empty DataFrame if missing."""
    try:
        df = xl.parse(name, **kwargs)
        df.columns = df.columns.str.strip()
        return df
    except Exception:
        return pd.DataFrame()


def validate_file(file_obj) -> dict:
    """
    Validate uploaded Excel file.
    Returns dict with keys: valid (bool), sheets_found, sheets_missing, sheet_status
    """
    try:
        xl = pd.ExcelFile(file_obj)
        found = set(xl.sheet_names)
        required = set(REQUIRED_SHEETS)
        missing = required - found
        present = required & found
        extra = found - required

        sheet_status = {}
        for s in REQUIRED_SHEETS:
            if s in found:
                try:
                    df = xl.parse(s)
                    rows = len(df)
                    sheet_status[s] = {"status": "ok", "rows": rows}
                except Exception as e:
                    sheet_status[s] = {"status": "error", "rows": 0, "error": str(e)}
            else:
                sheet_status[s] = {"status": "missing", "rows": 0}

        return {
            "valid": len(missing) == 0,
            "sheets_found": list(present),
            "sheets_missing": list(missing),
            "sheets_extra": list(extra),
            "sheet_status": sheet_status,
            "total_sheets": len(found),
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "sheets_found": [],
            "sheets_missing": REQUIRED_SHEETS,
            "sheet_status": {},
            "total_sheets": 0,
        }


def load_all_data(file_obj) -> dict:
    """
    Load all sheets from Excel file.
    Returns dict of dataframes + cover page metadata.
    """
    xl = pd.ExcelFile(file_obj)

    # Cover page — key/value pairs
    cover_raw = load_sheet(xl, "CoverPage", header=None)
    cover_dict = {}
    for _, row in cover_raw.iterrows():
        if pd.notna(row.iloc[0]):
            k = str(row.iloc[0]).strip().rstrip(":")
            v = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
            cover_dict[k] = v

    def cv(key, default="—"):
        for k, v in cover_dict.items():
            if key.lower() in k.lower():
                return v
        return default

    # All sheets
    data = {
        "xl":           xl,
        "cover_dict":   cover_dict,
        "company":      cv("Company Name", "Organisation"),
        "time_period":  cv("Time Period", "Q4"),
        "year":         cv("Year", "2025-26"),
        "report_date":  cv("Report Date", datetime.today().strftime("%d %b %Y")),
        "industry":     cv("Industry", "IT / SaaS"),

        # Core sheets
        "emp":           load_sheet(xl, "Employees"),
        "attrition":     load_sheet(xl, "Employee Attrition"),
        "skills_master": load_sheet(xl, "Skills Master"),
        "role_skills":   load_sheet(xl, "Role Skills"),
        "emp_skills":    load_sheet(xl, "Employee Skills"),
        "comp_master":   load_sheet(xl, "Competency Master"),
        "role_comps":    load_sheet(xl, "Role-Competency Mapping"),
        "emp_comps":     load_sheet(xl, "Employee Competencies"),
        "training":      load_sheet(xl, "Training"),
        "certs":         load_sheet(xl, "Certifications"),
        "projects":      load_sheet(xl, "Projects"),
        "proj_skills":   load_sheet(xl, "Project Skills"),
        "proj_comps":    load_sheet(xl, "Project Competencies"),
        "emp_projects":  load_sheet(xl, "Employee Projects"),
        "emp_tools":     load_sheet(xl, "Employee Tools"),
        "benchmark":     load_sheet(xl, "Org_Industry_Benchmark"),
    }

    # Active employees filter
    emp = data["emp"]
    if "Employment Status" in emp.columns:
        data["active_emp"] = emp[
            emp["Employment Status"].str.lower().str.contains("active", na=False)
        ]
    else:
        data["active_emp"] = emp

    return data
