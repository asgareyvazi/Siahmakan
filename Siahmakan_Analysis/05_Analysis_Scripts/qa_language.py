"""Language and document-integrity QA for the bilingual deliverables.

Checks performed, per file:

1. Persian prose leak  - a paragraph that is Persian by design must not contain
   a run of four or more consecutive Latin words.  Free-standing technical
   tokens (SI-006, pcf, ROP, M/D) are legitimate and are not counted.
2. Table-cell leak     - the same test on table cells, restricted to cells that
   consist only of Latin letters and spaces (a fully English label sitting in a
   Persian table).  Cells holding verbatim DDR narrative are reported
   separately, because quoting the source narrative verbatim is a deliberate,
   disclosed choice, not a translation failure.
3. RTL markup          - every Persian file must carry w:bidi paragraphs,
   w:rtl runs and w:bidiVisual tables.
4. OOXML child order   - rPr / pPr / tcPr children must appear in schema order
   (Word rejects files that violate this).
5. Cross-language contamination - the English files must contain no Arabic
   script at all, the Persian files must not be near-empty.

Usage:  python3 qa_language.py      (exit code 0 = all checks pass)
"""
import glob
import os
import re
import sys
import zipfile

from docx import Document

OUT = "Siahmakan_Analysis"
ARABIC = re.compile(r"[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF]")
LATIN_WORDS = re.compile(r"\b[A-Za-z]{3,}(\s+[A-Za-z]{2,}){3,}")
ONLY_LATIN = re.compile(r"^[A-Za-z][A-Za-z &/\-\.\(\)]{3,}$")

# A cell that is entirely Latin but is a proper noun / unit / tool designation.
BENIGN_CELLS = {
    "Siah Makan", "Siahmakan", "PEDC - PECO", "NIDC", "OEOC",
    "SPP (psi)", "WOB (kilolb)",
    # tool designations and casing thread types are kept in Latin script by design
    "TMK-PF", "BTC", "HSM-1", "PH-6", "J-55", "N-80", "P-110", "L-80", "K-55",
    "NKT-95,N80", "W&R Tight",
}

RPR = ["rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike",
       "dstrike", "outline", "shadow", "emboss", "imprint", "noProof", "snapToGrid",
       "vanish", "webHidden", "color", "spacing", "w", "kern", "position", "sz",
       "szCs", "highlight", "u", "effect", "bdr", "shd", "fitText", "vertAlign",
       "rtl", "cs", "em", "lang", "eastAsianLayout", "specVanish", "oMath"]
PPR = ["pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl",
       "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens",
       "kinsoku", "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE",
       "autoSpaceDN", "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind",
       "contextualSpacing", "mirrorIndents", "suppressOverlap", "jc", "textDirection",
       "textAlignment", "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr",
       "sectPr", "pPrChange"]
TCPR = ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd",
        "noWrap", "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark"]


def out_of_order(xml, tag, order):
    bad = 0
    for m in re.finditer(r"<w:%s>(.*?)</w:%s>" % (tag, tag), xml, re.S):
        kids = re.findall(r"<w:([A-Za-z]+)[ />]", m.group(1))
        idx = [order.index(k) for k in kids if k in order]
        if idx != sorted(idx):
            bad += 1
    return bad


