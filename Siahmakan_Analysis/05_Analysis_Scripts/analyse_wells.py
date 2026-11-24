"""Engineering analysis engine for the Siah Makan DDR dataset.

Consumes the normalised CSVs produced by extract_ddrs.py and produces:
  * well master register
  * hole-section / phase table with ROP and productive-time metrics
  * NPT register with taxonomy and root-cause linkage
  * bit-run register
  * bit / drilling parameter summary
  * mud-property summary
  * formation-top register
  * trajectory integrity assessment
  * depth-time series for plotting
All outputs are CSVs so every figure in the reports is reproducible.

Design rules enforced here
--------------------------
1. Every rate uses a stated numerator and denominator (both written to CSV).
2. Non-productive time (NPT) uses the DDR's own Type column (N = non-productive,
   U = unplanned/unclassified). Both are reported separately and combined, so
   the denominator is always explicit.
3. Nothing is interpolated across a reporting gap: gaps are recorded, not filled.
4. Survey data is not used to claim a trajectory: it is assessed and rejected as
   template data where the evidence shows that (see analyse_trajectory).
"""
import csv
import os
import re
from collections import Counter, defaultdict
from datetime import datetime

BASE = "Siahmakan_Analysis"
DAT = f"{BASE}/04_Engineering_Datasets"
CALC = f"{BASE}/04_Engineering_Datasets/Calculations"
WELLS = ["SI-006", "SI-007", "SI-008", "SI-009"]

# --------------------------------------------------------------------------
# Operation-code dictionary, transcribed from the DDR code legend printed on
# every sheet (columns O:S) - not invented.
# --------------------------------------------------------------------------
CODE_DESC = {
    "1-1": "Rig Moving (Up/Down)", "2-1": "Drilling", "2-2": "Directional Drilling",
    "2-3": "Connection", "2-4": "Side Tracking", "2-5": "Survey",
    "3-1": "Round Trip", "3-2": "Observe Well", "3-3": "Wearing Bushing",
    "3-4": "Prior Formation Evaluation", "3-5": "Prior Csg/Cmt/DST/CBL",
    "3-6": "Scraping", "3-7": "Drill / Clean Out", "3-8": "M/U L/D DP",
    "3-9": "M/U L/D BHA", "4-1": "Circulating", "4-2": "W&R Tight",
    "4-3": "Reaming", "4-4": "Mixing Mud", "4-5": "Condition Fluid",
    "4-6": "Hole Opening", "4-7": "Short Trip", "5-1": "Geo Circulation",
    "5-2": "LOT-FIT", "5-3": "Coring", "5-4": "DST / Test / Stimulation",
    "5-5": "Logging / TLC", "5-6": "Perforation", "6-1": "Casing Tools",
    "6-2": "Running Casing", "6-3": "Circ in Casing", "6-4": "Cementing",
    "6-5": "WOC", "6-6": "Plug Back", "6-7": "RTTS", "6-8": "Squeeze Cement",
    "6-9": "Dry Test", "6-10": "Tie Back", "6-11": "Pressure Test",
    "6-12": "Drill Out", "6-13": "CBL", "7-1": "N/D N/U BOP", "7-2": "Dress Neck",
    "7-3": "BOP Test", "7-4": "Wellhead", "7-5": "Setting RTTS",
    "8-1": "Run/Pull Completion", "8-2": "Abandonment", "8-3": "Slickline",
    "8-4": "Displacing Fluid", "8-5": "Pressure Test", "8-6": "Stim/N2/Gas Lift",
    "8-7": "Flow Well", "8-8": "Kill Well", "9-1": "Rig Service",
    "9-2": "Slip & Cut", "10-1": "Milling", "10-2": "Plug/Unplug",
    "10-3": "Stuck Pipe", "10-4": "Fishing", "10-5": "Well Control",
    "10-6": "Washout", "10-7": "Loss Circulation", "11-1": "Waiting Safety",
    "11-2": "Rig Repair", "11-3": "Wait Rig Contractor", "11-4": "Wait Procurement",
    "11-5": "Wait Material Quality", "11-6": "Wait Service Company",
    "11-7": "Wait Client", "11-8": "Wait Order/Program", "11-9": "Wait Civil",
    "11-10": "Wait Surface / Contingency",
}

# Phase assignment of codes
PHASE = {}
for c in ["1-1"]:
    PHASE[c] = "Drilling"
for c in ["2-1", "2-2", "2-3", "2-4", "2-5", "4-3", "4-6", "4-7", "10-1"]:
    PHASE[c] = "Drilling"
for c in ["6-1", "6-2", "6-3", "6-4", "6-5", "6-6", "6-7", "6-8", "6-9",
          "6-10", "6-11", "6-12", "6-13"]:
    PHASE[c] = "Casing & Cementing"
for c in ["5-1", "5-2", "5-3", "5-5"]:
    PHASE[c] = "Evaluation & Logging"
for c in ["5-4", "5-6", "8-6", "8-7"]:
    PHASE[c] = "Testing & Stimulation"
for c in ["8-1", "8-2", "8-3", "8-4", "8-5", "8-8"]:
    PHASE[c] = "Completion & Intervention"
for c in ["3-1", "3-2", "3-3", "3-4", "3-5", "3-6", "3-7", "3-8", "3-9"]:
    PHASE[c] = "Trip & Hole Conditioning"
