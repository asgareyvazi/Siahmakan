"""Extract all DDR sheets from SI 06-09 xlsx into normalized CSVs.

Design notes
------------
* Source workbooks are opened read-only and never modified.
* Every DDR template block is located by its own label/anchor cell, because the
  block start row drifts by up to 12 rows between wells AND between sheets.
  Fixed row/column assumptions are therefore not used anywhere.
* Daily-operation rows are parsed with an explicit "new operation" rule
  (hours or code present) plus continuation-text merging, which is required
  because long descriptions spill onto following rows with no other content.
* Non-operation tables (drilling-fluid, personnel, rig equipment, BOP drills)
  share the same columns as the operation block and are explicitly excluded.
  This was a confirmed defect in v1 (SI-006 sheet 86 rows 80-110 fabricated
  operations with values such as 95000 "hours").
* Provenance columns (source_file, source_sheet, sheet_index) are written on
  every row so any figure can be traced back to the original workbook cell.
"""
import csv
import os
import re
import sys
from collections import Counter
from datetime import date, datetime

import openpyxl

FILES = {
    "SI-006": "SI 06.xlsx",
    "SI-007": "SI 07.xlsx",
    "SI-008": "SI 08.xlsx",
    "SI-009": "SI 09.xlsx",
}
OUT = "Siahmakan_Analysis/04_Engineering_Datasets"
MAXCOL = 24

# Labels that must never be treated as operation codes.
NON_OP_CODES = {
    "mud pump", "liner size", "depth", "ph", "last fire drill", "last bop drill",
    "last h2s drill", "days without lta", "waste management", "survey data",
    "formation table", "cement bulk & additives", "material", "code", "total",
    "productive", "non-productive", "un planned", "description", "consumed",
    "last update", "equipment", "rams", "personnel on board",
}
# Rows in the operation block belong to the daily activity table only if the
# "From" cell is a clock time OR hours/code are numeric operation codes.
CODE_RE = re.compile(r"^\d{1,2}-\d{1,2}$")


def s(v):
    if v is None:
        return ""
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d")
    return str(v).strip()


def num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v) if not isinstance(v, bool) else None
    t = str(v).strip().replace(",", "")
    if t in ("", "-", "--", "N/A", "NA"):
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", t)
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def clean_code(v):
    """Return a normalised operation code, or '' when the cell is not one."""
    t = s(v)
    if not t:
        return ""
    if t.lower() in NON_OP_CODES:
        return ""
    t2 = t.replace(" ", "")
    if CODE_RE.match(t2):
        return t2
    # tolerate codes typed into the description column (SI-007/SI-008 shifts)
    m = re.match(r"^(\d{1,2})-(\d{1,2})$", t2)
    return f"{m.group(1)}-{m.group(2)}" if m else ""


def clean_type(v):
    t = s(v).upper()
    return t if t in ("P", "N", "U") else ""


def repair_date(v):
    """Repair malformed report dates and report what was changed."""
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d"), ""
    t = s(v)
    if not t:
        return "", ""
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", t)
    if m:
        d, mo, y = m.groups()
        if len(d) > 2:
            # A 3-digit day field is a source typo. Both interpretations
            # ('021'->'21' or '01') are plausible, so the value is left blank
            # here and resolved later from the rig-day sequence.
            return "", f"ambiguous 3-digit day in '{t}'"
        if len(d) <= 2:
            return f"{y}-{int(mo):02d}-{int(d):02d}", ""
    m = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})", t)
    if m:
        y, mo, d = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}", ""
    m = re.match(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{2})$", t)
    if m:
        d, mo, y = m.groups()
        return f"20{y}-{int(mo):02d}-{int(d):02d}", f"two-digit year in '{t}'"
    return "", f"unparseable '{t}'"


def grid_of(ws):
    rows = []
    for row in ws.iter_rows(min_col=1, max_col=MAXCOL, max_row=260, values_only=True):
        rows.append(list(row))
    return rows


def cell(rows, r, c):
    if r < 0 or r >= len(rows):
        return None
    row = rows[r]
    return row[c] if c < len(row) else None


def find_row(rows, col, predicate, start=0, stop=None):
    stop = len(rows) if stop is None else stop
    for i in range(start, min(stop, len(rows))):
        v = cell(rows, i, col)
        if v is not None and predicate(str(v).strip()):
            return i
    return None


