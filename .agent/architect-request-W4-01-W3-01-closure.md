# Architect request: close the W4-01 and W3-01 spec review

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`, in full;
- `.agent/post-W2-sequence.md`;
- `.agent/W4-01-build-spec.md` and `.agent/W3-01-build-spec.md`, with their packets in `tasks/`;
- `.agent/W4-01-W3-01-spec-review.md`, an independent implementer dry-read with 66 questions and 7 points on the provenance decision.

## Your task

Verify every claim in the review against the merged code on main and the v69 mock. Then answer **every** item (Blocker, Should and Nit) with concrete artifacts:
- literal JSON, column lists, SQL, state and mapping tables, copy, fixture contents, test names;
- or a correction, where the review is wrong — state why, with file:line.

## Specific corrections to make

- **W3-01:**
  - reconcile it with the real Finding and Action state vocabularies and the existing `/findings` and `/api/findings` routes;
  - decide what the Site lens chips do.
- **Shared provenance DTO:** make the change non-breaking for the roughly 21 W1 consumers. Give either a compatibility field or a same-commit consumer migration, with exact file lists. Also say which lane owns it, and when.
- **W4-01:**
  - fix the fixture Site codes: the real ones are COLD-LAB-001, KOBO-001 and EV-LAB-001. Avoid the W5-02-owned Work tab;
  - complete the migration columns and the list and detail JSON.

## Output

Amend each build spec in place where text is wrong, and append "Review closure (2026-10-20)" to each. Amend the `D-2026-10-20-*` decisions as needed. After closure, no question in the review may remain open; end each spec's closure with a one-line statement that this is so.

Write only those files. Do not commit.
