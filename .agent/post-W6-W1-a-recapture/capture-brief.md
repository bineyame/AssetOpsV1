# post-W6 W1-a recapture: brief for the capture agent

Worktree `C:\Users\assef\Bineyame\AssetOpsV1-review4`, branch `task/post-W6-W1-a`. Capture the CURRENT HEAD
(record `git rev-parse --short HEAD`). Rulings: `.agent/post-W6-W1-rulings.md` cross-card 4-5 and Q37-Q43.

## What to capture
`.agent/post-W6-W1-a-recapture/selection.json` lists 98 pairs: 88 indexed pairs of the seven W1-a screens (`mini`,
`evidence-analysis`, `dispatch`, `finding`, `finding-evidence`, `finding-history`, `sitefindings`) and 10 Q40
representative pairs (`alternatives`, `opportunity-finding`, `recommendation`, `cold-finding`, `ev-finding`). Fields:
`batch, screen, case, width, route, producer, frozen_app, frozen_titles, frozen_heights`. `frozen_app`
(`batch-NN/<part>/...png`) names the frozen part folder, so it names the producer mode and capture targets.

## How (same method as `.agent/post-W6-shell-recapture/capture-brief.md`)
- Read only what you need of each frozen batch: `.agent/post-W6-audit/batch-NN/batch-NN.md` (the "Frozen run" and
  producer sections), its capture script (`capture-bNN.mjs`), the `targets-*.json` files and the launch helpers.
  The shell recapture's `batch-02`, `batch-03`, `batch-04`, `batch-06`, `batch-08` and `batch-13` `run.md` files show
  the working commands. Run the SAME producers, unmodified, in the same modes. Build filtered targets files that
  hold only the selected cases.
- Reuse the capture script unchanged, except for the filtered targets file. Add no seeding, clicks or data.
- Start Vite from THIS worktree's `frontend/`, which holds the current code.
- Output goes to `.agent/post-W6-W1-a-recapture/batch-NN/<part>/`: screenshots plus the script's `evidence.json`
  (set `AUDIT_REVISION=<HEAD sha>`). Mock screenshots are not needed.
- For every captured pair, record the panel titles, each panel's closed height, and `scrollWidth - clientWidth`
  (overflow). The script's evidence.json normally carries these. If it does not, add them through a post-capture
  measurement step in a separate script, never by editing product code. Measure these panels by title:
  - `finding`: "What happened", "What limits this conclusion", "Where to look next";
  - `finding-history`: "Revision history";
  - `dispatch`: the Selected-block panel (its title starts "Selected block");
  - `evidence-analysis`: "How each limit is set" and "Accepted records behind the conclusions".
- Write `.agent/post-W6-W1-a-recapture/batch-NN/run.md` (at most 25 lines). Record the producer commands, DB names,
  ports, the SHA, the pair count captured against the count selected, and every case that could not be produced, with
  the reason. That is a capture gap; never fabricate one.

## Hard rules
- Do not edit product code or tests. Captures are capture-only. Data comes only from reviewed producer modes.
- DBs live only in container `assetopsv1-postgres-1`. You may create and drop `assetops_w1arc_bNN*_test`. A producer's
  own prefix plus `_audit` is allowed only through that producer's own modes. Check `pg_database` first. If an
  `_audit` DB already exists, another agent owns it: wait, or use a `_test` name if the producer accepts one. Never
  touch any other DB. Drop every DB you create.
- Ports: API 18121-18127, Vite 5183, CDP 9523 (`ASSETOPS_CDP_PORT=9523`).
  - Another agent is recapturing shell pairs now, on 18101-18109, 5181 and 9521. Never use 189xx, 5189 or 8971-8977.
  - Check every port with `netstat -ano | grep LISTEN` before you use it. A hard-coded producer port that is busy
    means wait, or use the producer's documented override.
  - Stop only the PIDs you spawned, by PID. At the end, confirm that none of your ports still listen.
- Do not run full vitest, `vite build` or backend suites. Do not commit.
- If the permission system blocks a step, do not work around it. Record the exact refusal as a capture gap.
- Be token-efficient: bounded reads, and trimmed logs written to files.