def find_row_any(rows, predicate, start=0, stop=None, ncol=MAXCOL):
    stop = len(rows) if stop is None else stop
    for i in range(start, min(stop, len(rows))):
        for c in range(ncol):
            v = cell(rows, i, c)
            if v is not None and predicate(str(v).strip()):
                return i
    return None


# --------------------------------------------------------------------------- #
# Header block
# --------------------------------------------------------------------------- #
HEADER_LABELS = {
    "depth00": "depth at 00:00",
    "depth06": "depth at 06:00",
    "depth24": "depth at 24:00",
    "meterage": "meterage",
    "rig_days": "rig days",
    "spud_date": "spud date",
    "report_date": "report date",
    "planned_td": "planned td",
    "hole_size": "hole size",
    "last_csg": "last csg size",
    "next_csg": "next csg size",
    "liner_lap": "liner lap depth",
    "section_start": "section start date",
    "hole_size_planned": "hole size",
    "fit": "fit depth",
    "offset": "offset well",
    "plan_duration": "plan duration",
    "well_type": "well type",
    "field": "field name",
    "well_name": "well name",
    "rig_contractor": "rig cont",
    "operator": "operator",
}


# Every known header label. A cell whose text matches one of these is a label,
# never a value - this matters because several labels are duplicated in
# adjacent cells (e.g. "Hole Size (in)" appears in both J8 and K8, with the
# actual value two columns further right).
HEADER_LABEL_WORDS = (
    "field name", "well name", "well type", "plan duration", "planned td",
    "rig cont", "operator", "rig days", "spud date", "report date",
    "depth at 00:00", "depth at 06:00", "depth at 24:00", "meterage",
    "last csg size", "next csg size", "next casing shoe", "liner lap depth",
    "hole size (in)", "section start date", "offset well", "gle", "geo. sys",
    "northing", "easting", "fit depth", "hole size", "drilling supervisor",
    "drilling superintendent", "well site geologist", "toolpusher",
    "client representative", "summary of activities", "next 24hrs",
)


def is_header_label(text):
    t = str(text).strip().lower()
    if not t:
        return True
    if len(t) > 45:
        return True
    return t.startswith(HEADER_LABEL_WORDS)


def header_pairs(rows):
    """Collect (label_lower, value) for the header block (rows 3-11).

    The value is the first cell to the right of the label that is neither empty
    nor itself a duplicated label word.
    """
    pairs = []
    for r in range(3, 12):
        for c in range(0, 14):
            v = cell(rows, r, c)
            if v is None:
                continue
            lab = str(v).strip().lower()
            if not lab or len(lab) > 45:
                continue
            for cc in range(c + 1, 16):
                vv = cell(rows, r, cc)
                if vv is None or str(vv).strip() == "":
                    continue
                if is_header_label(vv):
                    continue
                pairs.append((lab, vv))
                break
    return pairs


def pick(pairs, key):
    """First header value whose label starts with `key`."""
    for lab, val in pairs:
        if lab.startswith(key):
            return val
    return None


def pick_all(pairs, key):
    return [val for lab, val in pairs if lab.startswith(key)]


# --------------------------------------------------------------------------- #
# Daily operations
# --------------------------------------------------------------------------- #
def parse_ops(rows, hdr_row):
    """Parse the 24-hour operation table starting at hdr_row."""
    ops = []
    cur = None
    blanks = 0
    r = hdr_row + 1
    while r < len(rows):
        b = s(cell(rows, r, 1))
        d = s(cell(rows, r, 3))
        e = s(cell(rows, r, 4))
        f = s(cell(rows, r, 5))
        g = s(cell(rows, r, 6))
        # stop conditions: next table header, tour header, note block, long blank run
        if b.lower() in ("from",) and ("description" in g.lower() or "morning" in g.lower()):
            break
        if b.lower().startswith(("note", "notes")) and not d and not e:
            break
        if all(x == "" for x in (b, d, e, f, g)):
            blanks += 1
            if blanks >= 4 and cur is not None:
                break
            r += 1
            continue
        blanks = 0
        code = clean_code(e)
        typ = clean_type(f)
        hrs = num(d)
        # continuation text: description spilled onto its own row
        is_new = bool(code) or (hrs is not None and b != "")
        if is_new:
            if cur:
                ops.append(cur)
            cur = {
                "from": b,
                "to": s(cell(rows, r, 2)),
                "hrs": hrs,
                "code": code,
                "type": typ,
                "desc": g,
                "row": r + 1,
            }
        elif cur is not None and g:
            cur["desc"] = (cur["desc"] + " " + g).strip()
        elif cur is not None and b and not g:
            # text typed in the From column of a spill row
            cur["desc"] = (cur["desc"] + " " + b).strip()
        r += 1
    if cur:
        ops.append(cur)
    # reject rows that are clearly not operations (no code and no time)
    clean = []
    for o in ops:
        if o["code"] or re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", o["from"]):
            if o["code"] or (o["hrs"] is not None):
                clean.append(o)
    return clean


