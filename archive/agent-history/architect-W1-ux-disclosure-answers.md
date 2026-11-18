# W1-UX disclosure scan - Architect answer (2026-10-16)

Decision: `D-2026-10-16-w1-ux-disclosure`. Accept the W1-UX-01 amendment, with the precise scan boundary below. This refines `D-2026-10-04-plain-language-analysis-views` for the small closed "How this was worked out" disclosure only. The broader W1 vocabulary guard still applies to the default reading and to Analysis/Evidence prose. No task packet or code change is made here.

## Disclosure boundary

Scan every rendered text node and accessible name in the disclosure, including its closed summary. The narrower disclosure-prose ban is exactly:

- Internal analytics phrases: `claim ceiling`, `claim limit`, `basis fingerprint`, `basis digest`, `typed reason`, `analytic declaration`, `read model`.
- Implementation words when used for AssetOps mechanics: `run`, `runs`, `rerun`, `runtime`, `binding`, `stage`, `staged envelope`, `commit`, `committed`, `fixture`, `payload`, `backend`, `frontend`, `projection`, `replay`, `ingest`, `ingested`, `ingestion`, `normalization`, `normalized`. Ordinary operational uses, such as "the generator ran", are permitted.
- Raw state/outcome labels in prose: `CURRENT`, `STALE`, `UNKNOWN`, `UNASSESSED`, `PENDING`, `PENDING_REASSESSMENT`, `STALE_PROJECTION`, `FAILED`, `REFUSED`, `WITHDRAWN`, `INCONCLUSIVE`, `INEFFECTIVE`, `VERIFIED`, `GUARDRAIL_FAIL`, `NO_FINDING`, `NOT_ASSESSED`, and any other raw uppercase underscore status or reason token. These are code forms, not a ban on ordinary lower-case words.

The disclosure may contain a few **individually labelled exact values** needed to trace a result: source/record IDs, UUIDs, digests, rule or model versions, exact references and raw reason codes. A plain label explains what each value identifies. Each value gets the existing single-value reference treatment or one of the existing eligible single-value exemptions; the label and surrounding prose remain scanned. Do not exempt a container, disclosure, screen or API response. A raw code must never enter the closed summary or its accessible name. Source-owned/user-owned names and Lab entries retain only their existing narrowly scoped exceptions.

The disclosure is supplementary. Plain state, material limitations, scope and the "as of" bound remain visible beside the headline while it is closed. Method, coverage, calculation, comparison and evidence trail belong in the owning contextual destination. A labelled exact value does not authorize a technical explanation in the disclosure.

## Raw-code detection for W1-UX-01

Use case-sensitive matching for raw code shapes and case-sensitive entries for single-word enum labels. The shape matcher targets uppercase underscore tokens; it must not treat ordinary words, units or acronyms as codes. In particular, `SOC`, `UTC`, `kW`, `kWh` and `PV` must not be flagged by raw-code detection. An independently applicable prose/gloss rule may still require an explanation of an acronym in the default reading. Test both leaked codes and those five non-code examples. Labelled exact values are removed from the text being checked only at their individual value positions; the remaining prose is checked.

This is an Architect scan ruling, not owner acceptance or a review verdict. The W1 combined owner walkthrough remains required.
