# Architect request: W2-07 concrete-artifact closure, before any build

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`, sections "Mockup drives the design; implementers never decide" and the implementer dry-read;
- `tasks/W2-07-ev-site-evidence-money.md`;
- `.agent/W2-07-build-spec.md`, including its Pre-build closure;
- `.agent/W2-technical-design-ev.md`;
- the W2-06 build spec, all rulings including q1/q2. W2-07 consumes W2-06's tables, reads and column values;
- the W2-04 cold Site/evidence/money spec and its Run 8/Run 9 rulings, plus its code on main. These are the analogue.

The v69 EV mock screens are authoritative: every panel, row, column, chip and label.

**Lesson.** On W2-05b and W2-06, prose closures still left 10–15 questions per commit. One prose closure, then a second, both left W2-06's commit 2 blocked. So for W2-07, write concrete artifacts that the builder copies:

1. **Migration `0026`.** The exact table, column, type, nullability, CHECK, index and downgrade text, written as the migration body. Also list the existing tests whose head or constraint counts change.
2. **Every selected read.** The exact response JSON example for stocked, empty, refused and pending states, with every key and literal, plus a field-by-field derivation table.
3. **The gross tariff scenario.** The exact formula, rounding, currency and representation, with a worked numeric example from the W2-05b six cases.
4. **The five v69 routes.** For each route:
   - the ordered panel list;
   - closed-panel content and disclosure content, with exact labels;
   - column widths, wrapping and nowrap rules;
   - the per-panel height budget against the measured mock heights (ceiling 1.3x);
   - chip tones, using the W2-04 Run 9 M5 tokens with EV values;
   - null and link copy;
   - every visible string next to the response field that feeds it.
5. **Test vectors and fixtures.** The fixture content and expected values the tests assert.

Append the result to `.agent/W2-07-build-spec.md` as "Concrete-artifact closure (2026-10-19)". Write nothing else. Do not commit.