# --------------------------------------------------------------------------- #
# Bit / BHA / casing / mud / survey / formation / time breakdown
# --------------------------------------------------------------------------- #
BIT_LABELS = {
    "bit_no": "bit no.",
    "run_no": "run no.",
    "bit_size": "bit size",
    "bit_type": "bit type",
    "bit_manufacturer": "bit manufacture",
    "bit_serial": "bit serial",
    "bit_nozzles": "bit nozzles",
    "tfa": "tfa",
    "wob": "w.o.b",
    "rpm_surface": "surf. rpm",
    "rpm_motor": "motor rpm",
    "torque": "torque",
    "pump_output": "pump output",
    "ann_velocity": "ann. velocity",
    "hsi": "h.s.i",
    "spp": "spp",
    "depth_in": "depth in",
    "depth_out": "depth out",
    "bit_24": "bit 24",
    "bit_cum_drilled": "bit cum. drilled",
    "bit_hours": "bit hours",
    "bit_cum_hrs": "bit cum. hrs",
    "tbr": "tbr",
    "bit_ave_rop": "bit ave rop",
    "bit_dull": "bit dull",
}
MUD_LABELS = {
    "mud_type": "mud type",
    "mw": "mw (pcf)",
    "funnel_visc": "f.vis",
    "flowline_temp": "flow line temp",
    "pv": "pv (cp)",
    "yp": "yp (lb/100ft",
    "gel_10s10m": "gel (10 sec",
    "gel_10m30m": "gel (10 min",
    "hardness": "hardness",
    "calcium": "ca (mg",
    "chlorides": "chlorides",
    "kcl": "kcl",
    "fluid_loss": "fl (cc",
    "cake": "cake",
    "solids": "solid %",
    "ph": "ph",
    "oil_water": "oil % / water",
    "active_vol": "active vol",
    "total_vol": "total mud sys",
    "mud_made": "mud made",
    "form_loss": "form. loss",
    "surface_loss": "surface loss",
}


def label_value_pairs(rows, start, nrows, ncols=6):
    """Generic 'label in col B, value in col C..' reader for stack tables."""
    out = {}
    for r in range(start, min(start + nrows, len(rows))):
        lab = s(cell(rows, r, 1))
        if not lab:
            continue
        vals = []
        for c in range(2, ncols):
            v = cell(rows, r, c)
            if v is not None and s(v) != "":
                vals.append(s(v))
            if len(vals) >= 2:
                break
        if vals:
            out.setdefault(lab.lower(), vals)
    return out


# Values that belong to an adjacent table and must never be read as bit data.
BIT_VALUE_BLOCK = {
    "item", "equipment", "size", "wt", "grade", "threads", "from", "to", "od",
    "id", "len.(m)", "cum.len", "top conn.", "s/n", "sliding hrs",
    "cum. rot. hrs", "cum. pumping hrs.", "rec.", "consumed", "backload",
    "last inv.", "casing specification", "driller depth", "down hole equipment",
    "bit data", "bha", "physical properties",
}


