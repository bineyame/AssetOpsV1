# S6-01 — Action and controlled policy change

Status: implementation-ready as two bounded slices
Planner: Codex, 2026-10-15

- [S6-01a — Action store, controlled application and exact read](S6-01a-action-store-read.md): non-UI, independently reviewable and mergeable on main only after persisted Action/event/application proof and exact S6-01b consumer API. `USER_REVIEW_REQUIRED: false` while no UI or owner-facing copy changes.
- [S6-01b — Action, recommendation and change surfaces](S6-01b-action-ui.md): UI, `USER_REVIEW_REQUIRED: true`, held for owner walkthrough and acceptance.

The last phase review of each packet is its slice review. `I-S6-01` and its W1 panels close only after S6-01b. S5-01 is queue order, not an implementation dependency. S6-02 owns verification and S6-03 owns Site ActionIndex/Work list.
