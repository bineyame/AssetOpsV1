# Architect request: W5-02a core review M1 and L1

You are the AssetOps Architect (Codex). Read the review with `MSYS_NO_PATHCONV=1 git show task/W5-02a-cold-action-root:.agent/W5-02a-core-review.md`, then the K1c card and rulings in `.agent/W5-02-build-spec.md`.

1. **M1.** The backend now sends linked domain Actions with `action_event_id: null` (`backend/assetops_backend/work/detail.py:75`), but the W6 request-detail validator requires a string (`frontend/src/work/globalWorkClient.ts:439`), and line 531 turns that into a false "store unavailable". Choose one:
   - (a) allow null in the validator, with a test, adding `globalWorkClient.ts` and its test to K1c; this is the reviewer's preference;
   - (b) keep detail `action_links` W1-only.

   Give the literal change and test.
2. **L1.** Three test cases named in the K1 rulings are missing:
   - an operational record, or another case's or Site's maintenance record → 422;
   - retrying the original link after the case advances → 200;
   - an absent Action plus an invalid link → 404.

   Confirm they belong in K1c, with literal test names.

Append "W5-02a build rulings (core review M1/L1)" to `.agent/W5-02-build-spec.md`. Write nothing else. Do not commit. End your output with one line per item.