def parse_bit(rows):
    """Bit-data stack (label in column B, values in columns C-E).

    The stack ends at the BHA table / down-hole-equipment table, which start on
    the same rows on some sheets. Values that belong to those tables are
    explicitly rejected, because on sheets where the bit table is empty the
    adjacent table otherwise fills the fields (confirmed defect: bit number was
    being read as 'ITEM').
    """
    bi = find_row(rows, 1, lambda t: t.lower().startswith("bit no."), 20, 130)
    if bi is None:
        return None
    rec = {}
    seen_bit_no = False
    for r in range(bi, min(bi + 32, len(rows))):
        lab = s(cell(rows, r, 1))
        if lab.lower().startswith(("down hole", "mud properties", "mud type",
                                   "from", "bit data")):
            break
        vals = []
        for c in range(2, 5):
            v = cell(rows, r, c)
            if v is None or s(v) == "":
                continue
            if s(v).strip().lower() in BIT_VALUE_BLOCK:
                continue
            vals.append(s(v))
            break
        if not vals:
            continue
        lab_l = lab.lower().strip()
        for k, needle in BIT_LABELS.items():
            if lab_l.startswith(needle):
                rec[k] = vals[0]
                if k == "bit_no":
                    seen_bit_no = True
                # second value on the same row = previous/next bit
                more = []
                for c in range(2, 5):
                    v = cell(rows, r, c)
                    if v is None or s(v) == "":
                        continue
                    if s(v).strip().lower() in BIT_VALUE_BLOCK:
                        continue
                    more.append(s(v))
                if len(more) > 1:
                    rec[k + "_2"] = more[1]
                break
    if not rec or not seen_bit_no:
        return None
    if not re.search(r"\d|#", rec.get("bit_no", "")):
        return None
    rec["_row"] = bi + 1
    return rec


def parse_bha(rows):
    hi = find_row(rows, 6, lambda t: t.upper() == "ITEM", 30, 140)
    if hi is None:
        return []
    out = []
    r = hi + 1
    blanks = 0
    while r < len(rows):
        item = s(cell(rows, r, 6))
        if not item:
            blanks += 1
            if blanks >= 3:
                break
            r += 1
            continue
        if item.lower().startswith(("down hole", "equipment", "wellhead")):
            break
        blank_hdr = item.strip()
        if blank_hdr.lower() in ("item",):
            r += 1
            continue
        out.append({
            "bha_row": r + 1,
            "item": item,
            "od": s(cell(rows, r, 8)),
            "id": s(cell(rows, r, 9)),
            "length_m": num(cell(rows, r, 10)),
            "cum_length_m": num(cell(rows, r, 11)),
            "top_conn": s(cell(rows, r, 12)),
        })
        blanks = 0
        r += 1
    return out


def parse_casing(rows):
    hi = find_row(rows, 8, lambda t: t.lower() == "casing specification", 30, 160)
    if hi is None:
        return []
    out = []
    r = hi + 2
    while r < len(rows):
        size = s(cell(rows, r, 6))
        if not size:
            break
        if size.lower().startswith(("down hole", "equipment", "size")):
            break
        if not re.search(r"\d", size):
            break
        out.append({
            "casing_row": r + 1,
            "size": size,
            "wt": s(cell(rows, r, 8)),
            "grade": s(cell(rows, r, 9)),
            "threads": s(cell(rows, r, 10)),
            "from": s(cell(rows, r, 11)),
            "to": s(cell(rows, r, 12)),
        })
        r += 1
        if len(out) > 20:
            break
    return out


def parse_mud(rows):
    mi = find_row(rows, 1, lambda t: t.lower() == "mud properties", 30, 160)
    if mi is None:
        return None
    stack = label_value_pairs(rows, mi + 1, 26, 5)
    rec = {}
    for k, needle in MUD_LABELS.items():
        for lab, vals in stack.items():
            if lab.startswith(needle):
                rec[k] = vals[0]
                if len(vals) > 1:
                    rec[k + "_out"] = vals[1]
                break
    return rec or None


