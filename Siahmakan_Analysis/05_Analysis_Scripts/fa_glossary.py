"""Persian glossary for controlled vocabularies used in the Persian reports.

The source documents are English-language daily drilling reports. Their
controlled vocabularies (NPT cause families, operation phases, operation code
descriptions, formation names, lithology strings) are carried through the
analysis unchanged, because those strings are the join keys between the
datasets, the English reports and the audit trail.

For the Persian deliverables the same values are rendered through this
glossary, so a Persian reader never meets an English phrase inside a Persian
table while the underlying data stays traceable to the source wording.  Where
a term has no accepted Persian equivalent in Iranian drilling practice the
English term is kept verbatim (rig contractor names, bit manufacturers, IADC
dull codes, casing grades, tool designations).

`fa_term(kind, value)` returns the Persian rendering when one is defined and
the original value otherwise - it never returns an empty string for a
non-empty input.
"""

# --- non-productive-time cause families ------------------------------------ #
FAMILY = {
    "Operations contingency": "احتیاط عملیاتی (توقف سطحی)",
    "Waiting on rig contractor": "انتظار پیمانکار دکل",
    "Waiting on service company": "انتظار شرکت خدماتی",
    "Waiting on client": "انتظار کارفرما",
    "Waiting on procurement": "انتظار خرید و تأمین کالا",
    "Waiting on programme": "انتظار برنامه عملیاتی",
    "Waiting on material quality": "انتظار کیفیت مواد",
    "Stuck pipe": "گیر کردن رشته",
    "Fishing": "عملیات ماهیگیری",
    "Well control": "کنترل چاه",
    "Lost circulation": "هرزروی گل",
    "Hole instability": "ناپایداری دیواره چاه",
    "Rig equipment failure": "خرابی تجهیزات دکل",
    "Rig repair": "تعمیر دکل",
    "Rig service": "سرویس دکل",
    "Rig move": "جابه‌جایی دکل",
    "Wellhead & BOP": "سرچاهی و BOP",
    "Cementing problem": "مشکل سیمان‌کاری",
    "Unclassified": "طبقه‌بندی‌نشده",
    "Safety standby": "آماده‌باش ایمنی",
    "Trip": "خروج و ورود رشته",
    "Hole conditioning": "آماده‌سازی چاه",
    "Logging": "لاگ‌گیری",
    "Circulation": "گردش سیال",
    "Perforation": "مشبک‌کاری",
    "Drill out": "حفاری پلاگ و کف",
    "Casing": "جداری‌گذاری",
    "Completion": "تکمیل چاه",
    "Testing": "آزمون چاه",
    "Survey": "پیمایش",
    "Directional drilling": "حفاری جهت‌دار",
}

# --- operation phases ------------------------------------------------------ #
PHASE = {
    "Drilling": "حفاری",
    "Trip & Hole Conditioning": "خروج و ورود رشته و آماده‌سازی چاه",
    "Circulation & Fluid Treatment": "گردش و اصلاح سیال",
    "Casing & Cementing": "جداری‌گذاری و سیمان‌کاری",
    "Wellhead & BOP": "سرچاهی و BOP",
    "Evaluation & Logging": "ارزیابی و لاگ‌گیری",
    "Testing & Stimulation": "آزمون و تحریک چاه",
    "Completion & Intervention": "تکمیل و عملیات اصلاحی",
    "Hole Problem": "مشکل چاه",
    "Rig Service": "سرویس دکل",
    "Waiting / Standby": "انتظار و آماده‌باش",
    "Unclassified": "طبقه‌بندی‌نشده",
}

