# W5-02c K4: question for the Architect (ruling contradicts merged code)

Branch `task/W5-02c-K4-cold-action`. Raised while building K4b; everything else in K4a/K4b/K5 is built.

## Q1. Ruling 12 versus merged K3 ruling 20: one-line UUIDs inside `UTC and IDs`

**Ruling 12** (`.agent/W5-02c-K4-preflight-rulings.md`): restrict `contain:inline-size; overflow-x:auto` and the
capture's `openBodyFits` relaxation to disclosure bodies with a direct `code` child. "Other disclosure bodies must
wrap and pass containment."

**Merged K3 ruling 20 (M2)** (`.agent/W5-02-build-spec.md` K3 rulings; K3 handoff "rulings 17-22"): an opened
`UTC and IDs` **or** `Finding version` body keeps each 36-character UUID on one line and scrolls inside its cell. The
K3 capture enforces it with the claim `every opened UUID is one line and fully reachable in its body without widening
the cell (ruling 20)` (`tools/w502-cold-work-evidence.mjs`, `worstcase-every-disclosure` states).

**Conflict.** The `UTC and IDs` body has no direct `code` child: its UUIDs sit inside a `FactList`
(`dl > dd > code`, `frontend/src/sites/siteWorkCases.tsx:451-466`). Under ruling 12 that body must wrap, so its UUIDs
break across lines. Built literally (commits `ace6f269`, `7c2fb351`), the K3 recheck capture at tree `5db28f19` +
capture fix gives **930 PASS, 4 FAIL**. All four failures are that ruling-20 claim, in
`incidents|maintenance-worstcase-every-disclosure` at 1440 and 390. The UUIDs wrap to 2 lines (1440) or 2-3 lines
(390). They are fully reachable, the cell still fits, and there is no document overflow. Every other case claim
passes, including containment of the wrapped bodies. Evidence: `.agent/W5-02c-K4-evidence/cases-recheck/`.

The K4 `cold-action` strip is unaffected. Its `Finding version` body has a direct `code` child and passes
(`.agent/W5-02c-K4-evidence/w502c-k4-measurements.json`, 292/292).

**Options**
- (a) Keep ruling 12 as built. The `UTC and IDs` UUIDs wrap inside their cell, and the K3 one-line claim is narrowed
  to direct-code bodies (`Finding version`). This is a capture-tool edit only.
- (b) Keep one-line UUIDs everywhere. Give the fact value that holds a direct `code`
  (`.fact-list__value:has(> code)`) the same `contain:inline-size; overflow-x:auto`, and scope the capture
  relaxation to that code container. The `UTC and IDs` body itself still wraps its non-code text, and the K3 claim
  stays as it is.
- (c) Revert the case-cell narrowing to the merged K3 rule, and apply ruling 12 only to the Action strip.

No choice was made. The tree implements ruling 12 as written, and the four failing claims are reported, not edited.
