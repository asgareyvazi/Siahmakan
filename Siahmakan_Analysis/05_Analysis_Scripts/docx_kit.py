"""Shared DOCX construction helpers: styles, bilingual runs, RTL, tables,
captions, TOC field, headers and footers, page numbering.

Persian support is implemented at the OOXML level (not by visual right
alignment alone):
  * w:bidi on the paragraph properties
  * w:rtl on each run
  * w:bidiVisual on the table properties
  * w:lang w:bidi="fa-IR" on runs
  * a complex-script font (B Nazanin) set via w:rFonts w:cs
"""
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

EN_FONT = "Times New Roman"
FA_FONT = "B Nazanin"

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_NUMERIC_RE = None


def fa_digits(text):
    """Convert ASCII digits to Persian numerals."""
    return str(text).translate(_FA_DIGITS)


def fa_number(text):
    """Convert a value to Persian numerals only when the whole string is a
    numeric quantity (digits, separators, sign, percent). Identifiers such as
    SI-009 and units such as pcf are left untouched."""
    import re
    t = str(text)
    if not t:
        return t
    if re.fullmatch(r"[\s\d,.\-–%+/()]*", t) and any(ch.isdigit() for ch in t):
        return fa_digits(t)
    return t


ACCENT = RGBColor(0x1F, 0x4E, 0x79)
ACCENT2 = RGBColor(0xC0, 0x00, 0x00)
GREY = RGBColor(0x59, 0x59, 0x59)


# --------------------------------------------------------------------------- #
# low level
# --------------------------------------------------------------------------- #
def _set(el, tag, **attrs):
    child = OxmlElement(tag)
    for k, v in attrs.items():
        child.set(qn(k), v)
    el.append(child)
    return child


def rtl_paragraph(p, rtl=True):
    pPr = p._p.get_or_add_pPr()
    for old in pPr.findall(qn("w:bidi")):
        pPr.remove(old)
    if rtl:
        pPr.append(OxmlElement("w:bidi"))


def rtl_run(run, rtl=True):
    rPr = run._element.get_or_add_rPr()
    for old in rPr.findall(qn("w:rtl")):
        rPr.remove(old)
    if rtl:
        rPr.append(OxmlElement("w:rtl"))


def rtl_table(table):
    tblPr = table._tbl.tblPr
    for old in tblPr.findall(qn("w:bidiVisual")):
        tblPr.remove(old)
    tblPr.append(OxmlElement("w:bidiVisual"))


def set_run_font(run, name=None, size=None, bold=None, color=None, rtl=False,
                 italic=None):
    if rtl:
        name = name or FA_FONT
        rPr = run._element.get_or_add_rPr()
        rf = rPr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts")
            rPr.insert(0, rf)
        rf.set(qn("w:cs"), name)
        rf.set(qn("w:ascii"), name)
        rf.set(qn("w:hAnsi"), name)
        lang = OxmlElement("w:lang")
        lang.set(qn("w:bidi"), "fa-IR")
        rPr.append(lang)
        rtl_run(run, True)
    elif name:
        run.font.name = name
        rPr = run._element.get_or_add_rPr()
        rf = rPr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts")
            rPr.insert(0, rf)
        rf.set(qn("w:ascii"), name)
        rf.set(qn("w:hAnsi"), name)
        rf.set(qn("w:cs"), name)
    if size is not None:
        run.font.size = Pt(size)
        if rtl:
            rPr = run._element.get_or_add_rPr()
            szcs = OxmlElement("w:szCs")
            szcs.set(qn("w:val"), str(int(size * 2)))
            rPr.append(szcs)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color is not None:
        run.font.color.rgb = color


def style_document(doc):
    st = doc.styles["Normal"]
    st.font.name = EN_FONT
    st.font.size = Pt(10.5)
    rPr = st.element.get_or_add_rPr()
    rf = rPr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rPr.insert(0, rf)
    rf.set(qn("w:ascii"), EN_FONT)
    rf.set(qn("w:hAnsi"), EN_FONT)
    rf.set(qn("w:cs"), FA_FONT)
    pf = st.paragraph_format
    pf.space_after = Pt(4)
    pf.line_spacing = 1.12
    for i, sz in ((1, 16), (2, 13), (3, 11.5), (4, 10.5)):
        s = doc.styles[f"Heading {i}"]
        s.font.name = EN_FONT
        s.font.size = Pt(sz)
        s.font.color.rgb = ACCENT
        s.font.bold = True
        s.paragraph_format.space_before = Pt(10 if i <= 2 else 8)
        s.paragraph_format.space_after = Pt(4)
        s.paragraph_format.keep_with_next = True