def parse_survey(rows):
    """Survey block. Column order differs between wells (SI-008 uses
    MD/Inc/TVD/Azi/DLS, others MD/Inc/Az/DLS/TVD), so the header row is read
    to build an explicit column map. Composite cells such as '494/818/1165'
    are expanded into separate stations only when the MD cell matches."""
    si = find_row_any(rows, lambda t: t.lower() == "survey data", 30, 170)
    if si is None:
        return []
    hdr = None
    for r in range(si, min(si + 3, len(rows))):
        row = rows[r]
        names = [s(x).lower() for x in row]
        if any(n.startswith("md") for n in names):
            hdr = r
            break
    if hdr is None:
        return []
    cmap = {}
    for c, v in enumerate(rows[hdr]):
        n = s(v).lower()
        if not n:
            continue
        if n.startswith("md") and "md" not in cmap:
            cmap["md"] = c
        elif n.startswith("inc"):
            cmap["inc"] = c
        elif n.startswith("tvd"):
            cmap["tvd"] = c
        elif n.startswith(("az", "azi")):
            cmap["az"] = c
        elif n.startswith("dls"):
            cmap["dls"] = c
    if "md" not in cmap:
        return []

    def raw(r, key):
        c = cmap.get(key)
        return s(cell(rows, r, c)) if c is not None else ""

    out = []
    r = hdr + 1
    blanks = 0
    while r < len(rows):
        md_txt = raw(r, "md")
        if not md_txt:
            blanks += 1
            if blanks >= 3:
                break
            r += 1
            continue
        mds = [x for x in re.split(r"[/,;]", md_txt) if re.search(r"\d", x)]
        if not mds:
            blanks += 1
            r += 1
            continue
        tvds = [x for x in re.split(r"[/,;]", raw(r, "tvd")) if re.search(r"\d", x)]
        incs = [x for x in re.split(r"[/,;]", raw(r, "inc")) if re.search(r"\d", x)]
        azs = [x for x in re.split(r"[/,;]", raw(r, "az")) if re.search(r"\d", x)]
        dls_l = [x for x in re.split(r"[/,;]", raw(r, "dls")) if re.search(r"\d", x)]
        for k, md_s in enumerate(mds):
            md = num(md_s)
            if md is None or md < 0 or md > 12000:
                continue
            out.append({
                "md": md,
                "inc": num(incs[k]) if len(incs) == len(mds) else (num(incs[0]) if len(incs) == 1 else None),
                "az": num(azs[k]) if len(azs) == len(mds) else (num(azs[0]) if len(azs) == 1 else None),
                "dls": num(dls_l[k]) if len(dls_l) == len(mds) else (num(dls_l[0]) if len(dls_l) == 1 else None),
                "tvd": num(tvds[k]) if len(tvds) == len(mds) else (num(tvds[0]) if len(tvds) == 1 else None),
                "survey_row": r + 1,
            })
        blanks = 0
        r += 1
        if len(out) > 60:
            break
    return out


def parse_formations(rows):
    fi = find_row(rows, 10, lambda t: t.lower() == "formation table", 30, 170)
    if fi is None:
        return []
    out = []
    r = fi + 1
    blanks = 0
    while r < len(rows):
        f = s(cell(rows, r, 10))
        if f.lower() == "formation":
            r += 1
            continue
        if not f:
            blanks += 1
            if blanks >= 4:
                break
            r += 1
            continue
        out.append({
            "formation": f,
            "lithology": s(cell(rows, r, 11)),
            "top": s(cell(rows, r, 12)),
            "formation_row": r + 1,
        })
        blanks = 0
        r += 1
    return out


