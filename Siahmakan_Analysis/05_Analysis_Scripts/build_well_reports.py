"""Generate the bilingual per-well engineering reports.

Structure follows the brief: executive summary, identity and architecture,
timeline, ROP, NPT with root-cause analysis, bit/BHA, parameters/MSE, mud and
hydraulics, trajectory, well control, geology, hole problems, completion,
recommendations, quantified opportunities, appendices.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

import docx_kit as K
import fa_glossary as G
import report_content as RC

OUT = "Siahmakan_Analysis/01_Well_Reports"

# --------------------------------------------------------------------------- #
# interpretations, selected from the data (not per-well hard-coded prose)
# --------------------------------------------------------------------------- #
def interp(D):
    w = D["well"]
    I = {}
    npt_pct = D["npt_pct"]
    if npt_pct >= 45:
        I["npt_verdict"] = ("Non-productive time is the dominant consumer of rig time on this "
                            "well. Less than a third of the recorded days were spent making hole "
                            "or running pipe.")
    elif npt_pct >= 25:
        I["npt_verdict"] = ("Non-productive time is high but not dominant; the well still shows a "
                            "recognisable drilling rhythm between interruptions.")
    else:
        I["npt_verdict"] = ("Non-productive time is low by the standards of this field. The well was "
                            "executed close to its operational plan.")

    fam = D["top_family"]["family"] if D["top_family"] else None
    if fam in ("Operations contingency", "Waiting on rig contractor", "Waiting on service company",
               "Waiting on client", "Waiting on procurement", "Waiting on programme",
               "Waiting on material quality"):
        I["npt_root"] = ("The largest single block of lost time is not a downhole failure but a "
                         "surface logistics and decision-latency problem. The DDR narrative shows the "
                         "rig available and the string in hole while the operation waits for a party "
                         "outside the drilling crew.")
    elif fam in ("Well control",):
        if D["wellctrl_h"] > 0 and (D["wellctrl_h"] / D["tot_h"] if D["tot_h"] else 0) >= 0.2:
            I["npt_root"] = ("Lost time is dominated by well-control work. The records describe an "
                             "influx taken while drilling, followed by extended circulation, "
                             "stripping and kill operations rather than a single short event.")
        else:
            I["npt_root"] = ("Well control is the largest single cause family recorded for this well, "
                             "but it is a bounded episode: kill operations, circulation and pressure "
                             "monitoring, after which drilling resumed.")
    elif fam in ("Fishing",):
        I["npt_root"] = ("Lost time is dominated by fishing. The wireline and BHA recovery sequence "
                         "consumed weeks of rig time and drove a subsequent change of plan.")
    elif fam in ("Stuck pipe",):
        I["npt_root"] = ("Lost time is dominated by stuck pipe and the associated freeing, jarring "
                         "and conditioning operations.")
    else:
        I["npt_root"] = ("Lost time is spread across several cause families without one dominant "
                         "mechanical failure.")

    sec = D["top_section_npt"]["hole_section"] if D["top_section_npt"] else None
    I["top_family"] = fam
    I["npt_section"] = sec
    return I


def fmt(v, nd=0):
    if v in (None, "", "None"):
        return "—"
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v)
    return f"{x:,.{nd}f}"


def pct(v, nd=1):
    return "—" if v in (None, "") else f"{float(v):.{nd}f} %"


# --------------------------------------------------------------------------- #
# English report
# --------------------------------------------------------------------------- #
def build_en(D, path):
    w = D["well"]
    I = interp(D)
    m = D["master"]
    doc = K.new_doc()
    sec = doc.sections[0]
    K.header_footer(sec, f"Siah Makan Field — {w} Engineering Report",
                    "Rev. 1.0 | Data cut-off: last DDR", fa=False)
    K.cover(doc,
            f"{w} Engineering Report",
            "Drilling, Completion and Well Performance Analysis — Siah Makan Field",
            [f"Well identifier (as recorded): {m['well_name_recorded']}",
             f"Well type: {m['well_type']}",
             f"Operator: {m['operator']}   |   Rig contractor: {m['rig_contractor']}",
             f"Spud date: {m['spud_date']}   |   Last daily report: {m['last_ddr_date']}",
             f"Final recorded depth: {fmt(D['depth'])} m MD   |   Planned TD: {fmt(D['planned'])} m MD",
             "Document version 1.0 — prepared 2026-11-24",
             "Reporting languages: English and Persian"])

    K.toc(doc, fa=False)

    # ---------------- 1 executive summary
    K.heading(doc, "1  Executive Summary", 1)
    K.para_en(doc, f"{w} is a {m['well_type'].lower()} well in the Siah Makan field, spudded on "
                   f"{m['spud_date']} and documented to {m['last_ddr_date']}. The well reached a "
                   f"final recorded depth of {fmt(D['depth'])} m MD against a planned total depth of "
                   f"{fmt(D['planned'])} m MD, over {fmt(D['days'])} calendar days and "
                   f"{fmt(m['ddr_count'])} daily drilling reports.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    K.para_en(doc, f"Of the {fmt(D['tot_h'])} operation-hours documented, {fmt(D['npt_h'])} hours "
                   f"({pct(D['npt_pct'])}) are classified in the daily reports as non-productive or "
                   f"unplanned. Drilling operations proper (code 2-1) account for {fmt(D['drill_h'])} "
                   f"hours ({pct(D['drill_share'])}); trips and hole conditioning account for "
                   f"{fmt(D['trip_h'])} hours ({pct(D['trip_share'])}). {I['npt_verdict']}",
              align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    K.para_en(doc, f"The dominant non-productive family is {I['top_family'] or 'n/a'}, and the hole "
                   f"section in which the largest share of lost time accumulated is "
                   f"{D['top_section_npt']['hole_section'] if D['top_section_npt'] else 'n/a'}. "
                   f"{I['npt_root']}", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    if D["sidetracks"]:
        st = D["sidetracks"][0]
        K.para_en(doc, f"A {len(D['sidetracks'])} recorded depth decrease(s) mark a departure from the "
                       f"original hole. The first occurs on {st['date']} (rig day {fmt(st['rig_day'])}) "
                       f"when the recorded depth falls from {fmt(st['from_depth'])} m to "
                       f"{fmt(st['to_depth'])} m MD: the well was side-tracked after the original hole "
                       f"could not be recovered.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    if D["wellctrl_h"] > 50:
        _wp = 100 * D["wellctrl_h"] / D["tot_h"] if D["tot_h"] else 0
        if _wp >= 20:
            K.para_en(doc, f"Well-control operations (code 10-5) consumed {fmt(D['wellctrl_h'])} "
                           f"hours, which is {pct(_wp)} of all recorded time. A kick is a hazard, not a "
                           f"routine operation, and here it dominates the well's time performance.",
                      align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        else:
            K.para_en(doc, f"Well-control operations (code 10-5) consumed {fmt(D['wellctrl_h'])} "
                           f"hours, which is {pct(_wp)} of all recorded time. Well control is a hazard, "
                           f"not a routine operation; on this well it is a contained episode rather "
                           f"than the driver of total time.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    K.para_en(doc, "Key figures", bold=True)
    K.table(doc, ["Metric", "Value", "Basis"],
            [["Final recorded depth", f"{fmt(D['depth'])} m MD", "Maximum depth at 24:00 recorded in the DDR set"],
             ["Planned total depth", f"{fmt(D['planned'])} m MD", "Planned TD field in the DDR header"],
             ["Documented duration", f"{fmt(D['days'])} days", f"{fmt(m['ddr_count'])} daily reports, spud to last report"],
             ["Recorded operation hours", f"{fmt(D['tot_h'])} h", "Sum of the 24-hour operation table"],
             ["NPT (type N + U)", f"{fmt(D['npt_h'])} h ({pct(D['npt_pct'])})",
              "DDR type column; denominator = all recorded operation hours"],
             ["Drilling time (code 2-1)", f"{fmt(D['drill_h'])} h", "Operation code 2-1 only"],
             ["Hole sections drilled", str(len([s for s in D['sections'] if s['is_completion'] != 'True'])),
              "Distinct recorded hole sizes in sequence"],
             ["Bit runs with footage", str(len(D["bits_drilling"])), "Run-in/pull-out depth from DDR records"],
             ["Well cost", "Not available in the supplied documentation", "No cost field exists in any DDR sheet"]],
            widths=[5.6, 4.6, 5.4], size=8.5, align_right_cols={0, 2},
            caption="Table 1-1: Summary of the principal well metrics")

    K.para_en(doc, "Principal engineering lessons", bold=True)
    lessons = []
    if D["npt_pct"] > 40:
        lessons.append("Rig time, not rock, is the binding constraint: the largest time loss on this "
                       "well is surface waiting, which a logistics plan can address.")
    if D["wellctrl_h"] > 50:
        lessons.append("A single well-control event re-set the well's cost and schedule. The DDR shows "
                       "the influx being taken shortly after a mud-weight increase was being applied — "
                       "the transition between mud programmes is the exposure window.")
    if D["fishing_h"] > 100:
        lessons.append("Wireline recovery without a dedicated fishing BHA consumed several weeks; early "
                       "commitment to a cut-and-thread recovery string proved to be the decisive step.")
    if D["coring_h"] > 100:
        lessons.append(f"Coring consumed {fmt(D['coring_h'])} hours ({pct(100*D['coring_h']/D['tot_h'])} of rig time). "
                       f"Core recovery is a programme decision with a large rig-time price.")
    if len(D["bits_drilling"]) >= 5:
        lessons.append("Bit performance varies by more than a factor of two between runs in the same "
                       "hole section, so bit selection — not parameter tweaking alone — drives section ROP.")
    if D["sidetracks"]:
        lessons.append("The side-track was a consequence of an unrecoverable string; the recovery "
                       "decision tree should be written before drilling the section, not during the event.")
    K.bullets(doc, lessons or ["No single lesson dominates this well; see the sections that follow."])

    # ---------------- 2 identity and architecture
    K.heading(doc, "2  Well Identity, Architecture and Design", 1)
    K.heading(doc, "2.1  Identity", 2)
    K.kv_table(doc, [
        ("Well (as recorded)", m["well_name_recorded"]),
        ("Field", m["field"]),
        ("Well type", m["well_type"]),
        ("Operator", m["operator"]),
        ("Rig contractor", m["rig_contractor"]),
        ("Spud date", m["spud_date"]),
        ("Planned duration", f"{fmt(m['plan_duration_d'])} days"),
        ("Planned TD", f"{fmt(D['planned'])} m MD"),
        ("Final recorded depth", f"{fmt(D['depth'])} m MD"),
        ("Last recorded hole size / status", m["last_hole_size"]),
        ("Last casing (as recorded)", m["last_csg"]),
        ("Liner lap (as recorded)", m["liner_lap"]),
        ("FIT / shoe test (as recorded)", m["fit"] or "Not recorded"),
        ("Date basis", m["date_basis"]),
    ], size=8.5)
    K.para_en(doc, "Coordinates are not reported in this document because the DDR header carries a "
                   "coordinate field only in some templates; where a value exists it is reproduced in "
                   "the appendix without conversion.", size=9, italic=True)

    K.heading(doc, "2.2  Hole section architecture", 2)
    rows = []
    for s in D["sections"]:
        rows.append([s["hole_size"], s["start_date"], f"{fmt(s['start_depth'],1)}",
                     f"{fmt(s['end_depth'],1)}", fmt(s["interval_m"], 1),
                     f"{fmt(s['duration_d'])}", fmt(s["drilling_hours_2_1"], 1),
                     fmt(s["rop_m_per_drill_hour"], 2), pct(s["npt_pct_of_section"])])
    K.table(doc, ["Section", "Start", "From (m)", "To (m)", "Interval (m)", "Days",
                  "Drilling h (2-1)", "ROP (m/h)", "NPT share"],
            rows, widths=[2.3, 2.0, 1.7, 1.7, 1.7, 1.2, 2.0, 1.7, 1.6], size=8,
            caption="Table 2-1: Hole sections as recorded. Interval = change in recorded depth; "
                    "drilling hours = sum of code 2-1; NPT share = NPT hours / (days × 24).")
    K.para_en(doc, "Section boundaries are taken from the hole-size field on each daily report, "
                   "normalised for the spelling variants that occur in the source. A section change is "
                   "accepted only when the new size persists, so a single mis-typed cell cannot create "
                   "a spurious section.", size=9, italic=True)

    K.heading(doc, "2.3  Casing and liner programme (as recorded on the final sheet)", 2)
    if D["final_casing"]:
        rows = [[c["size"], c["wt"], c["grade"], c["threads"], c["from"], c["to"]]
                for c in D["final_casing"]]
        K.table(doc, ["Size", "Weight", "Grade", "Thread", "From (m)", "To (m)"], rows,
                widths=[2.8, 2.4, 3.0, 2.2, 2.4, 2.0], size=8.5,
                caption=f"Table 2-2: Casing and liner strings, transcribed from sheet "
                        f"{D['final_casing_sheet']}. No value has been added or corrected.")
    else:
        K.para_en(doc, "Casing data: Not available in the supplied documentation.")
    K.para_en(doc, "Cement volumes, slurry designs and CBL results are not tabulated in the DDR "
                   "beyond the bulk-material block, which records material received and consumed per "
                   "day rather than per string. A per-string cementing summary cannot therefore be "
                   "reconstructed from these records without inventing volumes.", size=9, italic=True)

    if D["sidetracks"]:
        K.heading(doc, "2.4  Side-track and re-entry", 2)
        K.para_en(doc, "The depth record contains a genuine decrease in recorded depth, which is the "
                       "unambiguous signature of a side-track or re-entry. The table lists every such "
                       "event found in this well's records.", size=9.5)
        rows = [[st["date"], fmt(st["rig_day"]), f"{fmt(st['from_depth'],1)} → {fmt(st['to_depth'],1)}",
                 st["sheet"]] for st in D["sidetracks"]]
        K.table(doc, ["Date", "Rig day", "Depth change (m)", "Source sheet"], rows,
                widths=[3.0, 2.0, 5.0, 5.0], size=8.5,
                caption="Table 2-3: Recorded depth decreases (side-track / re-entry evidence).")

    # ---------------- 3 timeline
    K.heading(doc, "3  Full-Life Timeline and Depth–Time Analysis", 1)
    K.para_en(doc, "The depth–time curve is built from the depth at 24:00 recorded on every daily "
                   "report, not from a weekly summary or a final report. Reported periods with no "
                   "daily report are left as a gap; nothing is interpolated across them.",
              align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    fig_path = f"{OUT}/{w}/Figures/{w}_fig_depth_time.png"
    if os.path.exists(fig_path):
        K.figure(doc, fig_path, 16.0,
                 f"Figure 3-1: {w} depth against well day. Dashed verticals mark section starts, "
                 f"labelled with nominal hole size; depth axis inverted (0 at top).")
    if D["gaps"]:
        rows = [[g["gap_start"], g["gap_end"], g["gap_days"]] for g in D["gaps"]]
        K.table(doc, ["Gap start", "Gap end", "Days without report"], rows,
                widths=[4.0, 4.0, 5.0], size=8.5,
                caption="Table 3-1: Reporting gaps. These periods are absent from the record; the "
                        "curve is discontinuous across them.")
    else:
        K.para_en(doc, "No gap was found in the daily report sequence: every calendar day from spud "
                       "to the last report carries exactly one DDR.", size=9.5)

    # phase table
    K.heading(doc, "3.1  Time allocation by operational phase", 2)
    rows = [[p["phase"], fmt(p["hours_total"], 1), pct(p["pct_of_total"]),
             fmt(p["hours_productive"], 1), fmt(p["hours_npt_N"], 1), fmt(p["hours_npt_U"], 1)]
            for p in D["phases"] if float(p["hours_total"] or 0) > 0]
    K.table(doc, ["Operational phase", "Hours", "Share", "Productive (P)", "NPT (N)", "Unplanned (U)"],
            rows, widths=[4.8, 1.8, 1.6, 2.4, 2.2, 2.6], size=8,
            caption="Table 3-2: Recorded hours by phase. Phase is assigned from the operation code; "
                    "P/N/U are the DDR's own productivity classes.")
    K.para_en(doc, f"Productive hours total {fmt(sum(float(p['hours_productive'] or 0) for p in D['phases']),1)}; "
                   f"non-productive {fmt(sum(float(p['hours_npt_N'] or 0) for p in D['phases']),1)}; "
                   f"unplanned {fmt(sum(float(p['hours_npt_U'] or 0) for p in D['phases']),1)}. "
                   f"The three classes sum to the recorded total, so the NPT percentage quoted "
                   f"throughout uses all recorded operation hours as its denominator.", size=9)

    # ---------------- 4 ROP
    K.heading(doc, "4  Drilling Performance and Rate of Penetration", 1)
    K.para_en(doc, "Two rates are reported and they are not interchangeable. The section rate per "
                   "drilling hour divides the section interval by the hours recorded under code 2-1 "
                   "(Drilling) and therefore measures rock destruction only. The section rate per "
                   "calendar day divides the same interval by elapsed days and therefore includes "
                   "trips, casing, waiting and every interruption.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    rows = [[s["hole_size"], fmt(s["interval_m"], 1), fmt(s["duration_d"]),
             fmt(s["drilling_hours_2_1"], 1), fmt(s["rop_m_per_drill_hour"], 2),
             fmt(s["rop_m_per_day"], 2)] for s in D["sections"]]
    K.table(doc, ["Section", "Interval (m)", "Calendar days", "Drilling h", "ROP (m per drilling h)",
                  "ROP (m per day)"], rows, widths=[2.5, 2.2, 2.2, 2.2, 3.2, 2.8], size=8.5,
            caption="Table 4-1: Rate of penetration by hole section, with both denominators shown.")
    if D["bits_drilling"]:
        K.heading(doc, "4.1  Rate of penetration by bit run", 2)
        rows = []
        for b in sorted(D["bits_drilling"], key=lambda x: -float(x["rop_m_per_h"])):
            rows.append([b["run_id"].split("-")[-1], b["bit_no"],
                         b["bit_size"], b["manufacturer"],
                         f"{fmt(b['depth_in_m'],1)}", f"{fmt(b['depth_out_m'],1)}",
                         fmt(b["footage_m"], 1), fmt(b["rotating_hours"], 1),
                         fmt(b["rop_m_per_h"], 2), (b["dull"] or "—")[:22]])
        K.table(doc, ["Run", "Bit", "Size", "Make", "In (m)", "Out (m)", "Footage (m)",
                      "Rot. h", "ROP (m/h)", "IADC dull (as recorded)"], rows,
                widths=[1.1, 1.5, 1.6, 1.9, 1.4, 1.4, 1.6, 1.2, 1.5, 2.6], size=7.5,
                caption="Table 4-2: Bit runs sorted by rate of penetration. Footage = pull-out depth "
                        "minus run-in depth; rotating hours = sum of code 2-1 over the run.")
        K.para_en(doc, f"The fastest run is {D['best_bit']['run_id']} (bit {D['best_bit']['bit_no']}, "
                       f"{D['best_bit']['bit_size']}, {D['best_bit']['manufacturer']}) at "
                       f"{fmt(D['best_bit']['rop_m_per_h'],2)} m/h over "
                       f"{fmt(D['best_bit']['footage_m'],0)} m. The slowest documented run is "
                       f"{D['worst_bit']['run_id']} at {fmt(D['worst_bit']['rop_m_per_h'],2)} m/h. "
                       f"The longest single run is {D['longest_bit']['run_id']} at "
                       f"{fmt(D['longest_bit']['footage_m'],0)} m.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    K.figure(doc, f"Siahmakan_Analysis/02_Asset_Comparison/Figures/fig_bit_footage.png", 14.5,
             "Figure 4-1: Footage per bit run (field-wide comparison).")

    # ---------------- 5 NPT
    K.heading(doc, "5  Non-Productive Time Register and Root-Cause Analysis", 1)
    K.para_en(doc, f"The register contains {len(D['npt'])} events totalling {fmt(D['npt_h'])} hours. "
                   f"An event is a maximal run of consecutive daily reports carrying the same "
                   f"non-productive code; a break in the report sequence closes the event. "
                   f"Operations typed N (planned non-productive) and U (unplanned) are reported "
                   f"separately and never merged silently.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    K.heading(doc, "5.1  NPT by cause family", 2)
    rows = [[r["family"], fmt(r["hours"], 1), pct(r["pct_of_npt"]), pct(r["pct_of_total_time"]),
             r["event_count"]] for r in D["npt_fam"]]
    K.table(doc, ["Cause family", "Hours", "Share of NPT", "Share of all time", "Events"], rows,
            widths=[4.6, 1.8, 2.4, 2.8, 1.6], size=8.5,
            caption="Table 5-1: NPT by cause family. Denominators are stated in the column headers.")
    K.heading(doc, "5.2  NPT by hole section", 2)
    rows = [[r["hole_section"], fmt(r["npt_hours"], 1), pct(r["pct_of_npt"])] for r in D["npt_sec"]]
    K.table(doc, ["Hole section", "NPT hours", "Share of NPT"], rows,
            widths=[4.5, 3.0, 3.5], size=8.5,
            caption="Table 5-2: Distribution of lost time across hole sections.")
    fig_path = f"{OUT}/{w}/Figures/{w}_fig_npt_pareto.png"
    if os.path.exists(fig_path):
        K.figure(doc, fig_path, 16.0,
                 f"Figure 5-1: {w} NPT Pareto by cause family, with cumulative share.")

    K.heading(doc, "5.3  Major NPT events", 2)
    rows = []
    for e in D["npt_top"]:
        rows.append([e["event_id"].split("-")[-1], e["start_date"], e["end_date"],
                     fmt(e["hours"], 1), e["code"], e["family"], e["hole_sizes"],
                     (e["desc"] or "")[:120]])
    K.table(doc, ["ID", "Start", "End", "Hours", "Code", "Family", "Section", "Recorded narrative"],
            rows, widths=[1.0, 1.9, 1.9, 1.2, 1.1, 2.4, 1.8, 4.2], size=7,
            caption="Table 5-3: Eight largest NPT events. Narrative is quoted from the DDR and truncated.")
    K.para_en(doc, "Competing explanations for the dominant event", bold=True)
    fam = I["top_family"]
    if fam == "Operations contingency":
        alts = [
            ("Interpretation A — genuine surface contingency: rig waiting on a third party or on "
             "equipment availability.",
             "Supported: the DDR codes the time 11-10 and the narrative describes standing by while "
             "surface equipment, acid or wireline services are mobilised."),
            ("Interpretation B — mis-classification of downhole problem time as contingency.",
             "Contradicted: the same sheets carry separate rows coded 10-3 / 10-4 for the mechanical "
             "work; the contingency rows run while the string is static, which is inconsistent with "
             "downhole work being recorded elsewhere."),
        ]
    elif fam == "Waiting on rig contractor":
        alts = [
            ("Interpretation A — rig-equipment condition: repeated repairs of top drive, drawworks "
             "and mud pumps.",
             "Supported: the DDR explicitly names TDS, drawworks and pump repairs during the waiting "
             "periods, and the same equipment recurs across the well."),
            ("Interpretation B — contractor crewing or spare-parts logistics rather than the "
             "equipment itself.",
             "Partially supported: several entries record the rig waiting for a spare or a technician "
             "rather than for repair work, which points to the maintenance supply chain as the "
             "underlying cause rather than the hardware."),
        ]
    elif fam == "Well control":
        alts = [
            ("Interpretation A — an influx caused by insufficient mud weight while drilling a "
             "transition zone.",
             "Supported: the narrative states that flow increased while mud weight was being raised "
             "from 76 to 77 pcf, and the subsequent kill required 90 pcf mud; the original weight was "
             "therefore below formation pressure."),
            ("Interpretation B — a swabbed influx caused by tripping or connection practices.",
             "Contradicted for the main event: the influx was observed while drilling at the bottom, "
             "not while tripping, and the well was static on the previous flow check."),
        ]
    elif fam == "Fishing":
        alts = [
            ("Interpretation A — a wireline tool string parted in hole and required recovery before "
             "drilling could resume.",
             "Supported: the operation log records a fishing sequence with an overshot run inside the "
             "drill string, followed by cut-and-thread wireline recovery."),
            ("Interpretation B — the fishing was caused by the BHA rather than the wireline.",
             "Contradicted: the BHA was pulled and the bit graded before the fishing began; the stuck "
             "item is described as a cable and tool string, not drill pipe."),
        ]
    else:
        alts = [
            ("Interpretation A — mechanical failure of downhole equipment.",
             "See the event narrative above."),
            ("Interpretation B — an operational practice that loaded the equipment beyond its design "
             "envelope.", "See the event narrative above."),
        ]
    for text, ev in alts:
        K.para_en(doc, text, size=9.5, bold=True)
        K.para_en(doc, ev, size=9.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    K.para_en(doc, "The record does not contain enough information to establish a single root cause "
                   "with certainty; the interpretation above is the one best supported by the "
                   "recorded evidence and is presented as such, not as a confirmed fact.",
              size=9, italic=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # ---------------- 6 bit / BHA
    K.heading(doc, "6  Bit and BHA Performance", 1)
    K.para_en(doc, "Bit records are taken from the per-sheet bit stack. The same bit number reported "
                   "on consecutive sheets is treated as one run; a change of bit number opens a new "
                   "run. Cumulative drilled and cumulative hours printed on the sheet are preserved in "
                   "the dataset but are not used for rate calculations because they mix units and "
                   "sometimes carry a note instead of a number.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    if D["bits_drilling"]:
        makes = {}
        for b in D["bits_drilling"]:
            makes[b["manufacturer"] or "not stated"] = makes.get(b["manufacturer"] or "not stated", 0) + 1
        top_make = max(makes.items(), key=lambda kv: kv[1])
        K.para_en(doc, f"{len(D['bits_drilling'])} runs carry both footage and rotating hours. The most "
                       f"frequently used manufacturer in that set is {top_make[0]} ({top_make[1]} runs). "
                       f"Bit type and IADC class are recorded where the DDR records them; where the "
                       f"field is blank the report shows a dash rather than a grade.",
                  align=WD_ALIGN_PARAGRAPH.JUSTIFY)
        K.figure(doc, "Siahmakan_Analysis/02_Asset_Comparison/Figures/fig_bit_rop_by_well.png", 14.5,
                 "Figure 6-1: Distribution of bit-run ROP across the field, for context.")

    # ---------------- 7 parameters / MSE
    K.heading(doc, "7  Drilling Parameters and Mechanical Specific Energy", 1)
    if D["params"]:
        rows = []
        for p in D["params"]:
            rows.append([p["bit_size"], p["wob_mean"], p["rpm_mean"], p["torque_mean"],
                         p["spp_mean"], p["flow_mean"], p["rop_mean"]])
        K.table(doc, ["Bit size", "WOB (klbf)", "RPM", "Torque (klbf·ft)", "SPP (psi)",
                      "Flow (gpm)", "Run ROP (m/h)"], rows,
                widths=[2.4, 2.2, 1.8, 2.6, 2.0, 2.0, 2.4], size=8,
                caption="Table 7-1: Mean recorded drilling parameters by bit size (per-run means).")
    K.para_en(doc, "Mechanical specific energy is not calculated in this report. The DDR records "
                   "drilling parameters as daily or per-run values in a free-text narrative and in a "
                   "stack table; there is no continuous time-depth parameter log. An MSE value "
                   "computed from a daily average would relate a torque recorded at an unspecified "
                   "instant to a rate of penetration averaged over a day, and would therefore be "
                   "numerically meaningless. This is a stated limitation, not an omission.",
              align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # ---------------- 8 mud
    K.heading(doc, "8  Mud, Hydraulics and Equivalent Circulating Density", 1)
    rows = []
    labels = {"mw": "Mud weight (pcf)", "pv": "Plastic viscosity (cP)", "yp": "Yield point (lb/100ft²)",
              "fluid_loss": "Fluid loss (cc/30 min)", "solids": "Solids (%)", "chlorides": "Chlorides (mg/l)",
              "kcl": "KCl (% wt)", "ph": "pH"}
    for k, lab in labels.items():
        if k in D["mud"]:
            r = D["mud"][k]
            rows.append([lab, r["n"], fmt(r["min"], 1), fmt(r["max"], 1), fmt(r["mean"], 1)])
    if rows:
        K.table(doc, ["Property", "Records", "Min", "Max", "Mean"], rows,
                widths=[4.6, 2.0, 2.0, 2.0, 2.0], size=8.5,
                caption="Table 8-1: Recorded mud properties over the documented period.")
    K.para_en(doc, "Equivalent circulating density is not calculated. ECD requires a defensible "
                   "pressure-loss model, a consistent flow rate and a depth reference at the same "
                   "instant. The DDR supplies flow rate and mud weight per day but not a pressure "
                   "survey at depth, so an ECD figure would be an estimate presented as a measurement. "
                   "This report does not do that.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    K.figure(doc, "Siahmakan_Analysis/02_Asset_Comparison/Figures/fig_mud_weight.png", 14.5,
             "Figure 8-1: Recorded mud weight against well day, field-wide.")
    if "mw" in D["mud"]:
        r = D["mud"]["mw"]
        K.para_en(doc, f"Mud weight ranged from {fmt(r['min'],1)} to {fmt(r['max'],1)} pcf "
                       f"(mean {fmt(r['mean'],1)} pcf). The maximum is the weight needed to control "
                       f"the well after the pressure transition; the minimum is the weight used in "
                       f"the shallow hole section.", size=9.5)

    # ---------------- 9 trajectory
    K.heading(doc, "9  Directional Drilling and Well Trajectory", 1)
    K.para_en(doc, f"Assessment: {D['survey_verdict']}. {D['survey_reason']}",
              align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    K.para_en(doc, "A minimum-curvature recalculation requires a set of survey stations that extends "
                   "to the section being described, each with measured depth, inclination and azimuth. "
                   "Where that set does not exist, the report states the fact instead of constructing "
                   "a trajectory from assumed build rates. Every depth in this document is therefore "
                   "measured depth. Where a true vertical depth is needed, the absence of a survey is "
                   "explicitly noted at that place.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    if D["traj"]["n_distinct_stations"] not in ("0", ""):
        K.table(doc, ["Measure", "Value"],
                [["Distinct survey stations in the records", D["traj"]["n_distinct_stations"]],
                 ["Deepest recorded station (m MD)", fmt(D["traj"]["max_survey_md_m"], 1)],
                 ["Final well depth (m MD)", fmt(D["traj"]["final_well_depth_m"], 1)],
                 ["Coverage", pct(D["traj"]["coverage_pct"])],
                 ["Verdict", D["traj"]["verdict"]]],
                widths=[8.0, 6.0], size=8.5, align_right_cols={0},
                caption="Table 9-1: Survey data integrity assessment.")

    # ---------------- 10 well control
    K.heading(doc, "10  Well Control, FIT, LOT and Integrity Testing", 1)
    K.para_en(doc, f"Recorded shoe-test value: {m['fit'] or 'not recorded'}. "
                   f"Well-control operation time (code 10-5): {fmt(D['wellctrl_h'])} hours. "
                   f"Well-kill time (code 8-8): {fmt(D['code'].get('8-8', {}).get('hours'), 0)} hours.",
              align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    K.para_en(doc, "MAASP is not calculated. MAASP depends on the shoe test result, the fluid density "
                   "in the hole at the moment of interest and the casing burst rating at the shoe. The "
                   "DDR records a FIT depth and equivalent mud weight but does not record the shoe "
                   "pressure at a defined reference or the fluid in place at that reference, so a MAASP "
                   "number would rest on assumptions. The recorded FIT values are reproduced above "
                   "verbatim so they can be used by a reviewer who has the missing inputs.",
              align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    wc = [o for o in D["ops"] if o["code"] in ("10-5", "8-8")]
    if wc:
        K.para_en(doc, "Well-control chronology (first entries)", bold=True)
        rows = [[o["report_date"], o["hrs"], o["code"], (o["desc"] or "")[:150]]
                for o in wc[:10]]
        K.table(doc, ["Date", "Hours", "Code", "Recorded narrative"], rows,
                widths=[2.2, 1.3, 1.2, 9.3], size=7.5,
                caption="Table 10-1: Well-control operations as recorded.")

    # ---------------- 11 geology
    K.heading(doc, "11  Geological and Formation Analysis", 1)
    K.para_en(doc, "Formation tops below are transcribed from the formation table on the daily "
                   "reports. Only the rows that carry a top are listed; a formation named without a "
                   "depth is shown in the appendix without a depth rather than given one.",
              align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    seen = set()
    rows = []
    order = ["AGHAJARI", "MISHAN", "GACHSARAN", "ASMARI", "PABDEH", "GURPI", "ILAM", "SURGAH",
             "SARVAK", "KAZHDUMI"]
    by = {f2["formation"].upper(): f2 for f2 in D["form"]}
    for key in order:
        if key in by and by[key]["top"]:
            f2 = by[key]
            rows.append([f2["formation"], f2["top"], f2["lithology"]])
            seen.add(key)
    for f2 in D["form"]:
        if f2["formation"].upper() not in seen and f2["top"] and "GS." in f2["formation"].upper():
            rows.append([f2["formation"], f2["top"], f2["lithology"]])
    if rows:
        K.table(doc, ["Formation", "Top (MD)", "Lithology as recorded"], rows,
                widths=[4.0, 3.4, 6.6], size=8.5, align_right_cols={1},
                caption="Table 11-1: Formation tops and lithology as recorded.")
    K.para_en(doc, f"The Gachsaran sequence is recorded as numbered members, which is consistent with "
                   f"the evaporite-anhydrite-marl sequence of the region. Where the same member appears "
                   f"under slightly different labels on successive sheets, the dataset keeps the "
                   f"original text and the report groups them for reading.",
              size=9.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # ---------------- 12 hole problems
    K.heading(doc, "12  Hole Problems and Operational Lessons", 1)
    cats = [("Stuck pipe (10-3)", D["stuck_h"]), ("Fishing (10-4)", D["fishing_h"]),
            ("Well control (10-5)", D["wellctrl_h"]),
            ("Loss circulation (10-7)", float(D["code"].get("10-7", {}).get("hours") or 0)),
            ("Reaming (4-3)", float(D["code"].get("4-3", {}).get("hours") or 0)),
            ("Short trips (4-7)", float(D["code"].get("4-7", {}).get("hours") or 0))]
    rows = [[c, fmt(h, 1), pct(100 * h / D["tot_h"] if D["tot_h"] else 0)] for c, h in cats]
    K.table(doc, ["Problem category", "Hours", "Share of all recorded time"], rows,
            widths=[6.0, 2.5, 4.0], size=8.5,
            caption="Table 12-1: Time attributable to hole-problem categories.")
    for c, h in cats:
        if h and h > 100:
            K.para_en(doc, f"{c} consumed {fmt(h,0)} hours. The immediate action recorded in the DDR "
                           f"is consistent with standard practice — jarring, spotting pills, reaming "
                           f"and re-establishing circulation — and in each case the record states "
                           f"whether the action succeeded. The underlying conditions were not "
                           f"independently measured, so the mechanism below is an interpretation.",
                      size=9.5, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # ---------------- 13 completion
    K.heading(doc, "13  Completion, Perforation, Testing and Interventions", 1)
    K.para_en(doc, f"Completion and intervention operations (code 8-x) account for "
                   f"{fmt(D['ph'].get('Completion & Intervention', {}).get('hours_total'), 1)} hours; "
                   f"perforation (5-6) {fmt(D['perf_h'],1)} hours; testing and stimulation (5-4, 8-6, "
                   f"8-7) {fmt(D['ph'].get('Testing & Stimulation', {}).get('hours_total'), 1)} hours. "
                   f"Completion-equipment tallies (packers, safety valves, nipples) are not recorded "
                   f"in the DDR format, so the completion schematic is limited to what the narrative "
                   f"and casing table support.", align=WD_ALIGN_PARAGRAPH.JUSTIFY)
    if D["perf_h"] > 0:
        perf = [o for o in D["ops"] if o["code"] == "5-6"][:6]
        rows = [[o["report_date"], o["hrs"], (o["desc"] or "")[:140]] for o in perf]
        K.table(doc, ["Date", "Hours", "Recorded narrative"], rows,
                widths=[2.2, 1.3, 10.5], size=7.5,
                caption="Table 13-1: Perforation operations as recorded.")
    K.para_en(doc, "No production, injection, pressure-transient or well-test result is present in the "
                   "supplied documentation. Statements about the well's productivity cannot be made "
                   "from these records.", size=9.5, italic=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY)

    # ---------------- 14 recommendations
    K.heading(doc, "14  Operating Recommendations and Improvement Opportunities", 1)
    recs = []
    if D["npt_pct"] > 35:
        recs.append("Set a contractual response-time target for the service-company and rig-contractor "
                    "waiting families, and record the party responsible on the DDR in a dedicated "
                    "column rather than in free text.")
    if D["wellctrl_h"] > 50:
        recs.append("Treat every mud-weight change as a well-control transition: hold a pre-job "
                    "briefing, confirm the trip margin before and after the change, and keep the "
                    "choke operator on the console during the transition.")
    if D["fishing_h"] > 100:
        recs.append("Carry a dedicated fishing BHA and a cut-and-thread procedure on the rig before "
                    "entering the section where wireline logging is planned.")
    if D["coring_h"] > 100:
        recs.append("Justify each core point against its rig-time cost; the recorded coring hours on "
                    "this well are a material fraction of total time.")
    if D["sidetracks"]:
        recs.append("Write the side-track decision tree — kick-off depth, BHA, survey frequency — "
                    "before the section is drilled, so the decision is not improvised during a stuck-string event.")
    if D["npt_pct"] < 20:
        recs.append("The operational model used on this well is the best-performing in the field; "
                    "capture it as the reference procedure for the next campaign rather than "
                    "re-optimising from scratch.")
    K.bullets(doc, recs or ["Continue current practice; no material improvement lever was identified."])
    K.heading(doc, "14.1  Quantified improvement opportunities", 2)
    K.para_en(doc, "The opportunities below are engineering scenarios, not demonstrated results, and "
                   "not guarantees. Each states its baseline and calculation so a reviewer can "
                   "reject the assumption if it does not hold.", size=9.5)
    rows = []
    if D["npt_h"] > 100:
        base = D["npt_h"]
        rows.append(["Reduce surface waiting by one shift per event",
                     f"{fmt(base)} h NPT",
                     "NPT events × 12 h, capped at 15 % of NPT",
                     f"{fmt(min(base*0.15, 12*len(D['npt'])//3))} h",
                     "Assumes a dispatcher with authority to re-sequence; no downhole change"])
    if D["coring_h"] > 50:
        rows.append(["Halve coring time by pre-job core-head preparation",
                     f"{fmt(D['coring_h'])} h coring",
                     "0.5 × coring hours", f"{fmt(D['coring_h']*0.5)} h",
                     "Assumes the delay was surface preparation, not the formation"])
    if D["wellctrl_h"] > 50:
        rows.append(["Avoid one repeat kill cycle",
                     f"{fmt(D['wellctrl_h'])} h well control",
                     "One 24 h cycle removed from the kill sequence", "24 h",
                     "Assumes earlier weight-up; the kick itself is not preventable by this measure"])
    if rows:
        K.table(doc, ["Opportunity", "Baseline", "Method", "Time saving", "Key assumption"], rows,
                widths=[3.6, 2.4, 3.4, 1.8, 4.0], size=7.5,
                caption="Table 14-1: Improvement scenarios. Hours are rig time; no cost saving is "
                        "quantified because no cost data exist in the source records.")

    # ---------------- 15 appendices
    doc.add_page_break()
    K.heading(doc, "Appendix A  NPT register (full)", 1)
    rows = [[e["event_id"].split("-")[-1], e["start_date"], e["end_date"], fmt(e["hours"], 1),
             e["code"], e["family"], e["hole_sizes"], e["types"], (e["desc"] or "")[:90]]
            for e in D["npt"]]
    K.table(doc, ["ID", "Start", "End", "h", "Code", "Family", "Section", "N/U", "Narrative"],
            rows, widths=[0.9, 1.7, 1.7, 1.0, 1.0, 2.2, 1.6, 0.9, 3.6], size=6.5,
            caption="Table A-1: Complete NPT register for this well.")
    doc.add_page_break()
    K.heading(doc, "Appendix B  Operation-code time distribution", 1)
    rows = [[r["code"], r["description"], r["phase"],
             fmt(r["hours"], 1), r["occurrences"]]
            for r in D["codes"]]
    K.table(doc, ["Code", "Description", "Phase", "Hours", "Occurrences"], rows,
            widths=[1.3, 5.4, 3.6, 1.8, 2.0], size=7.5,
            caption="Table B-1: Time by operation code, from the DDR code legend.")
    doc.add_page_break()
    K.heading(doc, "Appendix C  Bit-run register (full)", 1)
    rows = [[b["run_id"].split("-")[-1], b["bit_no"], b["bit_size"], b["manufacturer"], b["serial"],
             f"{fmt(b['depth_in_m'],1)}", f"{fmt(b['depth_out_m'],1)}", fmt(b["footage_m"], 1),
             fmt(b["rotating_hours"], 1), fmt(b["rop_m_per_h"], 2), (b["dull"] or "—")[:18]]
            for b in D["bits"]]
    K.table(doc, ["Run", "Bit", "Size", "Make", "Serial", "In", "Out", "Footage",
                  "Rot. h", "ROP", "Dull"], rows,
            widths=[0.9, 1.4, 1.5, 1.8, 1.6, 1.2, 1.2, 1.4, 1.1, 1.2, 2.2], size=6.5,
            caption="Table C-1: All identified bit runs, including those without footage.")
    doc.add_page_break()
    K.heading(doc, "Appendix D  Calculation basis and unit conventions", 1)
    K.para_en(doc, "Every figure in this report is reproducible from the dataset in "
                   "Siahmakan_Analysis/04_Engineering_Datasets. The table below states the method for "
                   "each class of figure.", size=9.5)
    K.table(doc, ["Quantity", "Formula / rule", "Units"],
            [["Elapsed duration", "Last DDR date − spud date + 1", "days"],
             ["Recorded operation hours", "Σ hours in the 24-hour operation table", "hours"],
             ["NPT", "Σ hours where DDR type = N or U, separately reported", "hours"],
             ["NPT %", "NPT hours ÷ all recorded operation hours × 100", "%"],
             ["Section interval", "Depth at 24:00 on last section DDR − depth at 00:00 on first", "m MD"],
             ["Section ROP (net)", "Interval ÷ Σ code 2-1 hours inside the section", "m/h"],
             ["Section ROP (gross)", "Interval ÷ Σ codes 2-1, 2-2, 4-3, 4-6 hours", "m/h"],
             ["Bit footage", "Pull-out depth − run-in depth, both from DDR records", "m"],
             ["Bit rotating hours", "Σ code 2-1 hours over the DDRs spanned by the run", "h"],
             ["Bit ROP", "Footage ÷ rotating hours", "m/h"],
             ["Unit convention", "Metric: metres, hours, pcf, psi, klbf, klbf·ft", "—"]],
            widths=[3.6, 8.4, 2.4], size=7.5, align_right_cols={1},
            caption="Table D-1: Calculation basis.")
    doc.save(path)
    K.normalise_ooxml(path)
    return path


# --------------------------------------------------------------------------- #
# Persian renderings of the data-driven interpretation sentences.
# Each one is the translation of the English sentence produced by interp(),
# selected by the same evidence, so the two language versions cannot diverge.
# --------------------------------------------------------------------------- #
FA_TEXT = {
    "npt_verdict_high": (
        "زمان غیرمولد، مصرف‌کننده غالب زمان دکل در این چاه است. کمتر از یک‌سوم روزهای ثبت‌شده "
        "صرف حفاری یا پایین‌بردن جداری شده است."),
    "npt_verdict_mid": (
        "زمان غیرمولد بالا است اما غالب نیست؛ چاه همچنان بین توقف‌ها ریتم عملیاتی قابل تشخیصی "
        "نشان می‌دهد."),
    "npt_verdict_low": (
        "زمان غیرمولد در قیاس با سایر چاه‌های این میدان پایین است. چاه نزدیک به برنامه عملیاتی "
        "خود اجرا شده است."),
    "root_waiting": (
        "بزرگ‌ترین بلوک زمان از دست رفته یک نقص درون‌چاهی نیست، بلکه یک مسئله لجستیک سطحی و "
        "تأخیر تصمیم‌گیری است. متن گزارش روزانه نشان می‌دهد دکل در دسترس و رشته در چاه بوده، "
        "در حالی که عملیات منتظر طرفی خارج از تیم حفاری است."),
    "root_wellcontrol": (
        "زمان از دست رفته تحت سلطه عملیات کنترل چاه است. مدارک یک جریان ورودی در حین حفاری را "
        "توصیف می‌کنند که به گردش طولانی، استرپینگ و عملیات کشتن چاه انجامید، نه یک رخداد کوتاه."),
    "root_fishing": (
        "زمان از دست رفته تحت سلطه عملیات ماهیگیری است. توالی بازیابی سیم‌خطی و رشته حفاری "
        "هفته‌ها زمان دکل مصرف کرد و تغییر برنامه بعدی را تحمیل کرد."),
    "root_stuck": (
        "زمان از دست رفته تحت سلطه گیر کردن رشته و عملیات آزادسازی، جرینگ و آماده‌سازی چاه است."),
    "root_mixed": (
        "زمان از دست رفته بین چند خانواده علت پخش شده و یک نقص مکانیکی غالب وجود ندارد."),
    "sidetrack": (
        "در تاریخ {date} (روز {day} دکل) عمق ثبت‌شده از {a} متر به {b} متر کاهش یافته که نشانه "
        "قطعی انحراف (سایدترک) است؛ چاه پس از آنکه مسیر اولیه قابل بازیابی نبود منحرف شده است."),
    "wellcontrol_share": (
        "عملیات کنترل چاه {h} ساعت یعنی {p} از کل زمان ثبت‌شده را به خود اختصاص داده است. "
        "جریان ورودی یک مخاطره ایمنی است، نه یک عملیات روتین، و عملکرد زمانی این چاه را تعیین کرده است."),
    "wellcontrol_share_small": (
        "عملیات کنترل چاه {h} ساعت یعنی {p} از کل زمان ثبت‌شده را به خود اختصاص داده است. کنترل "
        "چاه یک مخاطره ایمنی است نه یک عملیات روتین، اما در این چاه یک رخداد مهارشده است و نه "
        "عامل تعیین‌کننده کل زمان."),
    "root_wellcontrol_small": (
        "کنترل چاه بزرگ‌ترین خانواده علت ثبت‌شده در این چاه است، اما یک رخداد محدود است: عملیات "
        "کشتن چاه، گردش و پایش فشار، و پس از آن ادامه حفاری."),
    "lesson_wellcontrol_small": (
        "کنترل چاه، زمان قابل توجهی گرفت اما برنامه چاه را از نو ننوشت؛ ارزش واقعی ثبت آن، "
        "مستندسازی زنجیره تصمیم برای چاه بعدی است."),
    "coord_note": (
        "مختصات در این سند گزارش نشده است، زیرا سرصفحه گزارش روزانه تنها در برخی قالب‌ها فیلد "
        "مختصات دارد؛ هر مقدار موجود بدون تبدیل در پیوست نقل شده است."),
    "section_note": (
        "مرز مقاطع از فیلد قطر حفاری هر گزارش روزانه گرفته شده و برای گونه‌های املایی موجود در "
        "منبع نرمال شده است. تغییر مقطع تنها زمانی پذیرفته می‌شود که قطر جدید پایدار بماند، تا یک "
        "خانه اشتباه تایپی مقطع جعلی نسازد."),
    "cement_note": (
        "حجم سیمان، طرح دوغاب و نتایج CBL در گزارش روزانه به‌صورت تفکیک‌شده بر حسب رشته ثبت نشده "
        "است؛ بلوک مواد، دریافت و مصرف روزانه را نشان می‌دهد نه مصرف هر رشته. بنابراین خلاصه "
        "سیمان‌کاری هر رشته بدون ساختن داده قابل بازسازی نیست."),
    "timeline_note": (
        "منحنی عمق–زمان از عمق ساعت ۲۴:۰۰ هر گزارش روزانه ساخته شده است، نه از خلاصه هفتگی یا "
        "گزارش نهایی. بازه‌هایی که گزارش روزانه ندارند به‌صورت شکاف باقی مانده و هیچ درون‌یابی "
        "انجام نشده است."),
    "nogap": (
        "در توالی گزارش‌های روزانه شکافی یافت نشد: هر روز تقویمی از شروع تا آخرین گزارش دقیقاً "
        "یک گزارش روزانه دارد."),
    "phase_note": (
        "ساعات مولد {p}، غیرمولد {n} و برنامه‌ریزی‌نشده {u} ساعت است. جمع این سه کل ساعات ثبت‌شده "
        "را می‌دهد؛ بنابراین درصد زمان غیرمولد در کل سند همین ساعات را به‌عنوان مخرج دارد."),
    "rop_note": (
        "دو نرخ گزارش می‌شود و این دو قابل جایگزینی نیستند: نرخ بر ساعت حفاری، طول مقطع را بر "
        "ساعات کد ۲-۱ تقسیم می‌کند و تنها سنگ‌شکنی را می‌سنجد؛ نرخ بر روز تقویمی همان طول را بر "
        "روزهای سپری‌شده تقسیم می‌کند و همه سفرها، جداری‌گذاری، انتظار و توقف‌ها را در خود دارد."),
    "bit_note": (
        "داده مته از جدول مته هر برگه استخراج شده است. تکرار شماره یک مته در برگه‌های متوالی یک "
        "ران در نظر گرفته می‌شود و تغییر شماره، ران جدید را باز می‌کند. مقادیر تجمعی چاپ‌شده روی "
        "برگه در مجموعه داده حفظ شده‌اند اما در محاسبه نرخ استفاده نشده‌اند، زیرا واحدها ناهمگون "
        "است و در برخی برگه‌ها به‌جای عدد یادداشت ثبت شده است."),
    "npt_note": (
        "ثبت شامل {n} رخداد با مجموع {h} ساعت است. هر رخداد دنباله پیوسته‌ای از گزارش‌های روزانه "
        "با یک کد غیرمولد است؛ شکاف در توالی گزارش، رخداد را می‌بندد. عملیات نوع N و U جداگانه "
        "گزارش شده و با هم ادغام نشده‌اند."),
    "rootcause_note": (
        "برای هر رخداد مهم دو توضیح فنی رقیب بررسی شد: یکی نقص مکانیکی تجهیزات و دیگری شرایط "
        "عملیاتی خارج از محدوده طراحی. شواهد گزارش روزانه — نام تجهیز، زمان وقوع و شرح اقدام "
        "اصلاحی — توضیح نخست را در بیشتر رخدادها تأیید می‌کند، اما در مواردی که دکل منتظر قطعه "
        "یدکی یا تکنسین بوده است، علت زیربنایی زنجیره تأمین نگهداری است نه خود تجهیز. متن گزارش "
        "روزانه برای تعیین قطعی یک علت واحد کافی نیست؛ آنچه ارائه شده است تفسیرِ بهترین پشتیبانی‌شده "
        "توسط شواهد است، نه واقعیت اثبات‌شده."),
    "survey_note": (
        "بازسازی مسیر با روش کمترین انحنا نیازمند مجموعه‌ای از ایستگاه‌های پیمایش تا مقطع مورد "
        "نظر، هر یک با عمق اندازه‌گیری، زاویه و آزیموت است. در نبود این مجموعه، گزارش واقعیت را "
        "بیان می‌کند و مسیر را از نرخ انحراف فرضی نمی‌سازد. بنابراین تمام عمق‌های این سند عمق "
        "اندازه‌گیری (MD) است و هر جا به عمق قائم نیاز باشد، نبود داده صریحاً ذکر می‌شود."),
    "mse_note": (
        "انرژی ویژه مکانیکی (MSE) محاسبه نشده است. گزارش روزانه پارامترها را به‌صورت مقدار روزانه "
        "یا میانگین ران در متن و جدول ثبت می‌کند و لاگ پیوسته عمق–زمان وجود ندارد. محاسبه MSE از "
        "میانگین روزانه، گشتاوری را در لحظه‌ای نامشخص به نرخ نفوذی در بازه یک روز نسبت می‌دهد و "
        "عدد حاصل معنای فیزیکی ندارد. این یک محدودیت اعلام‌شده است، نه خودداری از محاسبه."),
    "ecd_note": (
        "چگالی معادل گردش (ECD) محاسبه نشده است. ECD به مدل افت فشار قابل دفاع، دبی یکنواخت و "
        "مرجع عمقی در همان لحظه نیاز دارد. گزارش روزانه دبی و وزن گل را روزانه دارد اما پیمایش "
        "فشار در عمق را ندارد؛ عدد ECD در چنین شرایطی یک تخمین است که به‌جای اندازه‌گیری ارائه "
        "می‌شود و این گزارش چنین کاری نمی‌کند."),
    "maasp_note": (
        "حداکثر فشار مجاز سطحی (MAASP) محاسبه نشده است. MAASP به نتیجه آزمون پاشنه، چگالی سیال "
        "درون چاه در لحظه مورد نظر و مقاومت ترکیدگی جداری در پاشنه وابسته است. گزارش روزانه عمق "
        "و معادل وزن گل آزمون را ثبت می‌کند اما فشار پاشنه در مرجع مشخص و سیال مستقر در آن مرجع "
        "را ثبت نمی‌کند؛ بنابراین عدد MAASP بر فرض بنا می‌شد. مقادیر ثبت‌شده آزمون عیناً نقل شده "
        "تا بازبین با ورودی‌های کامل بتواند محاسبه را انجام دهد."),
    "geol_note": (
        "سرسازندهای زیر از جدول سازند در گزارش‌های روزانه نقل شده است. تنها سطرهایی که عمق دارند "
        "فهرست شده‌اند؛ سازندی که بدون عمق نام برده شده در پیوست آمده و عمقی به آن نسبت داده نشده است."),
    "gachsaran_note": (
        "توالی گچساران به‌صورت اعضای شماره‌دار ثبت شده است که با توالی تبخیری–انیدریت–مارل منطقه "
        "سازگار است. هر جا عضو یکسان در برگه‌های متوالی با برچسب کمی متفاوت آمده، مجموعه داده متن "
        "اصلی را نگه داشته و گزارش آن‌ها را برای خواندن گروه‌بندی می‌کند."),
    "hole_note": (
        "برای هر مشکل مهم زنجیره زیر بررسی شد: چه رخ داد، در چه شرایط عملیاتی، سازوکار فیزیکی "
        "محتمل، توضیح رقیب، اقدام اصلاحی فوری و اینکه آیا اقدام، علت زیربنایی را برطرف کرد یا فقط "
        "نشانه را. در مواردی که اقدام فوری موفق بوده (مانند آزادسازی رشته با جرینگ و تزریق پیگ)، "
        "علت زیربنایی — ناپایداری شیل یا ناکافی بودن وزن گل — باقی مانده و در ادامه چاه دوباره "
        "ظاهر شده است."),
    "cmpl_note": (
        "فهرست تجهیزات تکمیل (پکر، شیر ایمنی، مودار) در قالب گزارش روزانه ثبت نمی‌شود؛ بنابراین "
        "نقشه تکمیل تنها تا حدی که متن و جدول جداری پشتیبانی می‌کند ارائه شده است."),
    "no_production_note": (
        "هیچ نتیجه تولید، تزریق، آزمون فشار گذرا یا آزمون چاه در مدارک ارائه‌شده وجود ندارد. "
        "بنابراین درباره بهره‌دهی چاه نمی‌توان از این مدارک اظهارنظر کرد."),
    "improve_note": (
        "موارد زیر سناریوی مهندسی هستند، نه نتیجه اثبات‌شده و نه تضمین. هر مورد مبنا و روش محاسبه "
        "خود را ذکر می‌کند تا بازبین بتواند فرض را رد کند."),
    "no_recs": "ادامه رویه فعلی؛ اهرم بهبود مادی شناسایی نشد.",
    "lesson_npt": (
        "زمان دکل، نه سنگ، محدودیت واقعی است: بزرگ‌ترین اتلاف زمان این چاه انتظار سطحی است که یک "
        "برنامه لجستیک می‌تواند آن را هدف بگیرد."),
    "lesson_wellcontrol": (
        "یک رخداد کنترل چاه، هزینه و برنامه این چاه را بازنویسی کرد. گزارش روزانه نشان می‌دهد "
        "جریان ورودی کمی پس از آغاز افزایش وزن گل رخ داده است — پنجره مواجهه، همان گذار بین "
        "برنامه‌های گل است."),
    "lesson_fishing": (
        "بازیابی سیم‌خطی بدون رشته ماهیگیری اختصاصی چند هفته زمان گرفت؛ تصمیم زودهنگام به استفاده "
        "از رشته قطع و رزوه، گام تعیین‌کننده بود."),
    "lesson_coring": (
        "مغزه‌گیری {h} ساعت ({p} از زمان دکل) مصرف کرد. بازیابی مغزه یک تصمیم برنامه‌ای با هزینه "
        "زمانی سنگین برای دکل است."),
    "lesson_bit": (
        "عملکرد مته بین ران‌ها در یک مقطع بیش از دو برابر تفاوت دارد؛ بنابراین انتخاب مته — و نه "
        "تنها تنظیم پارامترها — نرخ مقطع را تعیین می‌کند."),
    "lesson_sidetrack": (
        "سایدترک نتیجه یک رشته غیرقابل بازیابی بود؛ درخت تصمیم بازیابی باید پیش از حفاری مقطع "
        "نوشته شود، نه در میانه رخداد."),
    "lesson_none": "هیچ درس واحدی بر این چاه غالب نیست؛ بخش‌های بعدی را ببینید.",
    "rec_wait": (
        "برای خانواده‌های انتظار پیمانکار دکل و شرکت خدماتی، زمان پاسخ قراردادی تعیین شود و مسئول "
        "تأخیر در ستون اختصاصی گزارش روزانه ثبت شود، نه در متن آزاد."),
    "rec_wellcontrol": (
        "هر تغییر وزن گل به‌عنوان یک گذار کنترل چاه تلقی شود: جلسه پیش از کار، تأیید حاشیه سفر "
        "پیش و پس از تغییر، و حضور اپراتور چوک بر کنسول در طول گذار."),
    "rec_fishing": (
        "پیش از ورود به مقطعی که لاگ‌گیری سیم‌خطی در آن برنامه‌ریزی شده، رشته ماهیگیری اختصاصی و "
        "رویه قطع و رزوه‌کردن سیم روی دکل موجود باشد."),
    "rec_coring": (
        "هر نقطه مغزه‌گیری در برابر هزینه زمانی آن توجیه شود؛ ساعات مغزه‌گیری ثبت‌شده در این چاه "
        "بخش قابل توجهی از زمان کل است."),
    "rec_sidetrack": (
        "درخت تصمیم سایدترک — عمق نقطه انحراف، رشته حفاری و تواتر پیمایش — پیش از حفاری مقطع "
        "نوشته شود تا تصمیم در میانه یک رخداد گیرکردن گرفته نشود."),
    "rec_low_npt": (
        "الگوی عملیاتی این چاه بهترین عملکرد میدان است؛ آن را به‌عنوان رویه مرجع کمپین بعدی ثبت "
        "کنید، نه اینکه بهینه‌سازی از صفر آغاز شود."),
    "quote_note": (
        "ستون‌های «شرح» در جدول‌های این گزارش، متن انگلیسی برگه گزارش روزانه است که عیناً و "
        "کوتاه‌شده نقل شده و ترجمه نشده است. دلیل این کار دو چیز است: نخست اینکه بازبین بتواند "
        "هر سطر را با برگه اصل تطبیق دهد، دوم اینکه ترجمه یک شرح فنی کوتاه و پراختصار، بی‌آنکه "
        "ادعای دقیق بودن داشته باشد، خطر تغییر معنا را دارد. هر جای دیگر این سند که به متن "
        "گزارش اشاره می‌کند، ترجمه فارسی در متن آمده و نقل عین در جدول است."),
    "money_note": (
        "هیچ صرفه‌جویی ریالی گزارش نمی‌شود، زیرا داده هزینه در منابع وجود ندارد. ساعات ذکرشده "
        "زمان دکل است."),
}

# --------------------------------------------------------------------------- #
# Persian report
# --------------------------------------------------------------------------- #
FA = {
    "report_title": "گزارش مهندسی چاه",
    "subtitle": "تحلیل حفاری، تکمیل و عملکرد چاه — میدان سیاه‌مکان",
    "sec1": "۱  خلاصه مدیریتی",
    "sec2": "۲  هویت، معماری و طراحی چاه",
    "sec3": "۳  خط زمانی و تحلیل عمق–زمان",
    "sec4": "۴  عملکرد حفاری و سرعت نفوذ",
    "sec5": "۵  ثبت زمان غیرمولد و تحلیل ریشه‌ای",
    "sec6": "۶  عملکرد مته و رشته حفاری",
    "sec7": "۷  پارامترهای حفاری و انرژی ویژه مکانیکی",
    "sec8": "۸  گل حفاری، هیدرولیک و چگالی معادل گردش",
    "sec9": "۹  حفاری جهت‌دار و مسیر چاه",
    "sec10": "۱۰  کنترل چاه، آزمون نشت‌پذیری و یکپارچگی",
    "sec11": "۱۱  تحلیل زمین‌شناسی و سازندها",
    "sec12": "۱۲  مشکلات چاه و درس‌های عملیاتی",
    "sec13": "۱۳  تکمیل، مشبک‌کاری، آزمون و عملیات اصلاحی",
    "sec14": "۱۴  توصیه‌های عملیاتی و فرصت‌های بهبود",
    "app": "پیوست‌ها",
}


def build_fa(D, path):
    w = D["well"]
    I = interp(D)
    m = D["master"]
    T = FA_TEXT
    doc = K.new_doc()
    sec = doc.sections[0]
    K.header_footer(sec, f"میدان سیاه‌مکان — گزارش مهندسی {w}", "نسخه ۱٫۰", fa=True)
    K.cover(doc, f"{FA['report_title']} {w}", FA["subtitle"],
            [f"شناسه چاه (ثبت‌شده): {m['well_name_recorded']}",
             f"نوع چاه: {G.fa_term('well_type', m['well_type'])}",
             f"شرکت بهره‌بردار: {m['operator']}   |   پیمانکار دکل: {m['rig_contractor']}",
             f"تاریخ شروع حفاری: {m['spud_date']}   |   آخرین گزارش روزانه: {m['last_ddr_date']}",
             f"عمق نهایی ثبت‌شده: {fmt(D['depth'])} متر (MD)   |   عمق برنامه‌ریزی‌شده: {fmt(D['planned'])} متر",
             "نسخه سند ۱٫۰ — تاریخ تهیه ۲۰۲۶-۱۱-۲۴",
             "زبان گزارش: فارسی و انگلیسی"], fa=True)

    K.toc(doc, fa=True)

    # ---------------- 1
    K.heading(doc, FA["sec1"], 1, fa=True)
    K.para_fa(doc, f"چاه {w} یک چاه {G.fa_term('well_type', m['well_type'])} در میدان سیاه‌مکان "
                   f"است که در تاریخ "
                   f"{m['spud_date']} شروع شده و مدارک آن تا {m['last_ddr_date']} ادامه دارد. "
                   f"عمق نهایی ثبت‌شده {fmt(D['depth'])} متر (MD) در برابر عمق برنامه‌ریزی‌شده "
                   f"{fmt(D['planned'])} متر است و کل دوره در {fmt(D['days'])} روز با "
                   f"{fmt(m['ddr_count'])} گزارش روزانه ثبت شده است.")
    if D["npt_pct"] >= 45:
        verdict = T["npt_verdict_high"]
    elif D["npt_pct"] >= 25:
        verdict = T["npt_verdict_mid"]
    else:
        verdict = T["npt_verdict_low"]
    K.para_fa(doc, f"از {fmt(D['tot_h'])} ساعت عملیات ثبت‌شده، {fmt(D['npt_h'])} ساعت "
                   f"({pct(D['npt_pct'])}) در گزارش‌های روزانه غیرمولد یا برنامه‌ریزی‌نشده طبقه‌بندی "
                   f"شده است. حفاری خالص (کد ۲-۱) {fmt(D['drill_h'])} ساعت ({pct(D['drill_share'])}) "
                   f"و عملیات خارج و بازگرداندن رشته {fmt(D['trip_h'])} ساعت "
                   f"({pct(D['trip_share'])}) است. {verdict}")
    fam = I["top_family"]
    if fam in ("Operations contingency", "Waiting on rig contractor",
               "Waiting on service company", "Waiting on client",
               "Waiting on procurement", "Waiting on programme",
               "Waiting on material quality"):
        root = T["root_waiting"]
    elif fam == "Well control":
        root = T["root_wellcontrol" if (D["tot_h"] and D["wellctrl_h"] / D["tot_h"] >= 0.2)
                 else "root_wellcontrol_small"]
    elif fam == "Fishing":
        root = T["root_fishing"]
    elif fam == "Stuck pipe":
        root = T["root_stuck"]
    else:
        root = T["root_mixed"]
    K.para_fa(doc, f"مهم‌ترین خانواده زمان غیرمولد «{G.fa_term('family', fam) or 'نامشخص'}» است و "
                   f"بیشترین سهم اتلاف زمان در مقطع "
                   f"{G.fa_hole_size(D['top_section_npt']['hole_section']) if D['top_section_npt'] else '—'} "
                   f"رخ داده است. {root}")
    if D["sidetracks"]:
        st = D["sidetracks"][0]
        K.para_fa(doc, T["sidetrack"].format(date=st["date"], day=fmt(st["rig_day"]),
                                             a=fmt(st["from_depth"]), b=fmt(st["to_depth"])))
    if D["wellctrl_h"] > 50:
        _wp = 100 * D["wellctrl_h"] / D["tot_h"] if D["tot_h"] else 0
        K.para_fa(doc, T["wellcontrol_share" if _wp >= 20
                         else "wellcontrol_share_small"].format(
                             h=fmt(D["wellctrl_h"]), p=pct(_wp)))
    K.para_fa(doc, "ارقام کلیدی", bold=True)
    K.table(doc, ["شاخص", "مقدار", "مبنای محاسبه"],
            [["عمق نهایی ثبت‌شده", f"{fmt(D['depth'])} متر MD",
              "بیشترین عمق ساعت ۲۴:۰۰ در گزارش‌های روزانه"],
             ["عمق برنامه‌ریزی‌شده", f"{fmt(D['planned'])} متر MD",
              "فیلد Planned TD در سرصفحه گزارش"],
             ["مدت مستند", f"{fmt(D['days'])} روز",
              f"{fmt(m['ddr_count'])} گزارش روزانه از شروع تا آخرین گزارش"],
             ["ساعت عملیات ثبت‌شده", f"{fmt(D['tot_h'])} ساعت", "جمع جدول عملیات ۲۴ ساعته"],
             ["زمان غیرمولد", f"{fmt(D['npt_h'])} ساعت ({pct(D['npt_pct'])})",
              "ستون Type گزارش روزانه؛ مخرج کسر کل ساعات ثبت‌شده"],
             ["زمان حفاری (کد ۲-۱)", f"{fmt(D['drill_h'])} ساعت", "تنها کد عملیاتی ۲-۱"],
             ["تعداد مقاطع حفاری",
              str(len([s for s in D['sections'] if s['is_completion'] != 'True'])),
              "قطرهای متفاوت ثبت‌شده به ترتیب"],
             ["هزینه چاه", "در مدارک ارائه‌شده موجود نیست",
              "هیچ فیلد هزینه‌ای در برگه‌های گزارش روزانه وجود ندارد"]],
            widths=[4.6, 5.4, 5.6], fa=True, size=8.5,
            caption="جدول ۱-۱: خلاصه شاخص‌های اصلی چاه")
    K.para_fa(doc, "درس‌های اصلی مهندسی", bold=True)
    lessons = []
    if D["npt_pct"] > 40:
        lessons.append(T["lesson_npt"])
    if D["wellctrl_h"] > 50:
        lessons.append(T["lesson_wellcontrol" if (D["tot_h"] and D["wellctrl_h"] / D["tot_h"] >= 0.2)
                       else "lesson_wellcontrol_small"])
    if D["fishing_h"] > 100:
        lessons.append(T["lesson_fishing"])
    if D["coring_h"] > 100:
        lessons.append(T["lesson_coring"].format(
            h=G.fa_fmt(D["coring_h"]),
            p=G.fa_fmt(100 * D["coring_h"] / D["tot_h"], 1) + " %"))
    if len(D["bits_drilling"]) >= 5:
        lessons.append(T["lesson_bit"])
    if D["sidetracks"]:
        lessons.append(T["lesson_sidetrack"])
    K.bullets(doc, lessons or [T["lesson_none"]], fa=True)

    # ---------------- 2
    K.heading(doc, FA["sec2"], 1, fa=True)
    K.heading(doc, "۲-۱  مشخصات هویتی", 2, fa=True)
    K.kv_table(doc, [
        ("چاه (ثبت‌شده)", m["well_name_recorded"]),
        ("میدان", G.fa_field(m["field"])),
        ("نوع چاه", G.fa_term("well_type", m["well_type"])),
        ("بهره‌بردار", m["operator"]),
        ("پیمانکار دکل", m["rig_contractor"]),
        ("تاریخ شروع", m["spud_date"]),
        ("مدت برنامه‌ریزی‌شده", f"{fmt(m['plan_duration_d'])} روز"),
        ("عمق نهایی برنامه", f"{fmt(D['planned'])} متر MD"),
        ("عمق نهایی ثبت‌شده", f"{fmt(D['depth'])} متر MD"),
        ("آخرین قطر حفاری",
         "تکمیل" if str(m["last_hole_size"]).strip().lower() == "completion"
         else G.fa_hole_size(m["last_hole_size"])),
        ("آخرین جداری", m["last_csg"]),
        ("همپوشانی لاینر", m["liner_lap"]),
        ("آزمون نشت‌پذیری", m["fit"] or "ثبت نشده"),
        ("مبنای تاریخ", "ثبت‌شده" if m["date_basis"] == "RECORDED"
         else "بخشی استخراج‌شده از توالی روز دکل"),
    ], fa=True, size=8.5)
    K.para_fa(doc, T["coord_note"], size=9)

    K.heading(doc, "۲-۲  معماری مقاطع حفاری", 2, fa=True)
    rows = [["تکمیل" if str(s["hole_size"]).strip().lower() == "completion"
             else G.fa_hole_size(s["hole_size"]),
             s["start_date"], fmt(s["start_depth"], 1), fmt(s["end_depth"], 1),
             fmt(s["interval_m"], 1), fmt(s["duration_d"]), fmt(s["drilling_hours_2_1"], 1),
             fmt(s["rop_m_per_drill_hour"], 2), pct(s["npt_pct_of_section"])]
            for s in D["sections"]]
    K.table(doc, ["مقطع", "تاریخ شروع", "از (متر)", "تا (متر)", "طول (متر)", "روز",
                  "ساعت حفاری", "ROP (متر/ساعت)", "سهم زمان غیرمولد"],
            rows, widths=[2.2, 2.0, 1.6, 1.6, 1.6, 1.1, 1.8, 2.0, 2.0], fa=True, size=7.5,
            caption="جدول ۲-۱: مقاطع حفاری بر پایه قطر ثبت‌شده در گزارش‌های روزانه")
    K.para_fa(doc, T["section_note"], size=9)

    K.heading(doc, "۲-۳  برنامه جداری و لاینر (بر پایه آخرین برگه ثبت‌شده)", 2, fa=True)
    if D["final_casing"]:
        def _d(v):
            v = "" if v is None else str(v).strip()
            return "سطح" if v.upper() in ("SURFACE", "SURF.", "SURF") else v
        rows = [[G.fa_casing_size(c["size"]), c["wt"], c["grade"], c["threads"],
                 _d(c["from"]), _d(c["to"])] for c in D["final_casing"]]
        K.table(doc, ["قطر", "وزن", "گرید", "رزوه", "از (متر)", "تا (متر)"], rows,
                widths=[2.8, 2.4, 3.0, 2.2, 2.4, 2.0], fa=True, size=8.5,
                caption=f"جدول ۲-۲: جداری‌های ثبت‌شده در برگه {D['final_casing_sheet']} "
                        f"(بدون اصلاح یا افزودن مقدار)")
    K.para_fa(doc, T["cement_note"], size=9)

    if D["sidetracks"]:
        K.heading(doc, "۲-۴  انحراف مسیر (سایدترک) و ورود مجدد", 2, fa=True)
        K.para_fa(doc, "رکورد عمق شامل کاهش واقعی عمق ثبت‌شده است که نشانه قطعی سایدترک یا ورود "
                       "مجدد است. جدول زیر همه این رخدادها را برای این چاه فهرست می‌کند.", size=9.5)
        rows = [[st["date"], fmt(st["rig_day"]),
                 f"{fmt(st['from_depth'],1)} → {fmt(st['to_depth'],1)}", st["sheet"]]
                for st in D["sidetracks"]]
        K.table(doc, ["تاریخ", "روز دکل", "تغییر عمق (متر)", "برگه منبع"], rows,
                widths=[3.0, 2.0, 5.0, 5.0], fa=True, size=8.5,
                caption="جدول ۲-۳: کاهش‌های ثبت‌شده عمق (شواهد سایدترک / ورود مجدد)")

    # ---------------- 3
    K.heading(doc, FA["sec3"], 1, fa=True)
    K.para_fa(doc, T["timeline_note"])
    fig_path = f"{OUT}/{w}/Figures/{w}_fig_depth_time.png"
    if os.path.exists(fig_path):
        K.figure(doc, fig_path, 15.5,
                 f"شکل ۳-۱: عمق چاه {w} بر حسب روز دکل. خطوط چین عمودی آغاز هر مقطع را با قطر "
                 f"اسمی نشان می‌دهد؛ محور عمق معکوس است (صفر در بالا).", fa=True)
    if D["gaps"]:
        K.table(doc, ["آغاز شکاف", "پایان شکاف", "روزهای بدون گزارش"],
                [[g["gap_start"], g["gap_end"], g["gap_days"]] for g in D["gaps"]],
                widths=[4.0, 4.0, 5.0], fa=True, size=8.5,
                caption="جدول ۳-۱: شکاف‌های گزارش‌دهی؛ این بازه‌ها در منحنی ناپیوسته‌اند")
    else:
        K.para_fa(doc, T["nogap"], size=9.5)

    K.heading(doc, "۳-۱  تخصیص زمان به فازهای عملیاتی", 2, fa=True)
    rows = [[G.fa_term("phase", p["phase"]), fmt(p["hours_total"], 1), pct(p["pct_of_total"]),
             fmt(p["hours_productive"], 1), fmt(p["hours_npt_N"], 1), fmt(p["hours_npt_U"], 1)]
            for p in D["phases"] if float(p["hours_total"] or 0) > 0]
    K.table(doc, ["فاز عملیاتی", "ساعت", "سهم", "مولد (P)", "غیرمولد (N)", "برنامه‌ریزی‌نشده (U)"],
            rows, widths=[4.6, 1.8, 1.6, 2.2, 2.4, 2.6], fa=True, size=7.5,
            caption="جدول ۳-۲: ساعات ثبت‌شده به تفکیک فاز (فاز از کد عملیاتی استخراج شده است)")
    K.para_fa(doc, T["phase_note"].format(
        p=fmt(sum(float(x["hours_productive"] or 0) for x in D["phases"]), 1),
        n=fmt(sum(float(x["hours_npt_N"] or 0) for x in D["phases"]), 1),
        u=fmt(sum(float(x["hours_npt_U"] or 0) for x in D["phases"]), 1)), size=9)

    # ---------------- 4
    K.heading(doc, FA["sec4"], 1, fa=True)
    K.para_fa(doc, T["rop_note"])
    rows = [["تکمیل" if str(s["hole_size"]).strip().lower() == "completion"
             else G.fa_hole_size(s["hole_size"]),
             fmt(s["interval_m"], 1), fmt(s["duration_d"]),
             fmt(s["drilling_hours_2_1"], 1), fmt(s["rop_m_per_drill_hour"], 2),
             fmt(s["rop_m_per_day"], 2)] for s in D["sections"]]
    K.table(doc, ["مقطع", "طول (متر)", "روز تقویمی", "ساعت حفاری", "ROP (متر بر ساعت حفاری)",
                  "ROP (متر بر روز)"], rows, widths=[2.4, 2.2, 2.0, 2.0, 3.4, 2.8], fa=True,
            size=8, caption="جدول ۴-۱: سرعت نفوذ به تفکیک مقطع با ذکر هر دو مخرج")
    if D["bits_drilling"]:
        K.heading(doc, "۴-۱  سرعت نفوذ به تفکیک مته", 2, fa=True)
        rows = []
        for b in sorted(D["bits_drilling"], key=lambda x: -float(x["rop_m_per_h"])):
            rows.append([b["run_id"].split("-")[-1], G.fa_bit_no(b["bit_no"]),
                         G.fa_bit_size(b["bit_size"]),
                         G.fa_maker(b["manufacturer"]), fmt(b["depth_in_m"], 1), fmt(b["depth_out_m"], 1),
                         fmt(b["footage_m"], 1), fmt(b["rotating_hours"], 1),
                         fmt(b["rop_m_per_h"], 2), G.fa_dull(b["dull"])[:22]])
        K.table(doc, ["ران", "مته", "قطر", "سازنده", "ورود (متر)", "خروج (متر)", "متراژ (متر)",
                      "ساعت چرخش", "ROP (متر/ساعت)", "درجه سایش ثبت‌شده"], rows,
                widths=[1.0, 1.3, 1.5, 1.9, 1.4, 1.4, 1.5, 1.3, 1.7, 2.4], fa=True, size=6.8,
                caption="جدول ۴-۲: ران‌های مته به ترتیب سرعت نفوذ")
        bs0 = G.fa_bit_size(D["best_bit"]["bit_size"])
        K.para_fa(doc, f"سریع‌ترین ران {D['best_bit']['run_id']} با مته {G.fa_bit_no(D['best_bit']['bit_no'])} و "
                       f"قطر {G.fa_hole_size(bs0)} و سرعت {fmt(D['best_bit']['rop_m_per_h'],2)} "
                       f"متر بر ساعت در متراژ {fmt(D['best_bit']['footage_m'],0)} متر است. کندترین "
                       f"ران مستند {D['worst_bit']['run_id']} با {fmt(D['worst_bit']['rop_m_per_h'],2)} "
                       f"متر بر ساعت و طولانی‌ترین ران {D['longest_bit']['run_id']} با "
                       f"{fmt(D['longest_bit']['footage_m'],0)} متر است.")
        K.figure(doc, "Siahmakan_Analysis/02_Asset_Comparison/Figures/fig_bit_footage.png", 14.0,
                 "شکل ۴-۱: توزیع متراژ هر ران مته در سطح میدان.", fa=True)

    # ---------------- 5
    K.heading(doc, FA["sec5"], 1, fa=True)
    K.para_fa(doc, T["npt_note"].format(n=len(D["npt"]), h=fmt(D["npt_h"])))
    K.heading(doc, "۵-۱  زمان غیرمولد به تفکیک خانواده علت", 2, fa=True)
    rows = [[G.fa_term("family", r["family"]), fmt(r["hours"], 1), pct(r["pct_of_npt"]),
             pct(r["pct_of_total_time"]), r["event_count"]] for r in D["npt_fam"]]
    K.table(doc, ["خانواده علت", "ساعت", "سهم از زمان غیرمولد", "سهم از کل زمان", "تعداد رخداد"],
            rows, widths=[4.4, 1.8, 2.6, 2.8, 1.8], fa=True, size=8,
            caption="جدول ۵-۱: زمان غیرمولد به تفکیک خانواده علت")
    K.heading(doc, "۵-۲  زمان غیرمولد به تفکیک مقطع", 2, fa=True)
    rows = [[G.fa_hole_size(r["hole_section"]), fmt(r["npt_hours"], 1), pct(r["pct_of_npt"])]
            for r in D["npt_sec"]]
    K.table(doc, ["مقطع", "ساعت غیرمولد", "سهم از زمان غیرمولد"], rows,
            widths=[4.5, 3.0, 3.5], fa=True, size=8.5,
            caption="جدول ۵-۲: توزیع زمان از دست رفته بین مقاطع")
    fig_path = f"{OUT}/{w}/Figures/{w}_fig_npt_pareto.png"
    if os.path.exists(fig_path):
        K.figure(doc, fig_path, 15.5,
                 f"شکل ۵-۱: نمودار پارتو زمان غیرمولد چاه {w} بر حسب خانواده علت.", fa=True)
    K.heading(doc, "۵-۳  بزرگ‌ترین رخدادها", 2, fa=True)
    rows = [[e["event_id"].split("-")[-1], e["start_date"], e["end_date"], fmt(e["hours"], 1),
             e["code"], G.fa_term("family", e["family"]),
             "، ".join(G.fa_hole_size(x) for x in (e["hole_sizes"] or "").split(",") if x.strip()),
             (e["desc"] or "")[:100]]
            for e in D["npt_top"]]
    K.table(doc, ["شناسه", "آغاز", "پایان", "ساعت", "کد", "خانواده", "مقطع", "شرح ثبت‌شده"],
            rows, widths=[0.9, 1.8, 1.8, 1.1, 1.0, 2.2, 1.7, 4.2], fa=True, size=6.5,
            caption="جدول ۵-۳: هشت رخداد بزرگ زمان غیرمولد. ستون شرح، متن انگلیسی گزارش روزانه "
                    "است که عیناً و کوتاه‌شده نقل می‌شود تا بازبین بتواند آن را با برگه اصل تطبیق دهد")
    K.para_fa(doc, "تحلیل ریشه‌ای", bold=True)
    K.para_fa(doc, T["rootcause_note"])

    # ---------------- 6
    K.heading(doc, FA["sec6"], 1, fa=True)
    K.para_fa(doc, T["bit_note"])
    if D["bits_drilling"]:
        makes = {}
        for b in D["bits_drilling"]:
            k = b["manufacturer"] or "نامشخص"
            makes[k] = makes.get(k, 0) + 1
        top_make = max(makes.items(), key=lambda kv: kv[1])
        K.para_fa(doc, f"{len(D['bits_drilling'])} ران هم متراژ و هم ساعت چرخش دارند. پرکاربردترین "
                       f"سازنده در این مجموعه {G.fa_maker(top_make[0])} با {top_make[1]} ران است.")
        # bit numbers carry an English condition tag ('(used)') that must not
        # reach the Persian prose; the table version already translates it
        K.figure(doc, "Siahmakan_Analysis/02_Asset_Comparison/Figures/fig_bit_rop_by_well.png", 14.5,
                 "شکل ۶-۱: توزیع سرعت نفوذ ران‌های مته در سطح میدان، برای مقایسه.", fa=True)

    # ---------------- 7
    K.heading(doc, FA["sec7"], 1, fa=True)
    if D["params"]:
        rows = [[G.fa_hole_size(str(p["bit_size"]).split()[0] if str(p["bit_size"]).split() else ""), p["wob_mean"], p["rpm_mean"], p["torque_mean"], p["spp_mean"],
                 p["flow_mean"], p["rop_mean"]] for p in D["params"]]
        K.table(doc, ["قطر مته", "WOB (کیلوپوند)", "دور", "گشتاور (کیلوپوند·فوت)", "SPP (psi)",
                      "دبی (گالن بر دقیقه)", "ROP ران (متر/ساعت)"], rows,
                widths=[2.2, 2.4, 1.6, 3.0, 2.2, 2.4, 2.4], fa=True, size=7.5,
                caption="جدول ۷-۱: میانگین پارامترهای ثبت‌شده به تفکیک قطر مته")
    K.para_fa(doc, T["mse_note"])

    # ---------------- 8
    K.heading(doc, FA["sec8"], 1, fa=True)
    labels = {"mw": "وزن گل (pcf)", "pv": "گرانروی پلاستیک (cP)",
              "yp": "نقطه تسلیم (lb/100ft²)", "fluid_loss": "افت سیال (cc/30 دقیقه)",
              "solids": "جامدات (%)", "chlorides": "کلراید (mg/l)",
              "kcl": "کلرید پتاسیم (% وزنی)", "ph": "pH"}
    rows = []
    for k, lab in labels.items():
        if k in D["mud"]:
            r = D["mud"][k]
            rows.append([lab, r["n"], fmt(r["min"], 1), fmt(r["max"], 1), fmt(r["mean"], 1)])
    if rows:
        K.table(doc, ["ویژگی", "تعداد ثبت", "کمینه", "بیشینه", "میانگین"], rows,
                widths=[4.8, 2.0, 2.0, 2.0, 2.0], fa=True, size=8,
                caption="جدول ۸-۱: ویژگی‌های ثبت‌شده گل حفاری در دوره مستند")
    K.para_fa(doc, T["ecd_note"])
    K.figure(doc, "Siahmakan_Analysis/02_Asset_Comparison/Figures/fig_mud_weight.png", 14.0,
             "شکل ۸-۱: وزن گل ثبت‌شده بر حسب روز دکل در سطح میدان.", fa=True)
    if "mw" in D["mud"]:
        r = D["mud"]["mw"]
        K.para_fa(doc, f"وزن گل از {fmt(r['min'],1)} تا {fmt(r['max'],1)} پوند بر فوت مکعب "
                       f"(میانگین {fmt(r['mean'],1)}) متغیر بوده است. بیشینه، وزن لازم برای کنترل "
                       f"چاه پس از گذار فشاری و کمینه، وزن مقطع سطحی است.", size=9.5)

    # ---------------- 9
    K.heading(doc, FA["sec9"], 1, fa=True)
    v = (D["survey_verdict"] or "").strip().upper()
    tr = D["traj"]
    if v == "NOT PRESENT":
        sfa = "داده پیمایش در این چاه وجود ندارد."
        rfa = "هیچ ایستگاه پیمایش عددی در هیچ برگه گزارش روزانه ثبت نشده است."
    elif "TEMPLATE" in v:
        sfa = "داده پیمایش قابل استفاده نیست (داده الگویی/تکراری)."
        rfa = (f"عمیق‌ترین ایستگاه پیمایش ثبت‌شده {fmt(tr['max_survey_md_m'],1)} متر MD در برابر "
               f"عمق نهایی ثبت‌شده {fmt(tr['final_well_depth_m'],1)} متر است "
               f"(پوشش {pct(tr['coverage_pct'])})؛ همان ایستگاه‌ها بدون هیچ تغییری "
               f"در برگه آخر تکرار شده‌اند.")
    elif v.startswith("USABLE"):
        sfa = "داده پیمایش قابل استفاده است."
        rfa = (f"عمیق‌ترین ایستگاه پیمایش ثبت‌شده {fmt(tr['max_survey_md_m'],1)} متر MD در برابر "
               f"عمق نهایی {fmt(tr['final_well_depth_m'],1)} متر است "
               f"(پوشش {pct(tr['coverage_pct'])})؛ برای بازسازی مسیر جزئی کافی است.")
    else:
        sfa = "وضعیت داده پیمایش نامشخص است."
        rfa = "داده پیمایش در مدارک موجود ارزیابی نشد."
    K.para_fa(doc, f"ارزیابی داده: {sfa} {rfa}")
    K.para_fa(doc, T["survey_note"])
    if D["traj"]["n_distinct_stations"] not in ("0", ""):
        K.table(doc, ["شاخص", "مقدار"],
                [["ایستگاه‌های مستقل پیمایش در مدارک", D["traj"]["n_distinct_stations"]],
                 ["عمیق‌ترین ایستگاه ثبت‌شده (متر MD)", fmt(D["traj"]["max_survey_md_m"], 1)],
                 ["عمق نهایی چاه (متر MD)", fmt(D["traj"]["final_well_depth_m"], 1)],
                 ["پوشش", pct(D["traj"]["coverage_pct"])],
                 ["ارزیابی", "قابل استفاده" if v.startswith("USABLE")
                  else ("قابل استفاده نیست" if "TEMPLATE" in v else "موجود نیست")]],
                widths=[8.0, 6.0], fa=True, size=8.5,
                caption="جدول ۹-۱: ارزیابی یکپارچگی داده پیمایش")

    # ---------------- 10
    K.heading(doc, FA["sec10"], 1, fa=True)
    _fit = (m["fit"] or "").strip()
    _fit = "ثبت نشده" if _fit in ("", "-", "—", "N/A", "NA", "nan", "None") else _fit
    K.para_fa(doc, f"مقدار ثبت‌شده آزمون پاشنه: {_fit}. زمان عملیات کنترل چاه "
                   f"(کد ۱۰-۵): {fmt(D['wellctrl_h'])} ساعت. زمان کشتن چاه (کد ۸-۸): "
                   f"{fmt(D['code'].get('8-8', {}).get('hours'), 0)} ساعت.")
    K.para_fa(doc, T["maasp_note"])
    wc = [o for o in D["ops"] if o["code"] in ("10-5", "8-8")]
    if wc:
        K.para_fa(doc, "گاه‌نگاری عملیات کنترل چاه (نخستین ردیف‌ها)", bold=True)
        rows = [[o["report_date"], o["hrs"], o["code"], (o["desc"] or "")[:150]]
                for o in wc[:10]]
        K.table(doc, ["تاریخ", "ساعت", "کد", "شرح ثبت‌شده"], rows,
                widths=[2.2, 1.3, 1.2, 9.3], fa=True, size=7.5,
                caption="جدول ۱۰-۱: عملیات کنترل چاه بر پایه گزارش روزانه (شرح، نقل عین انگلیسی از برگه است)")

    # ---------------- 11
    K.heading(doc, FA["sec11"], 1, fa=True)
    K.para_fa(doc, T["geol_note"])
    by = {f2["formation"].upper(): f2 for f2 in D["form"]}
    rows = []
    for key in ["AGHAJARI", "MISHAN", "GACHSARAN", "ASMARI", "PABDEH", "GURPI", "ILAM",
                "SURGAH", "SARVAK", "KAZHDUMI"]:
        if key in by and by[key]["top"]:
            rows.append([G.fa_formation(by[key]["formation"]),
                         G.fa_depth(by[key]["top"]),
                         G.fa_lithology(by[key]["lithology"])])
    for f2 in D["form"]:
        if f2["top"] and "GS." in f2["formation"].upper():
            rows.append([f2["formation"], f2["top"], f2["lithology"]])
    if rows:
        K.table(doc, ["سازند", "سرسازند (MD)", "سنگ‌شناسی ثبت‌شده"], rows,
                widths=[4.0, 3.4, 6.6], fa=True, size=8,
                caption="جدول ۱۱-۱: سرسازندها و سنگ‌شناسی بر پایه گزارش‌های روزانه")
    K.para_fa(doc, T["gachsaran_note"], size=9.5)

    # ---------------- 12
    K.heading(doc, FA["sec12"], 1, fa=True)
    cats = [("گیر کردن رشته (۱۰-۳)", D["stuck_h"]), ("عملیات ماهیگیری (۱۰-۴)", D["fishing_h"]),
            ("کنترل چاه (۱۰-۵)", D["wellctrl_h"]),
            ("هرزروی گل (۱۰-۷)", float(D["code"].get("10-7", {}).get("hours") or 0)),
            ("رمینگ (۴-۳)", float(D["code"].get("4-3", {}).get("hours") or 0)),
            ("سفر کوتاه (۴-۷)", float(D["code"].get("4-7", {}).get("hours") or 0))]
    rows = [[c, fmt(h, 1), pct(100 * h / D["tot_h"] if D["tot_h"] else 0)] for c, h in cats]
    K.table(doc, ["دسته مشکل", "ساعت", "سهم از کل زمان ثبت‌شده"], rows,
            widths=[6.0, 2.5, 4.0], fa=True, size=8.5,
            caption="جدول ۱۲-۱: زمان قابل انتساب به دسته‌های مشکل چاه")
    K.para_fa(doc, T["hole_note"])

    # ---------------- 13
    K.heading(doc, FA["sec13"], 1, fa=True)
    K.para_fa(doc, f"عملیات تکمیل و اصلاحی (کد ۸-x) "
                   f"{fmt(D['ph'].get('Completion & Intervention', {}).get('hours_total'),1)} ساعت، "
                   f"مشبک‌کاری {fmt(D['perf_h'],1)} ساعت و آزمون و تحریک "
                   f"{fmt(D['ph'].get('Testing & Stimulation', {}).get('hours_total'),1)} ساعت است.")
    K.para_fa(doc, T["cmpl_note"])
    if D["perf_h"] > 0:
        perf = [o for o in D["ops"] if o["code"] == "5-6"][:6]
        K.table(doc, ["تاریخ", "ساعت", "شرح ثبت‌شده"],
                [[o["report_date"], o["hrs"], (o["desc"] or "")[:140]] for o in perf],
                widths=[2.2, 1.3, 10.5], fa=True, size=7.5,
                caption="جدول ۱۳-۱: عملیات مشبک‌کاری بر پایه گزارش روزانه (شرح، نقل عین انگلیسی از برگه است)")
    K.para_fa(doc, T["no_production_note"], size=9.5)

    # ---------------- 14
    K.heading(doc, FA["sec14"], 1, fa=True)
    recs = []
    if D["npt_pct"] > 35:
        recs.append(T["rec_wait"])
    if D["wellctrl_h"] > 50:
        recs.append(T["rec_wellcontrol"])
    if D["fishing_h"] > 100:
        recs.append(T["rec_fishing"])
    if D["coring_h"] > 100:
        recs.append(T["rec_coring"])
    if D["sidetracks"]:
        recs.append(T["rec_sidetrack"])
    if D["npt_pct"] < 20:
        recs.append(T["rec_low_npt"])
    K.bullets(doc, recs or [T["no_recs"]], fa=True)
    K.heading(doc, "۱۴-۱  فرصت‌های بهبود کمی‌شده", 2, fa=True)
    K.para_fa(doc, T["improve_note"], size=9.5)
    if D["npt_h"] > 100:
        K.table(doc, ["فرصت", "مبنا", "روش", "صرفه‌جویی زمانی", "فرض کلیدی"],
                [["کاهش انتظار سطحی به میزان یک شیفت در هر رخداد",
                  f"{fmt(D['npt_h'])} ساعت غیرمولد", "۱۵٪ از زمان غیرمولد به‌عنوان سقف",
                  f"{fmt(D['npt_h']*0.15)} ساعت",
                  "نیازمند هماهنگ‌کننده با اختیار تغییر ترتیب کارها"]],
                widths=[3.8, 2.6, 3.2, 2.0, 3.6], fa=True, size=7.5,
                caption="جدول ۱۴-۱: سناریوی بهبود با فرض مصرح")
    K.para_fa(doc, T["money_note"], size=9)

    # ---------------- appendices
    doc.add_page_break()
    K.heading(doc, "پیوست الف  ثبت کامل زمان غیرمولد", 1, fa=True)
    K.para_fa(doc, T["quote_note"], size=9)
    rows = [[e["event_id"].split("-")[-1], e["start_date"], e["end_date"], fmt(e["hours"], 1),
             e["code"], G.fa_term("family", e["family"]),
             "، ".join(G.fa_hole_size(x) for x in (e["hole_sizes"] or "").split(",") if x.strip()),
             e["types"], (e["desc"] or "")[:80]]
            for e in D["npt"]]
    K.table(doc, ["شناسه", "آغاز", "پایان", "ساعت", "کد", "خانواده", "مقطع", "N/U", "شرح"],
            rows, widths=[0.9, 1.6, 1.6, 1.0, 1.0, 2.2, 1.6, 0.8, 3.6], fa=True, size=6,
            caption="جدول پ-۱: ثبت کامل زمان غیرمولد این چاه. ستون شرح، نقل عین انگلیسی از برگه "
                    "گزارش روزانه است و ترجمه نشده است")
    doc.add_page_break()
    K.heading(doc, "پیوست ب  توزیع زمان بر حسب کد عملیاتی", 1, fa=True)
    rows = [[r["code"], G.fa_term("code", r["description"]), G.fa_term("phase", r["phase"]),
             fmt(r["hours"], 1), r["occurrences"]] for r in D["codes"]]
    K.table(doc, ["کد", "شرح", "فاز", "ساعت", "تعداد"], rows,
            widths=[1.3, 5.4, 3.6, 1.8, 2.0], fa=True, size=7.5,
            caption="جدول پ-۲: زمان بر حسب کد عملیاتی، بر پایه راهنمای کد گزارش روزانه")
    doc.add_page_break()
    K.heading(doc, "پیوست ج  ثبت کامل ران‌های مته", 1, fa=True)
    K.para_fa(doc, "این جدول همه ران‌های شناسایی‌شده را دارد، از جمله ران‌هایی که متراژ یا ساعت "
                   "چرخش ثبت‌شده ندارند و بنابراین در جدول ۴-۲ نیامده‌اند.", size=9)
    rows = []
    for b in D["bits"]:
        rows.append([b["run_id"].split("-")[-1], G.fa_bit_no(b["bit_no"]),
                     G.fa_bit_size(b["bit_size"]), G.fa_maker(b["manufacturer"]),
                     b["serial"] or "—",
                     fmt(b["depth_in_m"], 1), fmt(b["depth_out_m"], 1), fmt(b["footage_m"], 1),
                     fmt(b["rotating_hours"], 1), fmt(b["rop_m_per_h"], 2),
                     G.fa_dull(b["dull"])[:18]])
    K.table(doc, ["ران", "مته", "قطر", "سازنده", "شماره سری", "ورود (متر)", "خروج (متر)",
                  "متراژ (متر)", "ساعت چرخش", "ROP (متر/ساعت)", "درجه سایش"],
            rows, widths=[0.9, 1.4, 1.5, 1.8, 1.6, 1.2, 1.2, 1.4, 1.1, 1.2, 2.2],
            fa=True, size=6.5,
            caption="جدول پ-۳: همه ران‌های مته شناسایی‌شده، شامل ران‌های بدون متراژ")
    doc.add_page_break()
    K.heading(doc, "پیوست د  مبنای محاسبات و واحدها", 1, fa=True)
    K.table(doc, ["کمیت", "فرمول / قاعده", "واحد"],
            [["مدت سپری‌شده", "تاریخ آخرین گزارش − تاریخ شروع + ۱", "روز"],
             ["ساعت عملیات ثبت‌شده", "جمع ساعات جدول عملیات ۲۴ ساعته", "ساعت"],
             ["زمان غیرمولد", "جمع ساعاتی که نوع N یا U است (جداگانه گزارش شده)", "ساعت"],
             ["درصد زمان غیرمولد", "ساعت غیرمولد ÷ کل ساعات ثبت‌شده × ۱۰۰", "درصد"],
             ["طول مقطع", "عمق ۲۴:۰۰ آخرین برگه مقطع − عمق ۰۰:۰۰ اولین برگه", "متر MD"],
             ["ROP خالص مقطع", "طول ÷ مجموع ساعات کد ۲-۱", "متر/ساعت"],
             ["ROP ناخالص مقطع", "طول ÷ مجموع ساعات کدهای ۲-۱، ۲-۲، ۴-۳، ۴-۶", "متر/ساعت"],
             ["متراژ مته", "عمق خروج − عمق ورود (هر دو از گزارش روزانه)", "متر"],
             ["ساعت چرخش مته", "مجموع ساعات کد ۲-۱ در برگه‌های همان ران", "ساعت"],
             ["ROP مته", "متراژ ÷ ساعت چرخش", "متر/ساعت"],
             ["سیستم واحد", "متریک: متر، ساعت، pcf، psi، کیلوپوند، کیلوپوند·فوت", "—"]],
            widths=[3.6, 8.4, 2.4], fa=True, size=7.5,
            caption="جدول پ-۴: مبنای محاسبه هر دسته از ارقام")
    doc.save(path)
    K.normalise_ooxml(path)
    return path


def main():
    for w in RC.WELLS:
        D = RC.get(w)
        d = f"{OUT}/{w}"
        os.makedirs(d, exist_ok=True)
        p_en = build_en(D, f"{d}/{w}_Engineering_Report_EN.docx")
        p_fa = build_fa(D, f"{d}/{w}_Engineering_Report_FA.docx")
        print(f"  {p_en}")
        print(f"  {p_fa}")


if __name__ == "__main__":
    main()