# --------------------------------------------------------------------------- #
# bilingual paragraph builders
# --------------------------------------------------------------------------- #
def para_en(doc, text="", size=10.5, bold=False, italic=False, align=None,
            space_after=4, color=None, style=None):
    p = doc.add_paragraph(style=style)
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    r = p.add_run(text)
    set_run_font(r, EN_FONT, size, bold, color, rtl=False, italic=italic)
    return p


def para_fa(doc, text="", size=11, bold=False, align=WD_ALIGN_PARAGRAPH.RIGHT,
            space_after=4, color=None):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    rtl_paragraph(p, True)
    for chunk, is_latin in split_latin(text):
        r = p.add_run(chunk)
        set_run_font(r, FA_FONT, size, bold, color, rtl=True)
        if is_latin:
            _tag_english(r)
    return p


def _tag_english(run):
    """Mark a run as English so Word uses the Latin face inside a RTL paragraph."""
    rPr = run._element.get_or_add_rPr()
    lang = OxmlElement("w:lang")
    lang.set(qn("w:val"), "en-US")
    rPr.append(lang)


_LATIN_RE = __import__("re").compile(
    r"([A-Za-z][A-Za-z0-9 .,%_/\-]*[A-Za-z0-9%/]|[A-Za-z])")


def split_latin(text):
    """Split a bilingual string into (chunk, is_latin) pieces.

    Latin/technical tokens (well names, units, abbreviations) are split out so
    they can be given an English language attribute and rendered in the Latin
    face, while Persian text stays in the complex-script face. ASCII digits are
    converted to Persian numerals only inside Persian chunks.

    A Latin token keeps its neighbouring digits inside the same run (`#3`,
    `pcf`) but gives them up when that digit belongs to a word of its own -
    otherwise a bare `# ` before the Persian numerals of a bit number would be
    shuffled to the end of the cell by the bidi algorithm (`۳#`).
    """
    import re
    out = []
    pos = 0
    for m in _LATIN_RE.finditer(text):
        start, end = m.start(), m.end()
        if m.group(0) == "#":
            while end > start and text[end - 1].isdigit():
                end -= 1
        if start > pos:
            out.append((fa_digits(text[pos:start]), False))
        out.append((text[start:end], True))
        pos = end
    if pos < len(text):
        out.append((fa_digits(text[pos:]), False))
    return out or [(text, False)]


def heading(doc, text, level=1, fa=False):
    h = doc.add_heading(level=level)
    r = h.add_run(text)
    if fa:
        rtl_paragraph(h, True)
        h.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        set_run_font(r, FA_FONT, {1: 16, 2: 13, 3: 11.5, 4: 10.5}.get(level, 10.5),
                     True, ACCENT, rtl=True)
    else:
        set_run_font(r, EN_FONT, {1: 16, 2: 13, 3: 11.5, 4: 10.5}.get(level, 10.5),
                     True, ACCENT, rtl=False)
    return h


def bullets(doc, items, fa=False, size=None):
    for it in items:
        if fa:
            p = doc.add_paragraph(style="List Bullet")
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            rtl_paragraph(p, True)
            r = p.add_run(it)
            set_run_font(r, FA_FONT, size or 10.5, False, None, rtl=True)
        else:
            p = doc.add_paragraph(style="List Bullet")
            r = p.add_run(it)
            set_run_font(r, EN_FONT, size or 10, False, None, rtl=False)