def scan(path, fa):
    doc = Document(path)
    res = {"file": path, "ok": True, "notes": []}

    body = "\n".join(p.text for p in doc.paragraphs)
    cells = [c.text for tb in doc.tables for r in tb.rows for c in r.cells]
    cell_text = "\n".join(cells)

    if fa:
        leaks = [p.text for p in doc.paragraphs if LATIN_WORDS.search(p.text)]
        res["para_leaks"] = len(leaks)
        if leaks:
            res["ok"] = False
            res["notes"].append("prose leak: %s" % leaks[0][:90])

        # A Latin numeral inside a Persian sentence reads as a formatting
        # mistake; Persian prose must use Persian numerals throughout.
        latin_digits = 0
        for p in doc.paragraphs:
            t = p.text
            if not ARABIC.search(t):
                continue
            for m in re.finditer(r"[0-9][0-9,.]*", t):
                s, e = m.start(), m.end()
                left, right = t[max(0, s - 1):s], t[e:e + 1]
                if left and (left.isalnum() or left in "-/_.#"):
                    continue          # part of SI-006, 8-3/8", pcf-40
                if right and (right in "-_/#\u00b0" or right.isalpha()):
                    continue
                latin_digits += 1
        res["latin_digits"] = latin_digits
        if latin_digits:
            res["ok"] = False
            res["notes"].append("%d Latin numeral(s) inside Persian prose" % latin_digits)

        label_cells = [c.strip() for c in cells
                       if ONLY_LATIN.match(c.strip()) and c.strip() not in BENIGN_CELLS]
        # A short Latin cell ending in a full stop (or containing a lower-case
        # word) is a verbatim DDR narrative fragment; a Title Case or upper-case
        # phrase with no final stop is a controlled-vocabulary label that must
        # have been translated through fa_glossary.
        quoted, labels = [], []
        for c in label_cells:
            words = c.split()
            narrative = (c.endswith(".") or any(w[:1].islower() for w in words)
                         or len(words) > 6)
            (quoted if narrative else labels).append(c)
        res["cell_labels"] = labels
        res["cell_quotes"] = len(quoted)
        if labels:
            res["ok"] = False
            res["notes"].append("english label in table: %s" % labels[:3])

        res["arabic_chars"] = len(ARABIC.findall(body + cell_text))
        if res["arabic_chars"] < 2000:
            res["ok"] = False
            res["notes"].append("Persian text suspiciously short")

        z = zipfile.ZipFile(path)
        xml = z.read("word/document.xml").decode("utf-8")
        res["bidi"] = xml.count("<w:bidi/>")
        res["rtl"] = xml.count('<w:rtl w:val="true"/>') + xml.count("<w:rtl/>")
        res["bidiVisual"] = xml.count("<w:bidiVisual/>")
        if not (res["bidi"] and res["rtl"] and res["bidiVisual"]):
            res["ok"] = False
            res["notes"].append("missing RTL markup")
        res["order_bad"] = (out_of_order(xml, "rPr", RPR) +
                            out_of_order(xml, "pPr", PPR) +
                            out_of_order(xml, "tcPr", TCPR))
        if res["order_bad"]:
            res["ok"] = False
            res["notes"].append("%d out-of-order property blocks" % res["order_bad"])
    else:
        res["arabic_chars"] = len(ARABIC.findall(body + cell_text))
        if res["arabic_chars"]:
            res["ok"] = False
            res["notes"].append("%d Arabic-script characters in English file"
                                % res["arabic_chars"])

    res["paragraphs"] = len(doc.paragraphs)
    res["tables"] = len(doc.tables)
    res["figures"] = len(doc.inline_shapes)
    return res


def main():
    targets = []
    for p in sorted(glob.glob(f"{OUT}/01_Well_Reports/*/*_FA.docx")):
        targets.append((p, True))
    targets.append((f"{OUT}/02_Asset_Comparison/Siah_Makan_Comparison_Report_FA.docx", True))
    for p in sorted(glob.glob(f"{OUT}/01_Well_Reports/*/*_EN.docx")):
        targets.append((p, False))
    targets.append((f"{OUT}/02_Asset_Comparison/Siah_Makan_Comparison_Report_EN.docx", False))

    fails = 0
    print("%-46s %5s %5s %5s %8s %s" % ("file", "para", "tbl", "fig", "script", "verdict"))
    print("-" * 96)
    for path, fa in targets:
        if not os.path.exists(path):
            print("%-46s MISSING" % os.path.basename(path))
            fails += 1
            continue
        r = scan(path, fa)
        script = ("FA %d" % r["arabic_chars"]) if fa else ("EN %d" % r["arabic_chars"])
        print("%-46s %5d %5d %5d %8s %s" % (os.path.basename(path), r["paragraphs"],
                                            r["tables"], r["figures"], script,
                                            "PASS" if r["ok"] else "FAIL"))
        for n in r["notes"]:
            print("        - %s" % n)
        if fa:
            print("        bidi=%d rtl=%d bidiVisual=%d quoted-DDR-cells=%d "
                  "latin-numerals=%d out-of-order=%d"
                  % (r["bidi"], r["rtl"], r["bidiVisual"], r["cell_quotes"],
                     r["latin_digits"], r["order_bad"]))
        if not r["ok"]:
            fails += 1

    print("\n%d file(s) checked, %d failing" % (len(targets), fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
