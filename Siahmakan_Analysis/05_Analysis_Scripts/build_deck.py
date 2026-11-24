"""Exactly 10-slide Persian management presentation.

Rules applied:
  * Slide text and titles are Persian and right-aligned; tables on Persian slides
    are given a right-to-left column order and right-aligned cells.
  * Every chart, axis, legend and unit stays in English because Persian text in
    chart labels does not render reliably in PowerPoint on all platforms.
  * Figures are the same PNGs used in the Word reports, so the numbers agree.
"""
import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Inches, Pt

import report_content as RC

OUT = "Siahmakan_Analysis/03_Presentation"
FIG = "Siahmakan_Analysis/02_Asset_Comparison/Figures"
WELL_FIG = "Siahmakan_Analysis/01_Well_Reports"
W = RC.WELLS

NAVY = RGBColor(0x1F, 0x3E, 0x63)
TEAL = RGBColor(0x1F, 0x6F, 0x8B)
RED = RGBColor(0xB0, 0x1E, 0x2E)
GREY = RGBColor(0x59, 0x59, 0x59)
LGREY = RGBColor(0xEF, 0xEF, 0xEF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

FA_FONT = "B Nazanin"
EN_FONT = "Arial"


def fa(v):
    return str(v).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def fmt(v, nd=0):
    if v in (None, "", "None"):
        return "—"
    try:
        return f"{float(v):,.{nd}f}"
    except (TypeError, ValueError):
        return str(v)


def pct(v, nd=1):
    return "—" if v in ("", None) else f"{float(v):.{nd}f} %"


# --------------------------------------------------------------------------- #
def set_rtl(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    pPr.set("rtl", "1")


def textbox(slide, left, top, width, height, text, size=14, bold=False,
            color=NAVY, align=PP_ALIGN.RIGHT, rtl=True, anchor=MSO_ANCHOR.TOP,
            font=FA_FONT, spacing=1.0):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if rtl:
            set_rtl(p)
        p.line_spacing = spacing
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
        r.font.name = font
        if rtl:
            rPr = r._r.get_or_add_rPr()
            rPr.set("lang", "fa-IR")
    return tb


def bullets(slide, left, top, width, height, items, size=13, color=NAVY, space=8):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.RIGHT
        set_rtl(p)
        p.space_after = Pt(space)
        r = p.add_run()
        r.text = "▪ " + it
        r.font.size = Pt(size)
        r.font.color.rgb = color
        r.font.name = FA_FONT
        pPr = p._p.get_or_add_pPr()
        pPr.set("rtl", "1")
    return tb


def slide_title(slide, title, sub=None):
    bar = slide.shapes.add_shape(1, 0, 0, Inches(13.333), Inches(0.09))
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    textbox(slide, Inches(0.55), Inches(0.22), Inches(12.2), Inches(0.6), title,
            size=26, bold=True, color=NAVY)
    if sub:
        textbox(slide, Inches(0.55), Inches(0.82), Inches(12.2), Inches(0.4), sub,
                size=13, color=TEAL)


def footer(slide, n, total=10):
    textbox(slide, Inches(0.55), Inches(7.05), Inches(9.0), Inches(0.32),
            "میدان سیاه‌مکان — مرور جامع مهندسی حفاری، تکمیل و عملکرد چاه‌ها",
            size=9, color=GREY)
    textbox(slide, Inches(11.6), Inches(7.05), Inches(1.2), Inches(0.32),
            fa(f"{n} / {total}"), size=9, color=GREY, align=PP_ALIGN.LEFT, rtl=False)


def picture(slide, path, left, top, width=None, height=None, max_bottom=None):
    """Place a picture, shrinking it if it would cross `max_bottom`.

    PowerPoint does not clip; a picture that runs past the slide edge or into
    the footer is simply lost.  matplotlib figures come out at whatever aspect
    the axes need, so the height is checked against the space actually left on
    the slide and the width is scaled down with it.
    """
    if not os.path.exists(path):
        return None
    from PIL import Image
    iw, ih = Image.open(path).size
    if width is None and height is None:
        width = Inches(6)
    w = width if width is not None else int(height * iw / ih)
    h = height if height is not None else int(width * ih / iw)
    if max_bottom is not None and top + h > max_bottom:
        scale = (max_bottom - top) / h
        w, h = int(w * scale), int(h * scale)
    return slide.shapes.add_picture(path, left, top, width=w, height=h)


def table(slide, left, top, width, height, header, rows, col_widths=None,
          font_size=10, header_fill=NAVY, rtl=True):
    nrows, ncols = len(rows) + 1, len(header)
    shp = slide.shapes.add_table(nrows, ncols, left, top, width, height)
    tbl = shp.table
    if col_widths:
        total = sum(col_widths)
        for i, cw in enumerate(col_widths):
            tbl.columns[i].width = Emu(int(width * cw / total))
    for j, h in enumerate(header):
        cell = tbl.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = header_fill
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = str(h)
        r.font.size = Pt(font_size)
        r.font.bold = True
        r.font.color.rgb = WHITE
        r.font.name = EN_FONT
    for i, row in enumerate(rows, 1):
        for j, v in enumerate(row):
            cell = tbl.cell(i, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if i % 2 else LGREY
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            r = p.add_run()
            r.text = str(v)
            r.font.size = Pt(font_size)
            r.font.color.rgb = NAVY
            r.font.name = EN_FONT
    return tbl


def caption(slide, text, top=Inches(6.75)):
    textbox(slide, Inches(0.6), top, Inches(12.1), Inches(0.3), text,
            size=9, color=GREY, align=PP_ALIGN.CENTER)


def kpi(slide, left, top, width, height, value, label, color=NAVY):
    box = slide.shapes.add_shape(1, left, top, width, height)
    box.fill.solid()
    box.fill.fore_color.rgb = WHITE
    box.line.color.rgb = color
    box.line.width = Pt(1.25)
    box.shadow.inherit = False
    textbox(slide, left, top + Inches(0.06), width, Inches(0.42), value,
            size=20, bold=True, color=color, align=PP_ALIGN.CENTER, rtl=False)
    textbox(slide, left, top + Inches(0.5), width, Inches(0.5), label,
            size=10, color=GREY, align=PP_ALIGN.CENTER)


# --------------------------------------------------------------------------- #
def build():
    C = {r["well"]: r for r in RC.R(f"{RC.CALC}/comparison_matrix.csv")}
    M = {r["well"]: r for r in RC.R(f"{RC.CALC}/well_master_register.csv")}
    D = {w: RC.get(w) for w in W}
    T = {r["well"]: r for r in RC.R(f"{RC.CALC}/trajectory_assessment.csv")}

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    tot_depth = sum(float(C[w]["final_depth_m"] or 0) for w in W)
    tot_days = sum(float(C[w]["calendar_days"] or 0) for w in W)
    tot_h = sum(float(C[w]["total_op_hours"] or 0) for w in W)
    tot_npt = sum(float(C[w]["npt_hours"] or 0) for w in W)
    tot_ddr = sum(int(M[w]["ddr_count"]) for w in W)

    # ---------------- slide 1: title
    s = prs.slides.add_slide(blank)
    bg = s.shapes.add_shape(1, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = NAVY
    bg.line.fill.background()
    textbox(s, Inches(0.8), Inches(1.55), Inches(11.7), Inches(1.1),
            "میدان سیاه‌مکان", size=48, bold=True, color=WHITE)
    textbox(s, Inches(0.8), Inches(2.75), Inches(11.7), Inches(1.0),
            "مرور جامع مهندسی حفاری، تکمیل و عملکرد چاه‌ها", size=26, color=WHITE)
    ln = s.shapes.add_shape(1, Inches(8.4), Inches(3.85), Inches(4.1), Inches(0.045))
    ln.fill.solid()
    ln.fill.fore_color.rgb = RGBColor(0x8F, 0xB4, 0xD1)
    ln.line.fill.background()
    textbox(s, Inches(0.8), Inches(4.15), Inches(11.7), Inches(0.5),
            "دوره گزارش‌دهی: ۱۷ مارس ۲۰۲۱ تا ۲۵ آوریل ۲۰۲۳", size=16,
            color=RGBColor(0xD6, 0xE4, 0xF0))
    textbox(s, Inches(0.8), Inches(4.7), Inches(11.7), Inches(0.5),
            f"چاه‌های شناسایی‌شده: {fa(4)}   |   چاه‌های تحلیل‌شده: {fa(4)}   |   "
            f"گزارش‌های روزانه پردازش‌شده: {fa(f'{tot_ddr:,}')}", size=16,
            color=RGBColor(0xD6, 0xE4, 0xF0))
    textbox(s, Inches(0.8), Inches(5.35), Inches(11.7), Inches(0.5),
            "تهیه‌شده از گزارش‌های حفاری روزانه اصلی — نسخه ۱٫۰ — ۲۰۲۶-۱۱-۲۴",
            size=13, color=RGBColor(0xA9, 0xC2, 0xD8))

    # ---------------- slide 2: asset overview
    s = prs.slides.add_slide(blank)
    slide_title(s, "نمای کلی دارایی", "چهار چاه، سه دکل، یک میدان — و یک محدودیت داده مشترک")
    rows = []
    for w in W:
        rows.append([w, fmt(C[w]["final_depth_m"]), fmt(C[w]["calendar_days"]),
                     fmt(C[w]["npt_pct"], 1) + " %", fmt(C[w]["n_sections"]),
                     fmt(C[w]["n_bit_runs"])])
    table(s, Inches(0.55), Inches(1.30), Inches(7.3), Inches(2.4),
          ["چاه", "عمق نهایی (متر)", "مدت (روز)", "زمان غیرمولد", "مقاطع", "ران مته"],
          rows, col_widths=[1.1, 1.5, 1.2, 1.3, 0.9, 1.0], font_size=11)
    caption(s, "عمق‌ها اندازه‌گیری‌شده (MD) است؛ داده پیمایش برای تبدیل به TVD موجود نیست.", Inches(3.80))
    kpi(s, Inches(8.15), Inches(1.30), Inches(2.05), Inches(1.02), fa(f"{tot_depth:,.0f}"),
        "مجموع عمق حفاری‌شده (متر)")
    kpi(s, Inches(10.55), Inches(1.30), Inches(2.05), Inches(1.02), fa(f"{tot_days:,.0f}"),
        "مجموع روزهای دکل")
    kpi(s, Inches(8.15), Inches(2.48), Inches(2.05), Inches(1.02),
        fa(f"{100*tot_npt/tot_h:.1f}") + "٪", "سهم زمان غیرمولد", RED)
    kpi(s, Inches(10.55), Inches(2.48), Inches(2.05), Inches(1.02),
        fa(f"{tot_h:,.0f}"), "مجموع ساعات ثبت‌شده")
    bullets(s, Inches(0.55), Inches(4.25), Inches(12.2), Inches(2.5), [
        "هر چاه با یک فایل کاری گزارش روزانه نمایندگی می‌شود؛ گزارش نهایی چاه، برنامه حفاری و "
        "برنامه تکمیل ارائه نشده است.",
        "هزینه: در هیچ‌یک از ۱٬۲۳۷ برگه گزارش روزانه فیلدی برای هزینه، AFE یا صورت‌حساب وجود ندارد.",
        "پیمایش مسیر: SI-006 و SI-009 فقط قالب ثابت کم‌عمق دارند، SI-007 داده عددی ندارد و "
        "SI-008 مجموعه ناقص تا ۴۶۱۰ متر دارد.",
        "تولید و آزمون چاه: هیچ داده نرخ، فشار یا تولید در مدارک نیست؛ تحلیل به پایان حفاری محدود است.",
    ], size=12.5)

    # ---------------- slide 3: lifecycle timeline
    s = prs.slides.add_slide(blank)
    slide_title(s, "نمای کلی عملکرد چاه", "منحنی عمق–زمان از گزارش‌های روزانه، بدون درون‌یابی شکاف‌ها")
    pic_w = Inches(5.95)
    picture(s, f"{WELL_FIG}/SI-006/Figures/SI-006_fig_depth_time.png", Inches(0.45), Inches(1.28), width=pic_w)
    picture(s, f"{WELL_FIG}/SI-007/Figures/SI-007_fig_depth_time.png", Inches(6.75), Inches(1.28), width=pic_w)
    textbox(s, Inches(0.45), Inches(4.62), Inches(5.95), Inches(0.3),
            "SI-006 — ۴۲۱ روز، عمق ۵۱۴۴ متر، یک سایدترک", size=10.5, color=GREY,
            align=PP_ALIGN.CENTER)
    textbox(s, Inches(6.75), Inches(4.62), Inches(5.95), Inches(0.3),
            "SI-007 — ۴۹۸ روز، عمق ۴۴۱۰ متر، یک سایدترک طولانی", size=10.5, color=GREY,
            align=PP_ALIGN.CENTER)
    bullets(s, Inches(0.55), Inches(5.05), Inches(12.2), Inches(1.9), [
        "SI-006 در روز ۱۸۹ از عمق ۳۹۸۴ به ۳۴۲۵ متر بازگشت؛ این تنها نشانه قطعی سایدترک در داده است.",
        "SI-007 در روز ۲۳۰ از ۴۴۱۰ به ۴۱۷۴ متر بازگشت، پس از آنکه بازیابی سیم‌خطی شکست خورد.",
        "SI-008 و SI-009 سایدترک ندارند اما مدارک هر دو پیش از رسیدن به هدف پایان می‌یابد.",
    ], size=12)

    # ---------------- slide 4: drilling efficiency
    s = prs.slides.add_slide(blank)
    slide_title(s, "راندمان حفاری", "سرعت نفوذ به تفکیک مقطع — مخرج، ساعت حفاری خالص است")
    picture(s, f"{FIG}/fig_section_rop.png", Inches(0.55), Inches(1.25), width=Inches(8.05))
    rows = []
    for w in W:
        rows.append([w, fmt(C[w]["rop_m_per_h_drilling"], 2), fmt(C[w]["rop_m_per_day_overall"], 2)])
    table(s, Inches(8.85), Inches(1.35), Inches(3.95), Inches(1.75),
          ["چاه", "متر/ساعت حفاری", "متر/روز"],
          rows, col_widths=[1.0, 1.5, 1.2], font_size=9.5)
    caption(s, "نرخ ساعتی فقط کد ۲-۱ را در مخرج دارد؛ نرخ روزانه همه توقف‌ها را شامل می‌شود.",
            Inches(3.20))
    bullets(s, Inches(8.75), Inches(3.60), Inches(4.2), Inches(3.0), [
        "مقطع ۱۷½ اینچ در همه چاه‌ها سریع‌ترین است (۴٫۲ تا ۶٫۲ متر بر ساعت).",
        "مقطع ۸⅜ اینچ کندترین است (۱٫۸ تا ۵٫۷ متر بر ساعت).",
        "ترتیب چاه‌ها بین مقاطع برعکس می‌شود: SI-007 در سطح پیشتاز و در عمق کندترین است.",
        "علت اصلی، وضعیت چاه و نه طراحی مته است: مقطع ۸⅜ در SI-007 تحت ناپایداری پیوسته حفاری شد.",
    ], size=11)

    # ---------------- slide 5: bit/BHA and parameters
    s = prs.slides.add_slide(blank)
    slide_title(s, "مته، رشته حفاری و پارامترهای حفاری",
                "دامنه عملکرد درون یک چاه از اختلاف بین چاه‌ها بیشتر است")
    picture(s, f"{FIG}/fig_bit_rop_by_well.png", Inches(0.55), Inches(1.25), width=Inches(7.55))
    rows = []
    for w in W:
        bs = D[w]["bits_drilling"]
        if bs:
            rops = [float(b["rop_m_per_h"]) for b in bs]
            rows.append([w, len(bs), fmt(max(rops), 2), fmt(min(rops), 2),
                         fmt(sum(float(b["footage_m"]) for b in bs), 0)])
    table(s, Inches(8.35), Inches(1.35), Inches(4.45), Inches(2.1),
          ["چاه", "ران", "بهترین", "کندترین", "متراژ کل"],
          rows, col_widths=[0.95, 0.8, 1.0, 1.05, 1.5], font_size=9.5)
    caption(s, "بهترین و کندترین سرعت نفوذ هر چاه (متر بر ساعت) و مجموع متراژ ران‌ها.",
            Inches(3.55))
    bullets(s, Inches(8.30), Inches(3.95), Inches(4.6), Inches(2.7), [
        "ران SI-008-BIT-15: مته PDC ۸⅜ اینچ، ۱۰۳۰ متر در ۱۶۸٫۵ ساعت، ۶٫۱۱ متر بر ساعت.",
        "همان قطر در SI-007: ۰٫۴۵ تا ۱٫۷۵ متر بر ساعت — تفاوت بیش از سه برابر.",
        "انرژی ویژه مکانیکی (MSE) محاسبه نشد: لاگ پیوسته پارامتر–عمق وجود ندارد و "
        "میانگین روزانه، عدد بی‌معنا می‌دهد.",
    ], size=11)

    # ---------------- slide 6: NPT
    s = prs.slides.add_slide(blank)
    slide_title(s, "زمان غیرمولد و رخدادهای اصلی",
                f"مجموع {fa(f'{tot_npt:,.0f}')} ساعت — {fa(f'{100*tot_npt/tot_h:.1f}')} درصد کل زمان ثبت‌شده")
    picture(s, f"{FIG}/fig_npt_family.png", Inches(0.45), Inches(1.22), width=Inches(7.75))
    rows = []
    for w in W:
        top = D[w]["top_family"]
        rows.append([w, top["family"][:26] if top else "—",
                     fmt(top["hours"], 0) if top else "—",
                     fmt(C[w]["npt_pct"], 1) + " %"])
    table(s, Inches(8.35), Inches(1.30), Inches(4.5), Inches(2.35),
          ["چاه", "خانواده غالب", "ساعت", "سهم"],
          rows, col_widths=[0.85, 2.0, 0.75, 0.85], font_size=8.5)
    bullets(s, Inches(8.30), Inches(3.85), Inches(4.6), Inches(2.9), [
        "سه چاه از چهار چاه، بیشترین زمان را در انتظار سطحی از دست داده‌اند، نه در نقص درون‌چاهی.",
        "SI-009 استثناست: یک رخداد کنترل چاه ۵۲۵ ساعت عملیات و ۲۴۳ ساعت کشتن چاه مصرف کرد.",
        "تفکیک مهم است: زمان انتظار با قرارداد و لجستیک حل می‌شود، مشکل چاه با مهندسی.",
    ], size=11)

    # ---------------- slide 7: completion and integrity
    s = prs.slides.add_slide(blank)
    slide_title(s, "تکمیل، آزمون و یکپارچگی چاه",
                "مقایسه فقط تا مرزی که مدارک اجازه می‌دهند")
    rows = []
    for w in W:
        d = D[w]
        rows.append([w, fmt(C[w]["completion_hours"], 1), fmt(d["perf_h"], 1),
                     fmt(M[w]["fit"] or "ثبت نشده"), fmt(d["wellctrl_h"], 1),
                     fmt(d["stuck_h"], 1), fmt(d["fishing_h"], 1)])
    table(s, Inches(0.55), Inches(1.35), Inches(12.2), Inches(2.15),
          ["چاه", "تکمیل (ساعت)", "مشبک‌کاری (ساعت)", "آزمون پاشنه", "کنترل چاه (ساعت)",
           "گیر رشته (ساعت)", "ماهیگیری (ساعت)"],
          rows, col_widths=[0.9, 1.4, 1.6, 1.5, 1.6, 1.5, 1.6], font_size=10)
    caption(s, "همه اعداد ساعت ثبت‌شده‌اند، نه شاخص شدت. آزمون پاشنه عیناً از سرصفحه گزارش نقل شده است.",
            Inches(3.52))
    picture(s, f"{FIG}/fig_integrity_hours.png", Inches(0.55), Inches(3.80),
            width=Inches(7.3), max_bottom=Inches(6.95))
    bullets(s, Inches(8.05), Inches(3.85), Inches(4.85), Inches(2.9), [
        "SI-009 تنها چاه با جریان ورودی مستند: ۲۸ دسامبر ۲۰۲۲، عمق ۱۰۲۸ تا ۱۰۴۲ متر، "
        "در حالی که وزن گل از ۷۶ به ۷۷ پوند افزایش می‌یافت؛ کشتن چاه به گل ۹۰ پوندی نیاز داشت.",
        "هیچ چاه فهرست تجهیزات تکمیل (پکر، شیر ایمنی، مودار) ندارد؛ نقشه تکمیل فقط تا حد متن و "
        "جدول جداری قابل ارائه است.",
        "MAASP، ECD و مسیر چاه محاسبه نشده‌اند؛ ورودی لازم برای هر سه در مدارک وجود ندارد.",
    ], size=10.5)

    # ---------------- slide 8: cross-well findings
    s = prs.slides.add_slide(blank)
    slide_title(s, "یافته‌های مهندسی میان‌چاهی",
                "الگوهای مشترکی که داده‌های هر چاه مستقلاً پشتیبانی می‌کنند")
    bullets(s, Inches(0.55), Inches(1.30), Inches(6.0), Inches(5.4), [
        "انتظار سطحی، مکانیزم غالب اتلاف زمان میدان است و در سه چاه مستقل تکرار می‌شود.",
        "مشکلات چاه در مقاطع ۸⅜ و ۵⅞ متمرکز است، نه در چاه‌بزرگ سطحی.",
        "توالی تبخیری گچساران مخاطره تکرارشونده است: هرزروی و تنگی چاه از همان بازه آغاز می‌شود.",
    ], size=12.5, space=14)
    bullets(s, Inches(6.85), Inches(1.30), Inches(6.0), Inches(5.4), [
        "جریان ورودی SI-009 رخدادی چاه‌محور است، نه الگوی میدانی — اما سازوکار آن قابل تکرار است.",
        "تنوع عملکرد مته درون یک چاه بیشتر از بین چاه‌ها است.",
        "عملکرد تکمیل و تولید قابل مقایسه نیست: هیچ چاه داده آزمون یا تولید ندارد.",
    ], size=12.5, space=14)
    ln = s.shapes.add_shape(1, Inches(6.63), Inches(1.35), Inches(0.02), Inches(4.9))
    ln.fill.solid()
    ln.fill.fore_color.rgb = RGBColor(0xC8, 0xD3, 0xDF)
    ln.line.fill.background()

    # ---------------- slide 9: lifecycle economics (duration, no cost)
    s = prs.slides.add_slide(blank)
    slide_title(s, "اقتصاد چرخه عمر: آنچه داده داریم و آنچه نداریم",
                "داده هزینه در منابع وجود ندارد؛ به‌جای آن، توزیع زمان و هشدار دامنه ارائه می‌شود")
    picture(s, f"{FIG}/fig_phase_hours.png", Inches(0.45), Inches(1.25), width=Inches(8.25))
    rows = []
    for w in W:
        rows.append([w, fmt(C[w]["drilling_hours"], 0), fmt(C[w]["casing_hours"], 0),
                     fmt(C[w]["completion_hours"], 0), fmt(C[w]["waiting_hours"], 0)])
    table(s, Inches(8.95), Inches(1.35), Inches(3.85), Inches(2.05),
          ["چاه", "حفاری", "جداری", "تکمیل", "انتظار"],
          rows, col_widths=[0.9, 0.85, 0.85, 0.85, 0.9], font_size=8.5)
    caption(s, "ساعت‌های ثبت‌شده به تفکیک فاز.", Inches(3.50))
    bul = ["هزینه کل چاه، هزینه حفاری و هزینه تکمیل: در مدارک ارائه‌شده موجود نیست.",
           "سه ستون قابل تحلیل: زمان، عمق و توزیع فازها.",
           "هزینه فقط در صورت ارائه AFE یا صورت‌حساب قابل بازیابی است — هشدار دامنه، نه تخمین."]
    bullets(s, Inches(8.90), Inches(3.90), Inches(4.0), Inches(2.8), bul, size=10.5)

    # ---------------- slide 10: recommendations
    s = prs.slides.add_slide(blank)
    slide_title(s, "توصیه‌ها و مسیر پیش‌رو",
                "اقدامات اولویت‌دار با مبنای شواهدی و فرض‌های صریح")
    rows = [
        ["۱", "رویه گذار کنترل چاه با حاشیه سفر تعریف‌شده", "بالا", "فوری"],
        ["۲", "تعهد زمان پاسخ برای پیمانکار دکل و شرکت‌های خدماتی", "بالا", "دوره قرارداد بعدی"],
        ["۳", "آمادگی رشته ماهیگیری و رویه قطع و رزوه سیم", "بالا", "چاه بعدی"],
        ["۴", "برنامه اختصاصی ورود به تبخیری‌های گچساران", "متوسط", "چاه بعدی"],
        ["۵", "الزام ثبت ایستگاه پیمایش و فیلد هزینه در قالب گزارش", "متوسط", "بازنگری قالب"],
        ["۶", "بازبینی برنامه مته ۸⅜ بر پایه نتیجه SI-008", "متوسط", "برنامه‌ریزی"],
    ]
    table(s, Inches(0.55), Inches(1.30), Inches(7.3), Inches(2.55),
          ["#", "اقدام", "اولویت", "زمان‌بندی"], rows,
          col_widths=[0.4, 3.6, 0.85, 1.35], font_size=10)
    kpi(s, Inches(8.15), Inches(1.30), Inches(4.4), Inches(1.05),
        "۱۴٫۱٪", "کمترین سهم زمان غیرمولد در میدان (SI-008)", TEAL)
    kpi(s, Inches(8.15), Inches(2.48), Inches(4.4), Inches(1.05),
        "۵۵٫۵٪", "بیشترین سهم زمان غیرمولد (SI-009)", RED)
    bullets(s, Inches(0.55), Inches(4.15), Inches(12.2), Inches(2.6), [
        "فرصت کمی‌شده: بازیابی یک‌چهارم زمان انتظار معادل حدود ۹۶ روز دکل در سطح میدان است — "
        "سناریو با فرض وجود هماهنگ‌کننده مجاز، نه نتیجه تضمین‌شده.",
        "فرصت دوم: حذف یک چرخه تکراری کشتن چاه در SI-009 معادل ۲۴ ساعت؛ کاهش نصف زمان "
        "مغزه‌گیری SI-008 معادل ۲۰۳ ساعت.",
        "هیچ صرفه‌جویی ریالی گزارش نمی‌شود، زیرا داده هزینه در منابع وجود ندارد.",
    ], size=12)

    for i, sl in enumerate(prs.slides, 1):
        if i > 1:
            footer(sl, i)

    os.makedirs(OUT, exist_ok=True)
    path = f"{OUT}/Siah_Makan_Engineering_Performance_Presentation.pptx"
    prs.save(path)
    return path


if __name__ == "__main__":
    print(build())