# --- operation code descriptions (DDR legend) ------------------------------ #
CODE = {
    "Waiting / Standby": "انتظار و آماده‌باش",
    "Drilling": "حفاری",
    "Round Trip": "خروج و ورود کامل رشته",
    "Short Trip": "خروج و ورود کوتاه رشته",
    "Circulating": "گردش سیال",
    "Reaming": "رمینگ",
    "Scraping": "دیواره‌تراشی",
    "Drill / Clean Out": "حفاری و پاکسازی",
    "Drill Out": "حفاری پلاگ و کف",
    "Condition Fluid": "اصلاح خواص سیال",
    "Mixing Mud": "اختلاط گل",
    "Displacing Fluid": "جابه‌جایی سیال",
    "Circ in Casing": "گردش در جداری",
    "Running Casing": "پایین‌بردن جداری",
    "Casing Tools": "ابزار جداری‌گذاری",
    "Cementing": "سیمان‌کاری",
    "Squeeze Cement": "سیمان‌کاری فشاری",
    "WOC": "انتظار سفت‌شدن سیمان",
    "Tie Back": "تی‌بک لاینر",
    "LOT-FIT": "آزمون نشتی و یکپارچگی سازند",
    "BOP Test": "آزمون BOP",
    "N/D N/U BOP": "نصب و برچیدن BOP",
    "Pressure Test": "آزمون فشار",
    "Wellhead": "سرچاهی",
    "M/U L/D BHA": "بستن و بازکردن BHA",
    "M/U L/D DP": "بستن و بازکردن رشته حفاری",
    "Slip & Cut": "اسلیپ و کوتاه‌کردن رشته",
    "Connection": "اتصال لوله",
    "Directional Drilling": "حفاری جهت‌دار",
    "Survey": "پیمایش",
    "Logging / TLC": "لاگ‌گیری با سیم‌خط",
    "Slickline": "سیم‌خط",
    "Coring": "مغزه‌گیری",
    "Perforation": "مشبک‌کاری",
    "DST / Test / Stimulation": "آزمون چاه و تحریک",
    "Stim/N2/Gas Lift": "تحریک، تزریق نیتروژن و گازلیفت",
    "Dry Test": "آزمون خشک",
    "Flow Well": "جریان‌دهی چاه",
    "Observe Well": "پایش چاه",
    "Kill Well": "کشتن چاه",
    "Stuck Pipe": "گیر کردن رشته",
    "Fishing": "ماهیگیری",
    "Milling": "میلینگ",
    "Side Tracking": "انحراف مسیر (سایدترک)",
    "Plug Back": "پلاگ‌بک",
    "Plug/Unplug": "پلاگ و برداشتن پلاگ",
    "W&R Tight": "W&R تنگ",
    "Dress Neck": "آماده‌سازی گردنه",
    "Geo Circulation": "گردش زمین‌شناسی",
    "Loss Circulation": "هرزروی گل",
    "CBL": "لاگ سیمان (CBL)",
    "Prior Csg/Cmt/DST/CBL": "عملیات مقدماتی جداری، سیمان و آزمون",
    "Run/Pull Completion": "پایین‌بردن و خارج‌کردن تجهیزات تکمیل",
    "Rig Repair": "تعمیر دکل",
    "Rig Service": "سرویس دکل",
    "Rig Moving (Up/Down)": "برپایی و برچیدن دکل",
    "Wait Client": "انتظار کارفرما",
    "Wait Order/Program": "انتظار دستور و برنامه",
    "Wait Procurement": "انتظار تأمین کالا",
    "Wait Rig Contractor": "انتظار پیمانکار دکل",
    "Wait Service Company": "انتظار شرکت خدماتی",
    "Wait Surface / Contingency": "انتظار سطحی و احتیاط عملیاتی",
    "(not in legend)": "(خارج از راهنمای کد)",
    "Well Control": "کنترل چاه",
    "Wearing Bushing": "سایش بوشینگ",
    "Washout": "شست‌شدگی (واش‌اوت)",
    "Waiting Safety": "انتظار ایمنی",
}

# --- formations ------------------------------------------------------------ #
FORMATION = {
    "AGHAJARI": "آغاجاری",
    "MISHAN": "میشان",
    "GACHSARAN": "گچساران",
    "ASMARI": "آسماری",
    "PABDEH": "پابده",
    "GURPI": "گورپی",
    "ILAM": "ایلام",
    "SURGAH": "سورگاه",
    "SARVAK": "سروک",
    "KAZHDUMI": "کژدمی",
    "CAP ROCK": "سنگ پوش",
    "DARIYAN": "داریان",
    "GADVAN": "گدوان",
    "FAHLIYAN": "فهلیان",
}

