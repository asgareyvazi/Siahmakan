"""Derive per-well narrative facts from the calculation datasets.

Everything returned here is computed from the CSVs. Nothing is hard-coded per
well except the interpretation strings, which are selected by evidence from the
data so that no two wells receive the same conclusions unless the records
support it.
"""
import csv
from collections import Counter, defaultdict

BASE = "Siahmakan_Analysis"
DAT = f"{BASE}/04_Engineering_Datasets"
CALC = f"{DAT}/Calculations"
WELLS = ["SI-006", "SI-007", "SI-008", "SI-009"]


def R(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def f(v, d=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def get(w):
    """Return a dict of every derived fact needed to write one well report."""
    D = {}
    D["well"] = w
    D["master"] = [r for r in R(f"{CALC}/well_master_register.csv") if r["well"] == w][0]
    D["comp"] = [r for r in R(f"{CALC}/comparison_matrix.csv") if r["well"] == w][0]
    D["sections"] = [r for r in R(f"{CALC}/hole_sections.csv") if r["well"] == w]
    D["phases"] = [r for r in R(f"{CALC}/phase_hours.csv") if r["well"] == w]
    D["codes"] = [r for r in R(f"{CALC}/operation_codes.csv") if r["well"] == w]
    D["npt"] = [r for r in R(f"{CALC}/npt_register.csv") if r["well"] == w]
    D["npt_fam"] = [r for r in R(f"{CALC}/npt_by_family.csv") if r["well"] == w]
    D["npt_sec"] = [r for r in R(f"{CALC}/npt_by_section.csv") if r["well"] == w]
    D["npt_sum"] = [r for r in R(f"{CALC}/npt_summary.csv") if r["well"] == w][0]
    D["bits"] = [r for r in R(f"{CALC}/bit_run_register.csv") if r["well"] == w]
    D["params"] = [r for r in R(f"{CALC}/drilling_parameters.csv") if r["well"] == w]
    D["mud"] = {r["param"]: r for r in R(f"{CALC}/mud_summary.csv") if r["well"] == w}
    D["form"] = [r for r in R(f"{CALC}/formation_tops.csv") if r["well"] == w]
    D["traj"] = [r for r in R(f"{CALC}/trajectory_assessment.csv") if r["well"] == w][0]
    D["series"] = [r for r in R(f"{CALC}/depth_time_series.csv") if r["well"] == w]
    D["gaps"] = [r for r in R(f"{CALC}/reporting_gaps.csv") if r["well"] == w]
    D["casing"] = R(f"{DAT}/{w}_casing.csv")
    D["headers"] = R(f"{DAT}/{w}_headers.csv")
    D["ops"] = R(f"{DAT}/{w}_operations.csv")

    # ---- final casing programme: table on the highest rig-day sheet
    cs = [c for c in D["casing"] if f(c["rig_days"]) is not None]
    if cs:
        mx = max(f(c["rig_days"]) for c in cs)
        D["final_casing"] = [c for c in cs if f(c["rig_days"]) == mx]
        D["final_casing_sheet"] = D["final_casing"][0]["source_sheet"]
    else:
        D["final_casing"] = []
        D["final_casing_sheet"] = ""

    # ---- top NPT events with narrative
    D["npt_top"] = sorted(D["npt"], key=lambda r: -f(r["hours"], 0))[:8]

    # ---- drilling phase metrics
    m = D["master"]
    D["depth"] = f(m["final_depth_m"], 0)
    D["planned"] = f(m["planned_td_m"], 0)
    D["days"] = f(m["calendar_days_span"], 0)
    D["tot_h"] = f(m["total_op_hours"], 0)
    D["npt_h"] = f(D["npt_sum"]["npt_hours"], 0)
    D["npt_pct"] = f(D["npt_sum"]["npt_pct"], 0)

    # ---- bit summary
    bs = [b for b in D["bits"] if f(b["footage_m"], 0) > 0 and f(b["rop_m_per_h"])]
    D["bits_drilling"] = bs
    D["best_bit"] = max(bs, key=lambda b: f(b["rop_m_per_h"])) if bs else None
    D["worst_bit"] = min(bs, key=lambda b: f(b["rop_m_per_h"])) if bs else None
    D["longest_bit"] = max(bs, key=lambda b: f(b["footage_m"])) if bs else None

    # ---- dominant NPT family / section
    D["top_family"] = D["npt_fam"][0] if D["npt_fam"] else None
    D["top_section_npt"] = D["npt_sec"][0] if D["npt_sec"] else None

    # ---- phase lookups
    D["ph"] = {r["phase"]: r for r in D["phases"]}
    D["code"] = {r["code"]: r for r in D["codes"]}

    # ---- drilling-time split
    drill = f(D["ph"].get("Drilling", {}).get("hours_total"), 0)
    trips = f(D["ph"].get("Trip & Hole Conditioning", {}).get("hours_total"), 0)
    D["drill_h"] = drill
    D["trip_h"] = trips
    D["drill_share"] = 100 * drill / D["tot_h"] if D["tot_h"] else 0
    D["trip_share"] = 100 * trips / D["tot_h"] if D["tot_h"] else 0

    # ---- sidetrack evidence from the depth record
    H = [h for h in D["headers"] if h["report_date"]]
    H.sort(key=lambda h: (f(h["rig_days"], 0), h["report_date"]))
    D["sidetracks"] = []
    for i in range(1, len(H)):
        a, b = f(H[i - 1]["depth24"]), f(H[i]["depth24"])
        if a is not None and b is not None and b < a - 50:
            D["sidetracks"].append({"sheet": H[i]["source_sheet"],
                                    "from_depth": a, "to_depth": b,
                                    "date": H[i]["report_date"],
                                    "rig_day": H[i]["rig_days"]})

    # ---- well-control / hole-problem hours
    D["wellctrl_h"] = f(D["code"].get("10-5", {}).get("hours"), 0)
    D["stuck_h"] = f(D["code"].get("10-3", {}).get("hours"), 0)
    D["fishing_h"] = f(D["code"].get("10-4", {}).get("hours"), 0)
    D["coring_h"] = f(D["code"].get("5-3", {}).get("hours"), 0)
    D["perf_h"] = f(D["code"].get("5-6", {}).get("hours"), 0)
    D["cmpl_h"] = f(D["code"].get("8-1", {}).get("hours"), 0)

    # ---- survey verdict
    D["survey_verdict"] = D["traj"]["verdict"]
    D["survey_reason"] = D["traj"]["reason"]
    return D