# --------------------------------------------------------------------------- #
# tables
# --------------------------------------------------------------------------- #
def _shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def table(doc, header, rows, widths=None, fa=False, size=8.5, header_fill="1F4E79",
          align_right_cols=None, caption=None, caption_prefix="Table"):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    if fa:
        rtl_table(t)
    hdr = t.rows[0].cells
    for i, h in enumerate(header):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if fa else WD_ALIGN_PARAGRAPH.CENTER
        if fa:
            rtl_paragraph(p, True)
        r = p.add_run(str(h))
        set_run_font(r, FA_FONT if fa else EN_FONT, size, True,
                     RGBColor(0xFF, 0xFF, 0xFF), rtl=fa)
        _shade(hdr[i], header_fill)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            if fa:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                rtl_paragraph(p, True)
            elif align_right_cols and i in align_right_cols:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            txt = "" if v is None else str(v)
            if fa:
                for chunk, is_latin in split_latin(txt):
                    r = p.add_run(chunk)
                    set_run_font(r, FA_FONT, size, False, None, rtl=True)
                    if is_latin:
                        _tag_english(r)
                continue
            r = p.add_run(txt)
            set_run_font(r, EN_FONT, size, False, None, rtl=False)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                if i < len(row.cells):
                    row.cells[i].width = Cm(w)
    if caption:
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.RIGHT if fa else WD_ALIGN_PARAGRAPH.LEFT
        if fa:
            rtl_paragraph(cap, True)
        if fa:
            for chunk, is_latin in split_latin(caption):
                r = cap.add_run(chunk)
                set_run_font(r, FA_FONT, 8.5, False, GREY, rtl=True, italic=True)
                if is_latin:
                    _tag_english(r)
        else:
            r = cap.add_run(caption)
            set_run_font(r, EN_FONT, 8.5, False, GREY, rtl=fa, italic=True)
        cap.paragraph_format.space_after = Pt(8)
    return t


def kv_table(doc, pairs, fa=False, size=9, widths=(5.2, 7.0)):
    t = doc.add_table(rows=0, cols=2)
    t.style = "Table Grid"
    if fa:
        rtl_table(t)
    for k, v in pairs:
        cells = t.add_row().cells
        for i, val in enumerate((k, v)):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if fa else (
                WD_ALIGN_PARAGRAPH.LEFT if i == 0 else WD_ALIGN_PARAGRAPH.LEFT)
            if fa:
                rtl_paragraph(p, True)
            txt = str(val)
            if fa:
                txt = fa_number(txt)
            r = p.add_run(txt)
            set_run_font(r, FA_FONT if fa else EN_FONT, size, i == 0, None, rtl=fa)
        _shade(cells[0], "EFF3F8")
    for row in t.rows:
        row.cells[0].width = Cm(widths[0])
        row.cells[1].width = Cm(widths[1])
    return t


