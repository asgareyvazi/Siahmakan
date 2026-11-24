# Quality-assurance report — Siah Makan DDR analysis

Checks executed: 76. PASS 62, WARN 11, FAIL 0, N/A 3.

| Area | Check | Status | Detail |
|---|---|---|---|
| Dates | SI-006: all report dates resolved | **PASS** | 421 DDRs, 0 unresolved, 0 derived from rig-day sequence. |
| Dates | SI-006: duplicate reporting dates | **WARN** | 2 duplicated date(s): 2021-07-04 x2, 2021-09-12 x2 |
| Dates | SI-006: rig-day continuity | **WARN** | Rig days 1-421, 412 unique among 421 DDRs. |
| Dates | SI-007: all report dates resolved | **PASS** | 498 DDRs, 0 unresolved, 1 derived from rig-day sequence. |
| Dates | SI-007: duplicate reporting dates | **PASS** | No duplicated report date. |
| Dates | SI-007: rig-day continuity | **WARN** | Rig days 1-498, 495 unique among 498 DDRs. |
| Dates | SI-008: all report dates resolved | **PASS** | 209 DDRs, 0 unresolved, 0 derived from rig-day sequence. |
| Dates | SI-008: duplicate reporting dates | **PASS** | No duplicated report date. |
| Dates | SI-008: rig-day continuity | **PASS** | Rig days 1-209, 209 unique among 209 DDRs. |
| Dates | SI-009: all report dates resolved | **PASS** | 109 DDRs, 0 unresolved, 0 derived from rig-day sequence. |
| Dates | SI-009: duplicate reporting dates | **PASS** | No duplicated report date. |
| Dates | SI-009: rig-day continuity | **PASS** | Rig days 1-109, 109 unique among 109 DDRs. |
| Operations | SI-006: daily hours balance to 24 h | **PASS** | 421 sheets with operations; 4 outside 23-25 h (1.0 %). |
| Operations | SI-006: operation codes valid | **PASS** | 1934 operation rows, 0 with a non-standard code. |
| Operations | SI-006: P/N/U classification coverage | **PASS** | 1930/1934 rows typed (99.8 %). |
| Operations | SI-007: daily hours balance to 24 h | **PASS** | 498 sheets with operations; 6 outside 23-25 h (1.2 %). |
| Operations | SI-007: operation codes valid | **PASS** | 1684 operation rows, 0 with a non-standard code. |
| Operations | SI-007: P/N/U classification coverage | **PASS** | 1676/1684 rows typed (99.5 %). |
| Operations | SI-008: daily hours balance to 24 h | **PASS** | 209 sheets with operations; 2 outside 23-25 h (1.0 %). |
| Operations | SI-008: operation codes valid | **PASS** | 972 operation rows, 0 with a non-standard code. |
| Operations | SI-008: P/N/U classification coverage | **PASS** | 972/972 rows typed (100.0 %). |
| Operations | SI-009: daily hours balance to 24 h | **PASS** | 109 sheets with operations; 2 outside 23-25 h (1.8 %). |
| Operations | SI-009: operation codes valid | **PASS** | 448 operation rows, 0 with a non-standard code. |
| Operations | SI-009: P/N/U classification coverage | **WARN** | 435/448 rows typed (97.1 %). |
| Depth | SI-006: depth sequence continuity | **WARN** | 4 depth decrease(s) across 421 DDRs; 189-1 DDR: 3984->3425 m; 243-1 DDR: 5144->4395.5 m; 244-1 DDR: 5144->4395.5 m |
| Depth | SI-006: 24:00 depth not below 00:00 depth | **PASS** | 0 DDRs where depth at 24:00 is below depth at 00:00. |
| Depth | SI-007: depth sequence continuity | **PASS** | 1 depth decrease(s) across 498 DDRs; 230 DDR SI #07: 4410->4174 m |
| Depth | SI-007: 24:00 depth not below 00:00 depth | **WARN** | 4 DDRs where depth at 24:00 is below depth at 00:00. |
| Depth | SI-008: depth sequence continuity | **PASS** | 0 depth decrease(s) across 209 DDRs. |
| Depth | SI-008: 24:00 depth not below 00:00 depth | **PASS** | 0 DDRs where depth at 24:00 is below depth at 00:00. |
| Depth | SI-009: depth sequence continuity | **PASS** | 0 depth decrease(s) across 109 DDRs. |
| Depth | SI-009: 24:00 depth not below 00:00 depth | **PASS** | 0 DDRs where depth at 24:00 is below depth at 00:00. |
| Calculations | SI-006: NPT percentage recomputed | **PASS** | stored 43.08%, recomputed 43.08% (4342 h of 10078.5 h). |
| Calculations | SI-006: ROP recomputed | **PASS** | 5144 m / 1364.5 h = 3.77 m/h (stored 3.77). |
| Calculations | SI-006: phase hours sum to total | **PASS** | phases sum 10078.5 h vs total 10078.5 h. |
| Calculations | SI-007: NPT percentage recomputed | **PASS** | stored 48.03%, recomputed 48.03% (5721.5 h of 11912.5 h). |
| Calculations | SI-007: ROP recomputed | **PASS** | 4410 m / 1409 h = 3.13 m/h (stored 3.13). |
| Calculations | SI-007: phase hours sum to total | **PASS** | phases sum 11912.5 h vs total 11912.5 h. |
| Calculations | SI-008: NPT percentage recomputed | **PASS** | stored 14.12%, recomputed 14.12% (703 h of 4977.5 h). |
| Calculations | SI-008: ROP recomputed | **PASS** | 4900 m / 1227 h = 3.99 m/h (stored 3.99). |
| Calculations | SI-008: phase hours sum to total | **PASS** | phases sum 4977.5 h vs total 4977.5 h. |
| Calculations | SI-009: NPT percentage recomputed | **PASS** | stored 55.5%, recomputed 55.50% (1443 h of 2600 h). |
| Calculations | SI-009: ROP recomputed | **PASS** | 3084 m / 660 h = 4.67 m/h (stored 4.67). |
| Calculations | SI-009: phase hours sum to total | **PASS** | phases sum 2600.0 h vs total 2600 h. |
| Calculations | SI-006: section intervals close on final depth | **PASS** | sum of section intervals 5129.5 m vs 5129.5 m (6 sections). |
| Calculations | SI-007: section intervals close on final depth | **WARN** | sum of section intervals 4393.0 m vs 4398.0 m (5 sections). |
| Calculations | SI-008: section intervals close on final depth | **PASS** | sum of section intervals 4886.0 m vs 4886.0 m (5 sections). |
| Calculations | SI-009: section intervals close on final depth | **WARN** | sum of section intervals 3040.0 m vs 3068.0 m (3 sections). |
| Bit runs | SI-006: bit runs identified | **PASS** | 41 runs, 18 with footage, 16 with both footage and rotating hours. |
| Bit runs | SI-006: no negative footage | **PASS** | 0 runs with negative footage. |
| Bit runs | SI-006: footage with zero hours | **WARN** | 2 run(s) carry footage but no recorded 2-1 drilling hours (rate not reported for these). |
| Bit runs | SI-007: bit runs identified | **PASS** | 28 runs, 14 with footage, 12 with both footage and rotating hours. |
| Bit runs | SI-007: no negative footage | **PASS** | 0 runs with negative footage. |
| Bit runs | SI-007: footage with zero hours | **WARN** | 2 run(s) carry footage but no recorded 2-1 drilling hours (rate not reported for these). |
| Bit runs | SI-008: bit runs identified | **PASS** | 28 runs, 18 with footage, 16 with both footage and rotating hours. |
| Bit runs | SI-008: no negative footage | **PASS** | 0 runs with negative footage. |
| Bit runs | SI-008: footage with zero hours | **WARN** | 2 run(s) carry footage but no recorded 2-1 drilling hours (rate not reported for these). |
| Bit runs | SI-009: bit runs identified | **PASS** | 11 runs, 8 with footage, 8 with both footage and rotating hours. |
| Bit runs | SI-009: no negative footage | **PASS** | 0 runs with negative footage. |
| Bit runs | SI-009: footage with zero hours | **PASS** | 0 run(s) carry footage but no recorded 2-1 drilling hours (rate not reported for these). |
| Survey | SI-006: trajectory data | **N/A** | NOT USABLE - TEMPLATE DATA. Deepest recorded survey station is 1735 m MD against a final recorded depth of 5144 m (34 % coverage); the same stations repeat unchanged on the final sheet. |
| Survey | SI-007: trajectory data | **N/A** | NOT PRESENT. No numerical survey station is recorded in any DDR sheet. |
| Survey | SI-008: trajectory data | **PASS** | USABLE. |
| Survey | SI-009: trajectory data | **N/A** | NOT USABLE - TEMPLATE DATA. Deepest recorded survey station is 1500 m MD against a final recorded depth of 3084 m (49 % coverage); the same stations repeat unchanged on the final sheet. |
| Reconciliation | SI-006: final depth agrees across datasets | **PASS** | comparison 5144 m vs master 5144 m. |
| Reconciliation | SI-006: NPT hours agree across datasets | **PASS** | comparison 4342 h vs summary 4342 h. |
| Reconciliation | SI-006: DDR count agrees | **PASS** | master 421 vs register 421. |
| Reconciliation | SI-007: final depth agrees across datasets | **PASS** | comparison 4410 m vs master 4410 m. |
| Reconciliation | SI-007: NPT hours agree across datasets | **PASS** | comparison 5721.5 h vs summary 5721.5 h. |
| Reconciliation | SI-007: DDR count agrees | **PASS** | master 498 vs register 498. |
| Reconciliation | SI-008: final depth agrees across datasets | **PASS** | comparison 4900 m vs master 4900 m. |
| Reconciliation | SI-008: NPT hours agree across datasets | **PASS** | comparison 703 h vs summary 703 h. |
| Reconciliation | SI-008: DDR count agrees | **PASS** | master 209 vs register 209. |
| Reconciliation | SI-009: final depth agrees across datasets | **PASS** | comparison 3084 m vs master 3084 m. |
| Reconciliation | SI-009: NPT hours agree across datasets | **PASS** | comparison 1443 h vs summary 1443 h. |
| Reconciliation | SI-009: DDR count agrees | **PASS** | master 109 vs register 109. |