def parse_timebreakdown(rows):
    """Bottom-right summary block (label in col N, code in Q, hours in R)."""
    hits = []
    for r in range(len(rows)):
        if s(cell(rows, r, 13)).lower() == "time break down":
            hits.append(r)
    if not hits:
        return []
    start = hits[-1]
    out = []
    for r in range(start + 1, min(start + 10, len(rows))):
        lab = s(cell(rows, r, 13))
        code = s(cell(rows, r, 16))
        hrs = num(cell(rows, r, 17))
        if lab.lower() in ("code", ""):
            continue
        if hrs is None and not code:
            continue
        out.append({"category": lab, "code": code or lab, "hours": hrs})
    return out


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def process(well, path, writer, log):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for idx, sheet in enumerate(wb.sheetnames, 1):
        ws = wb[sheet]
        rows = grid_of(ws)
        pairs = header_pairs(rows)
        rep_raw = pick(pairs, "report date")
        rep, rep_note = repair_date(rep_raw)
        if rep_note:
            log.append([well, sheet, "report_date", rep_note])
        spud_raw = pick(pairs, "spud date")
        spud, spud_note = repair_date(spud_raw)
        if spud_note:
            log.append([well, sheet, "spud_date", spud_note])

        hdr = {
            "well": well,
            "source_file": os.path.basename(path),
            "source_sheet": sheet,
            "sheet_index": idx,
            "field": s(pick(pairs, "field name")),
            "well_name": s(pick(pairs, "well name")),
            "well_type": s(pick(pairs, "well type")),
            "rig_contractor": s(pick(pairs, "rig cont")),
            "operator": s(pick(pairs, "operator")),
            "rig_days": num(pick(pairs, "rig days")),
            "spud_date": spud,
            "report_date": rep,
            "report_date_raw": s(rep_raw),
            "depth00": num(pick(pairs, "depth at 00:00")),
            "depth06": num(pick(pairs, "depth at 06:00")),
            "depth24": num(pick(pairs, "depth at 24:00")),
            "meterage": num(pick(pairs, "meterage")),
            "planned_td": num(pick(pairs, "planned td")),
            "plan_duration": num(pick(pairs, "plan duration")),
            "hole_size": s(pick(pairs, "hole size")),
            "last_csg": s(pick(pairs, "last csg size")),
            "next_csg": s(pick(pairs, "next csg size")),
            "liner_lap": s(pick(pairs, "liner lap depth")),
            "section_start": s(pick(pairs, "section start date")),
            "fit": s(pick(pairs, "fit depth")),
            "offset_well": s(pick(pairs, "offset well")),
            "date_basis": "RECORDED" if rep else "UNRESOLVED",
        }
        # continue fields (Next CSG block has label in J, value in L)
        if not hdr["next_csg"]:
            hdr["next_csg"] = s(pick(pairs, "next casing shoe"))
        writer["headers"].writerow(hdr)

        # ---- 24 h operations
        op_hdr = None
        for r in range(len(rows)):
            if s(cell(rows, r, 1)) == "From" and "Description" in s(cell(rows, r, 6)):
                op_hdr = r
                break
        if op_hdr is not None:
            for o in parse_ops(rows, op_hdr):
                writer["operations"].writerow({
                    "well": well, "source_sheet": sheet, "sheet_index": idx,
                    "report_date": rep, "rig_days": hdr["rig_days"],
                    "hole_size": hdr["hole_size"],
                    "op_from": o["from"], "op_to": o["to"], "hrs": o["hrs"],
                    "code": o["code"], "type": o["type"], "desc": o["desc"],
                    "source_row": o["row"],
                })

        # ---- bit data
        bit = parse_bit(rows)
        if bit:
            for k, v in bit.items():
                if k.startswith("_"):
                    continue
                if v == "":
                    continue
                writer["bit"].writerow({
                    "well": well, "source_sheet": sheet, "sheet_index": idx,
                    "report_date": rep, "rig_days": hdr["rig_days"],
                    "hole_size": hdr["hole_size"], "param": k, "value": v,
                    "source_row": bit["_row"],
                })

        # ---- BHA
        for b in parse_bha(rows):
            b.update({"well": well, "source_sheet": sheet, "sheet_index": idx,
                      "report_date": rep, "rig_days": hdr["rig_days"],
                      "hole_size": hdr["hole_size"]})
            writer["bha"].writerow(b)

        # ---- casing
        for c in parse_casing(rows):
            c.update({"well": well, "source_sheet": sheet, "sheet_index": idx,
                      "report_date": rep, "rig_days": hdr["rig_days"]})
            writer["casing"].writerow(c)

        # ---- mud
        mud = parse_mud(rows)
        if mud:
            for k, v in mud.items():
                writer["mud"].writerow({
                    "well": well, "source_sheet": sheet, "sheet_index": idx,
                    "report_date": rep, "rig_days": hdr["rig_days"],
                    "hole_size": hdr["hole_size"], "param": k, "value": v,
                })

        # ---- survey
        for sv in parse_survey(rows):
            sv.update({"well": well, "source_sheet": sheet, "sheet_index": idx,
                       "report_date": rep, "rig_days": hdr["rig_days"],
                       "hole_size": hdr["hole_size"]})
            writer["survey"].writerow(sv)

        # ---- formations
        for f in parse_formations(rows):
            f.update({"well": well, "source_sheet": sheet, "sheet_index": idx,
                      "report_date": rep, "rig_days": hdr["rig_days"]})
            writer["formations"].writerow(f)

        # ---- time breakdown
        for t in parse_timebreakdown(rows):
            t.update({"well": well, "source_sheet": sheet, "sheet_index": idx,
                      "report_date": rep, "rig_days": hdr["rig_days"]})
            writer["timebreakdown"].writerow(t)

        if idx % 50 == 0:
            print(f"  {well}: {idx}/{len(wb.sheetnames)} sheets", flush=True)
    wb.close()


