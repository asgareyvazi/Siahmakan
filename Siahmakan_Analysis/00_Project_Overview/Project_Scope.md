# Project Scope

## 1  Asset identity

| Field | Value | Basis |
|---|---|---|
| Project / asset | Siah Makan field (Persian: سیاه‌مکان) | Field Name field, DDR header, all 1,237 sheets |
| Well population | SI-006, SI-007, SI-008, SI-009 | One workbook per well, one sheet per well-day |
| Operator | PEDC-PECO | DDR header |
| Rig contractors | NIDC (SI-006, SI-007, SI-008); OEOC (SI-009) | DDR header, Rig Cont. field |
| Country | Iran | Inferred from operator/contractor identity recorded in the DDRs |
| Basin / region | Zagros foreland (Dezful embayment style sequence: Aghajari-Mishan-Gachsaran-Asmari) | Formation table recorded in every DDR |
| Well type | Delineation-producer | Well Type field |
| Reporting period | 2021-03-17 to 2023-04-25 | First spud to last daily report |
| Reporting cut-off | 2023-04-25 (last available record) | Latest DDR sheet in the four workbooks |
| Units | Metric (m, hours, pcf, psi, klbf, klbf·ft) | As recorded; no conversion applied |
| Languages | English and Persian | Requirement |
| Presentation | Exactly 10 slides, Persian, charts in English | Requirement |

## 2  Source data

| File | Size (MB) | Sheets | SHA-256 (first 16) |
|---|---|---|---|
| SI 06.xlsx | 12.01 | 421 | `cf7a03f4c53511af` |
| SI 07.xlsx | 9.97 | 498 | `5bf3732ed86ab5be` |
| SI 08.xlsx | 6.73 | 209 | `b047b43083c0b1fd` |
| SI 09.xlsx | 3.28 | 109 | `a39b14368d7c026e` |

Total: 1,237 daily drilling report sheets, 33.0 MB of source workbooks. The four files are byte-unique (no duplicate workbooks).

## 3  Analysis scope actually delivered

| Subject | Status |
|---|---|
| Daily operations, depth, hole size, hours | Analysed for all 4 wells |
| Hole-section architecture and ROP | Analysed for all 4 wells |
| NPT register and taxonomy | Analysed for all 4 wells (466 events) |
| Bit runs and bit performance | Analysed for all 4 wells (108 runs, 58 with footage) |
| Mud properties | Analysed for all 4 wells |
| Casing / liner programme | Analysed for all 4 wells |
| Formation tops | Analysed for all 4 wells |
| Drilling parameters (WOB/RPM/SPP/flow) | Summarised per run and per bit size |
| Trajectory (minimum curvature) | **Not possible** — no usable survey set |
| TVD, displacement, DLS | **Not possible** — consequence of the above |
| MSE | **Not computed** — no continuous parameter log |
| ECD, annular pressure loss | **Not computed** — no pressure survey basis |
| MAASP | **Not computed** — insufficient casing/fluid reference data |
| Cost, AFE, lifecycle economics | **Not possible** — no cost field in any sheet |
| Completion equipment tally | **Not possible** — not recorded in the DDR format |
| Well test, production, injectivity | **Not possible** — not supplied |

## 4  Deliverables produced

| Deliverable | Path |
|---|---|
| SI-006 engineering report (EN) | `01_Well_Reports/SI-006/SI-006_Engineering_Report_EN.docx` |
| SI-006 engineering report (FA) | `01_Well_Reports/SI-006/SI-006_Engineering_Report_FA.docx` |
| SI-007 engineering report (EN) | `01_Well_Reports/SI-007/SI-007_Engineering_Report_EN.docx` |
| SI-007 engineering report (FA) | `01_Well_Reports/SI-007/SI-007_Engineering_Report_FA.docx` |
| SI-008 engineering report (EN) | `01_Well_Reports/SI-008/SI-008_Engineering_Report_EN.docx` |
| SI-008 engineering report (FA) | `01_Well_Reports/SI-008/SI-008_Engineering_Report_FA.docx` |
| SI-009 engineering report (EN) | `01_Well_Reports/SI-009/SI-009_Engineering_Report_EN.docx` |
| SI-009 engineering report (FA) | `01_Well_Reports/SI-009/SI-009_Engineering_Report_FA.docx` |
| Field comparison report (EN) | `02_Asset_Comparison/Siah_Makan_Comparison_Report_EN.docx` |
| Field comparison report (FA) | `02_Asset_Comparison/Siah_Makan_Comparison_Report_FA.docx` |
| Project README (folder map, headline numbers, run order) | `Siahmakan_Analysis/README.md` |
| Management presentation (10 slides, Persian) | `03_Presentation/Siah_Makan_Engineering_Performance_Presentation.pptx` |
| Normalised datasets | `04_Engineering_Datasets/` (36 CSVs: 9 tables x 4 wells) |
| Calculation outputs | `04_Engineering_Datasets/Calculations/` (16 cross-well CSVs) |
| Analysis scripts | `05_Analysis_Scripts/` (13 Python modules: 7 build, 3 QA, 2 support libraries, 1 glossary) |
| QA reports | `06_QA_Reports/QA_Report.md` + `qa_checks.csv` (numeric), `Language_and_Layout_QA.md` (language, OOXML, deck geometry), `date_repairs.csv` |

## 5  Explicit limitations

1. **No cost data.** A full-text scan of all 1,237 sheets for `usd`, `dollar`, `cost`, `invoice`, `$` returned zero hits. No financial analysis is possible and none is claimed.
2. **No usable well trajectory.** SI-006 and SI-009 carry a static three-station template that never updates with depth (SI-006 stations at 150/679/1735 m on a 5,144 m well). SI-007 has no numeric station at all. SI-008 has a partial set to 4,610 m MD. No minimum-curvature trajectory is fabricated.
3. **No final well report, drilling programme, completion programme or test data.** Final-state attributes are taken from the last DDR sheet, not from an approved report.
4. **One source date was malformed** (`021-04-2022` on SI-007 sheet `265 DDR SI #07`). The value was not guessed from the digits; it was derived from the rig-day sequence (rig day 265 = 2022-04-02) and flagged as DERIVED in `06_QA_Reports/date_repairs.csv`.
