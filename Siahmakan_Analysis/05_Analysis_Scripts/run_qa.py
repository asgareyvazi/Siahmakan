"""Quality-assurance checks on the extracted data and derived calculations.

Every check writes a PASS / WARN / FAIL line with the numbers that were
compared, so the QA report is evidence, not a claim.
"""
import csv
import os
from collections import Counter, defaultdict

BASE = "Siahmakan_Analysis"
DAT = f"{BASE}/04_Engineering_Datasets"
CALC = f"{DAT}/Calculations"
QA = f"{BASE}/06_QA_Reports"
WELLS = ["SI-006", "SI-007", "SI-008", "SI-009"]


def rcsv(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def f(v, d=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


results = []


def add(area, check, status, detail):
    results.append({"area": area, "check": check, "status": status, "detail": detail})


def check_dates():
    for w in WELLS:
        H = rcsv(f"{DAT}/{w}_headers.csv")
        bad = [h for h in H if not h["report_date"]]
        derived = [h for h in H if h["date_basis"] != "RECORDED"]
        dup = Counter(h["report_date"] for h in H if h["report_date"])
        dups = {k: v for k, v in dup.items() if v > 1}
        rd = [f(h["rig_days"]) for h in H if f(h["rig_days"]) is not None]
        rig_uniq = len(set(rd))
        add("Dates", f"{w}: all report dates resolved",
            "PASS" if not bad else "FAIL",
            f"{len(H)} DDRs, {len(bad)} unresolved, {len(derived)} derived from rig-day sequence.")
        add("Dates", f"{w}: duplicate reporting dates",
            "WARN" if dups else "PASS",
            f"{len(dups)} duplicated date(s): " + ", ".join(f"{k} x{v}" for k, v in dups.items())
            if dups else "No duplicated report date.")
        add("Dates", f"{w}: rig-day continuity",
            "PASS" if rig_uniq >= len(H) - 2 else "WARN",
            f"Rig days {min(rd):g}-{max(rd):g}, {rig_uniq} unique among {len(H)} DDRs.")


def check_ops():
    for w in WELLS:
        ops = rcsv(f"{DAT}/{w}_operations.csv")
        H = rcsv(f"{DAT}/{w}_headers.csv")
        per = defaultdict(float)
        for o in ops:
            per[o["source_sheet"]] += f(o["hrs"], 0)
        out = {k: v for k, v in per.items() if not (23.0 <= v <= 25.0)}
        add("Operations", f"{w}: daily hours balance to 24 h",
            "PASS" if len(out) <= 0.02 * len(H) else "WARN",
            f"{len(per)} sheets with operations; {len(out)} outside 23-25 h "
            f"({100*len(out)/max(1,len(per)):.1f} %).")
        bad_codes = [o for o in ops if o["code"] and not __import__("re").match(r"^\d{1,2}-\d{1,2}$", o["code"])]
        add("Operations", f"{w}: operation codes valid",
            "PASS" if not bad_codes else "WARN",
            f"{len(ops)} operation rows, {len(bad_codes)} with a non-standard code.")
        typed = sum(1 for o in ops if o["type"] in ("P", "N", "U"))
        add("Operations", f"{w}: P/N/U classification coverage",
            "PASS" if typed / max(1, len(ops)) > 0.98 else "WARN",
            f"{typed}/{len(ops)} rows typed ({100*typed/max(1,len(ops)):.1f} %).")


def check_depth():
    for w in WELLS:
        H = rcsv(f"{DAT}/{w}_headers.csv")
        H = [h for h in H if h["report_date"]]
        H.sort(key=lambda h: (f(h["rig_days"], 0), h["report_date"]))
        drops = []
        for i in range(1, len(H)):
            a, b = f(H[i-1]["depth24"]), f(H[i]["depth24"])
            if a is not None and b is not None and b < a - 0.05:
                drops.append((H[i]["source_sheet"], a, b))
        neg = [h for h in H if (f(h["depth24"], 0) or 0) < (f(h["depth00"], 0) or 0) - 0.05]
        add("Depth", f"{w}: depth sequence continuity",
            "PASS" if len(drops) <= 3 else "WARN",
            f"{len(drops)} depth decrease(s) across {len(H)} DDRs"
            + ("".join(f"; {s}: {a:g}->{b:g} m" for s, a, b in drops[:3]) if drops else "."))
        add("Depth", f"{w}: 24:00 depth not below 00:00 depth",
            "PASS" if not neg else "WARN",
            f"{len(neg)} DDRs where depth at 24:00 is below depth at 00:00.")


def check_calc():
    comp = rcsv(f"{CALC}/comparison_matrix.csv")
    for r in comp:
        tot = f(r["total_op_hours"], 0)
        npt = f(r["npt_hours"], 0)
        pct = f(r["npt_pct"], 0)
        calc = 100 * npt / tot if tot else 0
        add("Calculations", f"{r['well']}: NPT percentage recomputed",
            "PASS" if abs(calc - pct) < 0.05 else "FAIL",
            f"stored {pct}%, recomputed {calc:.2f}% ({npt:g} h of {tot:g} h).")
        d = f(r["final_depth_m"], 0)
        rop = f(r["rop_m_per_h_drilling"], 0)
        h = f(r["net_drilling_hours_2_1"], 0)
        add("Calculations", f"{r['well']}: ROP recomputed",
            "PASS" if h and abs(d / h - rop) < 0.02 else "FAIL",
            f"{d:g} m / {h:g} h = {d/h:.2f} m/h (stored {rop}).")
        ph = [p for p in rcsv(f"{CALC}/phase_hours.csv") if p["well"] == r["well"]]
        s = sum(f(p["hours_total"], 0) for p in ph)
        add("Calculations", f"{r['well']}: phase hours sum to total",
            "PASS" if abs(s - tot) < 1.0 else "FAIL",
            f"phases sum {s:.1f} h vs total {tot:g} h.")
    # section interval consistency
    secs = rcsv(f"{CALC}/hole_sections.csv")
    for w in WELLS:
        ws = [s for s in secs if s["well"] == w and s["is_completion"] != "True"]
        tot = sum(f(s["interval_m"], 0) for s in ws)
        final = max(f(s["end_depth"], 0) for s in ws) if ws else 0
        first = f(ws[0]["start_depth"], 0) if ws else 0
        add("Calculations", f"{w}: section intervals close on final depth",
            "PASS" if abs(tot - (final - first)) < 1.0 else "WARN",
            f"sum of section intervals {tot:.1f} m vs {final-first:.1f} m "
            f"({len(ws)} sections).")


def check_bits():
    runs = rcsv(f"{CALC}/bit_run_register.csv")
    for w in WELLS:
        rs = [r for r in runs if r["well"] == w]
        withf = [r for r in rs if f(r["footage_m"], 0) > 0]
        bad = [r for r in withf if f(r["footage_m"], 0) > 0 and (f(r["rotating_hours"], 0) or 0) <= 0]
        neg = [r for r in rs if f(r["footage_m"], 0) is not None and f(r["footage_m"], 0) < 0]
        add("Bit runs", f"{w}: bit runs identified",
            "PASS", f"{len(rs)} runs, {len(withf)} with footage, "
                    f"{len(withf) - len(bad)} with both footage and rotating hours.")
        add("Bit runs", f"{w}: no negative footage",
            "PASS" if not neg else "FAIL",
            f"{len(neg)} runs with negative footage.")
        add("Bit runs", f"{w}: footage with zero hours",
            "WARN" if bad else "PASS",
            f"{len(bad)} run(s) carry footage but no recorded 2-1 drilling hours "
            f"(rate not reported for these).")


def check_survey():
    for r in rcsv(f"{CALC}/trajectory_assessment.csv"):
        add("Survey", f"{r['well']}: trajectory data",
            "N/A" if r["verdict"].startswith("NOT") else "PASS",
            f"{r['verdict']}. {r['reason']}".strip())


def check_reconcile():
    comp = {r["well"]: r for r in rcsv(f"{CALC}/comparison_matrix.csv")}
    master = {r["well"]: r for r in rcsv(f"{CALC}/well_master_register.csv")}
    npt = {r["well"]: r for r in rcsv(f"{CALC}/npt_summary.csv")}
    reg = {r["well"]: r for r in rcsv(f"{BASE}/00_Project_Overview/well_documentation_register.csv")}
    for w in WELLS:
        a = f(comp[w]["final_depth_m"])
        b = f(master[w]["final_depth_m"])
        add("Reconciliation", f"{w}: final depth agrees across datasets",
            "PASS" if a == b else "FAIL", f"comparison {a:g} m vs master {b:g} m.")
        a = f(comp[w]["npt_hours"])
        b = f(npt[w]["npt_hours"])
        add("Reconciliation", f"{w}: NPT hours agree across datasets",
            "PASS" if abs(a - b) < 0.5 else "FAIL", f"comparison {a:g} h vs summary {b:g} h.")
        a = f(master[w]["ddr_count"])
        b = f(reg[w]["ddr_sheets"])
        add("Reconciliation", f"{w}: DDR count agrees",
            "PASS" if a == b else "FAIL", f"master {a:g} vs register {b:g}.")


def write_reports():
    os.makedirs(QA, exist_ok=True)
    with open(f"{QA}/qa_checks.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["area", "check", "status", "detail"])
        w.writeheader()
        w.writerows(results)
    c = Counter(r["status"] for r in results)
    lines = ["# Quality-assurance report — Siah Makan DDR analysis", "",
             f"Checks executed: {len(results)}. "
             f"PASS {c.get('PASS',0)}, WARN {c.get('WARN',0)}, "
             f"FAIL {c.get('FAIL',0)}, N/A {c.get('N/A',0)}.", "",
             "| Area | Check | Status | Detail |", "|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['area']} | {r['check']} | **{r['status']}** | {r['detail']} |")
    with open(f"{QA}/QA_Report.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"{len(results)} checks: " + ", ".join(f"{k}={v}" for k, v in c.items()))
    fails = [r for r in results if r["status"] == "FAIL"]
    for r in fails:
        print("  FAIL:", r["check"], "|", r["detail"])


if __name__ == "__main__":
    check_dates()
    check_ops()
    check_depth()
    check_calc()
    check_bits()
    check_survey()
    check_reconcile()
    write_reports()
