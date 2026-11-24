"""Build all figures. Chart text is English throughout (required by the brief,
because Persian text in chart labels does not render reliably).
Depth axes are inverted (0 at top) as required.
"""
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

BASE = "Siahmakan_Analysis"
CALC = f"{BASE}/04_Engineering_Datasets/Calculations"
WELLS = ["SI-006", "SI-007", "SI-008", "SI-009"]
FIG = f"{BASE}/02_Asset_Comparison/Figures"
WELL_FIG = f"{BASE}/01_Well_Reports"

COL = {"SI-006": "#1f4e79", "SI-007": "#c00000", "SI-008": "#2e7d32", "SI-009": "#ed7d31"}
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.grid": True,
    "grid.alpha": 0.3, "grid.linestyle": ":", "axes.axisbelow": True,
    "figure.dpi": 160, "savefig.bbox": "tight", "axes.titlesize": 10,
})


def rcsv(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def f(v, d=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


# --------------------------------------------------------------------------
def depth_time(well, outdir):
    rows = [r for r in rcsv(f"{CALC}/depth_time_series.csv") if r["well"] == well]
    if not rows:
        return None
    rows.sort(key=lambda r: f(r["day"], 0))
    x = [f(r["day"]) for r in rows]
    y = [f(r["depth24"]) for r in rows]
    dmax = max(v for v in y if v is not None)
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    ax.plot(x, y, "-", lw=1.4, color=COL[well], zorder=3)

    # Section boundaries: drawn full height, labelled inside the axes at the
    # bottom so they cannot collide with the title or the axis labels.
    secs = [s for s in rcsv(f"{CALC}/hole_sections.csv") if s["well"] == well]
    for s in secs:
        st = f(s["start_rig_day"])
        if st is None or st > max(x):
            continue
        ax.axvline(st, color="0.6", lw=0.7, ls="--", zorder=1)
        ax.annotate(s["hole_size"].replace('"', "") , xy=(st, dmax), xytext=(2, -4),
                    textcoords="offset points", rotation=90, fontsize=6.5,
                    color="0.3", va="bottom", ha="left")

    # Sidetrack marker: a genuine depth decrease is an engineering event
    for i in range(1, len(y)):
        if y[i] is not None and y[i - 1] is not None and y[i] < y[i - 1] - 50:
            ax.annotate("depth decrease (sidetrack / re-entry)",
                        xy=(x[i], y[i]), xytext=(8, -18), textcoords="offset points",
                        fontsize=6.5, color="0.25",
                        arrowprops=dict(arrowstyle="->", lw=0.7, color="0.35"))
            break

    ax.invert_yaxis()
    ax.set_xlim(0, max(x) * 1.01)
    ax.set_ylim(dmax * 1.02, -dmax * 0.02)
    ax.set_xlabel("Well day (spud = day 1)")
    ax.set_ylabel("Measured depth (m MD)")
    ax.set_title(f"{well} - depth versus time from daily reports", pad=8)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=8))
    ax.xaxis.set_major_locator(MaxNLocator(nbins=8))
    path = os.path.join(outdir, f"{well}_fig_depth_time.png")
    fig.savefig(path)
    plt.close(fig)
    return path


def bit_rop_all():
    rows = [r for r in rcsv(f"{CALC}/bit_run_register.csv") if f(r["rop_m_per_h"])]
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    data, labels, colors = [], [], []
    for w in WELLS:
        d = sorted([f(r["rop_m_per_h"]) for r in rows if r["well"] == w])
        if d:
            data.append(d); labels.append(f"{w}\n(n={len(d)})"); colors.append(COL[w])
    bp = ax.boxplot(data, patch_artist=True, widths=0.55, medianprops=dict(color="k", lw=1.2))
    for p, c in zip(bp["boxes"], colors):
        p.set_facecolor(c); p.set_alpha(0.55)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Bit-run ROP (m/h, on rotating hours)")
    ax.set_title("Bit-run rate of penetration by well")
    path = f"{FIG}/fig_bit_rop_by_well.png"
    fig.savefig(path); plt.close(fig)
    return path


def npt_family_chart():
    rows = rcsv(f"{CALC}/npt_by_family.csv")
    fams = defaultdict(dict)
    for r in rows:
        fams[r["family"]][r["well"]] = f(r["hours"], 0)
    top = sorted(fams.items(), key=lambda kv: -sum(kv[1].values()))[:10]
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    import numpy as np
    names = [t[0] for t in top][::-1]
    left = np.zeros(len(names))
    for w in WELLS:
        vals = np.array([fams[n].get(w, 0) for n in names])
        ax.barh(names, vals, left=left, color=COL[w], label=w, height=0.62)
        left += vals
    ax.set_xlabel("Non-productive time (hours)")
    ax.set_title("NPT by cause family (top 10 families, all wells)")
    ax.legend(frameon=False, fontsize=8)
    ax.tick_params(axis="y", labelsize=8)
    path = f"{FIG}/fig_npt_family.png"
    fig.savefig(path); plt.close(fig)
    return path


