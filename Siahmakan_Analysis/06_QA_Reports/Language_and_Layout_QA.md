# Language, script-direction and layout QA

This appendix covers what the numeric QA cannot see: that the Persian documents are actually Persian, that the bidirectional markup is present and schema-valid, and that no shape in the deck runs off the slide.

Reproduce every row with `05_Analysis_Scripts/qa_language.py` and `05_Analysis_Scripts/qa_deck.py`.

## 1. Documents

| Document | Lang | Para | Tables | Figures | Persian chars | English prose leaks | Verbatim DDR quotes | Latin numerals in Persian prose | Out-of-order blocks | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| SI-006_Engineering_Report_FA.docx | FA | 130 | 24 | 5 | 23836 | 0 | 22 | 0 | 0 | **PASS** |
| SI-007_Engineering_Report_FA.docx | FA | 132 | 22 | 5 | 26337 | 0 | 37 | 0 | 0 | **PASS** |
| SI-008_Engineering_Report_FA.docx | FA | 122 | 21 | 5 | 18203 | 0 | 21 | 0 | 0 | **PASS** |
| SI-009_Engineering_Report_FA.docx | FA | 124 | 21 | 5 | 16923 | 0 | 5 | 0 | 0 | **PASS** |
| Siah_Makan_Comparison_Report_FA.docx | FA | 88 | 13 | 6 | 8697 | 0 | 0 | 0 | 0 | **PASS** |
| SI-006_Engineering_Report_EN.docx | EN | 132 | 24 | 5 | 0 | 0 | - | - | - | **PASS** |
| SI-007_Engineering_Report_EN.docx | EN | 134 | 22 | 5 | 0 | 0 | - | - | - | **PASS** |
| SI-008_Engineering_Report_EN.docx | EN | 123 | 21 | 5 | 0 | 0 | - | - | - | **PASS** |
| SI-009_Engineering_Report_EN.docx | EN | 125 | 21 | 5 | 0 | 0 | - | - | - | **PASS** |
| Siah_Makan_Comparison_Report_EN.docx | EN | 92 | 14 | 6 | 0 | 0 | - | - | - | **PASS** |

Persian characters in every English document: 0. That is measured, not assumed - a stray Persian glyph in an English report would be a translation artefact. The reverse test matters just as much: a Latin numeral in the middle of a Persian sentence (`مغزه‌گیری 155 ساعت`) breaks the reading flow, so it is treated as a defect and counted.

## 2. Bidirectional markup

| Document | w:bidi paragraphs | w:rtl runs | w:bidiVisual tables |
|---|---|---|---|
| SI-006_Engineering_Report_FA.docx | 3058 | 3721 | 24 |
| SI-007_Engineering_Report_FA.docx | 3459 | 4453 | 22 |
| SI-008_Engineering_Report_FA.docx | 2044 | 2375 | 21 |
| SI-009_Engineering_Report_FA.docx | 1659 | 2115 | 21 |
| Siah_Makan_Comparison_Report_FA.docx | 464 | 536 | 13 |

`w:bidi` sets paragraph direction right-to-left, `w:rtl` marks a run complex-script, and `w:bidiVisual` reverses table column order. All three are needed: a document with only one still looks correct in a Latin Word profile and breaks in a Persian one.

## 3. OOXML child order

Word rejects a document whose `rPr`, `pPr` or `tcPr` children are out of schema order, and the failure is an unreadable-file prompt rather than a warning. `docx_kit.normalise_ooxml()` re-sorts every block after `doc.save()`; the checker re-parses the written file to confirm it.

| Property block | Blocks inspected | Out of order |
|---|---|---|
| `w:rPr` | 13200 | 0 |
| `w:pPr` | 10725 | 0 |
| `w:tcPr` | 10190 | 0 |

## 4. Language policy actually applied

The daily drilling reports are English, so two kinds of English text reach the Persian deliverables, and they are treated differently:

* **Controlled vocabulary** - NPT cause families, operation phases, operation-code descriptions, formation names, lithology abbreviations, hole and bit sizes, casing sizes, well type, bit manufacturer and worded dull grading - is translated through `05_Analysis_Scripts/fa_glossary.py`. These are labels, so a Persian reader must get Persian, and the mapping is one-to-one and auditable.
* **Verbatim narrative** - the free-text description of an operation, incident or failure - is not translated inside the tables. It is quoted exactly as recorded and flagged in the table caption, so a reviewer can match each row to the original sheet. Translating a terse, abbreviation-heavy field note risks changing the meaning of the record, which is worse than leaving it in the source language. Everywhere else the narrative is discussed in Persian prose.

Two defects were found this way that the automated leak test could not see, because both produced plausible-looking English inside an otherwise correct Persian table:

1. **Hole and bit size truncation.** The DDR writes one size several ways (`17 1/2"`, `17-1/2"`, `17-1/2" PDC`). Taking the first space-delimited token turned 17½ in into `17 inch` - a different hole size, and a wrong number in a Persian table. Sizes now go through `fa_bit_size()`, which normalises the spelling first.
2. **Bidi mis-ordering of bit numbers.** The bit column carries `#3`, `#4  (USED)`. The `#` is bidi-neutral, so inside a right-to-left cell it detaches from its digits and the number reads back-to-front (`۳#`). `fa_bit_no()` drops the marker - the column heading already says *bit* - and `split_latin()` no longer keeps a bare `#` with the following Latin text.

## 5. Presentation geometry

| Slide | Shapes | Pictures | Tables | Persian chars | Verdict |
|---|---|---|---|---|---|
| 1 | 7 | 0 | 0 | 191 | PASS |
| 2 | 20 | 0 | 1 | 541 | PASS |
| 3 | 10 | 2 | 0 | 352 | PASS |
| 4 | 9 | 1 | 1 | 363 | PASS |
| 5 | 9 | 1 | 1 | 349 | PASS |
| 6 | 8 | 1 | 1 | 296 | PASS |
| 7 | 9 | 1 | 1 | 439 | PASS |
| 8 | 8 | 0 | 0 | 461 | PASS |
| 9 | 9 | 1 | 1 | 328 | PASS |
| 10 | 13 | 0 | 1 | 410 | PASS |

Slide 7 originally carried the integrity chart at its natural aspect, which put the bottom edge 0.12 in below the slide and across the footer. `picture()` now accepts a `max_bottom` and scales the picture into the space actually left. With no renderer in this environment the check is arithmetic on shape geometry, not a visual inspection; that limitation is stated rather than hidden.

## 6. Summary

| Check | Result |
|---|---|
| Documents scanned | 10 |
| Documents failing | 0 |
| Persian characters inside English documents | 0 |
| English prose leaks inside Persian documents | 0 |
| Latin numerals inside Persian prose | 0 |
| Out-of-order OOXML property blocks | 0 |
| Slides with a shape outside the slide box | 0 |
