# Post-W6 audit classification

Architect decision on the frozen product baseline `fddf5cad`, 2026-10-24. Every ledger disposition was a proposal. Rows with multiple observations use the disposition that gates the screen; related accepted gaps remain in the register. A duplicate arrow names the canonical observation. D3 is open until a reviewed fix and paired recapture.

## Completeness

- 379 distinct ledger IDs across 19 batches; 1414 linked pairs (minimum 174). All 87 original spec IDs have at least one pair at both 1440 and 390.
- Canonical dispositions: D1 86, D2 26, D3 131, D4 17, alias 46, existing 19, info 54.
- The `cold-finding-excursion` producer proves one more implemented manifest ID: 88 implemented and 22 outside W1–W6. The 88 captured screen IDs include the misrouted `ev-findings` cross-check, but omit `cold-finding-excursion`; add its own representative 1440/390 pairs in W2-cold recapture before claiming coverage.

| ID | Screens / pairs | Disposition |
| --- | --- | --- |
| B1-01 | * ([batch 01](batch-01/index.html); 40 pairs) | D1 R114 — open, visible MOCK DEVIATION D1 label required |
| B1-02 | changes,asset ([batch 01](batch-01/index.html); 40 pairs) | D3 R115 — shell-typography-copy — Low |
| B1-03 | * ([batch 01](batch-01/index.html); 40 pairs) | D2 R116 — open, visible MOCK DEVIATION D2 label required |
| B1-04 | * ([batch 01](batch-01/index.html); 40 pairs) | D1 R117 — open, visible MOCK DEVIATION D1 label required |
| B1-05 | foundation,readiness,sld,changes,asset,sites ([batch 01](batch-01/index.html); 40 pairs) | D2 R118 — open, visible MOCK DEVIATION D2 label required |
| B1-06 | readiness,sites,sld,changes,asset ([batch 01](batch-01/index.html); 40 pairs) | D3 R119 — shell-typography-copy — Low |
| B1-07 | sites,foundation,sld,asset,readiness ([batch 01](batch-01/index.html); 40 pairs) | D3 R120 — shell-typography-copy — Low |
| B1-10 | sites ([batch 01](batch-01/index.html); 40 pairs) | D1 R121 — open, visible MOCK DEVIATION D1 label required |
| B1-11 | sites ([batch 01](batch-01/index.html); 40 pairs) | D4 R122 — open, visible MOCK DEVIATION D4 label required |
| B1-12 | sites ([batch 01](batch-01/index.html); 40 pairs) | D1 R123 — open, visible MOCK DEVIATION D1 label required |
| B1-13 | sites ([batch 01](batch-01/index.html); 40 pairs) | D1 R124 — open, visible MOCK DEVIATION D1 label required |
| B1-14 | sites,foundation ([batch 01](batch-01/index.html); 40 pairs) | D3 R125 — shell-typography-copy — Low |
| B1-15 | sites ([batch 01](batch-01/index.html); 40 pairs) | D1 R126 — open, visible MOCK DEVIATION D1 label required |
| B1-16 | sites ([batch 01](batch-01/index.html); 40 pairs) | D3 R127 — shell-typography-copy — Low |
| B1-20 | foundation ([batch 01](batch-01/index.html); 40 pairs) | D2 R128 — open, visible MOCK DEVIATION D2 label required |
| B1-21 | foundation ([batch 01](batch-01/index.html); 40 pairs) | D3 R129 — shell-typography-copy — Low |
| B1-22 | foundation ([batch 01](batch-01/index.html); 40 pairs) | D3 R130 — shell-typography-copy — Low |
| B1-23 | foundation ([batch 01](batch-01/index.html); 40 pairs) | D1 R131 — open, visible MOCK DEVIATION D1 label required |
| B1-24 | foundation ([batch 01](batch-01/index.html); 40 pairs) | D2 R132 — open, visible MOCK DEVIATION D2 label required |
| B1-25 | foundation,readiness ([batch 01](batch-01/index.html); 40 pairs) | D3 R133 — shell-typography-copy — Low |
| B1-30 | readiness ([batch 01](batch-01/index.html); 40 pairs) | D4 R134 — open, visible MOCK DEVIATION D4 label required |
| B1-31 | readiness ([batch 01](batch-01/index.html); 40 pairs) | D1 R135 — open, visible MOCK DEVIATION D1 label required |
| B1-32 | readiness ([batch 01](batch-01/index.html); 40 pairs) | D1 R136 — open, visible MOCK DEVIATION D1 label required |
| B1-40 | sld ([batch 01](batch-01/index.html); 40 pairs) | D1 R137 — open, visible MOCK DEVIATION D1 label required |
| B1-41 | sld ([batch 01](batch-01/index.html); 40 pairs) | D1 R138 — open, visible MOCK DEVIATION D1 label required |
| B1-42 | sld ([batch 01](batch-01/index.html); 40 pairs) | D1 R139 — open, visible MOCK DEVIATION D1 label required |
| B1-43 | sld ([batch 01](batch-01/index.html); 40 pairs) | D3 R140 — shell-typography-copy — Low |
| B1-50 | changes ([batch 01](batch-01/index.html); 40 pairs) | informational/no change |
| B1-55 | changes ([batch 01](batch-01/index.html); 40 pairs) | D3 R141 — shell-typography-copy — Low |
| B1-51 | changes ([batch 01](batch-01/index.html); 40 pairs) | D1 R142 — open, visible MOCK DEVIATION D1 label required |
| B1-60 | asset ([batch 01](batch-01/index.html); 40 pairs) | D1 R143 — open, visible MOCK DEVIATION D1 label required |
| B1-61 | asset ([batch 01](batch-01/index.html); 40 pairs) | D2 R144 — open, visible MOCK DEVIATION D2 label required |
| B1-62 | asset ([batch 01](batch-01/index.html); 40 pairs) | D1 R145 — open, visible MOCK DEVIATION D1 label required |
| B1-63 | asset ([batch 01](batch-01/index.html); 40 pairs) | D1 R146 — open, visible MOCK DEVIATION D1 label required |
| B1-64 | asset ([batch 01](batch-01/index.html); 40 pairs) | D1 R147 — open, visible MOCK DEVIATION D1 label required |
| B1-65 | asset ([batch 01](batch-01/index.html); 40 pairs) | D4 R148 — open, visible MOCK DEVIATION D4 label required |
| B1-66 | asset ([batch 01](batch-01/index.html); 40 pairs) | D3 R149 — shell-typography-copy — Low |
| B1-52 | changes ([batch 01](batch-01/index.html); 40 pairs) | D1 R150 — open, visible MOCK DEVIATION D1 label required |
| B1-53 | changes ([batch 01](batch-01/index.html); 40 pairs) | D3 R151 — shell-typography-copy — Low |
| B1-54 | changes ([batch 01](batch-01/index.html); 40 pairs) | D3 R152 — shell-typography-copy — Low |
| B2-01 | mini, evidence, evidence-analysis, dispatch, analysis, health ([batch 02](batch-02/index.html); 62 pairs) | → B1-01 (merged duplicate) |
| B2-02 | mini, evidence, evidence-analysis, dispatch, analysis ([batch 02](batch-02/index.html); 62 pairs) | D1 R153 — open, visible MOCK DEVIATION D1 label required |
| B2-03 | mini, evidence, evidence-analysis, dispatch, analysis, health ([batch 02](batch-02/index.html); 62 pairs) | → B1-07 (merged duplicate) |
| B2-04 | health, analysis ([batch 02](batch-02/index.html); 62 pairs) | → B1-02 (merged duplicate) |
| B2-05 | mini, evidence, dispatch, analysis, health ([batch 02](batch-02/index.html); 62 pairs) | D1 R154 — open, visible MOCK DEVIATION D1 label required |
| B2-06 | mini ([batch 02](batch-02/index.html); 62 pairs) | D4 R155 — open, visible MOCK DEVIATION D4 label required |
| B2-07 | mini ([batch 02](batch-02/index.html); 62 pairs) | D3 R156 — W1-mini-Action — Low |
| B2-08 | mini ([batch 02](batch-02/index.html); 62 pairs) | D3 R157 — W1-mini-Action — Low |
| B2-09 | mini ([batch 02](batch-02/index.html); 62 pairs) | D1 R158 — open, visible MOCK DEVIATION D1 label required |
| B2-10 | mini ([batch 02](batch-02/index.html); 62 pairs) | D3 R159 — W1-mini-Action — Low |
| B2-11 | mini ([batch 02](batch-02/index.html); 62 pairs) | D4 R160 — open, visible MOCK DEVIATION D4 label required |
| B2-12 | mini ([batch 02](batch-02/index.html); 62 pairs) | D2 R161 — open, visible MOCK DEVIATION D2 label required |
| B2-13 | mini ([batch 02](batch-02/index.html); 62 pairs) | D1 R162 — open, visible MOCK DEVIATION D1 label required |
| B2-14 | mini ([batch 02](batch-02/index.html); 62 pairs) | D2 R163 — open, visible MOCK DEVIATION D2 label required |
| B2-15 | mini ([batch 02](batch-02/index.html); 62 pairs) | D3 R164 — W1-mini-Action — Low |
| B2-16 | evidence ([batch 02](batch-02/index.html); 62 pairs) | D1 R165 — open, visible MOCK DEVIATION D1 label required |
| B2-17 | evidence, health ([batch 02](batch-02/index.html); 62 pairs) | D1 R166 — open, visible MOCK DEVIATION D1 label required |
| B2-18 | evidence ([batch 02](batch-02/index.html); 62 pairs) | D1 R167 — open, visible MOCK DEVIATION D1 label required |
| B2-19 | evidence ([batch 02](batch-02/index.html); 62 pairs) | D1 R168 — open, visible MOCK DEVIATION D1 label required |
| B2-20 | evidence-analysis ([batch 02](batch-02/index.html); 62 pairs) | D2 R169 — open, visible MOCK DEVIATION D2 label required |
| B2-21 | evidence-analysis ([batch 02](batch-02/index.html); 62 pairs) | D3 R170 — shell-typography-copy — Low |
| B2-22 | evidence-analysis ([batch 02](batch-02/index.html); 62 pairs) | D3 R171 — W1-mini-Action — Low |
| B2-23 | dispatch, analysis ([batch 02](batch-02/index.html); 62 pairs) | D2 R172 — open, visible MOCK DEVIATION D2 label required |
| B2-24 | dispatch ([batch 02](batch-02/index.html); 62 pairs) | D2 R173 — open, visible MOCK DEVIATION D2 label required |
| B2-25 | dispatch ([batch 02](batch-02/index.html); 62 pairs) | D1 R174 — open, visible MOCK DEVIATION D1 label required |
| B2-26 | dispatch ([batch 02](batch-02/index.html); 62 pairs) | D1 R175 — open, visible MOCK DEVIATION D1 label required |
| B2-27 | dispatch ([batch 02](batch-02/index.html); 62 pairs) | D1 R176 — open, visible MOCK DEVIATION D1 label required |
| B2-28 | dispatch ([batch 02](batch-02/index.html); 62 pairs) | D1 R177 — open, visible MOCK DEVIATION D1 label required |
| B2-29 | dispatch ([batch 02](batch-02/index.html); 62 pairs) | D3 R178 — W1-mini-Action — Medium |
| B2-30 | analysis ([batch 02](batch-02/index.html); 62 pairs) | D1 R179 — open, visible MOCK DEVIATION D1 label required |
| B2-31 | analysis ([batch 02](batch-02/index.html); 62 pairs) | informational/no change |
| B2-32 | analysis ([batch 02](batch-02/index.html); 62 pairs) | D1 R180 — open, visible MOCK DEVIATION D1 label required |
| B2-33 | analysis ([batch 02](batch-02/index.html); 62 pairs) | D1 R181 — open, visible MOCK DEVIATION D1 label required |
| B2-34 | analysis ([batch 02](batch-02/index.html); 62 pairs) | D1 R182 — open, visible MOCK DEVIATION D1 label required |
| B2-35 | health ([batch 02](batch-02/index.html); 62 pairs) | D1 R183 — open, visible MOCK DEVIATION D1 label required |
| B2-36 | mini, evidence, evidence-analysis, dispatch, analysis, health ([batch 02](batch-02/index.html); 62 pairs) | → B1-04 (merged duplicate) |
| B3-X1 | finding, finding-evidence, finding-history, sitefindings, financials, assumptions ([batch 03](batch-03/index.html); 72 pairs) | informational/no change |
| B3-01 | finding, finding-evidence, finding-history ([batch 03](batch-03/index.html); 72 pairs) | D3 R184 — W1-mini-Action — Low |
| B3-02 | finding, finding-evidence, finding-history ([batch 03](batch-03/index.html); 72 pairs) | D3 R185 — W1-mini-Action — Low |
| B3-03 | finding, finding-evidence, finding-history ([batch 03](batch-03/index.html); 72 pairs) | D3 R186 — W1-mini-Action — Low |
| B3-04 | finding ([batch 03](batch-03/index.html); 72 pairs) | D3 R187 — W1-mini-Action — Low |
| B3-05 | finding ([batch 03](batch-03/index.html); 72 pairs) | D3 R188 — W1-mini-Action — Low |
| B3-06 | finding ([batch 03](batch-03/index.html); 72 pairs) | D3 R189 — W1-mini-Action — Low |
| B3-07 | finding ([batch 03](batch-03/index.html); 72 pairs) | D3 R190 — W1-mini-Action — Low |
| B3-08 | finding ([batch 03](batch-03/index.html); 72 pairs) | D3 R191 — W1-mini-Action — Low |
| B3-09 | finding ([batch 03](batch-03/index.html); 72 pairs) | D3 R192 — W1-mini-Action — Low |
| B3-10 | finding, finding-evidence, finding-history ([batch 03](batch-03/index.html); 72 pairs) | D3 R193 — W1-mini-Action — Low |
| B3-11 | finding-evidence ([batch 03](batch-03/index.html); 72 pairs) | D1 R194 — open, visible MOCK DEVIATION D1 label required |
| B3-12 | finding-history ([batch 03](batch-03/index.html); 72 pairs) | D3 R195 — W1-mini-Action — Low |
| B3-13 | sitefindings ([batch 03](batch-03/index.html); 72 pairs) | D3 R196 — W1-mini-Action — Low |
| B3-14 | sitefindings ([batch 03](batch-03/index.html); 72 pairs) | D3 R197 — W1-mini-Action — Low |
| B3-15 | financials ([batch 03](batch-03/index.html); 72 pairs) | D3 R198 — W1-mini-Action — Low |
| B3-16 | financials ([batch 03](batch-03/index.html); 72 pairs) | D3 R199 — W1-mini-Action — Low |
| B3-17 | assumptions ([batch 03](batch-03/index.html); 72 pairs) | D3 R200 — W1-mini-Action — Medium |
| B3-18 | assumptions ([batch 03](batch-03/index.html); 72 pairs) | D3 R201 — W1-mini-Action — Low |
| B4-01 | recommendation ([batch 04](batch-04/index.html); 50 pairs) | D3 R202 — W1-mini-Action — Low |
| R69-verified | action-overview, action-execution, action-history, action-plan, action-evidence ([batch 04](batch-04/index.html); 50 pairs) | R69 — verified built/resolved |
| B4-03 | action-* (all five) ([batch 04](batch-04/index.html); 50 pairs) | D3 R203 — shell-typography-copy — Low |
| B4-04 | all six ([batch 04](batch-04/index.html); 50 pairs) | D3 R204 — W1-mini-Action — Low |
| B4-05 | all six ([batch 04](batch-04/index.html); 50 pairs) | D3 R205 — W1-mini-Action — Low |
| B4-06 | all six ([batch 04](batch-04/index.html); 50 pairs) | D4 R206 — open, visible MOCK DEVIATION D4 label required |
| B4-07 | action-* (all five) ([batch 04](batch-04/index.html); 50 pairs) | D2 R207 — open, visible MOCK DEVIATION D2 label required |
| B4-08 | recommendation ([batch 04](batch-04/index.html); 50 pairs) | R21 — verified built/resolved |
| B4-09 | recommendation ([batch 04](batch-04/index.html); 50 pairs) | D1 R208 — open, visible MOCK DEVIATION D1 label required |
| B4-10 | recommendation ([batch 04](batch-04/index.html); 50 pairs) | D3 R209 — W1-mini-Action — Low |
| B4-11 | all six ([batch 04](batch-04/index.html); 50 pairs) | D2 R210 — open, visible MOCK DEVIATION D2 label required |
| B4-12 | recommendation ([batch 04](batch-04/index.html); 50 pairs) | D2 R211 — open, visible MOCK DEVIATION D2 label required |
| B4-13 | recommendation ([batch 04](batch-04/index.html); 50 pairs) | D1 R212 — open, visible MOCK DEVIATION D1 label required |
| B4-14 | recommendation ([batch 04](batch-04/index.html); 50 pairs) | D1 R213 — open, visible MOCK DEVIATION D1 label required |
| B4-15 | recommendation ([batch 04](batch-04/index.html); 50 pairs) | D1 R214 — open, visible MOCK DEVIATION D1 label required |
| B4-16 | action-overview ([batch 04](batch-04/index.html); 50 pairs) | D1 R215 — open, visible MOCK DEVIATION D1 label required |
| B4-17 | action-execution ([batch 04](batch-04/index.html); 50 pairs) | D2 R216 — open, visible MOCK DEVIATION D2 label required |
| B4-18 | action-history ([batch 04](batch-04/index.html); 50 pairs) | D2 R217 — open, visible MOCK DEVIATION D2 label required |
| B4-19 | action-history (s602b verified-replay) ([batch 04](batch-04/index.html); 50 pairs) | D3 R218 — W1-mini-Action — Low |
| B4-20 | action-history ([batch 04](batch-04/index.html); 50 pairs) | D3 R219 — W1-mini-Action — Low |
| B4-21 | action-plan ([batch 04](batch-04/index.html); 50 pairs) | D3 R220 — W1-mini-Action — Low |
| B4-22 | action-evidence ([batch 04](batch-04/index.html); 50 pairs) | D3 R221 — W1-mini-Action — Low |
| B4-23 | action-plan, action-evidence (s601b pre-plan) ([batch 04](batch-04/index.html); 50 pairs) | R69 — verified built/resolved |
| B4-24 | action-overview (unknown section /nosuch) ([batch 04](batch-04/index.html); 50 pairs) | D3 R222 — W1-mini-Action — Low |
| B4-25 | recommendation (s601b 'unavailable' link) ([batch 04](batch-04/index.html); 50 pairs) | informational/no change |
| B5-X1 | verification, sitework ([batch 05](batch-05/index.html); 26 pairs) | informational/no change |
| B5-01 | verification ([batch 05](batch-05/index.html); 26 pairs) | D3 R223 — W1-mini-Action — Low |
| B5-02 | verification ([batch 05](batch-05/index.html); 26 pairs) | D2 R224 — open, visible MOCK DEVIATION D2 label required |
| B5-03 | verification ([batch 05](batch-05/index.html); 26 pairs) | D1 R225 — open, visible MOCK DEVIATION D1 label required |
| B5-04 | verification ([batch 05](batch-05/index.html); 26 pairs) | D1 R226 — open, visible MOCK DEVIATION D1 label required |
| B5-05 | verification ([batch 05](batch-05/index.html); 26 pairs) | R69 — verified built/resolved |
| B5-06 | verification ([batch 05](batch-05/index.html); 26 pairs) | D1 R227 — open, visible MOCK DEVIATION D1 label required |
| B5-07 | verification ([batch 05](batch-05/index.html); 26 pairs) | D3 R228 — W1-mini-Action — Low |
| B5-08 | verification ([batch 05](batch-05/index.html); 26 pairs) | D3 R229 — W1-mini-Action — Low |
| B5-09 | sitework ([batch 05](batch-05/index.html); 26 pairs) | D3 R230 — W1-mini-Action — Low |
| B5-10 | sitework ([batch 05](batch-05/index.html); 26 pairs) | D1 R231 — open, visible MOCK DEVIATION D1 label required |
| B5-11 | sitework ([batch 05](batch-05/index.html); 26 pairs) | D1 R232 — open, visible MOCK DEVIATION D1 label required |
| B5-12 | verification, sitework ([batch 05](batch-05/index.html); 26 pairs) | informational/no change |
| B6-01 | cold-foundation, cold-readiness, cold-sld ([batch 06](batch-06/index.html); 14 pairs) | D2 R233 — open, visible MOCK DEVIATION D2 label required |
| B6-02 | cold-foundation ([batch 06](batch-06/index.html); 4 pairs) | D4 R234 — open, visible MOCK DEVIATION D4 label required |
| B6-03 | cold-foundation, cold-readiness, cold-sld, temperature, coldbackup, cold-finding ([batch 06](batch-06/index.html); 46 pairs) | D4 R235 — open, visible MOCK DEVIATION D4 label required |
| B6-04 | cold-foundation, cold-readiness, cold-sld, temperature, coldbackup ([batch 06](batch-06/index.html); 36 pairs) | → B1-06 (merged duplicate) |
| B6-05 | cold-readiness ([batch 06](batch-06/index.html); 2 pairs) | D4 R236 — open, visible MOCK DEVIATION D4 label required |
| B6-06 | cold-readiness ([batch 06](batch-06/index.html); 2 pairs) | D1 R237 — open, visible MOCK DEVIATION D1 label required |
| B6-07 | cold-readiness, cold-sld ([batch 06](batch-06/index.html); 8 pairs) | D2 R238 — open, visible MOCK DEVIATION D2 label required |
| B6-08 | cold-sld ([batch 06](batch-06/index.html); 2 pairs) | D1 R239 — open, visible MOCK DEVIATION D1 label required |
| B6-09 | cold-sld ([batch 06](batch-06/index.html); 2 pairs) | D1 R240 — open, visible MOCK DEVIATION D1 label required |
| B6-10 | temperature ([batch 06](batch-06/index.html); 10 pairs) | D3 R241 — W2-cold — Low |
| B6-11 | temperature, coldbackup ([batch 06](batch-06/index.html); 22 pairs) | D3 R242 — W2-cold — Low |
| B6-12 | temperature ([batch 06](batch-06/index.html); 6 pairs) | D1 R243 — open, visible MOCK DEVIATION D1 label required |
| B6-13 | temperature, coldbackup ([batch 06](batch-06/index.html); 4 pairs) | D3 R244 — W2-cold — Low |
| B6-14 | temperature ([batch 06](batch-06/index.html); 2 pairs) | D3 R245 — W2-cold — Low |
| B6-15 | coldbackup ([batch 06](batch-06/index.html); 12 pairs) | D3 R246 — W2-cold — Low |
| B6-16 | coldbackup ([batch 06](batch-06/index.html); 8 pairs) | R20 — verified built/resolved |
| B6-17 | coldbackup ([batch 06](batch-06/index.html); 2 pairs) | D3 R247 — W2-cold — Low |
| B6-18 | cold-finding ([batch 06](batch-06/index.html); 10 pairs) | R65 — verified built/resolved |
| B6-19 | cold-finding ([batch 06](batch-06/index.html); 10 pairs) | D1 R248 — open, visible MOCK DEVIATION D1 label required |
| B6-20 | cold-finding ([batch 06](batch-06/index.html); 10 pairs) | D3 R249 — W2-cold — Low |
| B6-21 | cold-finding ([batch 06](batch-06/index.html); 6 pairs) | D4 R250 — open, visible MOCK DEVIATION D4 label required |
| B6-22 | cold-finding ([batch 06](batch-06/index.html); 4 pairs) | D1 R251 — open, visible MOCK DEVIATION D1 label required |
| B6-23 | cold-finding ([batch 06](batch-06/index.html); 2 pairs) | informational/no change |
| B6-24 | cold-foundation, cold-readiness, cold-sld ([batch 06](batch-06/index.html); 6 pairs) | D1 R252 — open, visible MOCK DEVIATION D1 label required |
| B7-X1 | cold-findings, cold, cold-evidence, cold-evidence-analysis, cold-financials, cold-assumptions ([batch 07](batch-07/index.html); 60 pairs) | informational/no change |
| B7-01 | cold-findings ([batch 07](batch-07/index.html); 60 pairs) | D3 R253 — W2-cold — High |
| B7-02 | cold, cold-evidence, cold-evidence-analysis, cold-financials, cold-assumptions ([batch 07](batch-07/index.html); 60 pairs) | → B2-02 (merged duplicate) |
| B7-03 | cold ([batch 07](batch-07/index.html); 60 pairs) | D3 R254 — W2-cold — Medium |
| B7-04 | cold ([batch 07](batch-07/index.html); 60 pairs) | D3 R255 — W2-cold — Low |
| B7-05 | cold ([batch 07](batch-07/index.html); 60 pairs) | D3 R256 — W2-cold — Low |
| B7-06 | cold ([batch 07](batch-07/index.html); 60 pairs) | D1 R257 — open, visible MOCK DEVIATION D1 label required |
| B7-07 | cold-evidence ([batch 07](batch-07/index.html); 60 pairs) | D3 R258 — W2-cold — Low |
| B7-08 | cold-evidence-analysis ([batch 07](batch-07/index.html); 60 pairs) | D3 R259 — W2-cold — Low |
| B7-09 | cold-financials ([batch 07](batch-07/index.html); 60 pairs) | R65 — verified built/resolved |
| B7-10 | cold-assumptions ([batch 07](batch-07/index.html); 60 pairs) | D2 R260 — open, visible MOCK DEVIATION D2 label required |
| B7-11 | cold, cold-evidence, cold-financials, cold-assumptions, cold-evidence-analysis ([batch 07](batch-07/index.html); 60 pairs) | D3 R261 — W2-cold — Low |
| B7-12 | cold-findings, cold, cold-evidence, cold-evidence-analysis, cold-financials, cold-assumptions ([batch 07](batch-07/index.html); 60 pairs) | informational/no change |
| B8-01 | ev-foundation, ev-readiness, ev-sld ([batch 08](batch-08/index.html); 16 pairs) | → B1-05 (merged duplicate) |
| B8-02 | ev-foundation ([batch 08](batch-08/index.html); 4 pairs) | D4 R262 — open, visible MOCK DEVIATION D4 label required |
| B8-03 | ev-foundation, ev-readiness ([batch 08](batch-08/index.html); 8 pairs) | D4 R263 — open, visible MOCK DEVIATION D4 label required |
| B8-04 | ev-foundation, ev-readiness, ev-sld, sessions, ev-finding ([batch 08](batch-08/index.html); 52 pairs) | D4 R264 — open, visible MOCK DEVIATION D4 label required |
| B8-05 | ev-foundation, ev-readiness, ev-sld ([batch 08](batch-08/index.html); 16 pairs) | → B1-06 (merged duplicate) |
| B8-06 | ev-readiness ([batch 08](batch-08/index.html); 4 pairs) | D3 R265 — W2-EV — Low |
| B8-07 | ev-readiness ([batch 08](batch-08/index.html); 4 pairs) | D1 R266 — open, visible MOCK DEVIATION D1 label required |
| B8-08 | ev-readiness ([batch 08](batch-08/index.html); 4 pairs) | D3 R267 — W2-EV — Low |
| B8-09 | ev-readiness, ev-sld ([batch 08](batch-08/index.html); 10 pairs) | → B6-07 (merged duplicate) |
| B8-10 | ev-sld ([batch 08](batch-08/index.html); 2 pairs) | R36 — verified built/resolved |
| B8-11 | ev-sld ([batch 08](batch-08/index.html); 2 pairs) | → B1-42 (merged duplicate) |
| B8-12 | sessions ([batch 08](batch-08/index.html); 20 pairs) | D3 R268 — W2-EV — Low |
| B8-13 | sessions ([batch 08](batch-08/index.html); 20 pairs) | D1 R269 — open, visible MOCK DEVIATION D1 label required |
| B8-14 | sessions ([batch 08](batch-08/index.html); 8 pairs) | D3 R270 — W2-EV — Low |
| B8-15 | sessions ([batch 08](batch-08/index.html); 4 pairs) | D3 R271 — W2-EV — Low |
| B8-16 | sessions ([batch 08](batch-08/index.html); 20 pairs) | D4 R272 — open, visible MOCK DEVIATION D4 label required |
| B8-17 | sessions, ev-finding ([batch 08](batch-08/index.html); 4 pairs) | D1 R273 — open, visible MOCK DEVIATION D1 label required |
| B8-18 | ev-finding ([batch 08](batch-08/index.html); 12 pairs) | D1 R274 — open, visible MOCK DEVIATION D1 label required |
| B8-19 | ev-finding ([batch 08](batch-08/index.html); 4 pairs) | D3 R275 — W2-EV — Low |
| B8-20 | ev-finding ([batch 08](batch-08/index.html); 4 pairs) | D3 R276 — W2-EV — Low |
| B8-21 | ev-finding ([batch 08](batch-08/index.html); 4 pairs) | D1 R277 — open, visible MOCK DEVIATION D1 label required |
| B8-22 | ev-finding ([batch 08](batch-08/index.html); 10 pairs) | D1 R278 — open, visible MOCK DEVIATION D1 label required |
| B8-23 | ev-finding ([batch 08](batch-08/index.html); 4 pairs) | D1 R279 — open, visible MOCK DEVIATION D1 label required |
| B8-24 | ev-finding ([batch 08](batch-08/index.html); 4 pairs) | D3 R280 — W2-EV — Low |
| B8-25 | ev-findings (inventory check) ([batch 08](batch-08/index.html); 4 pairs) | informational/no change |
| B8-27 | sessions ([batch 08](batch-08/index.html); 20 pairs) | D3 R281 — W2-EV — Low |
| B8-26 | ev-foundation, ev-readiness, ev-sld ([batch 08](batch-08/index.html); 6 pairs) | D1 R282 — open, visible MOCK DEVIATION D1 label required |
| B9-X1 | ev, ev-evidence, ev-evidence-analysis, ev-financials, ev-assumptions ([batch 09](batch-09/index.html); 50 pairs) | informational/no change |
| B9-01 | ev, ev-evidence, ev-evidence-analysis, ev-financials, ev-assumptions ([batch 09](batch-09/index.html); 50 pairs) | → B2-02 (merged duplicate) |
| B9-02 | ev ([batch 09](batch-09/index.html); 50 pairs) | → B7-03 (merged duplicate) |
| B9-03 | ev ([batch 09](batch-09/index.html); 50 pairs) | D3 R283 — W2-EV — Low |
| B9-04 | ev ([batch 09](batch-09/index.html); 50 pairs) | R74 — verified built/resolved |
| B9-05 | ev, ev-evidence, ev-evidence-analysis, ev-financials, ev-assumptions ([batch 09](batch-09/index.html); 50 pairs) | D3 R284 — W2-EV — Medium |
| B9-06 | ev-evidence ([batch 09](batch-09/index.html); 50 pairs) | → B7-07 (merged duplicate) |
| B9-07 | ev-evidence-analysis ([batch 09](batch-09/index.html); 50 pairs) | → B7-08 (merged duplicate) |
| B9-08 | ev-financials ([batch 09](batch-09/index.html); 50 pairs) | D3 R285 — W2-EV — Low |
| B9-09 | ev-assumptions ([batch 09](batch-09/index.html); 50 pairs) | D3 R286 — W2-EV — Low |
| B9-10 | batch 9 ([batch 09](batch-09/index.html); 50 pairs) | → B7-01 (merged duplicate) |
| B9-11 | ev, ev-evidence, ev-evidence-analysis, ev-financials, ev-assumptions ([batch 09](batch-09/index.html); 50 pairs) | informational/no change |
| B10-X1 | findings, findings-cost, findings-risks, findings-opportunities, actions ([batch 10](batch-10/index.html); 62 pairs) | informational/no change |
| B10-01 | findings, findings-cost, findings-risks, findings-opportunities, actions ([batch 10](batch-10/index.html); 62 pairs) | D1 R287 — open, visible MOCK DEVIATION D1 label required |
| B10-02 | findings, findings-cost, findings-risks, findings-opportunities, actions ([batch 10](batch-10/index.html); 62 pairs) | D1 R288 — open, visible MOCK DEVIATION D1 label required |
| B10-03 | findings, findings-cost, findings-risks, findings-opportunities ([batch 10](batch-10/index.html); 62 pairs) | D2 R289 — open, visible MOCK DEVIATION D2 label required |
| B10-04 | findings ([batch 10](batch-10/index.html); 62 pairs) | D1 R290 — open, visible MOCK DEVIATION D1 label required |
| B10-05 | findings, findings-cost, findings-risks, findings-opportunities ([batch 10](batch-10/index.html); 62 pairs) | D1 R291 — open, visible MOCK DEVIATION D1 label required |
| B10-06 | findings-cost, findings-risks, findings-opportunities ([batch 10](batch-10/index.html); 62 pairs) | D1 R292 — open, visible MOCK DEVIATION D1 label required |
| B10-07 | actions ([batch 10](batch-10/index.html); 62 pairs) | D3 R293 — W3-estate — Low |
| B10-08 | findings, findings-cost, findings-risks, findings-opportunities ([batch 10](batch-10/index.html); 62 pairs) | D3 R294 — W3-estate — Low |
| B10-09 | findings ([batch 10](batch-10/index.html); 62 pairs) | D3 R295 — W3-estate — Low |
| B10-10 | findings, findings-cost, findings-risks, findings-opportunities, actions ([batch 10](batch-10/index.html); 62 pairs) | informational/no change |
| B10-11 | batch 10 ([batch 10](batch-10/index.html); 62 pairs) | informational/no change |
| B11-X1 | globalevidence, globalfinancials, portfolio ([batch 11](batch-11/index.html); 66 pairs) | informational/no change |
| B11-01 | globalfinancials ([batch 11](batch-11/index.html); 66 pairs) | D3 R296 — W3-estate — Medium |
| B11-02 | portfolio ([batch 11](batch-11/index.html); 66 pairs) | D3 R297 — W3-estate — Low |
| B11-03 | globalevidence, globalfinancials, portfolio ([batch 11](batch-11/index.html); 66 pairs) | D1 R298 — open, visible MOCK DEVIATION D1 label required |
| B11-04 | globalevidence ([batch 11](batch-11/index.html); 66 pairs) | D2 R299 — open, visible MOCK DEVIATION D2 label required |
| B11-05 | globalevidence ([batch 11](batch-11/index.html); 66 pairs) | D3 R300 — W3-estate — Low |
| B11-06 | globalevidence ([batch 11](batch-11/index.html); 66 pairs) | D1 R301 — open, visible MOCK DEVIATION D1 label required |
| B11-07 | globalfinancials ([batch 11](batch-11/index.html); 66 pairs) | D3 R302 — W3-estate — Low |
| B11-08 | globalfinancials ([batch 11](batch-11/index.html); 66 pairs) | D2 R303 — open, visible MOCK DEVIATION D2 label required |
| B11-09 | portfolio ([batch 11](batch-11/index.html); 66 pairs) | D1 R304 — open, visible MOCK DEVIATION D1 label required |
| B11-10 | portfolio ([batch 11](batch-11/index.html); 66 pairs) | D1 R305 — open, visible MOCK DEVIATION D1 label required |
| B11-11 | portfolio ([batch 11](batch-11/index.html); 66 pairs) | D2 R306 — open, visible MOCK DEVIATION D2 label required |
| B11-12 | portfolio ([batch 11](batch-11/index.html); 66 pairs) | D3 R307 — W3-estate — Low |
| B11-13 | globalevidence, globalfinancials, portfolio ([batch 11](batch-11/index.html); 66 pairs) | D3 R308 — W3-estate — Low |
| B11-14 | globalevidence, globalfinancials, portfolio ([batch 11](batch-11/index.html); 66 pairs) | informational/no change |
| B11-15 | batch 11 ([batch 11](batch-11/index.html); 66 pairs) | informational/no change |
| B11-16 | portfolio ([batch 11](batch-11/index.html); 66 pairs) | informational/no change |
| B12-X1 | renewable, service, fuel, backup ([batch 12](batch-12/index.html); 42 pairs) | informational/no change |
| B12-01 | renewable, service, fuel, backup ([batch 12](batch-12/index.html); 42 pairs) | informational/no change |
| B12-02 | renewable, service, fuel, backup ([batch 12](batch-12/index.html); 42 pairs) | D3 R309 — W4-mini — Low |
| B12-03 | renewable ([batch 12](batch-12/index.html); 42 pairs) | D3 R310 — W4-mini — Low |
| B12-04 | renewable ([batch 12](batch-12/index.html); 42 pairs) | D3 R311 — W4-mini — Low |
| B12-05 | renewable ([batch 12](batch-12/index.html); 42 pairs) | D3 R312 — W4-mini — Low |
| B12-06 | renewable, service, fuel, backup ([batch 12](batch-12/index.html); 42 pairs) | D3 R313 — W4-mini — Low |
| B12-07 | renewable, service ([batch 12](batch-12/index.html); 42 pairs) | D1 R314 — open, visible MOCK DEVIATION D1 label required |
| B12-08 | renewable, service, fuel, backup ([batch 12](batch-12/index.html); 42 pairs) | D1 R315 — open, visible MOCK DEVIATION D1 label required |
| B12-09 | service ([batch 12](batch-12/index.html); 42 pairs) | D3 R316 — W4-mini — Low |
| B12-10 | renewable, service, fuel, backup ([batch 12](batch-12/index.html); 42 pairs) | D1 R317 — open, visible MOCK DEVIATION D1 label required |
| B12-11 | renewable, service, fuel, backup ([batch 12](batch-12/index.html); 42 pairs) | D3 R318 — W4-mini — Low |
| B12-12 | link-check ([batch 12](batch-12/index.html); 42 pairs) | → B2-08 (merged duplicate) |
| B12-13 | batch 12 ([batch 12](batch-12/index.html); 42 pairs) | informational/no change |
| B12-14 | renewable, service, fuel, backup ([batch 12](batch-12/index.html); 42 pairs) | informational/no change |
| B13-X1 | sitework-incidents, sitework-maintenance, scenarios, alternatives, opportunity-finding ([batch 13](batch-13/index.html); 54 pairs) | informational/no change |
| B13-01 | sitework-incidents, sitework-maintenance ([batch 13](batch-13/index.html); 54 pairs) | D3 R319 — shell-typography-copy — Low |
| B13-02 | sitework-incidents ([batch 13](batch-13/index.html); 54 pairs) | D3 R320 — W4-mini — Low |
| B13-03 | opportunity-finding ([batch 13](batch-13/index.html); 54 pairs) | D3 R321 — W4-mini — Low |
| B13-04 | sitework-incidents, sitework-maintenance ([batch 13](batch-13/index.html); 54 pairs) | D3 R322 — W4-mini — Low |
| B13-05 | sitework-incidents, sitework-maintenance ([batch 13](batch-13/index.html); 54 pairs) | D2 R323 — open, visible MOCK DEVIATION D2 label required |
| B13-06 | sitework-incidents ([batch 13](batch-13/index.html); 54 pairs) | D3 R324 — W4-mini — Low |
| B13-07 | scenarios ([batch 13](batch-13/index.html); 54 pairs) | D3 R325 — W4-mini — Low |
| B13-08 | scenarios ([batch 13](batch-13/index.html); 54 pairs) | D4 R326 — open, visible MOCK DEVIATION D4 label required |
| B13-09 | scenarios ([batch 13](batch-13/index.html); 54 pairs) | D1 R327 — open, visible MOCK DEVIATION D1 label required |
| B13-10 | alternatives ([batch 13](batch-13/index.html); 54 pairs) | informational/no change |
| B13-11 | alternatives ([batch 13](batch-13/index.html); 54 pairs) | D3 R328 — W4-mini — Low |
| B13-12 | alternatives, opportunity-finding ([batch 13](batch-13/index.html); 54 pairs) | → B4-01 (merged duplicate) |
| B13-13 | opportunity-finding ([batch 13](batch-13/index.html); 54 pairs) | D1 R329 — open, visible MOCK DEVIATION D1 label required |
| B13-14 | opportunity-finding ([batch 13](batch-13/index.html); 54 pairs) | D1 R330 — open, visible MOCK DEVIATION D1 label required |
| B13-15 | opportunity-finding ([batch 13](batch-13/index.html); 54 pairs) | D3 R331 — W4-mini — Low |
| B13-16 | sitework-incidents, sitework-maintenance ([batch 13](batch-13/index.html); 54 pairs) | → B2-19 (merged duplicate) |
| B13-17 | sitework-incidents ([batch 13](batch-13/index.html); 54 pairs) | D1 R332 — open, visible MOCK DEVIATION D1 label required |
| B13-18 | sitework-incidents, sitework-maintenance, scenarios ([batch 13](batch-13/index.html); 54 pairs) | D3 R333 — W4-mini — Low |
| B13-19 | sitework-incidents, sitework-maintenance, scenarios, alternatives, opportunity-finding ([batch 13](batch-13/index.html); 54 pairs) | informational/no change |
| B13-20 | batch 13 ([batch 13](batch-13/index.html); 54 pairs) | informational/no change |
| B14-X1 | cooling, cold-health, cold-scenarios, cold-work ([batch 14](batch-14/index.html); 88 pairs) | informational/no change |
| B14-01 | cooling, cold-health, cold-scenarios ([batch 14](batch-14/index.html); 88 pairs) | → B6-13 (merged duplicate) |
| B14-02 | cold-work ([batch 14](batch-14/index.html); 88 pairs) | → B7-11 (merged duplicate) |
| B14-03 | cold-work ([batch 14](batch-14/index.html); 88 pairs) | D3 R334 — W5-cold-Work — Low |
| B14-04 | cooling, cold-health, cold-scenarios, cold-work ([batch 14](batch-14/index.html); 88 pairs) | → B12-02 (merged duplicate) |
| B14-05 | cooling, cold-health ([batch 14](batch-14/index.html); 88 pairs) | → B1-53 (merged duplicate) |
| B14-06 | cooling ([batch 14](batch-14/index.html); 88 pairs) | D1 R335 — open, visible MOCK DEVIATION D1 label required |
| B14-07 | cooling, cold-health ([batch 14](batch-14/index.html); 88 pairs) | D3 R336 — W5-cold-Work — Low |
| B14-08 | cold-scenarios ([batch 14](batch-14/index.html); 88 pairs) | D3 R337 — W5-cold-Work — Low |
| B14-09 | cold-work ([batch 14](batch-14/index.html); 88 pairs) | D3 R338 — W5-cold-Work — Low |
| B14-10 | cooling, cold-health, cold-scenarios, cold-work ([batch 14](batch-14/index.html); 88 pairs) | D3 R339 — W5-cold-Work — Low |
| B14-11 | cold-work ([batch 14](batch-14/index.html); 88 pairs) | informational/no change |
| B14-12 | cold-work ([batch 14](batch-14/index.html); 88 pairs) | informational/no change |
| B14-13 | cold-health ([batch 14](batch-14/index.html); 88 pairs) | R22 — verified built/resolved |
| B14-14 | link-check ([batch 14](batch-14/index.html); 88 pairs) | D1 R340 — open, visible MOCK DEVIATION D1 label required |
| B14-15 | batch 14 ([batch 14](batch-14/index.html); 88 pairs) | informational/no change |
| B14-16 | cold-scenarios ([batch 14](batch-14/index.html); 88 pairs) | informational/no change |
| B14-17 | cold-health, cold-work ([batch 14](batch-14/index.html); 88 pairs) | D1 R341 — open, visible MOCK DEVIATION D1 label required |
| B15-X1 | cold-work-incidents, cold-work-maintenance, cold-action ([batch 15](batch-15/index.html); 88 pairs) | informational/no change |
| B15-01 | cold-action ([batch 15](batch-15/index.html); 88 pairs) | D1 R342 — open, visible MOCK DEVIATION D1 label required |
| B15-02 | cold-work-incidents, cold-work-maintenance ([batch 15](batch-15/index.html); 88 pairs) | → B13-01 (merged duplicate) |
| B15-03 | cold-work-incidents, cold-work-maintenance ([batch 15](batch-15/index.html); 88 pairs) | → B13-04 (merged duplicate) |
| B15-04 | cold-action ([batch 15](batch-15/index.html); 88 pairs) | → B13-04 (merged duplicate) |
| B15-05 | cold-work-incidents, cold-work-maintenance ([batch 15](batch-15/index.html); 88 pairs) | R88 — verified built/resolved |
| B15-06 | cold-work-incidents, cold-work-maintenance ([batch 15](batch-15/index.html); 88 pairs) | → B14-09 (merged duplicate) |
| B15-07 | cold-work-incidents, cold-work-maintenance ([batch 15](batch-15/index.html); 88 pairs) | D1 R343 — open, visible MOCK DEVIATION D1 label required |
| B15-08 | cold-work-incidents, cold-work-maintenance, cold-action ([batch 15](batch-15/index.html); 88 pairs) | R65 — verified built/resolved |
| B15-09 | cold-work-incidents, cold-work-maintenance, cold-action ([batch 15](batch-15/index.html); 88 pairs) | informational/no change |
| B15-10 | cold-action ([batch 15](batch-15/index.html); 88 pairs) | D3 R344 — W5-cold-Work — Low |
| B15-11 | cold-work-incidents, cold-work-maintenance, cold-action ([batch 15](batch-15/index.html); 88 pairs) | R91 — verified built/resolved |
| B15-12 | cold-work-incidents ([batch 15](batch-15/index.html); 88 pairs) | R23 — verified built/resolved |
| B15-13 | batch 15 ([batch 15](batch-15/index.html); 88 pairs) | informational/no change |
| B16-X1 | availability, energy, ev-health, ev-scenarios, ev-work ([batch 16](batch-16/index.html); 88 pairs) | informational/no change |
| B16-01 | availability, energy, ev-health, ev-scenarios ([batch 16](batch-16/index.html); 88 pairs) | → B6-13 (merged duplicate) |
| B16-02 | ev-work ([batch 16](batch-16/index.html); 88 pairs) | → B7-11 (merged duplicate) |
| B16-03 | ev-work ([batch 16](batch-16/index.html); 88 pairs) | R112 — verified built/resolved |
| B16-04 | ev-work ([batch 16](batch-16/index.html); 88 pairs) | → B14-09 (merged duplicate) |
| B16-05 | ev-health, ev-work ([batch 16](batch-16/index.html); 88 pairs) | → B1-53 (merged duplicate) |
| B16-06 | availability ([batch 16](batch-16/index.html); 88 pairs) | D3 R345 — W5-EV-Work — Low |
| B16-07 | energy ([batch 16](batch-16/index.html); 88 pairs) | D3 R346 — W5-EV-Work — Low |
| B16-08 | ev-scenarios ([batch 16](batch-16/index.html); 88 pairs) | → B14-08 (merged duplicate) |
| B16-09 | ev-scenarios ([batch 16](batch-16/index.html); 88 pairs) | informational/no change |
| B16-10 | availability, energy, ev-health, ev-scenarios ([batch 16](batch-16/index.html); 88 pairs) | informational/no change |
| B16-11 | ev-health ([batch 16](batch-16/index.html); 88 pairs) | R58 — verified built/resolved |
| B16-12 | ev-work ([batch 16](batch-16/index.html); 88 pairs) | informational/no change |
| B16-13 | ev-work, availability ([batch 16](batch-16/index.html); 88 pairs) | informational/no change |
| B16-14 | link-check ([batch 16](batch-16/index.html); 88 pairs) | → B13-01 (merged duplicate) |
| B16-15 | link-check ([batch 16](batch-16/index.html); 88 pairs) | → B7-03 (merged duplicate) |
| B16-16 | availability, energy, ev-health, ev-scenarios, ev-work ([batch 16](batch-16/index.html); 88 pairs) | D3 R347 — W5-EV-Work — Medium |
| B16-17 | energy, ev-work, availability ([batch 16](batch-16/index.html); 88 pairs) | informational/no change |
| B17-X1 | ev-work-incidents, ev-work-maintenance, ev-action ([batch 17](batch-17/index.html); 84 pairs) | informational/no change |
| B17-01 | ev-work-incidents, ev-work-maintenance ([batch 17](batch-17/index.html); 84 pairs) | → B13-01 (merged duplicate) |
| B17-02 | ev-work-maintenance ([batch 17](batch-17/index.html); 84 pairs) | → B1-53 (merged duplicate) |
| B17-03 | ev-work-incidents, ev-work-maintenance ([batch 17](batch-17/index.html); 84 pairs) | → B13-04 (merged duplicate) |
| B17-04 | ev-action ([batch 17](batch-17/index.html); 84 pairs) | D3 R348 — W5-EV-Work — Low |
| B17-05 | ev-work-incidents, ev-work-maintenance ([batch 17](batch-17/index.html); 84 pairs) | → B1-53 (merged duplicate) |
| B17-06 | ev-action ([batch 17](batch-17/index.html); 84 pairs) | D3 R349 — W5-EV-Work — Low |
| B17-07 | ev-action ([batch 17](batch-17/index.html); 84 pairs) | R111 — verified built/resolved |
| B17-08 | link-check ([batch 17](batch-17/index.html); 84 pairs) | D3 R350 — W5-EV-Work — Low |
| B17-09 | ev-work-incidents, ev-work-maintenance, ev-action ([batch 17](batch-17/index.html); 84 pairs) | informational/no change |
| B17-10 | ev-work-incidents, ev-work-maintenance ([batch 17](batch-17/index.html); 84 pairs) | R112 — verified built/resolved |
| B17-11 | ev-work-incidents, ev-work-maintenance ([batch 17](batch-17/index.html); 84 pairs) | D4 R351 — open, visible MOCK DEVIATION D4 label required |
| B17-12 | ev-work-incidents, ev-work-maintenance, ev-action ([batch 17](batch-17/index.html); 84 pairs) | → B15-10 (merged duplicate) |
| B17-13 | ev-work-incidents, ev-work-maintenance, ev-action ([batch 17](batch-17/index.html); 84 pairs) | informational/no change |
| B17-14 | ev-work-incidents, ev-work-maintenance ([batch 17](batch-17/index.html); 84 pairs) | → B14-09 (merged duplicate) |
| B17-15 | ev-work-incidents, ev-work-maintenance ([batch 17](batch-17/index.html); 84 pairs) | → B16-16 (merged duplicate) |
| B17-16 | ev-work-incidents, ev-work-maintenance, ev-action ([batch 17](batch-17/index.html); 84 pairs) | informational/no change |
| B18-X1 | incidents, maintenance, maintenance-preventive, oprecords ([batch 18](batch-18/index.html); 186 pairs) | informational/no change |
| B18-01 | maintenance ([batch 18](batch-18/index.html); 186 pairs) | → B13-01 (merged duplicate) |
| B18-02 | maintenance ([batch 18](batch-18/index.html); 186 pairs) | → B1-53 (merged duplicate) |
| B18-03 | incidents, maintenance ([batch 18](batch-18/index.html); 186 pairs) | D3 R352 — W6-global-Work — Medium |
| B18-04 | incidents, maintenance, maintenance-preventive, oprecords ([batch 18](batch-18/index.html); 186 pairs) | D3 R353 — W6-global-Work — Medium |
| B18-05 | incidents, maintenance, oprecords ([batch 18](batch-18/index.html); 186 pairs) | D3 R354 — W6-global-Work — Low |
| B18-06 | maintenance ([batch 18](batch-18/index.html); 186 pairs) | D1 R355 — open, visible MOCK DEVIATION D1 label required |
| B18-07 | oprecords ([batch 18](batch-18/index.html); 186 pairs) | D3 R356 — W6-global-Work — Low |
| B18-08 | incidents ([batch 18](batch-18/index.html); 186 pairs) | D3 R357 — W6-global-Work — Low |
| B18-09 | incidents, maintenance ([batch 18](batch-18/index.html); 186 pairs) | D1 R358 — open, visible MOCK DEVIATION D1 label required |
| B18-10 | incidents ([batch 18](batch-18/index.html); 186 pairs) | D3 R359 — W6-global-Work — Low |
| B18-11 | incidents ([batch 18](batch-18/index.html); 186 pairs) | D3 R360 — W6-global-Work — Low |
| B18-12 | incidents, maintenance, maintenance-preventive, oprecords ([batch 18](batch-18/index.html); 186 pairs) | → B14-09 (merged duplicate) |
| B18-13 | incidents, maintenance, maintenance-preventive, oprecords ([batch 18](batch-18/index.html); 186 pairs) | D3 R361 — W6-global-Work — Low |
| B18-14 | oprecords ([batch 18](batch-18/index.html); 186 pairs) | D4 R362 — open, visible MOCK DEVIATION D4 label required |
| B18-15 | incidents, maintenance, maintenance-preventive, oprecords ([batch 18](batch-18/index.html); 186 pairs) | R12 — verified built/resolved |
| B18-16 | incidents, maintenance, maintenance-preventive, oprecords ([batch 18](batch-18/index.html); 186 pairs) | informational/no change |
| B18-17 | incidents, maintenance, maintenance-preventive, oprecords ([batch 18](batch-18/index.html); 186 pairs) | informational/no change |
| B18-18 | incidents, maintenance, maintenance-preventive, oprecords ([batch 18](batch-18/index.html); 186 pairs) | informational/no change |
| B19-X1 | wr-overview, wr-record, wr-history ([batch 19](batch-19/index.html); 194 pairs) | informational/no change |
| B19-01 | wr-overview, wr-record, wr-history ([batch 19](batch-19/index.html); 194 pairs) | informational/no change |
| B19-02 | wr-overview, wr-record, wr-history ([batch 19](batch-19/index.html); 194 pairs) | D2 R363 — open, visible MOCK DEVIATION D2 label required |
| B19-03 | wr-overview, wr-record, wr-history ([batch 19](batch-19/index.html); 194 pairs) | D3 R364 — W6-global-Work — Low |
| B19-04 | wr-overview, wr-record ([batch 19](batch-19/index.html); 194 pairs) | D1 R365 — open, visible MOCK DEVIATION D1 label required |
| B19-05 | wr-overview, wr-record, wr-history ([batch 19](batch-19/index.html); 194 pairs) | D3 R366 — W6-global-Work — Low |
| B19-06 | wr-overview ([batch 19](batch-19/index.html); 194 pairs) | → B1-53 (merged duplicate) |
| B19-07 | wr-overview, wr-record, wr-history ([batch 19](batch-19/index.html); 194 pairs) | D3 R367 — W6-global-Work — Low |
| B19-08 | wr-record ([batch 19](batch-19/index.html); 194 pairs) | D3 R368 — W6-global-Work — Low |
| B19-09 | wr-history ([batch 19](batch-19/index.html); 194 pairs) | D2 R369 — open, visible MOCK DEVIATION D2 label required |
| B19-10 | wr-overview, wr-record, wr-history ([batch 19](batch-19/index.html); 194 pairs) | D3 R370 — W6-global-Work — Low |
| B19-11 | wr-overview, wr-record, wr-history ([batch 19](batch-19/index.html); 194 pairs) | informational/no change |
| B19-12 | link-check ([batch 19](batch-19/index.html); 194 pairs) | D3 R371 — W6-global-Work — Low |
| B19-13 | wr-overview, wr-record, wr-history ([batch 19](batch-19/index.html); 194 pairs) | D3 R372 — W6-global-Work — Low |
| B19-14 | link-check ([batch 19](batch-19/index.html); 194 pairs) | → B13-01 (merged duplicate) |
| B19-15 | wr-overview, wr-record, wr-history ([batch 19](batch-19/index.html); 194 pairs) | D3 R373 — W6-global-Work — High |
| B19-16 | wr-overview, wr-record, wr-history ([batch 19](batch-19/index.html); 194 pairs) | informational/no change |
| B19-17 | wr-overview, wr-record, wr-history ([batch 19](batch-19/index.html); 194 pairs) | → B4-03 (merged duplicate) |
| B19-18 | wr-overview, wr-record, wr-history ([batch 19](batch-19/index.html); 194 pairs) | informational/no change |
