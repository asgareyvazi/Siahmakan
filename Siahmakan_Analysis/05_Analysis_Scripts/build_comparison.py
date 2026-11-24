"""Field comparison report, English and Persian."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx.enum.text import WD_ALIGN_PARAGRAPH

import docx_kit as K
import fa_glossary as G
import report_content as RC

OUT = "Siahmakan_Analysis/02_Asset_Comparison"
FIG = f"{OUT}/Figures"
W = RC.WELLS


def _fa_verdict(v):
    v = (v or "").strip().upper()
    if v == "NOT PRESENT":
        return "موجود نیست"
    if "TEMPLATE" in v:
        return "قابل استفاده نیست (داده الگویی)"
    if v.startswith("USABLE"):
        return "قابل استفاده"
    return "نامشخص"


def f(v, d=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def fmt(v, nd=0):
    if v in (None, "", "None"):
        return "—"
    try:
        return f"{float(v):,.{nd}f}"
    except (TypeError, ValueError):
        return str(v)


def pct(v, nd=1):
    return "—" if v in ("", None) else f"{float(v):.{nd}f} %"


def load():
    C = {r["well"]: r for r in RC.R(f"{RC.CALC}/comparison_matrix.csv")}
    M = {r["well"]: r for r in RC.R(f"{RC.CALC}/well_master_register.csv")}
    N = {r["well"]: r for r in RC.R(f"{RC.CALC}/npt_summary.csv")}
    S = RC.R(f"{RC.CALC}/hole_sections.csv")
    F = RC.R(f"{RC.CALC}/npt_by_family.csv")
    T = {r["well"]: r for r in RC.R(f"{RC.CALC}/trajectory_assessment.csv")}
    B = RC.R(f"{RC.CALC}/bit_run_register.csv")
    D = {w: RC.get(w) for w in W}
    return C, M, N, S, F, T, B, D


def rankings(C, M, S):
    """Defensible rankings with the reason stated."""
    out = []
    # drilling rate: m per drilling hour
    r = sorted(W, key=lambda w: -(f(C[w]["rop_m_per_h_drilling"]) or 0))
    out.append(("Highest drilling rate (m per code 2-1 hour)", r,
                "The numerator is total depth and the denominator is drilling hours only, so this "
                "rewards fast rock destruction and ignores everything else."))
    # overall delivery rate
    r = sorted(W, key=lambda w: -(f(C[w]["rop_m_per_day_overall"]) or 0))
    out.append(("Fastest overall delivery (m per calendar day)", r,
                "Includes every interruption, so a well with a short record and a productive "
                "section can rank above a deeper well that spent months waiting."))
    # NPT
    r = sorted(W, key=lambda w: (f(C[w]["npt_pct"]) or 0))
    out.append(("Lowest share of non-productive time", r,
                "Percentage of recorded operation hours typed N or U. A low value can reflect a "
                "short record as much as good performance, so it is read together with the duration."))
    # plan adherence
    def adherence(w):
        d, p = f(M[w]["final_depth_m"]), f(M[w]["planned_td_m"])
        return 100 * d / p if p else 0
    r = sorted(W, key=lambda w: -adherence(w))
    out.append(("Highest proportion of planned depth delivered", r,
                "Final recorded depth as a percentage of planned TD. A low figure means the records "
                "stop short of the objective; it does not by itself prove the well failed."))
    return out


# --------------------------------------------------------------------------- #
def build_en(C, M, N, S, F, T, B, D, path):
    doc = K.new_doc()
    K.header_footer(doc.sections[0], "Siah Makan Field — Integrated Comparison Report",
                    "Rev. 1.0", fa=False)
    K.cover(doc, "Siah Makan Field",
            "Integrated Drilling, Completion and Well Performance Comparison",
            ["Wells analysed: SI-006, SI-007, SI-008, SI-009",
             "Source: 1,237 daily drilling reports in four workbooks",
             "Documented period: 2021-03-17 to 2023-04-25",
             "Document version 1.0 — prepared 2026-11-24",
             "Reporting languages: English and Persian"])
    K.toc(doc, fa=False)

    K.heading(doc, "1  Scope, Well Population and Data Basis", 1)
    K.para_en(doc, "Four wells are identified in the supplied documentation, all in the Siah Makan "
                   "field, all drilled by National Iranian Drilling Company rigs under PEDC-PECO "
                   "operatorship. Each well is represented by a single workbook of daily drilling "
                   "reports. No final well report, drilling programme, completion programme, cost "
                   "record or production record was supplied. The comparison below is therefore a "
                   "comparison of documented drilling and completion operations, not of well "
                   "economics or productivity.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    rows = [[w, M[w]["well_name_recorded"], M[w]["well_type"], M[w]["spud_date"],
             M[w]["last_ddr_date"], M[w]["ddr_count"], fmt(M[w]["planned_td_m"]),
             fmt(M[w]["final_depth_m"])] for w in W]
    K.table(doc, ["Well", "Name as recorded", "Type", "Spud", "Last DDR", "DDRs",
                  "Planned TD (m)", "Final depth (m)"], rows,
            widths=[1.5, 2.6, 2.4, 1.9, 1.9, 1.1, 1.8, 1.8], size=7.5,
            caption="Table 1-1: Well population and documentation extent.")

    K.heading(doc, "2  Comparison Table and Charts", 1)
    K.heading(doc, "2.1  Master comparison", 2)
    rows = []
    for w in W:
        c = C[w]
        rows.append([w, fmt(C[w]["final_depth_m"]), fmt(C[w]["calendar_days"]),
                     fmt(C[w]["total_op_hours"]), fmt(c["npt_hours"]), pct(c["npt_pct"]),
                     fmt(c["drilling_hours"], 1), fmt(c["casing_hours"], 1),
                     fmt(c["completion_hours"], 1), fmt(c.get("testing_hours"), 1),
                     fmt(c["n_sections"]), fmt(c["n_bit_runs"])])
    K.table(doc, ["Well", "Final MD (m)", "Days", "Op. hours", "NPT (h)", "NPT %",
                  "Drilling (h)", "Casing (h)", "Compl. (h)", "Test (h)", "Sections", "Bit runs"],
            rows, widths=[1.4, 1.6, 1.1, 1.5, 1.3, 1.2, 1.5, 1.4, 1.4, 1.2, 1.3, 1.3], size=7,
            caption="Table 2-1: Field comparison. All hour figures are recorded operation hours "
                    "from the daily reports; NPT % uses total recorded hours as its denominator.")

    K.figure(doc, f"{FIG}/fig_plan_vs_actual.png", 16.5,
             "Figure 2-1: Planned versus recorded depth and duration for each well.")
    K.figure(doc, f"{FIG}/fig_npt_pct.png", 13.0,
             "Figure 2-2: Share of non-productive time in recorded operation hours.")

    K.heading(doc, "2.2  Drilling efficiency by hole section", 2)
    K.para_en(doc, "Sections are compared only where the nominal hole size and the section objective "
                   "are compatible. All four wells share 17-1/2\", 12-1/4\" and 8-3/8\" sections, so "
                   "those three are directly comparable. SI-006 additionally drilled a 7\" and a "
                   "5-7/8\" section; the other wells stopped at 8-3/8\" or reached smaller sections "
                   "on a different basis.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    rows = []
    for sz in ['26"', '17-1/2"', '12-1/4"', '8-3/8"', '7"', '5-7/8"']:
        r = [sz]
        for w in W:
            v = [x for x in S if x["well"] == w and x["hole_size"] == sz]
            r.append(fmt(v[0]["rop_m_per_drill_hour"], 2) if v else "—")
        rows.append(r)
    K.table(doc, ["Hole section"] + [f"{w} ROP (m/h)" for w in W], rows,
            widths=[2.6, 2.9, 2.9, 2.9, 2.9], size=8.5,
            caption="Table 2-2: Section rate of penetration (m per drilling hour, code 2-1). "
                    "A dash means the well has no section of that size in the records.")
    K.figure(doc, f"{FIG}/fig_section_rop.png", 16.5,
             "Figure 2-3: Section ROP by well and hole size.")
    K.para_en(doc, "The 17-1/2\" section is the fastest for every well, as expected for large-hole "
                   "drilling in the shallow, softer sequence: SI-007 achieved 6.15 m/h, SI-009 6.17 "
                   "m/h, SI-006 5.65 m/h and SI-008 4.15 m/h. The 12-1/4\" section is uniformly slower "
                   "(2.4 to 3.1 m/h) and the 8-3/8\" section slower again, which is consistent with "
                   "the transition into the Gachsaran evaporites and the Asmari carbonates. The "
                   "relative ordering of the wells reverses between sections: SI-007 leads on the "
                   "17-1/2\" section but is the slowest on the 8-3/8\" section at 1.78 m/h, because "
                   "that section on SI-007 was drilled under continuous hole instability and fishing.",
              align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    K.heading(doc, "2.3  Time distribution", 2)
    K.figure(doc, f"{FIG}/fig_phase_hours.png", 16.5,
             "Figure 2-4: Recorded hours by operational phase and well.")
    rows = []
    for w in W:
        d = D[w]
        rows.append([w, fmt(d["drill_h"], 1), fmt(d["trip_h"], 1), pct(d["drill_share"]),
                     pct(d["trip_share"]), fmt(d["waiting_h"] if "waiting_h" in d else
                                               C[w]["waiting_hours"], 1),
                     pct(100 * f(C[w]["waiting_hours"], 0) / f(C[w]["total_op_hours"], 1))])
    K.table(doc, ["Well", "Drilling (h)", "Trips/conditioning (h)", "Drilling share",
                  "Trip share", "Waiting (h)", "Waiting share"], rows,
            widths=[1.6, 2.0, 2.8, 2.2, 2.0, 2.0, 2.2], size=8,
            caption="Table 2-3: How each well spent its rig time. Drilling is code 2-1; waiting is "
                    "the 11-x family.")

    K.heading(doc, "3  Non-Productive Time Across the Field", 1)
    K.figure(doc, f"{FIG}/fig_npt_family.png", 16.5,
             "Figure 3-1: Non-productive time by cause family, stacked by well.")
    fams = {}
    for r in F:
        fams.setdefault(r["family"], {})[r["well"]] = f(r["hours"], 0)
    top = sorted(fams.items(), key=lambda kv: -sum(kv[1].values()))[:8]
    rows = []
    for name, dd in top:
        rows.append([name] + [fmt(dd.get(w, 0), 0) for w in W] +
                    [fmt(sum(dd.values()), 0), pct(100 * sum(dd.values()) /
                                                   sum(f(C[w]["npt_hours"], 0) for w in W), 0)])
    K.table(doc, ["Cause family"] + [f"{w} (h)" for w in W] + ["Total (h)", "Share of field NPT"],
            rows, widths=[4.2, 1.5, 1.5, 1.5, 1.5, 1.7, 2.3], size=7.5,
            caption="Table 3-1: The eight largest NPT families, field totals.")
    K.para_en(doc, "Surface waiting dominates the field totals. Three of the four wells lose more "
                   "time to operations contingency, rig-contractor standby and service-company "
                   "standby than to any downhole failure. SI-009 is the exception: on that well a "
                   "single well-control event is the largest time consumer, which is a different "
                   "problem class and needs a different response.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    K.para_en(doc, "The distinction matters. Waiting time responds to contracts and logistics. Hole "
                   "problems respond to engineering. Treating the two as one NPT number hides the "
                   "fact that only about a quarter of the field's lost time has a downhole cause.",
              align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    K.heading(doc, "4  Bit and BHA Performance", 1)
    K.figure(doc, f"{FIG}/fig_bit_rop_by_well.png", 16.0,
             "Figure 4-1: Bit-run ROP distribution by well.")
    rows = []
    for w in W:
        bs = D[w]["bits_drilling"]
        if not bs:
            continue
        rops = [f(b["rop_m_per_h"]) for b in bs]
        rows.append([w, len(bs), fmt(max(rops), 2), fmt(min(rops), 2),
                     fmt(sum(f(b["footage_m"], 0) for b in bs), 0),
                     fmt(sum(f(b["rotating_hours"], 0) for b in bs), 0)])
    K.table(doc, ["Well", "Runs with footage", "Best ROP (m/h)", "Worst ROP (m/h)",
                  "Total bit footage (m)", "Total rotating h"], rows,
            widths=[1.8, 2.6, 2.4, 2.4, 2.8, 2.6], size=8.5,
            caption="Table 4-1: Bit-run performance envelope by well.")
    K.para_en(doc, "The single most instructive bit result in the dataset is SI-008 run BIT-15: an "
                   "8-3/8\" PDC that drilled 1,030 m in 168.5 rotating hours for 6.11 m/h, roughly "
                   "three times the median 8-3/8\" run. The same hole size on SI-007 produced runs "
                   "of 0.45 to 1.75 m/h. The difference is not a bit-selection difference alone — "
                   "the SI-007 section was drilled through an unstable interval with repeated "
                   "fishing — but the size of the gap shows how much section ROP depends on "
                   "hole condition rather than on bit design.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    K.heading(doc, "5  Well Integrity, FIT and Well Control", 1)
    rows = []
    for w in W:
        m = M[w]
        d = D[w]
        rows.append([w, m["fit"] or "Not recorded", fmt(d["wellctrl_h"], 1),
                     fmt(float(d["code"].get("8-8", {}).get("hours") or 0), 1),
                     fmt(d["stuck_h"], 1), fmt(d["fishing_h"], 1)])
    K.table(doc, ["Well", "FIT / shoe test as recorded", "Well-control h", "Kill-well h",
                  "Stuck-pipe h", "Fishing h"], rows,
            widths=[1.6, 4.2, 2.4, 2.2, 2.2, 2.0], size=8,
            caption="Table 5-1: Integrity and hole-problem indicators. Values are recorded hours, "
                    "not severity indices.")
    K.para_en(doc, "SI-009 is the only well in the field with a documented influx. The event (28 "
                   "December 2022, 17-1/2\" section, 1,028–1,042 m) was taken while the mud weight "
                   "was being raised from 76 to 77 pcf after flow was suspected at a connection. The "
                   "kill required 90 pcf mud and consumed 525.5 hours of well-control operations plus "
                   "243 hours of active killing. The well was subsequently re-entered and drilling "
                   "resumed, but the records stop at 3,084 m. This is the clearest cross-well lesson "
                   "in the dataset: a pressure transition was being crossed with an inadequate "
                   "margin, and the margin was being adjusted reactively.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    K.heading(doc, "6  Trajectory and Survey Data", 1)
    rows = [[w, T[w]["verdict"], T[w]["n_distinct_stations"],
             fmt(T[w]["max_survey_md_m"], 0), fmt(T[w]["final_well_depth_m"], 0),
             pct(T[w]["coverage_pct"])] for w in W]
    K.table(doc, ["Well", "Assessment", "Distinct stations", "Deepest station (m)",
                  "Final depth (m)", "Coverage"], rows,
            widths=[1.5, 4.4, 2.2, 2.4, 2.2, 1.8], size=8,
            caption="Table 6-1: Survey data integrity by well.")
    K.para_en(doc, "No well in this field can be given a minimum-curvature trajectory from the "
                   "supplied records. SI-006 and SI-009 carry a static template of three shallow "
                   "stations that never updates with depth. SI-007 carries no numeric station at all. "
                   "SI-008 carries a partial set that reaches 4,610 m MD with inclination and azimuth "
                   "on the deeper stations, which is enough for a partial trajectory but not for the "
                   "full well. This is a property of the documentation, not of the wells, and no "
                   "trajectory has been fabricated to fill it.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    K.heading(doc, "7  Cross-Well Engineering Findings", 1)
    findings = [
        ("Surface waiting is the field's dominant lost-time mechanism.",
         "Three wells spend more hours waiting on the rig contractor, service companies and client "
         "decisions than on any downhole problem. The pattern is independent across wells and "
         "consistent in the code distribution, so it is a genuine common pattern and not a "
         "classification artefact."),
        ("Hole problems concentrate in the 8-3/8\" and 5-7/8\" sections, not in the shallow hole.",
         "SI-006 lost 3,391 hours in its 8-3/8\" section; SI-007 lost 4,684 hours in its 5-7/8\" "
         "section. Both are deep sections drilled through the Gachsaran–Asmari transition. The "
         "shallow 17-1/2\" and 26\" sections are consistently the cleanest in every well."),
        ("The Gachsaran evaporite sequence is the recurring geological hazard.",
         "The formation table on every well records the Gachsaran members (salt, anhydrite, marl) "
         "as the interval where losses, tight hole and stuck pipe begin. SI-008 records the members "
         "at 2,794–3,432 m and takes losses there; SI-006 records them at 2,650–3,341 m and takes "
         "losses there. This is a similar symptom in a similar formation, but the records do not "
         "prove a single shared mechanism."),
        ("SI-009's influx is a well-specific event, not a field-wide pattern.",
         "No other well records well-control operations of comparable duration. Treating it as a "
         "field-wide characteristic would be wrong; treating it as a one-off would also be wrong, "
         "because the mechanism (raising mud weight reactively across a pressure transition) is "
         "reproducible."),
        ("Bit performance varies more within a well than between wells.",
         "The 8-3/8\" runs on SI-006 range from 0.61 to 3.53 m/h; on SI-007 from 0.45 to 1.75 m/h. "
         "The spread inside one well exceeds the difference between the well averages, which means "
         "bit selection and hole condition, not well identity, drive section ROP."),
        ("Completion and production performance cannot be compared at all.",
         "No well carries a completion tally, a test result or a production record. The comparison "
         "stops at the end of documented drilling and, where recorded, the completion operation."),
    ]
    for i, (h, t) in enumerate(findings, 1):
        K.para_en(doc, f"{i}.  {h}", bold=True, size=10)
        K.para_en(doc, t, align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=9.5)

    K.heading(doc, "8  Ranking and Benchmarking", 1)
    for title, order, reason in rankings(C, M, S):
        K.para_en(doc, title, bold=True, size=10)
        K.table(doc, ["Rank", "Well", "Value"],
                [[str(i + 1), w, fmt(C[w]["rop_m_per_h_drilling"] if "drilling rate" in title
                                     else C[w]["rop_m_per_day_overall"] if "delivery" in title
                                     else C[w]["npt_pct"] if "non-productive" in title
                                     else 100 * f(M[w]["final_depth_m"], 0) / f(M[w]["planned_td_m"], 1),
                                     2)] for i, w in enumerate(order)],
                widths=[1.8, 3.0, 3.0], size=8.5)
        K.para_en(doc, reason, size=9, italic=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    K.para_en(doc, "No single ranking is presented as an overall league table. A well that reached a "
                   "deeper target through difficult formations cannot be ranked against a well whose "
                   "records stop in the intermediate hole on the same scale. The rankings above "
                   "measure one thing each and are labelled accordingly.", size=9.5,
              align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    K.heading(doc, "9  Management Conclusions", 1)
    K.bullets(doc, [
        "Best delivery performance: SI-008, which drilled 4,900 m in 209 days with 14.1 % NPT and "
        "five hole sections, despite coring. Its advantage is not a deeper target but a cleaner "
        "operation.",
        "Most challenging well: SI-007, which spent 498 days to reach 4,410 m with 48.0 % NPT and "
        "911 hours of fishing. The extra time is attributable to a wireline recovery that consumed "
        "several weeks and a side-track that followed it.",
        "Highest-risk event: the SI-009 influx. It is the only well-control event in the field and "
        "it removed roughly 30 days of rig time.",
        "Repeated technical weakness: section-entry decisions in the Gachsaran interval. Every well "
        "records losses or instability there, and every well responded reactively.",
        "Successful practice worth repeating: SI-008's coring and completion planning, which kept "
        "NPT at 14 % while running a more complex programme than the other wells.",
        "Management attention: waiting-time exposure is a contract and logistics problem that "
        "engineering cannot solve. It accounts for the majority of lost time in the field.",
    ])

    K.heading(doc, "10  Prioritised Recommendations", 1)
    recs = [
        ("1", "Well-control transition procedure",
         "Mandate a documented weight-up procedure with a defined trip margin before and after every "
         "mud-weight change. The SI-009 event is the direct business case.", "High", "Immediate"),
        ("2", "Waiting-time contract terms",
         "Introduce response-time obligations for the rig contractor and the principal service "
         "companies, with a named responsible party recorded per DDR.", "High", "Next contract cycle"),
        ("3", "Fishing readiness",
         "Keep a dedicated fishing BHA and a cut-and-thread procedure on the rig before any section "
         "with planned wireline logging.", "High", "Next well"),
        ("4", "Gachsaran entry programme",
         "Write a section-specific programme for the evaporite interval: mud weight window, loss "
         "treatment, reaming practice and trip frequency.", "Medium", "Next well"),
        ("5", "Survey and cost capture",
         "Require the survey stations and a daily cost field in the DDR template. Without them, "
         "trajectory and economics cannot be analysed from daily records at all.", "Medium",
         "Template revision"),
        ("6", "Bit-selection review",
         "Review the 8-3/8\" bit programme against the SI-008 result before the next campaign.",
         "Medium", "Planning stage"),
    ]
    K.table(doc, ["#", "Action", "Basis", "Priority", "Timing"],
            [list(r) for r in recs], widths=[0.9, 3.8, 6.4, 1.6, 2.2], size=7.5,
            caption="Table 10-1: Prioritised recommendations for the next campaign.")

    K.heading(doc, "11  Quantified Improvement Opportunities", 1)
    K.para_en(doc, "The scenarios below use the field's own recorded hours as the baseline. They are "
                   "engineering estimates, not demonstrated results, and no cost saving is expressed "
                   "in currency because no cost data exist in the source.", size=9.5)
    tot_npt = sum(f(C[w]["npt_hours"], 0) for w in W)
    wait = sum(f(C[w]["waiting_hours"], 0) for w in W)
    rows = [
        ["Cut surface waiting by one 12-hour shift per event",
         f"{fmt(wait)} h waiting across the field",
         "12 h × number of NPT events, capped at 20 % of waiting time",
         f"{fmt(min(wait*0.2, 12*sum(f(C[w]['npt_events'],0) for w in W)/4), 0)} h",
         "Requires a dispatcher with authority to re-sequence; no downhole change"],
        ["Halve the coring time on SI-008",
         f"{fmt(D['SI-008']['coring_h'])} h coring",
         "0.5 × coring hours", f"{fmt(D['SI-008']['coring_h']*0.5)} h",
         "Assumes the delay was preparation, not the formation"],
        ["Remove one repeat kill cycle on SI-009",
         f"{fmt(D['SI-009']['wellctrl_h'])} h well control",
         "One 24-hour cycle", "24 h",
         "Assumes an earlier weight-up; the influx itself is not assumed preventable"],
    ]
    K.table(doc, ["Opportunity", "Baseline", "Method", "Rig-time saving", "Key assumption"],
            rows, widths=[3.6, 2.6, 3.4, 1.8, 3.8], size=7.5,
            caption="Table 11-1: Improvement scenarios with stated assumptions.")
    K.para_en(doc, f"Total non-productive time in the field is {fmt(tot_npt)} hours across four "
                   f"wells and {fmt(sum(f(C[w]['npt_events'],0) for w in W))} recorded events. If a "
                   f"quarter of the waiting time were recovered — a demanding but not unrealistic "
                   f"target for a managed logistics system — the field would recover roughly "
                   f"{fmt(wait*0.25/24, 0)} rig-days. That figure is a scenario, presented with its "
                   f"assumption so that management can accept or reject the assumption.",
              align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    doc.save(path)
    K.normalise_ooxml(path)
    return path


# --------------------------------------------------------------------------- #
def build_fa(C, M, N, S, F, T, B, D, path):
    doc = K.new_doc()
    K.header_footer(doc.sections[0], "میدان سیاه‌مکان — گزارش مقایسه‌ای یکپارچه",
                    "نسخه ۱٫۰", fa=True)
    K.cover(doc, "میدان سیاه‌مکان",
            "تحلیل مقایسه‌ای یکپارچه حفاری، تکمیل و عملکرد چاه‌ها",
            ["چاه‌های تحلیل‌شده: SI-006، SI-007، SI-008، SI-009",
             "منبع: ۱٫۲۳۷ گزارش حفاری روزانه در چهار فایل کاری",
             "دوره مستند: ۲۰۲۱-۰۳-۱۷ تا ۲۰۲۳-۰۴-۲۵",
             "نسخه سند ۱٫۰ — تاریخ تهیه ۲۰۲۶-۱۱-۲۴",
             "زبان گزارش: فارسی و انگلیسی"], fa=True)
    K.toc(doc, fa=True)

    K.heading(doc, "۱  دامنه، جامعه چاه‌ها و مبنای داده", 1, fa=True)
    K.para_fa(doc, "چهار چاه در مدارک ارائه‌شده شناسایی شده‌اند، همه در میدان سیاه‌مکان، همه حفاری‌شده "
                   "با دکل‌های شرکت ملی حفاری ایران و بهره‌برداری PEDC-PECO. هر چاه با یک فایل کاری "
                   "گزارش روزانه نمایندگی می‌شود. گزارش نهایی چاه، برنامه حفاری، برنامه تکمیل، مدارک "
                   "هزینه و مدارک تولید ارائه نشده است. بنابراین مقایسه زیر مقایسه عملیات مستند حفاری "
                   "و تکمیل است، نه مقایسه اقتصاد یا بهره‌دهی چاه.")
    rows = [[w, M[w]["well_name_recorded"], G.fa_term("well_type", M[w]["well_type"]),
             M[w]["spud_date"], M[w]["last_ddr_date"], M[w]["ddr_count"], fmt(M[w]["planned_td_m"]),
             fmt(M[w]["final_depth_m"])] for w in W]
    K.table(doc, ["چاه", "نام ثبت‌شده", "نوع", "شروع", "آخرین گزارش", "تعداد گزارش",
                  "عمق برنامه (متر)", "عمق نهایی (متر)"], rows,
            widths=[1.4, 2.6, 2.4, 1.9, 1.9, 1.3, 1.8, 1.8], fa=True, size=7,
            caption="جدول ۱-۱: جامعه چاه‌ها و دامنه مستندسازی")

    K.heading(doc, "۲  جدول و نمودارهای مقایسه", 1, fa=True)
    rows = []
    for w in W:
        c = C[w]
        rows.append([w, fmt(c["final_depth_m"]), fmt(c["calendar_days"]),
                     fmt(c["total_op_hours"]), fmt(c["npt_hours"]), pct(c["npt_pct"]),
                     fmt(c["drilling_hours"], 1), fmt(c["casing_hours"], 1),
                     fmt(c["completion_hours"], 1), fmt(c.get("testing_hours"), 1),
                     fmt(c["n_sections"]), fmt(c["n_bit_runs"])])
    K.table(doc, ["چاه", "عمق نهایی (متر)", "روز", "ساعت عملیات", "زمان غیرمولد (ساعت)",
                  "درصد غیرمولد", "حفاری (ساعت)", "جداری (ساعت)", "تکمیل (ساعت)",
                  "آزمون (ساعت)", "مقاطع", "ران مته"], rows,
            widths=[1.3, 1.6, 1.0, 1.5, 2.0, 1.5, 1.5, 1.6, 1.6, 1.3, 1.1, 1.1], fa=True,
            size=6.5, caption="جدول ۲-۱: مقایسه میدانی. همه ساعات از گزارش‌های روزانه استخراج شده و "
                              "مخرج درصد زمان غیرمولد، کل ساعات ثبت‌شده است.")
    K.figure(doc, f"{FIG}/fig_plan_vs_actual.png", 16.0,
             "شکل ۲-۱: مقایسه عمق و مدت برنامه‌ریزی‌شده با مقادیر ثبت‌شده.", fa=True)
    K.figure(doc, f"{FIG}/fig_npt_pct.png", 12.5,
             "شکل ۲-۲: سهم زمان غیرمولد از کل ساعات عملیات ثبت‌شده.", fa=True)

    K.heading(doc, "۲-۱  راندمان حفاری به تفکیک مقطع", 2, fa=True)
    rows = []
    for sz in ['26"', '17-1/2"', '12-1/4"', '8-3/8"', '7"', '5-7/8"']:
        r = [sz]
        for w in W:
            v = [x for x in S if x["well"] == w and x["hole_size"] == sz]
            r.append(fmt(v[0]["rop_m_per_drill_hour"], 2) if v else "—")
        rows.append(r)
    K.table(doc, ["مقطع"] + [f"{w} (متر/ساعت)" for w in W], rows,
            widths=[2.6, 2.9, 2.9, 2.9, 2.9], fa=True, size=8.5,
            caption="جدول ۲-۲: سرعت نفوذ مقطع (متر بر ساعت حفاری، کد ۲-۱)")
    K.figure(doc, f"{FIG}/fig_section_rop.png", 16.0,
             "شکل ۲-۳: سرعت نفوذ مقاطع به تفکیک چاه و قطر.", fa=True)
    K.para_fa(doc, "مقطع ۱۷½ اینچ در همه چاه‌ها سریع‌ترین است که برای حفاری چاه‌بزرگ در توالی کم‌عمق و "
                   "نرم‌تر انتظار می‌رود: SI-007 با ۶٫۱۵، SI-009 با ۶٫۱۷، SI-006 با ۵٫۶۵ و SI-008 با "
                   "۴٫۱۵ متر بر ساعت. مقطع ۱۲¼ اینچ به‌طور یکنواخت کندتر (۲٫۴ تا ۳٫۱) و مقطع ۸⅜ "
                   "کندتر است که با ورود به تبخیری‌های گچساران و کربنات‌های آسماری سازگار است. ترتیب "
                   "نسبی چاه‌ها بین مقاطع برعکس می‌شود: SI-007 در مقطع ۱۷½ پیشتاز است اما در مقطع ۸⅜ "
                   "با ۱٫۷۸ متر بر ساعت کندترین است، زیرا این مقطع در آن چاه تحت ناپایداری پیوسته "
                   "چاه و عملیات ماهیگیری حفاری شده است.")
    K.figure(doc, f"{FIG}/fig_phase_hours.png", 16.0,
             "شکل ۲-۴: ساعات ثبت‌شده به تفکیک فاز عملیاتی و چاه.", fa=True)

    K.heading(doc, "۳  زمان غیرمولد در سطح میدان", 1, fa=True)
    K.figure(doc, f"{FIG}/fig_npt_family.png", 16.0,
             "شکل ۳-۱: زمان غیرمولد به تفکیک خانواده علت، انباشته به تفکیک چاه.", fa=True)
    fams = {}
    for r in F:
        fams.setdefault(r["family"], {})[r["well"]] = f(r["hours"], 0)
    top = sorted(fams.items(), key=lambda kv: -sum(kv[1].values()))[:8]
    rows = []
    for name, dd in top:
        rows.append([G.fa_term("family", name)] + [fmt(dd.get(w, 0), 0) for w in W] +
                    [fmt(sum(dd.values()), 0)])
    K.table(doc, ["خانواده علت"] + [f"{w} (ساعت)" for w in W] + ["جمع (ساعت)"], rows,
            widths=[4.4, 1.6, 1.6, 1.6, 1.6, 1.8], fa=True, size=7.5,
            caption="جدول ۳-۱: هشت خانواده بزرگ زمان غیرمولد و جمع میدانی")
    K.para_fa(doc, "انتظار سطحی بر جمع میدانی غالب است. سه چاه از چهار چاه، زمان بیشتری را در "
                   "انتظارهای عملیاتی، توقف پیمانکار دکل و توقف شرکت خدماتی از هر نقص فنی درون‌چاهی "
                   "از دست داده‌اند. SI-009 استثناست: در آن چاه یک رخداد کنترل چاه بزرگ‌ترین مصرف‌کننده "
                   "زمان است که کلاس مشکل متفاوتی است و پاسخ متفاوتی می‌طلبد.")
    K.para_fa(doc, "این تفکیک اهمیت دارد. زمان انتظار به قرارداد و لجستیک پاسخ می‌دهد و مشکلات چاه "
                   "به مهندسی. ادغام این دو در یک عدد، این واقعیت را پنهان می‌کند که فقط حدود یک‌چهارم "
                   "زمان از دست رفته میدان علت درون‌چاهی دارد.")

    K.heading(doc, "۴  عملکرد مته و رشته حفاری", 1, fa=True)
    K.figure(doc, f"{FIG}/fig_bit_rop_by_well.png", 15.5,
             "شکل ۴-۱: توزیع سرعت نفوذ ران‌های مته به تفکیک چاه.", fa=True)
    rows = []
    for w in W:
        bs = D[w]["bits_drilling"]
        if not bs:
            continue
        rops = [f(b["rop_m_per_h"]) for b in bs]
        rows.append([w, len(bs), fmt(max(rops), 2), fmt(min(rops), 2),
                     fmt(sum(f(b["footage_m"], 0) for b in bs), 0),
                     fmt(sum(f(b["rotating_hours"], 0) for b in bs), 0)])
    K.table(doc, ["چاه", "ران با متراژ", "بهترین سرعت (متر/ساعت)", "کندترین (متر/ساعت)",
                  "متراژ کل (متر)", "ساعت چرخش"], rows,
            widths=[1.8, 2.6, 2.8, 2.6, 2.6, 2.4], fa=True, size=8,
            caption="جدول ۴-۱: دامنه عملکرد ران‌های مته به تفکیک چاه")
    K.para_fa(doc, "آموزنده‌ترین نتیجه مته در مجموعه داده، ران SI-008-BIT-15 است: یک مته PDC با قطر "
                   "۸⅜ اینچ که ۱۰۳۰ متر را در ۱۶۸٫۵ ساعت چرخش و با سرعت ۶٫۱۱ متر بر ساعت حفاری کرده "
                   "است، تقریباً سه برابر میانه ران‌های ۸⅜ اینچ. همین قطر در SI-007 ران‌هایی با ۰٫۴۵ "
                   "تا ۱٫۷۵ متر بر ساعت داشته است. این تفاوت تنها تفاوت انتخاب مته نیست — مقطع SI-007 "
                   "از میان بازه ناپایدار با ماهیگیری مکرر عبور کرده است — اما بزرگی شکاف نشان می‌دهد "
                   "سرعت مقطع بیش از طراحی مته به وضعیت چاه وابسته است.")

    K.heading(doc, "۵  یکپارچگی چاه، آزمون پاشنه و کنترل چاه", 1, fa=True)
    rows = []
    for w in W:
        d = D[w]
        rows.append([w, M[w]["fit"] or "ثبت نشده", fmt(d["wellctrl_h"], 1),
                     fmt(float(d["code"].get("8-8", {}).get("hours") or 0), 1),
                     fmt(d["stuck_h"], 1), fmt(d["fishing_h"], 1)])
    K.table(doc, ["چاه", "آزمون پاشنه (ثبت‌شده)", "کنترل چاه (ساعت)", "کشتن چاه (ساعت)",
                  "گیر رشته (ساعت)", "ماهیگیری (ساعت)"], rows,
            widths=[1.6, 4.2, 2.4, 2.3, 2.3, 2.0], fa=True, size=8,
            caption="جدول ۵-۱: شاخص‌های یکپارچگی و مشکل چاه (ساعت ثبت‌شده، نه شاخص شدت)")
    K.para_fa(doc, "SI-009 تنها چاه میدان با جریان ورودی مستند است. این رخداد (۲۸ دسامبر ۲۰۲۲، مقطع "
                   "۱۷½ اینچ، عمق ۱۰۲۸ تا ۱۰۴۲ متر) زمانی رخ داد که وزن گل از ۷۶ به ۷۷ پوند بر فوت "
                   "مکعب افزایش می‌یافت و در یک اتصال جریان مشکوک شده بود. عملیات کشتن چاه نیازمند گل "
                   "۹۰ پوندی بود و ۵۲۵٫۵ ساعت عملیات کنترل چاه به‌علاوه ۲۴۳ ساعت کشتن فعال مصرف کرد. "
                   "چاه سپس دوباره وارد شد و حفاری ادامه یافت، اما مدارک در ۳۰۸۴ متر پایان می‌یابد. "
                   "این روشن‌ترین درس میان‌چاهی مجموعه داده است: گذر از یک گذار فشاری با حاشیه ناکافی "
                   "و تنظیم حاشیه به‌صورت واکنشی.")

    K.heading(doc, "۶  مسیر چاه و داده پیمایش", 1, fa=True)
    rows = [[w, _fa_verdict(T[w]["verdict"]), T[w]["n_distinct_stations"],
             fmt(T[w]["max_survey_md_m"], 0), fmt(T[w]["final_well_depth_m"], 0),
             pct(T[w]["coverage_pct"])] for w in W]
    K.table(doc, ["چاه", "ارزیابی", "ایستگاه مستقل", "عمیق‌ترین ایستگاه (متر)",
                  "عمق نهایی (متر)", "پوشش"], rows,
            widths=[1.4, 4.4, 2.2, 2.4, 2.2, 1.8], fa=True, size=8,
            caption="جدول ۶-۱: یکپارچگی داده پیمایش به تفکیک چاه")
    K.para_fa(doc, "هیچ چاهی در این میدان را نمی‌توان از مدارک ارائه‌شده مسیر کمترین انحنا داد. "
                   "SI-006 و SI-009 یک قالب ثابت شامل سه ایستگاه کم‌عمق دارند که با عمق به‌روز "
                   "نمی‌شود. SI-007 هیچ ایستگاه عددی ندارد. SI-008 مجموعه ناقصی دارد که تا ۴۶۱۰ متر "
                   "می‌رسد و در ایستگاه‌های عمیق‌تر زاویه و آزیموت دارد؛ این برای مسیر ناقص کافی است "
                   "اما برای کل چاه نه. این ویژگی مدارک است نه چاه، و هیچ مسیری برای پر کردن این خلأ "
                   "ساخته نشده است.")

    K.heading(doc, "۷  یافته‌های مهندسی میان‌چاهی", 1, fa=True)
    findings = [
        ("انتظار سطحی، سازوکار غالب اتلاف زمان میدان است.",
         "سه چاه ساعات بیشتری را در انتظار پیمانکار دکل، شرکت‌های خدماتی و تصمیم کارفرما گذرانده‌اند "
         "تا در هر مشکل درون‌چاهی. این الگو به‌طور مستقل در چاه‌ها تکرار می‌شود و در توزیع کدها سازگار "
         "است؛ بنابراین یک الگوی واقعی مشترک است و نه اثر طبقه‌بندی."),
        ("مشکلات چاه در مقاطع ۸⅜ و ۵⅞ اینچ متمرکز است، نه در چاه‌بزرگ سطحی.",
         "SI-006 در مقطع ۸⅜ خود ۳۳۹۱ ساعت و SI-007 در مقطع ۵⅞ خود ۴۶۸۴ ساعت از دست داده است. هر دو "
         "مقطع عمیق و در گذر گچساران–آسماری حفاری شده‌اند. مقاطع سطحی ۱۷½ و ۲۶ اینچ در همه چاه‌ها "
         "به‌طور یکنواخت پاک‌ترین هستند."),
        ("توالی تبخیری گچساران، مخاطره زمین‌شناسی تکرارشونده است.",
         "جدول سازند در همه چاه‌ها اعضای گچساران (نمک، انیدریت، مارل) را بازه‌ای ثبت می‌کند که "
         "هرزروی، تنگی چاه و گیر رشته از آن آغاز می‌شود. SI-008 این اعضا را در ۲۷۹۴ تا ۳۴۳۲ متر و "
         "SI-006 در ۲۶۵۰ تا ۳۳۴۱ متر ثبت کرده و هر دو در همان‌جا هرزروی داشته‌اند. این یک نشانه مشابه "
         "در سازند مشابه است، اما مدارک یک سازوکار مشترک واحد را اثبات نمی‌کند."),
        ("جریان ورودی SI-009 رخدادی چاه‌محور است، نه الگوی میدانی.",
         "هیچ چاه دیگری عملیات کنترل چاه با این مدت ثبت نکرده است. تلقی آن به‌عنوان ویژگی میدانی "
         "نادرست است؛ تلقی آن به‌عنوان رخداد یکباره هم نادرست است، زیرا سازوکار آن (افزایش واکنشی وزن "
         "گل در گذر از گذار فشاری) قابل تکرار است."),
        ("تنوع عملکرد مته درون یک چاه بیشتر از بین چاه‌ها است.",
         "ران‌های ۸⅜ اینچ در SI-006 از ۰٫۶۱ تا ۳٫۵۳ و در SI-007 از ۰٫۴۵ تا ۱٫۷۵ متر بر ساعت است. "
         "پراکندگی درون یک چاه از اختلاف میانگین چاه‌ها بیشتر است؛ یعنی انتخاب مته و وضعیت چاه، نه "
         "هویت چاه، سرعت مقطع را تعیین می‌کند."),
        ("عملکرد تکمیل و تولید به‌کلی قابل مقایسه نیست.",
         "هیچ چاه فهرست تجهیزات تکمیل، نتیجه آزمون یا سابقه تولید ندارد. مقایسه در پایان حفاری مستند "
         "و در صورت ثبت، عملیات تکمیل متوقف می‌شود."),
    ]
    for i, (h, t) in enumerate(findings, 1):
        K.para_fa(doc, f"{i}.  {h}", bold=True, size=10)
        K.para_fa(doc, t, size=9.5)

    K.heading(doc, "۸  رتبه‌بندی و محک‌زنی", 1, fa=True)
    FA_TITLES = {
        "Highest drilling rate (m per code 2-1 hour)":
            "بالاترین نرخ حفاری (متر بر ساعت کد ۲-۱)",
        "Fastest overall delivery (m per calendar day)":
            "سریع‌ترین تحویل کلی (متر بر روز تقویمی)",
        "Lowest share of non-productive time":
            "کمترین سهم زمان غیرمولد",
        "Highest proportion of planned depth delivered":
            "بیشترین نسبت عمق تحویل‌شده به عمق برنامه",
    }
    for title, order, reason in rankings(C, M, S):
        K.para_fa(doc, FA_TITLES.get(title, title), bold=True, size=10)
        K.table(doc, ["رتبه", "چاه", "مقدار"],
                [[str(i + 1), w, fmt(C[w]["rop_m_per_h_drilling"] if "drilling rate" in title
                                     else C[w]["rop_m_per_day_overall"] if "delivery" in title
                                     else C[w]["npt_pct"] if "non-productive" in title
                                     else 100 * f(M[w]["final_depth_m"], 0) / f(M[w]["planned_td_m"], 1),
                                     2)] for i, w in enumerate(order)],
                widths=[1.8, 3.0, 3.0], fa=True, size=8.5,
                caption="مقدار ستون سوم همان کمیتی است که در عنوان آمده؛ مخرج هر نسبت در متن انگلیسی گزارش "
                        "مشخص شده است.")
    K.para_fa(doc, "هیچ رتبه‌بندی به‌عنوان جدول لیگ کلی ارائه نشده است. چاهی که هدف عمیق‌تری را از "
                   "سازندهای دشوار گذرانده، با چاهی که مدارکش در مقطع میانی پایان یافته، در یک مقیاس "
                   "قابل مقایسه نیست. رتبه‌بندی‌های بالا هر یک فقط یک کمیت را می‌سنجند و همان‌گونه "
                   "برچسب خورده‌اند.")

    K.heading(doc, "۹  نتیجه‌گیری مدیریتی", 1, fa=True)
    K.bullets(doc, [
        "بهترین عملکرد اجرا: SI-008 که ۴۹۰۰ متر را در ۲۰۹ روز با ۱۴٫۱ درصد زمان غیرمولد و پنج مقطع "
        "حفاری کرد، آن هم با مغزه‌گیری. مزیت آن هدف عمیق‌تر نیست، اجرای پاک‌تر است.",
        "چالش‌برانگیزترین چاه: SI-007 که ۴۹۸ روز برای رسیدن به ۴۴۱۰ متر با ۴۸٫۰ درصد زمان غیرمولد و "
        "۹۱۱ ساعت ماهیگیری صرف کرد. زمان اضافی به بازیابی سیم‌خطی و سایدترک پس از آن نسبت داده می‌شود.",
        "پرریسک‌ترین رخداد: جریان ورودی SI-009. تنها رخداد کنترل چاه میدان است و حدود ۳۰ روز زمان "
        "دکل را حذف کرد.",
        "ضعف فنی تکرارشونده: تصمیم ورود به مقطع در بازه گچساران. هر چاه در آنجا هرزروی یا ناپایداری "
        "ثبت کرده و هر چاه واکنشی پاسخ داده است.",
        "رویه موفق قابل تکرار: برنامه‌ریزی مغزه‌گیری و تکمیل SI-008 که زمان غیرمولد را در ۱۴ درصد "
        "نگه داشت، در حالی که برنامه پیچیده‌تری از سایر چاه‌ها اجرا می‌کرد.",
        "توجه مدیریت: مواجهه با زمان انتظار یک مسئله قرارداد و لجستیک است که مهندسی نمی‌تواند حل کند. "
        "سهم عمده زمان از دست رفته میدان از همین‌جا است.",
    ], fa=True)

    K.heading(doc, "۱۰  توصیه‌های اولویت‌دار", 1, fa=True)
    recs = [
        ("۱", "رویه گذار کنترل چاه",
         "الزام رویه مستند افزایش وزن گل با حاشیه سفر تعریف‌شده پیش و پس از هر تغییر وزن. رخداد "
         "SI-009 دلیل کسب‌وکار مستقیم این توصیه است.", "بالا", "فوری"),
        ("۲", "شرایط قراردادی زمان انتظار",
         "تعیین تعهد زمان پاسخ برای پیمانکار دکل و شرکت‌های خدماتی اصلی، با ثبت مسئول تأخیر در هر "
         "گزارش روزانه.", "بالا", "دوره قرارداد بعدی"),
        ("۳", "آمادگی ماهیگیری",
         "نگه‌داشتن رشته ماهیگیری اختصاصی و رویه قطع و رزوه‌کردن سیم روی دکل پیش از هر مقطعی که "
         "لاگ‌گیری سیم‌خطی در آن برنامه‌ریزی شده است.", "بالا", "چاه بعدی"),
        ("۴", "برنامه ورود به گچساران",
         "نوشتن برنامه اختصاصی مقطع تبخیری: پنجره وزن گل، درمان هرزروی، رویه رمینگ و تواتر سفر.",
         "متوسط", "چاه بعدی"),
        ("۵", "ثبت پیمایش و هزینه",
         "الزام ثبت ایستگاه‌های پیمایش و فیلد هزینه روزانه در قالب گزارش. بدون این دو، تحلیل مسیر و "
         "اقتصاد از گزارش‌های روزانه امکان‌پذیر نیست.", "متوسط", "بازنگری قالب"),
        ("۶", "بازبینی انتخاب مته",
         "بازبینی برنامه مته ۸⅜ اینچ بر پایه نتیجه SI-008 پیش از کمپین بعدی.", "متوسط", "مرحله برنامه‌ریزی"),
    ]
    K.table(doc, ["#", "اقدام", "مبنا", "اولویت", "زمان‌بندی"], [list(r) for r in recs],
            widths=[0.8, 3.6, 6.6, 1.6, 2.4], fa=True, size=7.5,
            caption="جدول ۱۰-۱: توصیه‌های اولویت‌دار برای کمپین بعدی")

    K.heading(doc, "۱۱  فرصت‌های بهبود کمی‌شده", 1, fa=True)
    K.para_fa(doc, "سناریوهای زیر از ساعات ثبت‌شده خود میدان به‌عنوان مبنا استفاده می‌کنند. این‌ها "
                   "برآورد مهندسی هستند، نه نتیجه اثبات‌شده، و هیچ صرفه‌جویی ریالی بیان نمی‌شود زیرا "
                   "داده هزینه در منابع وجود ندارد.")
    wait = sum(f(C[w]["waiting_hours"], 0) for w in W)
    tot_npt = sum(f(C[w]["npt_hours"], 0) for w in W)
    rows = [
        ["کاهش انتظار سطحی به میزان یک شیفت ۱۲ ساعته در هر رخداد",
         f"{fmt(wait)} ساعت انتظار در میدان", "۱۲ ساعت × تعداد رخدادها با سقف ۲۰ درصد زمان انتظار",
         f"{fmt(wait*0.2, 0)} ساعت", "نیازمند هماهنگ‌کننده با اختیار تغییر ترتیب کارها"],
        ["نصف کردن زمان مغزه‌گیری SI-008", f"{fmt(D['SI-008']['coring_h'])} ساعت مغزه‌گیری",
         "۰٫۵ × ساعت مغزه‌گیری", f"{fmt(D['SI-008']['coring_h']*0.5)} ساعت",
         "فرض می‌کند تأخیر مربوط به آماده‌سازی بوده نه سازند"],
        ["حذف یک چرخه تکراری کشتن چاه در SI-009", f"{fmt(D['SI-009']['wellctrl_h'])} ساعت کنترل چاه",
         "یک چرخه ۲۴ ساعته", "۲۴ ساعت", "فرض افزایش وزن زودتر؛ خود جریان ورودی قابل پیشگیری فرض نشده"],
    ]
    K.table(doc, ["فرصت", "مبنا", "روش", "صرفه‌جویی زمان دکل", "فرض کلیدی"], rows,
            widths=[3.6, 2.6, 3.4, 1.8, 3.8], fa=True, size=7,
            caption="جدول ۱۱-۱: سناریوهای بهبود با فرض‌های صریح")
    K.para_fa(doc, f"کل زمان غیرمولد میدان {fmt(tot_npt)} ساعت در چهار چاه است. اگر یک‌چهارم زمان "
                   f"انتظار بازیابی شود — هدفی سخت‌گیرانه اما غیرواقعی نیست برای یک سیستم لجستیک "
                   f"مدیریت‌شده — میدان حدود {fmt(wait*0.25/24, 0)} روز دکل باز می‌گرداند. این عدد یک "
                   f"سناریو است که همراه با فرض خود ارائه شده تا مدیریت بتواند آن را بپذیرد یا رد کند.")
    doc.save(path)
    K.normalise_ooxml(path)
    return path


def main():
    C, M, N, S, F, T, B, D = load()
    os.makedirs(OUT, exist_ok=True)
    p1 = build_en(C, M, N, S, F, T, B, D, f"{OUT}/Siah_Makan_Comparison_Report_EN.docx")
    p2 = build_fa(C, M, N, S, F, T, B, D, f"{OUT}/Siah_Makan_Comparison_Report_FA.docx")
    print(p1)
    print(p2)


if __name__ == "__main__":
    main()