# --- lithology abbreviations used on the DDR formation table --------------- #
LITHOLOGY = {
    "LST": "آهک",
    "Lst": "آهک",
    "LST.": "آهک",
    "Mrl": "مارل",
    "Mrl.": "مارل",
    "Anhy": "انیدریت",
    "Salt": "نمک",
    "Sh": "شیل",
    "Shale": "شیل",
    "Clst": "گل‌سنگ",
    "SLst": "ماسه‌سنگ",
    "ArgLst": "آهک رسی",
    "Arg Lst": "آهک رسی",
    "Arg lst": "آهک رسی",
    "Argi Lst": "آهک رسی",
    "GyMrl": "مارل گچی",
    "Gr Mrl": "مارل خاکستری",
    "Gry Mrl": "مارل خاکستری",
    "G.marl": "مارل گچی",
    "Gy Marl": "مارل گچی",
    "RdMrl": "مارل قرمز",
    "Gry lst": "آهک خاکستری",
    "glauc": "گلوکونیتی",
    "DolLst": "دولومیت آهکی",
}

# --- well type ------------------------------------------------------------- #
WELL_TYPE = {
    "Delineation - Producer": "توصیفی–تولیدی (Delineation-Producer)",
    "Delineation/Producer": "توصیفی–تولیدی (Delineation-Producer)",
    "Delineation-Producer": "توصیفی–تولیدی (Delineation-Producer)",
    "Delineation/Produce": "توصیفی–تولیدی (Delineation-Producer)",
    "Exploration": "اکتشافی",
    "Appraisal": "ارزیابی",
    "Development": "توسعه‌ای",
    "Producer": "تولیدی",
    "Injection": "تزریقی",
}

MAPS = {
    "family": FAMILY,
    "phase": PHASE,
    "code": CODE,
    "formation": FORMATION,
    "lithology": LITHOLOGY,
    "well_type": WELL_TYPE,
}


def fa_term(kind, value):
    """Persian rendering of a controlled-vocabulary term, or the original."""
    if value is None:
        return ""
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return ""
    m = MAPS.get(kind, {})
    if s in m:
        return m[s]
    if s.upper() in m:
        return m[s.upper()]
    return value


def fa_formation(value):
    """Formation label, including the 'Cap Rock/ASMARI' and 'Gs. Mbr #7' forms."""
    s = "" if value is None else str(value).strip()
    if not s or s.lower() == "nan":
        return ""
    import re
    out = s
    for k, v in FORMATION.items():
        out = re.sub(rf"\b{re.escape(k)}\b", v, out, flags=re.I)
    out = out.replace("Cap Rock", "سنگ پوش").replace("CAP ROCK", "سنگ پوش")
    out = re.sub(r"\bGs\.?\s*Mbr\b", "عضو گچساران", out, flags=re.I)
    out = re.sub(r"\bGs\.\s*", "گچساران ", out)
    out = out.replace("Mbr", "عضو").replace("Cap Rock/", "سنگ پوش/")
    return out


def fa_lithology(value):
    """Lithology string, translating the abbreviations while keeping order."""
    s = "" if value is None else str(value).strip()
    if not s or s.lower() == "nan":
        return ""
    parts = [p.strip() for p in s.replace("\n", ",").replace("/", ",").split(",")]
    out = []
    for p in parts:
        if not p or p == "-":
            continue
        key = p
        hit = None
        for k in sorted(LITHOLOGY, key=len, reverse=True):
            if key.lower().replace(" ", "") == k.lower().replace(" ", ""):
                hit = LITHOLOGY[k]
                break
        out.append(hit if hit else p)
    return "، ".join(out)