def resolve_blank_dates(log):
    """Resolve report dates that could not be parsed, using the linear
    relationship report_date = spud_date + (rig_days - 1) which holds on every
    well in this dataset. The inferred value is flagged in the QA log as
    DERIVED (never presented as a recorded value)."""
    for well in FILES:
        path = f"{OUT}/{well}_headers.csv"
        with open(path, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            continue
        fields = list(rows[0].keys())
        # anchors: sheets with a valid date AND rig days
        anchors = [(float(r["rig_days"]), r["report_date"]) for r in rows
                   if r["report_date"] and r["rig_days"] not in ("", "None")]
        if not anchors:
            continue
        from datetime import timedelta
        offs = []
        for rd, dtv in anchors:
            try:
                d = datetime.strptime(dtv, "%Y-%m-%d").date()
            except ValueError:
                continue
            spud = datetime.strptime([r["spud_date"] for r in rows if r["spud_date"]][0],
                                     "%Y-%m-%d").date()
            offs.append((d - spud).days - (rd - 1))
        if not offs:
            continue
        base = Counter(offs).most_common(1)[0][0]
        spud = datetime.strptime([r["spud_date"] for r in rows if r["spud_date"]][0],
                                 "%Y-%m-%d").date()
        for r in rows:
            if r["report_date"] or r["rig_days"] in ("", "None"):
                continue
            rd = float(r["rig_days"])
            inferred = spud + timedelta(days=int(rd - 1 + base))
            r["report_date"] = inferred.strftime("%Y-%m-%d")
            r["date_basis"] = "DERIVED from rig-day sequence"
            log.append([well, r["source_sheet"], "report_date",
                        f"DERIVED {r['report_date']} from rig_days={rd:g} "
                        f"(spud {spud} + {int(rd-1+base)} d); raw='{r['report_date_raw']}'"])
        with open(path, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs("Siahmakan_Analysis/06_QA_Reports", exist_ok=True)
    schemas = {
        "headers": ["well", "source_file", "source_sheet", "sheet_index", "field",
                    "well_name", "well_type", "rig_contractor", "operator", "rig_days",
                    "spud_date", "report_date", "report_date_raw", "depth00", "depth06",
                    "depth24", "meterage", "planned_td", "plan_duration", "hole_size",
                    "last_csg", "next_csg", "liner_lap", "section_start", "fit", "offset_well", "date_basis"],
        "operations": ["well", "source_sheet", "sheet_index", "report_date", "rig_days",
                       "hole_size", "op_from", "op_to", "hrs", "code", "type", "desc",
                       "source_row"],
        "bit": ["well", "source_sheet", "sheet_index", "report_date", "rig_days",
                "hole_size", "param", "value", "source_row"],
        "bha": ["well", "source_sheet", "sheet_index", "report_date", "rig_days",
                "hole_size", "bha_row", "item", "od", "id", "length_m", "cum_length_m",
                "top_conn"],
        "casing": ["well", "source_sheet", "sheet_index", "report_date", "rig_days",
                   "casing_row", "size", "wt", "grade", "threads", "from", "to"],
        "mud": ["well", "source_sheet", "sheet_index", "report_date", "rig_days",
                "hole_size", "param", "value"],
        "survey": ["well", "source_sheet", "sheet_index", "report_date", "rig_days",
                   "hole_size", "md", "inc", "az", "dls", "tvd", "survey_row"],
        "formations": ["well", "source_sheet", "sheet_index", "report_date", "rig_days",
                       "formation", "lithology", "top", "formation_row"],
        "timebreakdown": ["well", "source_sheet", "sheet_index", "report_date",
                          "rig_days", "category", "code", "hours"],
    }
    log = []
    for well, path in FILES.items():
        handles, writers = {}, {}
        for name, cols in schemas.items():
            fh = open(f"{OUT}/{well}_{name}.csv", "w", newline="", encoding="utf-8")
            handles[name] = fh
            writers[name] = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            writers[name].writeheader()
        print(f"Parsing {well} ({path}) ...", flush=True)
        process(well, path, writers, log)
        for fh in handles.values():
            fh.close()

    resolve_blank_dates(log)

    with open("Siahmakan_Analysis/06_QA_Reports/date_repairs.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["well", "source_sheet", "field", "note"])
        w.writerows(log)
    print(f"date repairs logged: {len(log)}")


if __name__ == "__main__":
    main()