def npt_pareto(well, outdir):
    rows = [r for r in rcsv(f"{CALC}/npt_by_family.csv") if r["well"] == well]
    rows.sort(key=lambda r: -f(r["hours"], 0))
    rows = [r for r in rows if f(r["hours"], 0) > 0][:9]
    if not rows:
        return None
    vals = [f(r["hours"], 0) for r in rows]
    tot = sum(vals)
    cum = []
    s = 0
    for v in vals:
        s += v
        cum.append(100 * s / tot)
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.bar([r["family"] for r in rows], vals, color=COL[well], alpha=0.75)
    ax.set_ylabel("NPT hours")
    ax.tick_params(axis="x", rotation=32, labelsize=7.5)
    for lbl in ax.get_xticklabels():
        lbl.set_ha("right")
    ax2 = ax.twinx()
    ax2.plot(range(len(rows)), cum, "o-", color="#333", ms=3.5, lw=1)
    ax2.set_ylabel("Cumulative % of NPT")
    ax2.set_ylim(0, 105)
    ax2.grid(False)
    ax.set_title(f"{well} — NPT Pareto by cause family")
    path = os.path.join(outdir, f"{well}_fig_npt_pareto.png")
    fig.savefig(path); plt.close(fig)
    return path


def section_rop():
    rows = [r for r in rcsv(f"{CALC}/hole_sections.csv") if not r["is_completion"] == "True"]
    order = ["26\"", "17-1/2\"", "12-1/4\"", "8-3/8\"", "7\"", "5-7/8\""]
    fig, ax = plt.subplots(figsize=(7.6, 4.0))
    import numpy as np
    w = 0.2
    x = np.arange(len(order))
    for i, well in enumerate(WELLS):
        vals = []
        for sz in order:
            v = [f(r["rop_m_per_drill_hour"]) for r in rows
                 if r["well"] == well and r["hole_size"] == sz]
            vals.append(max(v) if v and max(v) is not None else np.nan)
        ax.bar(x + (i - 1.5) * w, vals, w, label=well, color=COL[well], alpha=0.85)
    ax.set_xticks(x); ax.set_xticklabels(order)
    ax.set_xlabel("Hole section (nominal size)")
    ax.set_ylabel("Section ROP (m per drilling hour, code 2-1)")
    ax.set_title("Drilling rate of penetration by hole section")
    ax.legend(frameon=False, ncol=4, fontsize=8)
    path = f"{FIG}/fig_section_rop.png"
    fig.savefig(path); plt.close(fig)
    return path


def phase_stack():
    rows = rcsv(f"{CALC}/phase_hours.csv")
    phases = []
    for r in rows:
        if r["phase"] not in phases:
            phases.append(r["phase"])
    phases = [p for p in phases if p != "Unclassified"]
    piv = defaultdict(dict)
    for r in rows:
        piv[r["phase"]][r["well"]] = f(r["hours_total"], 0)
    fig, ax = plt.subplots(figsize=(7.6, 3.9))
    import numpy as np
    bottom = np.zeros(len(WELLS))
    cmap = plt.get_cmap("tab20")
    for i, ph in enumerate(phases):
        vals = np.array([piv[ph].get(w, 0) for w in WELLS])
        ax.bar(WELLS, vals, bottom=bottom, label=ph, color=cmap(i % 20), width=0.6)
        bottom += vals
    ax.set_ylabel("Recorded operation hours")
    ax.set_title("Recorded time by operational phase and well")
    ax.legend(frameon=False, fontsize=7, ncol=2, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    path = f"{FIG}/fig_phase_hours.png"
    fig.savefig(path); plt.close(fig)
    return path


def plan_vs_actual():
    comp = rcsv(f"{CALC}/comparison_matrix.csv")
    import numpy as np
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.0, 3.4))
    x = np.arange(len(comp)); w = 0.36
    a1.bar(x - w / 2, [f(r["planned_td_m"], 0) for r in comp], w, label="Planned TD", color="#9e9e9e")
    a1.bar(x + w / 2, [f(r["final_depth_m"], 0) for r in comp], w,
           label="Final recorded depth", color=[COL[r["well"]] for r in comp])
    a1.set_xticks(x); a1.set_xticklabels([r["well"] for r in comp])
    a1.set_ylabel("Depth (m MD)"); a1.set_title("Planned versus recorded depth")
    a1.legend(frameon=False, fontsize=7.5)
    a2.bar(x - w / 2, [f(r["plan_duration_d"], 0) for r in comp], w, label="Planned duration", color="#9e9e9e")
    a2.bar(x + w / 2, [f(r["calendar_days"], 0) for r in comp], w,
           label="Actual documented days", color=[COL[r["well"]] for r in comp])
    a2.set_xticks(x); a2.set_xticklabels([r["well"] for r in comp])
    a2.set_ylabel("Days"); a2.set_title("Planned versus actual duration")
    a2.legend(frameon=False, fontsize=7.5)
    path = f"{FIG}/fig_plan_vs_actual.png"
    fig.savefig(path); plt.close(fig)
    return path


