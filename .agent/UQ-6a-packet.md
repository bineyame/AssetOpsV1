# UQ-6a review packet: server message seam (English only)

Card: A5 in `.agent/architect-sequence-client-scope-2026-11-11.md`; spec UQ-6a row and §4.3 D-I18N.1/D-I18N.2 in
`.agent/architect-plan-pre-client-2026-11-10.md`. Branch `task/UQ-6a-message-seam`, worktree `AssetOpsV1-uq6a`.

## Delivered
- `backend/assetops_backend/i18n/` (new):
  - `messages.py`: `Message` = `{key, params}` (TypedDict, params `str|int|float`), `message(key, **params)`,
    `CATALOGUE` (`en` only, one key so far).
  - `render.py`: `render(msg, locale=None)`: template for the locale, else `en`; params via `format_map`
    (inserted verbatim); unknown key raises `KeyError`; locale defaults to the request locale.
  - `locale.py`: `resolve(Accept-Language)` by q-value then header order, primary subtag, against `SUPPORTED`
    (`("en",)` per D-I18N.3); else `en`. `LocaleMiddleware` (pure ASGI) sets a context var for the request and adds
    `Content-Language` to every response the app answers (not an unhandled 500; see Residual risk). Outside a request (pre-build, tick) the locale is `en`.
- `chain/response_store.py`: `request_key(..., locale="en")` always includes `"locale"`; `StoredRoute.locale`
  defaults to `current_locale()` at construction (inside the request); lookup and insert use it (D-I18N.2).
- `main.py`: `create_app` adds `LocaleMiddleware`.
- Reference user: `analytics_api.py` SITE_NOT_FOUND message (the smallest composed server sentence) now
  `render(message("analytics.site_not_found", site_id=...))`.

## Demo store compatibility
`chain/prebuild.py` sends its requests through an in-process `TestClient` with no `Accept-Language` -> `en`; a
browser `en-US,en;q=0.9` (or any header, since only `en` is offered) -> `en`: same key, same stored row. Test
`test_a_request_with_no_or_english_accept_language_hits_the_prebuilt_row` stores with no header, then gets `hit`
with identical bytes for `en`, `en-US,en;q=0.9`, `en-GB`, `sw`, `*`, one compose, one distinct lookup key.
Existing `chain_response` rows are not reused across this merge anyway: `code_version` hashes the source files, so
any code change re-keys them; the next pre-build rewrites them under the new key.

## Acceptance (card tests)
- render of `{key, params}`: PASS (`test_render_*`).
- unknown locale falls back to `en`: PASS (render with `xx`; resolution of `sw`, `fr-FR`, `*`, malformed).
- cache key differs by locale: PASS (`test_the_store_key_differs_by_locale`, `test_a_second_locale_is_stored_under_its_own_key`).
- `Content-Language` header: PASS (sync + async routes, product app `/api/health`).
- converted body byte-equal in English: PASS, `b'{"detail":{"code":"SITE_NOT_FOUND","message":"No Site kobo-1 is configured."}}'`.

## Checks (revision 5683d7231 code; packet commit after)
- Tests-first: `test_uq6a_message_seam.py` failed at collection before the code (no `i18n` module).
- `test_uq6a_message_seam.py` 31 passed; `test_ch5c_response_store_postgres.py` 8 passed;
  `test_ch5c2_store_safety_postgres.py` 10 passed; `test_ch5c_store_off.py` 17 passed; `test_ch5b_why.py` 48 passed;
  `test_ch5c2_clock_guard.py` 8 passed; `test_health.py` 4 passed; `test_sites_api.py` 62 passed.
  DB base `assetops_uq6a_test` (created for this slice).
- `test_ch5c2_real_composers_postgres.py` (env var set on every run): NOT VERIFIED GREEN. These failures are not
  caused by this branch. Every failure seen is `FATAL: sorry, too many clients already`: a 503
  `SITE_STORE_UNAVAILABLE` or a fixture connect. None is an assertion on keys, bodies or the module list.
  - f6_summary + f4_no_unlisted alone on the branch: 2 passed.
  - A/B: the file's connections on its case DB `assetops_out_ch5c2_guardrail_test` climb over the run with the
    middleware (sampled peak 86) and **without it** (`add_middleware` line removed: peak 73+). Both runs fail the same
    way once the server total reaches 200. `assetops_polish_client6_test` held 71-115 of those connections.
  - `request_key` adds a JSON field and opens nothing, so the climb is pre-existing. The case DB name is fixed: two
    concurrent runs of this file (e.g. the coordinator's and mine) share and drop the same DB.
  - Rerun on a quiet server.
- `tools\check-architecture.ps1` (ASSETOPS_GUARD_PYTHON = plan2 venv): "Architecture check passed."

## Known deviations
- No Pre-flight named the smallest body; picked analytics SITE_NOT_FOUND.
- The slice commit message was passed by heredoc (rule breach in process, not in content).

## Residual risk
- `real_composers` unverified (above).
- `Content-Language` is on every response the app itself answers: 2xx, 304, and `HTTPException` 4xx/5xx. It is NOT
  on an unhandled-exception 500. Starlette's `ServerErrorMiddleware` is always outermost, so it builds that 500
  outside `LocaleMiddleware` (review Low, claim corrected rather than adding an error handler).
- Out of scope, as the card says: catalogue move (UQ-6b), Babel formatting (UQ-4).

USER_REVIEW: not required (server seam, no UI change); Reviewer review then merge before AR-1.
