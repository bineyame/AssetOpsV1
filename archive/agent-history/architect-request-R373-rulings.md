# Architect request: R373 pre-flight rulings

You are the AssetOps Architect. Read `.agent/post-W6-R373-preflight.md`: the builder's 8 questions with recommended defaults for the security D3 R373 (audit B19-15). Also read your ruling "B19-15 access" in `.agent/post-W6-audit/fix-slices.md` and the code it cites (`backend/.../main.py` around 555-585, `global_work_api.py`, the WorkGate).

Write `.agent/post-W6-R373-rulings.md` with one numbered ruling per question (Q1–Q8). Each ruling is accept-default or a stated alternative, with exact names, files, response codes, copy, tests and the merge proof. You must also decide:
- **Scope.** Should R373 include the four global list routes? The builder found they share the gap. Should the estate roots and other Site routes that are wired the same way be fixed here, or get their own register row and slice? Assign the row ID if new.
- **Denied-read response.** Choose 403 `SITE_SCOPE_FORBIDDEN` with a byte-identical body or 404, considering existence leakage and the W4 impact.
- **Frontend copy.** Rule on the change, or keep the slice backend-only.

Keep it tight. Do not edit product code.