def npt_pct_chart():
    comp = rcsv(f"{CALC}/comparison_matrix.csv")
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    vals = [f(r["npt_pct"], 0) for r in comp]
    bars = ax.bar([r["well"] for r in comp], vals,
                  color=[COL[r["well"]] for r in comp], width=0.55, alpha=0.85)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.1f}%", ha="center", fontsize=8)
    ax.set_ylabel("NPT as % of recorded operation time")
    ax.set_ylim(0, max(vals) * 1.25)
    ax.set_title("Non-productive time share by well")
    path = f"{FIG}/fig_npt_pct.png"
    fig.savefig(path); plt.close(fig)
    return path


def mud_chart():
    rows = rcsv(f"{DAT}/SI-006_mud.csv") if False else None
    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    for well in WELLS:
        pts = [(f(r["rig_days"]), f(r["value"]))
               for r in rcsv(f"{BASE}/04_Engineering_Datasets/{well}_mud.csv")
               if r["param"] == "mw" and f(r["value"])]
        pts.sort()
        if pts:
            ax.plot([p[0] for p in pts], [p[1] for p in pts], ".", ms=2.4,
                    color=COL[well], label=well, alpha=0.8)
    ax.set_xlabel("Rig day")
    ax.set_ylabel("Mud weight (pcf)")
    ax.set_title("Recorded mud weight against well day")
    ax.legend(frameon=False, ncol=4, fontsize=8)
    path = f"{FIG}/fig_mud_weight.png"
    fig.savefig(path); plt.close(fig)
    return path


def bit_footage_chart():
    rows = [r for r in rcsv(f"{CALC}/bit_run_register.csv") if f(r["footage_m"], 0) > 0]
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    import numpy as np
    for i, well in enumerate(WELLS):
        d = [f(r["footage_m"]) for r in rows if r["well"] == well]
        if d:
            ax.scatter([i] * len(d), d, s=26, color=COL[well], alpha=0.8, edgecolor="k", lw=0.3)
    ax.set_xticks(range(len(WELLS))); ax.set_xticklabels(WELLS)
    ax.set_ylabel("Footage per bit run (m)")
    ax.set_title("Bit-run footage distribution")
    path = f"{FIG}/fig_bit_footage.png"
    fig.savefig(path); plt.close(fig)
    return path


def main():
    os.makedirs(FIG, exist_ok=True)
    made = []
    for w in WELLS:
        d = os.path.join(WELL_FIG, w, "Figures")
        os.makedirs(d, exist_ok=True)
        for fn in (depth_time, npt_pareto):
            p = fn(w, d)
            if p:
                made.append(p)
    for fn in (bit_rop_all, npt_family_chart, section_rop, phase_stack,
               plan_vs_actual, npt_pct_chart, mud_chart, bit_footage_chart):
        made.append(fn())
    print(f"{len(made)} figures written")
    for p in made:
        print("  ", p)





def integrity_chart():
    """Completion / integrity / hole-problem hours by well (deck slide 7)."""
    import csv as _csv
    wells = ["SI-006", "SI-007", "SI-008", "SI-009"]
    cats = {"Completion & intervention": [], "Perforation": [],
            "Well control": [], "Stuck pipe": [], "Fishing": []}
    for w in wells:
        codes = {r["code"]: float(r["hours"] or 0)
                 for r in _csv.DictReader(open(f"{CALC}/operation_codes.csv", encoding="utf-8"))
                 if r["well"] == w}
        ph = {r["phase"]: float(r["hours_total"] or 0)
              for r in _csv.DictReader(open(f"{CALC}/phase_hours.csv", encoding="utf-8"))
              if r["well"] == w}
        cats["Completion & intervention"].append(ph.get("Completion & Intervention", 0))
        cats["Perforation"].append(codes.get("5-6", 0))
        cats["Well control"].append(codes.get("10-5", 0))
        cats["Stuck pipe"].append(codes.get("10-3", 0))
        cats["Fishing"].append(codes.get("10-4", 0))
    import numpy as np
    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    x = np.arange(len(wells))
    w = 0.16
    cmap = plt.get_cmap("tab10")
    for i, (name, vals) in enumerate(cats.items()):
        ax.bar(x + (i - 2) * w, vals, w, label=name, color=cmap(i))
    ax.set_xticks(x); ax.set_xticklabels(wells)
    ax.set_ylabel("Recorded hours")
    ax.set_title("Completion, integrity and hole-problem time by well")
    ax.legend(frameon=False, fontsize=7.5, ncol=2)
    path = f"{FIG}/fig_integrity_hours.png"
    fig.savefig(path); plt.close(fig)
    return path


if __name__ == "__main__":
    main()
    print(integrity_chart())