# --------------------------------------------------------------------------- #
# figures, captions, TOC, fields
# --------------------------------------------------------------------------- #
def figure(doc, path, width_cm=15.5, caption=None, fa=False, numbering=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(path, width=Cm(width_cm))
    if caption:
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if fa:
            rtl_paragraph(cap, True)
        r = cap.add_run(caption)
        set_run_font(r, FA_FONT if fa else EN_FONT, 8.5, False, GREY, rtl=fa, italic=True)
        cap.paragraph_format.space_after = Pt(10)


def add_field(paragraph, instr, fa=False):
    r = paragraph.add_run()
    fld = OxmlElement("w:fldChar")
    fld.set(qn("w:fldCharType"), "begin")
    r._r.append(fld)
    r2 = paragraph.add_run()
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = instr
    r2._r.append(it)
    r3 = paragraph.add_run()
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    r3._r.append(sep)
    r4 = paragraph.add_run(
        "برای ساخت این فهرست، روی فیلد راست‌کلیک کرده و Update Field را انتخاب کنید."
        if fa else
        "Right-click and choose 'Update Field' to build this list.")
    set_run_font(r4, FA_FONT if fa else EN_FONT, 9, False, GREY, rtl=fa)
    r5 = paragraph.add_run()
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    r5._r.append(end)


def toc(doc, fa=False):
    heading(doc, "فهرست مطالب" if fa else "Table of Contents", 1, fa=fa)
    p = doc.add_paragraph()
    add_field(p, 'TOC \\o "1-3" \\h \\z \\u', fa=fa)
    note = doc.add_paragraph()
    if fa:
        rtl_paragraph(note, True)
        r = note.add_run("این فهرست به‌صورت خودکار است؛ در Word روی آن راست‌کلیک کرده و "
                         "«Update Field» را انتخاب کنید.")
    else:
        r = note.add_run("This is an automatic field. In Word, right-click the field and "
                         "choose Update Field to populate the page numbers.")
    set_run_font(r, FA_FONT if fa else EN_FONT, 8.5, False, GREY, rtl=fa, italic=True)


def page_number_field(paragraph, fa=False):
    r = paragraph.add_run()
    fld = OxmlElement("w:fldChar")
    fld.set(qn("w:fldCharType"), "begin")
    r._r.append(fld)
    r2 = paragraph.add_run()
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = "PAGE"
    r2._r.append(it)
    r3 = paragraph.add_run()
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    r3._r.append(sep)
    r4 = paragraph.add_run("1")
    set_run_font(r4, FA_FONT if fa else EN_FONT, 8.5, False, GREY, rtl=fa)
    r5 = paragraph.add_run()
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    r5._r.append(end)


def header_footer(section, left, right, fa=False):
    hdr = section.header
    hdr.is_linked_to_previous = False
    p = hdr.paragraphs[0]
    p.text = ""
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if fa else WD_ALIGN_PARAGRAPH.LEFT
    if fa:
        rtl_paragraph(p, True)
    r = p.add_run(left)
    set_run_font(r, FA_FONT if fa else EN_FONT, 8, False, GREY, rtl=fa)
    # tab then right detail
    r2 = p.add_run("\t\t" + right)
    set_run_font(r2, FA_FONT if fa else EN_FONT, 8, False, GREY, rtl=fa)
    # bottom border
    pPr = p._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr")
    bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"), "single")
    bot.set(qn("w:sz"), "4")
    bot.set(qn("w:space"), "1")
    bot.set(qn("w:color"), "BFBFBF")
    bdr.append(bot)
    pPr.append(bdr)

    ftr = section.footer
    ftr.is_linked_to_previous = False
    fp = ftr.paragraphs[0]
    fp.text = ""
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if fa:
        rtl_paragraph(fp, True)
    page_number_field(fp, fa=fa)


def new_doc():
    doc = Document()
    style_document(doc)
    s = doc.sections[0]
    s.top_margin = Cm(2.0)
    s.bottom_margin = Cm(2.0)
    s.left_margin = Cm(2.2)
    s.right_margin = Cm(2.2)
    return doc


def cover(doc, title, subtitle, meta_lines, fa=False):
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(title)
    set_run_font(r, FA_FONT if fa else EN_FONT, 24 if not fa else 26, True, ACCENT, rtl=fa)
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run(subtitle)
    set_run_font(r2, FA_FONT if fa else EN_FONT, 14, False, ACCENT2, rtl=fa)
    doc.add_paragraph()
    doc.add_paragraph()
    for line in meta_lines:
        pm = doc.add_paragraph()
        pm.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if fa:
            rtl_paragraph(pm, True)
            for chunk, is_latin in split_latin(line):
                rm = pm.add_run(chunk)
                set_run_font(rm, FA_FONT, 10.5, False, None, rtl=True)
                if is_latin:
                    _tag_english(rm)
            continue
        rm = pm.add_run(line)
        set_run_font(rm, EN_FONT, 10.5, False, None, rtl=fa)
    doc.add_paragraph()
    doc.add_paragraph()
    pn = doc.add_paragraph()
    pn.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rn = pn.add_run("Prepared from the original daily drilling reports. No value in this "
                    "document is estimated unless it is explicitly labelled as such."
                    if not fa else
                    "این سند بر پایه گزارش‌های روزانه حفاری تهیه شده است. هیچ مقداری "
                    "تخمینی نیست مگر آنکه صریحاً ذکر شود.")
    set_run_font(rn, FA_FONT if fa else EN_FONT, 8.5, False, GREY, rtl=fa, italic=True)
    doc.add_page_break()


# --------------------------------------------------------------------------- #
# OOXML schema-order normalisation
# --------------------------------------------------------------------------- #
_RPR_ORDER = [
    "rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike",
    "dstrike", "outline", "shadow", "emboss", "imprint", "noProof", "snapToGrid",
    "vanish", "webHidden", "color", "spacing", "w", "kern", "position", "sz",
    "szCs", "highlight", "u", "effect", "bdr", "shd", "fitText", "vertAlign",
    "rtl", "cs", "em", "lang", "eastAsianLayout", "specVanish", "oMath",
]
_PPR_ORDER = [
    "pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr",
    "widowControl", "numPr", "suppressLineNumbers", "pBdr", "shd", "tabs",
    "suppressAutoHyphens", "kinsoku", "wordWrap", "overflowPunct",
    "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
    "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents",
    "suppressOverlap", "jc", "textDirection", "textAlignment",
    "textboxTightWrap", "outlineLvl", "divId", "cnfStyle", "rPr",
    "sectPr", "pPrChange",
]
_TCPR_ORDER = [
    "cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd",
    "noWrap", "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark",
]


def _reorder(parent, order):
    """Reorder element children of `parent` to match the schema sequence."""
    if parent is None:
        return
    idx = {name: i for i, name in enumerate(order)}
    children = list(parent)
    keyed = []
    for pos, child in enumerate(children):
        tag = child.tag.split("}")[-1]
        keyed.append((idx.get(tag, 999), pos, child))
    keyed.sort(key=lambda t: (t[0], t[1]))
    for child in children:
        parent.remove(child)
    for _, _, child in keyed:
        parent.append(child)


def _tag_latin(text):
    """Wrap Latin/technical tokens inside a Persian run with a language marker.

    Word applies the paragraph's complex-script font to Latin characters unless
    the run carries w:lang w:val="en-US", which makes technical identifiers render
    in the wrong face. The marker is a zero-width run split, applied at build time
    in `para_fa`/`table`.
    """
    return text


_CS_RE = None


def normalise_ooxml(path):
    """Rewrite a DOCX so every rPr / pPr / tcPr child sequence is schema-valid.

    python-docx and manual OxmlElement insertion do not enforce child order, and
    Word tolerates that. Strict OOXML validators and some converters do not, so
    the order is repaired here as a post-processing step.
    """
    import os
    import shutil
    import tempfile
    import zipfile

    tmp = tempfile.mkdtemp()
    out = os.path.join(tmp, "out.docx")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("word/") and item.filename.endswith(".xml"):
                text = data.decode("utf-8")
                for tag, order in (("w:rPr", _RPR_ORDER), ("w:pPr", _PPR_ORDER),
                                   ("w:tcPr", _TCPR_ORDER)):
                    text = _fix_block(text, tag, order)
                data = text.encode("utf-8")
            zout.writestr(item, data)
    shutil.move(out, path)
    shutil.rmtree(tmp, ignore_errors=True)


def _fix_block(xml, tag, order):
    """Find each <tag>...</tag> (non-nested content) and sort its children."""
    import re
    open_tag = f"<{tag}>"
    open_attr = f"<{tag} "
    close_tag = f"</{tag}>"
    out = []
    i = 0
    while True:
        a = xml.find(open_tag, i)
        b = xml.find(open_attr, i)
        if a == -1 and b == -1:
            out.append(xml[i:])
            break
        s = a if (a != -1 and (b == -1 or a < b)) else b
        out.append(xml[i:s])
        gt = xml.find(">", s)
        head = xml[s:gt + 1]
        e = xml.find(close_tag, gt)
        if e == -1:
            out.append(xml[s:])
            break
        inner = xml[gt + 1:e]
        # only reorder if children are flat (no nested same-tag blocks)
        if f"<{tag}" not in inner:
            kids = _split_children(inner, order)
            out.append(head + "".join(kids) + close_tag)
        else:
            out.append(xml[s:e + len(close_tag)])
        i = e + len(close_tag)
    return "".join(out)


def _split_children(inner, order):
    import re
    idx = {n: i for i, n in enumerate(order)}
    tokens = re.findall(r"<(?!/)[^>]+/>|<(?!/)[^>]+>[^<]*</[^>]+>|[^<]+", inner)
    keyed = []
    for pos, t in enumerate(tokens):
        m = re.match(r"<([A-Za-z0-9]+:)?([A-Za-z0-9]+)", t)
        name = m.group(2) if m else None
        keyed.append((idx.get(name, 999) if name else 1000, pos, t))
    keyed.sort(key=lambda x: (x[0], x[1]))
    return [t for _, _, t in keyed]