for c in ["4-1", "4-2", "4-4", "4-5"]:
    PHASE[c] = "Circulation & Fluid Treatment"
for c in ["7-1", "7-2", "7-3", "7-4", "7-5"]:
    PHASE[c] = "Wellhead & BOP"
for c in ["9-1", "9-2"]:
    PHASE[c] = "Rig Service"
for c in ["10-3", "10-4", "10-5", "10-6", "10-7"]:
    PHASE[c] = "Hole Problem"
for c in ["11-1", "11-2", "11-3", "11-4", "11-5", "11-6", "11-7", "11-8",
          "11-9", "11-10"]:
    PHASE[c] = "Waiting / Standby"

# NPT taxonomy: (family, immediate mechanism). Only codes whose nature is
# inherently unplanned are auto-classified; N-typed waiting codes are mapped by
# their own code meaning so the family never contradicts the recorded code.
NPT_FAMILY = {
    "10-3": ("Stuck pipe", "String stuck"),
    "10-4": ("Fishing", "Fishing / recovery operation"),
    "10-5": ("Well control", "Kick / influx / well kill"),
    "10-6": ("Hole instability", "Washout / cavings"),
    "10-7": ("Lost circulation", "Lost returns"),
    "11-2": ("Rig equipment failure", "Rig repair"),
    "11-3": ("Waiting on rig contractor", "Rig contractor standby"),
    "11-4": ("Waiting on procurement", "Material/equipment procurement"),
    "11-5": ("Waiting on material quality", "Material quality rejection"),
    "11-6": ("Waiting on service company", "Service company standby"),
    "11-7": ("Waiting on client", "Client decision / instruction"),
    "11-8": ("Waiting on programme", "Programme / order wait"),
    "11-9": ("Waiting on civil works", "Civil works"),
    "11-10": ("Operations contingency", "Surface/contingency standby"),
    "11-1": ("Safety standby", "Safety-related standby"),
    "6-8": ("Cementing problem", "Squeeze cement"),
    "6-6": ("Cementing problem", "Plug back"),
    "6-9": ("Well integrity test", "Dry test / pressure test"),
    "6-11": ("Well integrity test", "Pressure test"),
    "6-13": ("Cementing problem", "CBL / cement evaluation"),
    "7-3": ("Wellhead & BOP", "BOP test"),
    "4-2": ("Hole instability", "Tight hole / reaming while working"),
    "8-8": ("Well control", "Well kill"),
    "8-2": ("Abandonment", "Abandonment operations"),
    "3-1": ("Trip", "Round trip"),
    "3-8": ("Trip", "M/U L/D drill pipe"),
    "3-9": ("Trip", "M/U L/D BHA"),
    "3-6": ("Hole conditioning", "Scraping"),
    "3-7": ("Hole conditioning", "Drill/clean out"),
    "4-3": ("Hole conditioning", "Reaming"),
    "4-7": ("Hole conditioning", "Short trip"),
    "4-1": ("Circulation", "Circulating"),
    "5-5": ("Logging", "Logging / TLC"),
    "6-12": ("Drill out", "Drill out cement"),
    "6-2": ("Casing", "Running casing"),
    "8-1": ("Completion", "Run/pull completion"),
    "5-6": ("Perforation", "Perforation"),
    "5-3": ("Coring", "Coring"),
    "1-1": ("Rig move", "Rig moving"),
}

PHASE_ORDER = ["Drilling", "Trip & Hole Conditioning", "Circulation & Fluid Treatment",
               "Casing & Cementing", "Wellhead & BOP", "Evaluation & Logging",
               "Testing & Stimulation", "Completion & Intervention",
               "Hole Problem", "Rig Service", "Waiting / Standby"]