# --- hole sizes ------------------------------------------------------------ #
HOLE_SIZE = {
    '36"': "۳۶ اینچ",
    '26"': "۲۶ اینچ",
    '24"': "۲۴ اینچ",
    '17-1/2"': "۱۷½ اینچ",
    '16"': "۱۶ اینچ",
    '12-1/4"': "۱۲¼ اینچ",
    '9-5/8"': "۹⅝ اینچ",
    '8-1/2"': "۸½ اینچ",
    '8-3/8"': "۸⅜ اینچ",
    '8-1/4"': "۸¼ اینچ",
    '6-1/8"': "۶⅛ اینچ",
    '5-7/8"': "۵⅞ اینچ",
    '4-1/8"': "۴⅛ اینچ",
    '7"': "۷ اینچ",
    '5"': "۵ اینچ",
    "Completion": "تکمیل",
}


def fa_casing_size(value):
    """Casing size as recorded ('13-3/8"', '9-5/8"'), rendered for Persian text."""
    s = "" if value is None else str(value).strip()
    if not s or s.lower() == "nan":
        return ""
    if s in HOLE_SIZE:
        return HOLE_SIZE[s]
    return s.replace("-", "‑")


def fa_hole_size(value):
    """Nominal hole/casing size rendered for a Persian table."""
    s = "" if value is None else str(value).strip()
    if not s or s.lower() == "nan":
        return ""
    if s in HOLE_SIZE:
        return HOLE_SIZE[s]
    if s.isdigit():
        return "%s اینچ" % s
    return value


# --- bit condition written in words instead of an IADC dull code ----------- #
DULL = {
    "Left in hole": "در چاه رها شد",
    "LEFT IN HOLE": "در چاه رها شد",
    "Left in Hole": "در چاه رها شد",
    "In Hole": "در چاه",
    "IN HOLE": "در چاه",
    "In hole": "در چاه",
    "Not recorded": "ثبت نشده",
}


def fa_dull(value):
    """IADC dull grading code kept verbatim; worded condition translated."""
    s = "" if value is None else str(value).strip()
    if not s or s.lower() == "nan":
        return "—"
    if s in DULL:
        return DULL[s]
    return value


# --- bit manufacturer (recorded in mixed case and with truncation) --------- #
MANUFACTURER = {
    "VAREL": "وارل",
    "Varel": "وارل",
    "BAKER HUGHES": "بیکر هیوز",
    "Baker Hughes": "بیکر هیوز",
    "BAKER HUGHE": "بیکر هیوز",
    "Baker Hughe": "بیکر هیوز",
    "HALLIBURTON": "هالیبرتون",
    "Halliburton": "هالیبرتون",
    "SMITH": "اسمیت",
    "Smith": "اسمیت",
    "REEDHYCALOG": "رید هایکالوگ",
    "ReedHycalog": "رید هایکالوگ",
    "KINGDREAM": "کینگ‌دریم",
    "Kingdream": "کینگ‌دریم",
    "King Dream": "کینگ‌دریم",
    "JAHAD DANESHGAHI": "جهاد دانشگاهی",
    "Jahad Daneshgahi": "جهاد دانشگاهی",
    "TSK": "TSK",
    "CYLINDER SAZI TEHRAN": "سیلندرسازی تهران",
    "Cylinder Sazi Tehran": "سیلندر‌سازی تهران",
    "CYLINDER SAZI CO.": "سیلندر‌سازی تهران",
    "Cylinder Sazi Co.": "سیلندر‌سازی تهران",
    "NOV": "NOV",
    "REED HYCalog": "رید هایکالوگ",
    "Reed Hycalog": "رید هایکالوگ",
    "KINGDREAM": "کینگ‌دریم",
    "KingDream": "کینگ‌دریم",
}


def fa_maker(value):
    """Bit manufacturer - the one place where a proper name is transliterated."""
    s = "" if value is None else str(value).strip()
    if not s or s.lower() == "nan":
        return "نامشخص"
    if s in MANUFACTURER:
        return MANUFACTURER[s]
    hit = MANUFACTURER.get(s.upper().title())
    if hit:
        return hit
    if s.isdigit():
        return "نامشخص (مقدار نامعتبر در برگه: %s)" % s
    return value


