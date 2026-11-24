# Siah Makan — Daily Drilling Report Analysis

Engineering analysis of the four Siah Makan wells (SI-006, SI-007, SI-008, SI-009)
built from the daily drilling reports (DDR) supplied in `SI 06.xlsx`, `SI 07.xlsx`,
`SI 08.xlsx` and `SI 09.xlsx`. The workbooks are read-only inputs and are not modified.

The deliverables are produced in English and Persian. Every number in them is
reproducible from the extracted datasets in `04_Engineering_Datasets`; nothing is
estimated unless the report says so in the same sentence.

## Where to start

| If you want | Open |
|---|---|
| The scope, the source inventory and what is missing from the data | `00_Project_Overview/Project_Scope.md`, then `Data_Coverage_Summary.md` |
| The cross-well comparison (the one-picture answer) | `02_Asset_Comparison/Siah_Makan_Comparison_Report_EN.docx` or `..._FA.docx` |
| One well in depth | `01_Well_Reports/SI-006/..._EN.docx` (repeat for 007, 008, 009) |
| A presentation to walk through | `03_Presentation/Siah_Makan_Engineering_Performance_Presentation.pptx` |
| The raw numbers to check or re-use | `04_Engineering_Datasets` |
| How each figure was computed | report Appendix D, and `05_Analysis_Scripts` |
| Whether to trust any of it | `06_QA_Reports/QA_Report.md` and `Language_and_Layout_QA.md` |

## Folder map

```
Siahmakan_Analysis/
  00_Project_Overview/     scope, source inventory, data-coverage and data-gap registers
  01_Well_Reports/         per-well engineering report, EN + FA, with that well's figures
  02_Asset_Comparison/     four-well comparison report, EN + FA, and the 9 field figures
  03_Presentation/         10-slide Persian deck
  04_Engineering_Datasets/ extracted per-well CSVs + Calculations/ derived tables
  05_Analysis_Scripts/     the pipeline that produced everything above
  06_QA_Reports/           check register, date repairs, language/layout QA
```

## Headline numbers

| | SI-006 | SI-007 | SI-008 | SI-009 |
|---|---|---|---|---|
| Planned TD (m) | 5,059 | 4,416 | 5,298 | 5,143.5 |
| Final recorded depth (m) | 5,144 | 4,410 | 4,900 | 3,084 |
| Planned / actual duration (d) | 180 / 421 | 180 / 498 | 277 / 209 | 160 / 109 |
| Recorded operation hours | 10,078.5 | 11,912.5 | 4,977.5 | 2,600 |
| NPT hours (share of recorded hours) | 4,342 (43.1 %) | 5,721.5 (48.0 %) | 703 (14.1 %) | 1,443 (55.5 %) |
| Drilling rate over the whole well (m/day) | 12.22 | 8.86 | 23.44 | 28.29 |

Across the field: 5,038 operation rows, 1,237 DDR sheets, 466 NPT events,
108 bit runs (58 with footage, 17,551 m), and 5,013 of 5,038 operation rows
typed productive / non-productive / unplanned (99.5 %).

The single most important finding is that the lost time is mostly not geological.
Three of the four wells lost more time to surface waiting — on the rig contractor,
the service company and operations contingency — than to any downhole failure.
Only SI-009 breaks that pattern, where a single documented influx consumed
768.5 hours of well-control work.

## Running the pipeline

Python 3.11 with `openpyxl pandas matplotlib python-docx python-pptx numpy Pillow`
(`pip install --break-system-packages` in this environment). Run from the
repository root, in this order:

```
python3 Siahmakan_Analysis/05_Analysis_Scripts/extract_ddrs.py     # XLSX -> per-well CSVs (~48 s)
python3 Siahmakan_Analysis/05_Analysis_Scripts/analyse_wells.py   # derived calculation tables
python3 Siahmakan_Analysis/05_Analysis_Scripts/build_overview.py  # scope / coverage registers
python3 Siahmakan_Analysis/05_Analysis_Scripts/build_figures.py   # 8 per-well + 9 field figures
python3 Siahmakan_Analysis/05_Analysis_Scripts/build_well_reports.py   # 8 per-well DOCX
python3 Siahmakan_Analysis/05_Analysis_Scripts/build_comparison.py     # 2 comparison DOCX
python3 Siahmakan_Analysis/05_Analysis_Scripts/build_deck.py           # 1 PPTX
python3 Siahmakan_Analysis/05_Analysis_Scripts/run_qa.py               # 76 numeric checks
python3 Siahmakan_Analysis/05_Analysis_Scripts/qa_language.py          # language + OOXML checks
python3 Siahmakan_Analysis/05_Analysis_Scripts/qa_deck.py              # slide geometry checks
```

`extract_ddrs.py` rewrites every dataset and takes about a minute; the later
scripts are idempotent and can be re-run individually.

## Conventions and deliberate choices

* **Units are metric** — metres, hours, pcf, psi, kilopound, kilopound·foot —
  because that is what the DDR sheets record. No unit is converted silently.
* **All depths are measured depth (MD).** True vertical depth is not derivable:
  the survey data is absent (SI-007), a static template (SI-006, SI-009) or
  partial (SI-008). The reports state this rather than assume a trajectory.
* **NPT is the DDR's own classification**, the type column on each operation row
  (N = non-productive, U = unplanned). The denominator is all recorded
  operation hours, and it is stated on every percentage.
* **No cost analysis.** No cost field exists in any of the 1,237 sheets. This is
  recorded as a data gap, not worked around with an assumed day rate. Where a
  saving is quantified it is quantified in rig hours.
* **Chart labels stay in English.** matplotlib cannot shape Arabic script, so a
  Persian axis label would render as disconnected letters. Persian captions
  carry the meaning; every figure is titled in English and referred to from
  Persian prose.
* **Persian tables translate labels, not narrative.** Controlled vocabulary
  (cause families, phases, code descriptions, formations, lithology, sizes,
  manufacturers) goes through `05_Analysis_Scripts/fa_glossary.py`. Verbatim
  DDR descriptions are quoted in English and flagged in the caption, so each
  row can be matched to the source sheet. See
  `06_QA_Reports/Language_and_Layout_QA.md` §4.
* **Documents are generated, never hand-edited.** `docx_kit.normalise_ooxml()`
  sorts the OOXML property blocks after every save, because hand-appended
  `w:rtl` or `w:b` children land out of schema order and Word then refuses to
  open the file.

## Known limits

* The documents were verified by inspecting their OOXML and shape geometry, not
  by rendering them — no LibreOffice or PowerPoint renderer exists in this
  environment. Layout is arithmetic-checked; it has not been looked at.
* Persian numerals are rendered as `۱۲۳` with a Latin thousands separator, which
  is normal in Iranian technical documents but will look inconsistent to a
  strict reader.
* The Persian table of contents is a Word field. It is correct only after the
  reader right-clicks it and chooses *Update Field*; the document says so
  inline.