def rcsv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def wcsv(path, rows, fields=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if fields is None:
        fields = list(rows[0].keys()) if rows else []
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def fnum(v, default=None):
    if v in (None, "", "None"):
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# --------------------------------------------------------------------------
def load_well(well):
    d = {"well": well}
    d["headers"] = rcsv(f"{DAT}/{well}_headers.csv")
    d["ops"] = rcsv(f"{DAT}/{well}_operations.csv")
    d["bit"] = rcsv(f"{DAT}/{well}_bit.csv")
    d["bha"] = rcsv(f"{DAT}/{well}_bha.csv")
    d["casing"] = rcsv(f"{DAT}/{well}_casing.csv")
    d["mud"] = rcsv(f"{DAT}/{well}_mud.csv")
    d["survey"] = rcsv(f"{DAT}/{well}_survey.csv")
    d["formations"] = rcsv(f"{DAT}/{well}_formations.csv")
    d["tb"] = rcsv(f"{DAT}/{well}_timebreakdown.csv")
    return d


def master_register(d):
    H = d["headers"]
    dated = [h for h in H if h["report_date"]]
    dated.sort(key=lambda h: (h["report_date"], fnum(h["sheet_index"], 0)))
    first, last = dated[0], dated[-1]
    depths = [fnum(h["depth24"]) for h in H if fnum(h["depth24"]) is not None]
    ops = d["ops"]
    tot_h = sum(fnum(o["hrs"], 0) for o in ops)
    npt = sum(fnum(o["hrs"], 0) for o in ops if o["type"] in ("N", "U"))
    spud = parse_date(first["spud_date"])
    last_d = parse_date(last["report_date"])
    return {
        "well": d["well"],
        "source_file": first["source_file"],
        "field": first["field"],
        "well_name_recorded": first["well_name"],
        "well_type": first["well_type"],
        "rig_contractor": first["rig_contractor"],
        "operator": first["operator"],
        "spud_date": first["spud_date"],
        "first_ddr_date": first["report_date"],
        "last_ddr_date": last["report_date"],
        "last_ddr_sheet": last["source_sheet"],
        "calendar_days_span": (last_d - spud).days + 1 if spud else None,
        "ddr_count": len(H),
        "rig_days_max": max(fnum(h["rig_days"], 0) for h in H),
        "planned_td_m": fnum(first["planned_td"]),
        "plan_duration_d": fnum(first["plan_duration"]),
        "final_depth_m": max(depths) if depths else None,
        "last_hole_size": last["hole_size"],
        "last_csg": last["csg"] if "csg" in last else last["last_csg"],
        "next_csg_recorded": last["next_csg"],
        "liner_lap": last["liner_lap"],
        "fit": last["fit"],
        "total_op_hours": round(tot_h, 1),
        "npt_hours_NU": round(npt, 1),
        "npt_pct_NU": round(100 * npt / tot_h, 2) if tot_h else None,
        "date_basis": "RECORDED" if all(h["date_basis"] == "RECORDED" for h in H) else "PARTLY DERIVED",
    }


HS_VARIANTS = {
    "26": '26"', "26\"": '26"', "26\" CSG": '26"',
    "17-1/2\"": '17-1/2"', "17½\"": '17-1/2"', "171/2\"": '17-1/2"',
    "17.5": '17-1/2"', "17-1/2": '17-1/2"',
    "12-1/4\"": '12-1/4"', "12¼\"": '12-1/4"', "12.25": '12-1/4"',
    "12-1/4": '12-1/4"', "121/4\"": '12-1/4"',
    "8-3/8\"": '8-3/8"', "8.375": '8-3/8"', "8-3/8": '8-3/8"', "83/8\"": '8-3/8"',
    "5-7/8\"": '5-7/8"', "5.875": '5-7/8"', "5-7/8": '5-7/8"', "57/8\"": '5-7/8"',
    "7\"": '7"', "7": '7"', "COMPLETION": "Completion",
}


def norm_hs(hs):
    t = (hs or "").strip().replace("  ", " ")
    if not t:
        return ""
    key = t.upper().replace(" ", "")
    for k, v in HS_VARIANTS.items():
        if key == k.upper().replace(" ", ""):
            return v
    return t


def section_table(d):
    """Hole-section table built from the recorded hole-size column.

    Hole size is recorded in free text and appears with several spellings for
    the same nominal size (e.g. '12.25', '12-1/4"', '12¼"'; '57/8"' vs
    '5-7/8"'). It is therefore normalised first, and a section change is only
    accepted when the new size persists for at least two consecutive DDRs -
    otherwise a single mis-typed cell would create a spurious section.

    Section boundaries and progress come from the DDR recorded depth at 24:00.
    Drilling hours come from operation code 2-1 (Drilling) on the DDRs inside
    the section, so the ROP denominator is stated explicitly.
    """
    H = [h for h in d["headers"] if h["report_date"]]
    H.sort(key=lambda h: (fnum(h["rig_days"], 0), h["report_date"]))
    sizes = [norm_hs(h["hole_size"]) for h in H]
    # smooth: a value that disagrees with both neighbours is replaced
    for i in range(1, len(sizes) - 1):
        if sizes[i] and sizes[i] != sizes[i - 1] and sizes[i - 1] == sizes[i + 1]:
            sizes[i] = sizes[i - 1]
    # forward-fill blanks
    last = ""
    for i, s in enumerate(sizes):
        if not s:
            sizes[i] = last
        else:
            last = s

    # assign section ids
    sec_id = []
    cur = 0
    for i, s in enumerate(sizes):
        if i > 0 and s != sizes[i - 1]:
            cur += 1
        sec_id.append(cur)

    # drilling hours per sheet
    drill_h = defaultdict(float)
    gross_h = defaultdict(float)
    GROSS = {"2-1", "2-2", "4-3", "4-6"}
    for o in d["ops"]:
        if o["code"] == "2-1":
            drill_h[o["source_sheet"]] += fnum(o["hrs"], 0)
        if o["code"] in GROSS:
            gross_h[o["source_sheet"]] += fnum(o["hrs"], 0)
    npt_h = defaultdict(float)
    for o in d["ops"]:
        if o["type"] in ("N", "U"):
            npt_h[o["source_sheet"]] += fnum(o["hrs"], 0)

    secs = []
    for sid in sorted(set(sec_id)):
        idxs = [i for i, x in enumerate(sec_id) if x == sid]
        first, lastr = H[idxs[0]], H[idxs[-1]]
        s = {
            "well": d["well"], "hole_size": sizes[idxs[0]],
            "start_date": first["report_date"], "start_rig_day": fnum(first["rig_days"]),
            "start_depth": fnum(first["depth00"]),
            "end_date": lastr["report_date"], "end_rig_day": fnum(lastr["rig_days"]),
            "end_depth": fnum(lastr["depth24"]),
            "ddr_count": len(idxs),
            "sheets": first["source_sheet"] + ("" if len(idxs) == 1 else f" ... {lastr['source_sheet']}"),
            "first_sheet": first["source_sheet"], "last_sheet": lastr["source_sheet"],
        }
        s["duration_d"] = (s["end_rig_day"] or 0) - (s["start_rig_day"] or 0) + 1
        s["interval_m"] = round((s["end_depth"] or 0) - (s["start_depth"] or 0), 2)
        s["is_completion"] = sizes[idxs[0]] == "Completion"
        s["drilling_hours_2_1"] = round(sum(drill_h[h["source_sheet"]] for h in H if h["source_sheet"] in
                                            {H[i]["source_sheet"] for i in idxs}), 1)
        s["npt_hours"] = round(sum(npt_h[h["source_sheet"]] for h in H if h["source_sheet"] in
                                   {H[i]["source_sheet"] for i in idxs}), 1)
        s["rop_m_per_day"] = (round(s["interval_m"] / s["duration_d"], 2)
                              if s["duration_d"] and s["duration_d"] > 0 else None)
        s["rop_m_per_drill_hour"] = (round(s["interval_m"] / s["drilling_hours_2_1"], 2)
                                     if s["drilling_hours_2_1"] else None)
        s["npt_pct_of_section"] = (round(100 * s["npt_hours"] / (s["duration_d"] * 24), 1)
                                   if s["duration_d"] else None)
        secs.append(s)
    return secs


def phase_table(d):
    """Hours by operational phase and by productive class."""
    agg = defaultdict(lambda: defaultdict(float))
    nagg = defaultdict(float)
    for o in d["ops"]:
        h = fnum(o["hrs"], 0)
        ph = PHASE.get(o["code"], "Unclassified")
        agg[ph]["hours"] += h
        agg[ph][o["type"] or "untyped"] += h
        nagg[o["code"]] += h
    tot = sum(v["hours"] for v in agg.values())
    rows = []
    for ph in PHASE_ORDER + ["Unclassified"]:
        if ph not in agg:
            continue
        v = agg[ph]
        rows.append({
            "well": d["well"], "phase": ph,
            "hours_total": round(v["hours"], 1),
            "pct_of_total": round(100 * v["hours"] / tot, 2) if tot else None,
            "hours_productive": round(v.get("P", 0), 1),
            "hours_npt_N": round(v.get("N", 0), 1),
            "hours_npt_U": round(v.get("U", 0), 1),
            "hours_untyped": round(v.get("untyped", 0), 1),
        })
    return rows, nagg, tot


def code_table(d):
    agg = defaultdict(lambda: {"hours": 0.0, "count": 0, "P": 0.0, "N": 0.0, "U": 0.0})
    for o in d["ops"]:
        k = o["code"] or "(blank)"
        a = agg[k]
        a["hours"] += fnum(o["hrs"], 0)
        a["count"] += 1
        a[o["type"] or "untyped"] = a.get(o["type"] or "untyped", 0) + fnum(o["hrs"], 0)
    tot = sum(v["hours"] for v in agg.values())
    rows = []
    for k, v in sorted(agg.items(), key=lambda kv: -kv[1]["hours"]):
        rows.append({
            "well": d["well"], "code": k,
            "description": CODE_DESC.get(k, "(not in legend)"),
            "phase": PHASE.get(k, "Unclassified"),
            "npt_family": NPT_FAMILY.get(k, ("", ""))[0],
            "hours": round(v["hours"], 1),
            "pct_of_total": round(100 * v["hours"] / tot, 2) if tot else None,
            "occurrences": v["count"],
            "hours_P": round(v.get("P", 0), 1),
            "hours_N": round(v.get("N", 0), 1),
            "hours_U": round(v.get("U", 0), 1),
        })
    return rows, tot


def npt_register(d):
    """Event register. An event is a maximal run of consecutive DDRs carrying
    the same NPT code. Durations are summed from the DDR hour fields; a gap in
    the DDR date sequence closes the event and is flagged."""
    ops = [o for o in d["ops"] if o["type"] in ("N", "U") and o["code"]]
    by_date = defaultdict(list)
    for o in ops:
        by_date[o["report_date"]].append(o)
    hdr_date = {h["source_sheet"]: h["report_date"] for h in d["headers"]}
    dates = sorted({h["report_date"] for h in d["headers"] if h["report_date"]})
    idx = {dt: i for i, dt in enumerate(dates)}

    events = []
    open_ev = {}
    for dt in dates:
        present = {o["code"] for o in by_date.get(dt, [])}
        # close events not present today
        for code in list(open_ev):
            if code not in present:
                events.append(open_ev.pop(code))
        for code in present:
            lst = [o for o in by_date[dt] if o["code"] == code]
            hrs = sum(fnum(o["hrs"], 0) for o in lst)
            if code in open_ev:
                ev = open_ev[code]
                ev["end_date"] = dt
                ev["hours"] += hrs
                ev["ddr_count"] += 1
                ev["types"] = sorted(set(ev["types"]) | {o["type"] for o in lst})
                if len(ev["desc"]) < 700:
                    ev["desc"] += " | " + lst[0]["desc"]
            else:
                open_ev[code] = {
                    "well": d["well"], "code": code,
                    "family": NPT_FAMILY.get(code, ("Unclassified", ""))[0],
                    "mechanism": NPT_FAMILY.get(code, ("", "Unclassified"))[1],
                    "description": CODE_DESC.get(code, ""),
                    "start_date": dt, "end_date": dt, "hours": hrs, "ddr_count": 1,
                    "types": [o["type"] for o in lst],
                    "hole_sizes": sorted({o["hole_size"] for o in lst}),
                    "desc": lst[0]["desc"][:350],
                    "first_sheet": lst[0]["source_sheet"],
                }
    for code in open_ev:
        events.append(open_ev[code])
    for ev in events:
        ev["types"] = "".join(sorted(set(ev["types"])))
        ev["hole_sizes"] = "; ".join(x for x in ev["hole_sizes"] if x)
        try:
            a = parse_date(ev["start_date"])
            b = parse_date(ev["end_date"])
            ev["span_days"] = (b - a).days + 1
        except TypeError:
            ev["span_days"] = None
    events.sort(key=lambda e: -e["hours"])
    for i, ev in enumerate(events, 1):
        ev["event_id"] = f"{d['well']}-NPT-{i:03d}"
    return events


def npt_summary(d, events):
    tot_h = sum(fnum(o["hrs"], 0) for o in d["ops"])
    npt_h = sum(e["hours"] for e in events)
    byfam = defaultdict(float)
    bysec = defaultdict(float)
    for e in events:
        byfam[e["family"]] += e["hours"]
    # by hole section using the section table
    secs = section_table(d)
    for e in events:
        placed = False
        for s in secs:
            if s["start_date"] and e["start_date"] and s["start_date"] <= e["start_date"] <= (s["end_date"] or "9999"):
                bysec[s["hole_size"]] += e["hours"]
                placed = True
                break
        if not placed:
            bysec["(outside section table)"] += e["hours"]
    fam_rows = [{"well": d["well"], "family": k, "hours": round(v, 1),
                 "pct_of_npt": round(100 * v / npt_h, 2) if npt_h else None,
                 "pct_of_total_time": round(100 * v / tot_h, 2) if tot_h else None,
                 "event_count": sum(1 for e in events if e["family"] == k)}
                for k, v in sorted(byfam.items(), key=lambda kv: -kv[1])]
    sec_rows = [{"well": d["well"], "hole_section": k, "npt_hours": round(v, 1),
                 "pct_of_npt": round(100 * v / npt_h, 2) if npt_h else None}
                for k, v in sorted(bysec.items(), key=lambda kv: -kv[1])]
    return fam_rows, sec_rows, {"well": d["well"], "total_hours": round(tot_h, 1),
                               "npt_hours": round(npt_h, 1),
                               "npt_pct": round(100 * npt_h / tot_h, 2) if tot_h else None,
                               "event_count": len(events)}


def bit_runs(d):
    """Bit-run register.

    A run is opened when the reported Bit No. changes. Footage and rotating
    hours are NOT taken from the free-text cumulative fields on the sheet (those
    are inconsistent: they mix metres, notes such as '223m D/O CMT', and
    sometimes carry a different bit's cumulative total). Instead:

        footage  = depth at the pull-out DDR minus depth at the run-in DDR
        hours    = sum of operation-code 2-1 (Drilling) hours on the DDRs
                   spanned by the run

    Both are derived from the structured DDR records, so their basis is stated
    and identical for every run. The sheet-reported values are kept alongside as
    documented (unverified) figures and never used in rate calculations.
    """
    per_sheet = defaultdict(dict)
    for r in d["bit"]:
        per_sheet[r["source_sheet"]][r["param"]] = r["value"]
    H = {h["source_sheet"]: h for h in d["headers"]}
    order = {k: (fnum(v["rig_days"], 0), v["report_date"] or "") for k, v in H.items()}
    sheets = sorted([s for s in per_sheet if s in H], key=lambda s: order[s])

    drill_h = defaultdict(float)
    gross_h = defaultdict(float)
    GROSS = {"2-1", "2-2", "4-3", "4-6"}
    for o in d["ops"]:
        if o["code"] == "2-1":
            drill_h[o["source_sheet"]] += fnum(o["hrs"], 0)
        if o["code"] in GROSS:
            gross_h[o["source_sheet"]] += fnum(o["hrs"], 0)
    npt_h = defaultdict(float)
    for o in d["ops"]:
        if o["type"] in ("N", "U"):
            npt_h[o["source_sheet"]] += fnum(o["hrs"], 0)

    runs = []
    cur = None
    for sh in sheets:
        p = per_sheet[sh]
        bno = (p.get("bit_no") or "").strip()
        if not bno:
            continue
        if cur is None or bno != cur["bit_no"]:
            if cur:
                runs.append(cur)
            cur = {
                "well": d["well"], "bit_no": bno,
                "bit_size": p.get("bit_size", ""), "bit_type": p.get("bit_type", ""),
                "manufacturer": p.get("bit_manufacturer", ""),
                "serial": p.get("bit_serial", ""), "nozzles": p.get("bit_nozzles", ""),
                "tfa": fnum(p.get("tfa")),
                "first_sheet": sh, "last_sheet": sh,
                "start_date": H[sh]["report_date"], "end_date": H[sh]["report_date"],
                "depth_in_m": fnum(H[sh]["depth00"]),
                "hole_size": norm_hs(H[sh]["hole_size"]),
                "sheets": [sh], "dull": "", "cum_drilled_recorded": "",
                "bit_hours_reported": None, "cum_hours_reported": None,
                "depth_out_reported": None,
                "wob": [], "rpm": [], "torque": [], "spp": [], "flow": [], "hsi": [],
            }
        else:
            cur["last_sheet"] = sh
            cur["sheets"].append(sh)
            cur["end_date"] = H[sh]["report_date"]
        if p.get("depth_out"):
            cur["depth_out_reported"] = fnum(p.get("depth_out"))
            cur["last_sheet"] = sh
            cur["end_date"] = H[sh]["report_date"]
        if p.get("bit_hours"):
            cur["bit_hours_reported"] = fnum(p.get("bit_hours"))
        if p.get("bit_cum_hrs"):
            cur["cum_hours_reported"] = fnum(p.get("bit_cum_hrs"))
        if p.get("bit_dull") and p["bit_dull"].strip().upper() not in ("-", "N/A"):
            cur["dull"] = p["bit_dull"]
        if p.get("bit_cum_drilled"):
            cur["cum_drilled_recorded"] = p.get("bit_cum_drilled")
        for key, pk in (("wob", "wob"), ("rpm", "rpm_surface"), ("torque", "torque"),
                        ("spp", "spp"), ("flow", "pump_output"), ("hsi", "hsi")):
            v = fnum(p.get(pk))
            if v is not None and v > 0:
                cur[key].append(v)
    if cur:
        runs.append(cur)

    # only keep runs that actually span at least one DDR with a depth record
    out = []
    for i, r in enumerate(runs, 1):
        shs = r.pop("sheets")
        pull_depth = None
        if r["depth_out_reported"] is not None:
            pull_depth = r["depth_out_reported"]
        else:
            dmax = None
            for sh in shs:
                dd = fnum(H[sh]["depth24"])
                if dd is not None:
                    dmax = dd
            pull_depth = dmax
        r["depth_out_m"] = pull_depth
        if r["depth_in_m"] is not None and pull_depth is not None:
            r["footage_m"] = round(max(0.0, pull_depth - r["depth_in_m"]), 2)
        else:
            r["footage_m"] = None
        r["rotating_hours"] = round(sum(drill_h[sh] for sh in shs), 1)
        r["drilling_hours_gross"] = round(sum(gross_h[sh] for sh in shs), 1)
        r["npt_hours_in_run"] = round(sum(npt_h[sh] for sh in shs), 1)
        r["ddr_count"] = len(shs)
        r["run_id"] = f"{d['well']}-BIT-{i:02d}"
        r["hours_basis"] = "Sum of code 2-1 Drilling hours over run DDRs"
        r["footage_basis"] = "Depth at pull-out minus depth at run-in (DDR records)"
        r["rop_m_per_h"] = (round(r["footage_m"] / r["rotating_hours"], 3)
                            if r["footage_m"] and r["rotating_hours"] else None)
        r["rop_m_per_h_gross"] = (round(r["footage_m"] / r["drilling_hours_gross"], 3)
                                  if r["footage_m"] and r["drilling_hours_gross"] else None)
        r["status"] = ("Drilled footage" if (r["footage_m"] or 0) > 0
                       else "No footage recorded (trip / re-run / shell record)")
        for k in ("wob", "rpm", "torque", "spp", "flow", "hsi"):
            vals = r.pop(k)
            r[f"{k}_mean"] = round(sum(vals) / len(vals), 2) if vals else None
            r[f"{k}_n"] = len(vals)
        r["depth_in_reported"] = r.pop("bit_hours_reported", None)
        out.append(r)
    # drop empty shells (a bit number that never progressed and has no data)
    out = [r for r in out if r["ddr_count"] or r["footage_m"]]
    for i, r in enumerate(out, 1):
        r["run_id"] = f"{d['well']}-BIT-{i:02d}"
    return out


def param_summary(d, runs):
    """Parameter statistics by hole section from the bit-run register."""
    bysec = defaultdict(lambda: defaultdict(list))
    for r in runs:
        sz = (r["bit_size"] or "").upper().replace(" ", "")
        for k in ("wob", "rpm", "torque", "spp", "flow", "hsi"):
            v = r.get(f"{k}_mean")
            if v:
                bysec[sz][k].append(v)
        if r.get("rop_m_per_h"):
            bysec[sz]["rop"].append(r["rop_m_per_h"])
    rows = []
    for sz, dd in bysec.items():
        row = {"well": d["well"], "bit_size": sz}
        for k in ("wob", "rpm", "torque", "spp", "flow", "hsi", "rop"):
            v = dd.get(k, [])
            row[f"{k}_n"] = len(v)
            row[f"{k}_mean"] = round(sum(v) / len(v), 2) if v else None
            row[f"{k}_min"] = round(min(v), 2) if v else None
            row[f"{k}_max"] = round(max(v), 2) if v else None
        rows.append(row)
    return rows


def mud_summary(d):
    P = defaultdict(list)
    for r in d["mud"]:
        v = fnum(r["value"])
        if v is None:
            continue
        P[r["param"]].append((fnum(r["rig_days"], 0), v, r["hole_size"]))
    rows = []
    for param, vals in P.items():
        nums = [v for _, v, _ in vals]
        rows.append({
            "well": d["well"], "param": param, "n": len(nums),
            "min": round(min(nums), 2), "max": round(max(nums), 2),
            "mean": round(sum(nums) / len(nums), 2),
            "first_rig_day": min(x[0] for x in vals),
            "last_rig_day": max(x[0] for x in vals),
        })
    return rows, P


def formation_tops(d):
    """Latest recorded formation top per formation (final sheet wins)."""
    by = {}
    for r in d["formations"]:
        f = r["formation"].strip()
        if not f or len(f) > 40:
            continue
        rd = fnum(r["rig_days"], 0)
        cur = by.get(f.upper())
        if cur is None or rd >= cur["_rd"]:
            by[f.upper()] = {"formation": f, "top": r["top"], "lithology": r["lithology"],
                             "_rd": rd, "report_date": r["report_date"],
                             "source_sheet": r["source_sheet"]}
    rows = []
    for k, v in by.items():
        v = dict(v)
        v.pop("_rd")
        v["well"] = d["well"]
        rows.append(v)
    return rows


def analyse_trajectory(d):
    """Assess whether the DDR survey block can support a trajectory.

    Evidence tested:
      a) maximum surveyed MD versus the recorded final well depth;
      b) whether the identical station set repeats on the final sheet;
      c) presence of an azimuth column populated with data.
    """
    sv = d["survey"]
    H = d["headers"]
    final_depth = max((fnum(h["depth24"], 0) for h in H), default=0)
    mds = [fnum(r["md"]) for r in sv if fnum(r["md"]) is not None]
    max_md = max(mds) if mds else None
    az_filled = sum(1 for r in sv if fnum(r["az"]) not in (None, 0))
    inc_filled = sum(1 for r in sv if fnum(r["inc"]) is not None)
    uniq = {(r["md"], r["inc"], r["az"], r["tvd"]) for r in sv}
    last_sheets = [h["source_sheet"] for h in H if fnum(h["depth24"], 0) == final_depth][-1:]
    last_stations = sorted({(r["md"], r["inc"], r["tvd"]) for r in sv
                            if r["source_sheet"] in last_sheets})
    verdict = "USABLE"
    reason = ""
    if not mds:
        verdict = "NOT PRESENT"
        reason = "No numerical survey station is recorded in any DDR sheet."
    elif max_md is not None and final_depth and max_md < 0.5 * final_depth:
        verdict = "NOT USABLE - TEMPLATE DATA"
        reason = (f"Deepest recorded survey station is {max_md:g} m MD against a "
                  f"final recorded depth of {final_depth:g} m "
                  f"({100*max_md/final_depth:.0f} % coverage); the same stations "
                  f"repeat unchanged on the final sheet.")
    elif len(uniq) < 5:
        verdict = "NOT USABLE - INSUFFICIENT STATIONS"
        reason = f"Only {len(uniq)} distinct station(s) recorded."
    return {
        "well": d["well"], "n_survey_rows": len(sv), "n_distinct_stations": len(uniq),
        "max_survey_md_m": max_md, "final_well_depth_m": final_depth,
        "coverage_pct": round(100 * max_md / final_depth, 1) if max_md and final_depth else None,
        "stations_with_inclination": inc_filled,
        "stations_with_azimuth": az_filled,
        "unique_stations": "; ".join(f"{a[0]}/{a[1]}/{a[3]}" for a in sorted(uniq)[:8]),
        "verdict": verdict, "reason": reason,
    }


def depth_time(d):
    """Depth-time series. One row per DDR; gaps are marked, never interpolated."""
    H = [h for h in d["headers"] if h["report_date"]]
    H.sort(key=lambda h: (h["report_date"], fnum(h["sheet_index"], 0)))
    if not H:
        return [], []
    spud = parse_date(H[0]["spud_date"])
    series, gaps = [], []
    prev = None
    for h in H:
        dt = parse_date(h["report_date"])
        if dt is None:
            continue
        day = (dt - spud).days + 1 if spud else None
        if prev and (dt - prev).days > 1:
            gaps.append({"well": d["well"], "gap_start": prev.isoformat(),
                         "gap_end": dt.isoformat(), "gap_days": (dt - prev).days - 1})
        prev = dt
        series.append({
            "well": d["well"], "date": h["report_date"], "day": day,
            "rig_days": fnum(h["rig_days"]),
            "depth00": fnum(h["depth00"]), "depth24": fnum(h["depth24"]),
            "hole_size": h["hole_size"], "meterage": fnum(h["meterage"], 0),
            "source_sheet": h["source_sheet"],
        })
    return series, gaps


def main():
    os.makedirs(CALC, exist_ok=True)
    master, sections, phases, codes = [], [], [], []
    npt_all, npt_fam, npt_sec, npt_sum = [], [], [], []
    bit_all, param_all, mud_all, form_all, traj_all = [], [], [], [], []
    dt_all, gap_all = [], []
    per_well = {}
    for well in WELLS:
        print(f"analysing {well} ...", flush=True)
        d = load_well(well)
        m = master_register(d)
        master.append(m)
        secs = section_table(d)
        sections.extend(secs)
        ph, nagg, tot = phase_table(d)
        phases.extend(ph)
        ct, _ = code_table(d)
        codes.extend(ct)
        ev = npt_register(d)
        npt_all.extend(ev)
        fam, sec, summ = npt_summary(d, ev)
        npt_fam.extend(fam); npt_sec.extend(sec); npt_sum.append(summ)
        runs = bit_runs(d)
        bit_all.extend(runs)
        param_all.extend(param_summary(d, runs))
        mudr, _P = mud_summary(d)
        mud_all.extend(mudr)
        form_all.extend(formation_tops(d))
        traj_all.append(analyse_trajectory(d))
        ser, gaps = depth_time(d)
        dt_all.extend(ser); gap_all.extend(gaps)
        per_well[well] = {"master": m, "sections": secs, "phases": ph,
                          "codes": ct, "npt": ev, "npt_sum": summ, "bits": runs,
                          "params": param_all[-len(param_summary(d, runs)):] if runs else [],
                          "mud": mudr, "formations": formation_tops(d),
                          "trajectory": traj_all[-1], "series": ser, "gaps": gaps,
                          "total_op_hours": tot, "npt_by_code": nagg}

    wcsv(f"{CALC}/well_master_register.csv", master)
    wcsv(f"{CALC}/hole_sections.csv", sections)
    wcsv(f"{CALC}/phase_hours.csv", phases)
    wcsv(f"{CALC}/operation_codes.csv", codes)
    wcsv(f"{CALC}/npt_register.csv", npt_all)
    wcsv(f"{CALC}/npt_by_family.csv", npt_fam)
    wcsv(f"{CALC}/npt_by_section.csv", npt_sec)
    wcsv(f"{CALC}/npt_summary.csv", npt_sum)
    wcsv(f"{CALC}/bit_run_register.csv", bit_all)
    wcsv(f"{CALC}/drilling_parameters.csv", param_all)
    wcsv(f"{CALC}/mud_summary.csv", mud_all)
    wcsv(f"{CALC}/formation_tops.csv", form_all)
    wcsv(f"{CALC}/trajectory_assessment.csv", traj_all)
    wcsv(f"{CALC}/depth_time_series.csv", dt_all)
    wcsv(f"{CALC}/reporting_gaps.csv", gap_all)

    # ---------- comparison matrix (one row per well) ----------
    comp = []
    for m in master:
        w = m["well"]
        pw = per_well[w]
        nsum = pw["npt_sum"]
        s = {"well": w,
             "planned_td_m": m["planned_td_m"], "final_depth_m": m["final_depth_m"],
             "plan_duration_d": m["plan_duration_d"],
             "actual_ddrs": m["ddr_count"], "calendar_days": m["calendar_days_span"],
             "total_op_hours": m["total_op_hours"],
             "npt_hours": nsum["npt_hours"], "npt_pct": nsum["npt_pct"],
             "npt_events": nsum["event_count"],
             "drilling_hours": next((p["hours_total"] for p in pw["phases"] if p["phase"] == "Drilling"), 0),
             "casing_hours": next((p["hours_total"] for p in pw["phases"] if p["phase"] == "Casing & Cementing"), 0),
             "completion_hours": next((p["hours_total"] for p in pw["phases"] if p["phase"] == "Completion & Intervention"), 0),
             "testing_hours": next((p["hours_total"] for p in pw["phases"] if p["phase"] == "Testing & Stimulation"), 0),
             "hole_problem_hours": next((p["hours_total"] for p in pw["phases"] if p["phase"] == "Hole Problem"), 0),
             "waiting_hours": next((p["hours_total"] for p in pw["phases"] if p["phase"] == "Waiting / Standby"), 0),
             "n_sections": len([x for x in pw["sections"] if not x["is_completion"]]),
             "n_bit_runs": len(pw["bits"]),
             }
        # overall ROP: drilled depth / drilling+connection time
        drill_depth = (m["final_depth_m"] or 0)
        net_drill_codes = {"2-1", "2-2", "4-3", "4-6", "4-7"}
        net_h = sum(fnum(o["hrs"], 0) for o in d_ops_cache[w] if o["code"] in net_drill_codes)
        rot_h = sum(fnum(o["hrs"], 0) for o in d_ops_cache[w] if o["code"] == "2-1")
        s["net_drilling_hours_2_1"] = round(rot_h, 1)
        s["gross_drilling_hours"] = round(net_h, 1)
        s["rop_m_per_day_overall"] = round(drill_depth / (m["calendar_days_span"] or 1), 2)
        s["rop_m_per_h_drilling"] = round(drill_depth / rot_h, 2) if rot_h else None
        s["rop_m_per_h_gross"] = round(drill_depth / net_h, 2) if net_h else None
        comp.append(s)
    wcsv(f"{CALC}/comparison_matrix.csv", comp)
    print("\nWritten to", CALC)


# cache of operations for the ROP loop
d_ops_cache = {}

if __name__ == "__main__":
    # populate cache first
    for _w in WELLS:
        d_ops_cache[_w] = rcsv(f"{DAT}/{_w}_operations.csv")
    main()