def fa_bit_no(value):
    """Bit number label with the '(used)' condition tag translated."""
    import re
    s = "" if value is None else str(value).strip()
    if not s or s.lower() == "nan":
        return ""
    s = re.sub(r"\s*\(\s*used\s*\)", " (مستعمل)", s, flags=re.I)
    s = re.sub(r"\s*\(\s*new\s*\)", " (نو)", s, flags=re.I)
    # A bare '#' is a bidi-neutral character: inside an RTL cell it detaches
    # from its digits and the number reads back-to-front. The column heading is
    # already 'bit', so the marker is dropped rather than risk a mis-ordered
    # number.
    s = re.sub(r"^#\s*", "", s)
    s = re.sub(r"\s*#$", "", s)
    return s.strip()


def fa_depth(value):
    """Depth string from the formation table: unit letter moved to Persian."""
    import re
    s = "" if value is None else str(value).strip()
    if not s or s.lower() == "nan":
        return ""
    if s.upper() in ("SURFACE", "SURF", "SURF."):
        return "سطح"
    m = re.fullmatch(r"([0-9][0-9\.,/\s\-]*?)\s*[mM]$", s)
    if m:
        return "%s متر" % m.group(1).strip()
    return s


# --- bit size, written in several spellings on the DDR bit table ----------- #
_BIT_DESC = ("PDC Bit", "PDC", "R.Bit", "B.Bit", "TCI", "J.Mill", "Bit", "Impregnated")


def fa_bit_size(value):
    """Bit nominal size from a free-text DDR cell ('17 1/2" PDC' -> 17½ inch).

    The DDR writes the same size as '17 1/2"', '17-1/2"', '17-1/2" PDC' or
    '17.5'.  The size prefix is normalised first and then mapped through the
    hole-size table, so a Persian reader sees the same nominal size the English
    table shows instead of a truncated integer.
    """
    import re
    s = "" if value is None else str(value).strip()
    if not s or s.lower() == "nan":
        return ""
    for d in _BIT_DESC:
        s = re.sub(rf"\s*{re.escape(d)}\s*$", "", s, flags=re.I)
    s = s.strip().rstrip('"').strip()
    m = re.fullmatch(r"(\d+)\s+([1-8])\s*/\s*([248])", s)      # 17 1/2
    if m:
        s = '%s-%s/%s"' % (m.group(1), m.group(2), m.group(3))
    else:
        m = re.fullmatch(r"(\d+)\s*-\s*(\d+)\s*/\s*(\d+)", s)  # 17-1/2
        if m:
            s = '%s-%s/%s"' % (m.group(1), m.group(2), m.group(3))
        elif re.fullmatch(r"\d+", s):
            s = s + '"'
    return fa_hole_size(s)


def fa_field(value):
    """Field name in Persian, with the Latin name kept for traceability."""
    s = "" if value is None else str(value).strip()
    if not s or s.lower() == "nan":
        return ""
    norm = s.replace(" ", "").lower()
    if norm in ("siahyeshmakan", "siahyeshmakn", "siahyeshmakan"):
        return "سیاه‌مکان (Siah Makan)"
    if norm.startswith("siah"):
        return "سیاه‌مکان (%s)" % s
    return s


def fa_fmt(value, nd=0):
    """Format a number for Persian text: same separators, Persian numerals.

    `report_content.fmt` produces the English form (1,234.5). Persian prose in
    this project keeps the same separators - that is what an Iranian drilling
    report does - but the glyphs must be Persian, otherwise the reader meets a
    Latin number inside a Persian sentence.
    """
    import docx_kit as _K
    if value is None or value == "":
        return ""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return _K.fa_digits(str(value))
    if nd == 0:
        s = "{:,.0f}".format(v)
    else:
        s = "{:,.{nd}f}".format(v, nd=nd)
    return _K.fa_digits(s)
