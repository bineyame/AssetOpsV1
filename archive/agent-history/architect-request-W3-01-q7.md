# Architect request: W3-01 q7-1 (watermark clamp selects nothing)

Read:
- `.agent/W3-01-build-spec.md`: "Run 6 rulings (q6)", Blocker 1, which clamps `:k` to the latest committed evidence watermark;
- `.agent/W4-01-build-spec.md` q3 ruling 6;
- `.agent/W3-01-pending-rulings.md` Q7-1.

The code is at `f8ca78d1`: commit `4442d33c`'s `_snapshot(..., selection_cutoff=..., selection_seqs=...)`.

Analytic run selections are written after the last evidence they cover, so clamping the selection cutoff to the evidence watermark selects nothing. Rule the exact predicate, in literal SQL terms:
- which cutoff applies to `analytic_run_selection.selected_at`, `analytic_run.knowledge_cutoff` / `completed_at` and `assessment_revision.created_at`;
- which cutoff applies to the evidence/watermark side;
- what `known_at` the wire reports.

Give the test that proves a historical cutoff still excludes a later reselection. Keep the W4 link-coverage use consistent.

Append the result as "Run 7 rulings (q7)" to `.agent/W3-01-build-spec.md`, and add a one-line cross-reference in `.agent/W4-01-build-spec.md` if it changes how W4 uses the API. Write nothing else. Do not commit.
