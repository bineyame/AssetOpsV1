/**
 * INFRA-1 (D-E5.47 rule 4): a stored route that could not read its data answers 503 `TEMPORARILY_UNAVAILABLE`.
 * The board and summary fetches retry it after 2, 4 and 8 s, showing "Temporarily unavailable. Retrying…" while
 * they wait and "Still unavailable. Refresh to try again." after the last attempt. It is never rendered as a data
 * state (Unknown, PARTIAL, "No target set yet").
 */
export const TEMPORARILY_UNAVAILABLE = "TEMPORARILY_UNAVAILABLE";
export const RETRYING_COPY = "Temporarily unavailable. Retrying…";
export const STILL_UNAVAILABLE_COPY = "Still unavailable. Refresh to try again.";
export const RETRY_DELAYS_MS: readonly number[] = [2000, 4000, 8000];

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** True for the 503 whose body (top-level or under `detail`) carries `code: TEMPORARILY_UNAVAILABLE`. */
export function isTemporarilyUnavailable(status: number, body: unknown): boolean {
  if (status !== 503 || !isObject(body)) return false;
  const detail = isObject(body.detail) ? body.detail : body;
  return detail.code === TEMPORARILY_UNAVAILABLE || body.code === TEMPORARILY_UNAVAILABLE;
}

const wait = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

/**
 * `fetch(path)` and its JSON body, retried after each of `delays` while the answer is 503 `TEMPORARILY_UNAVAILABLE`;
 * `onRetrying` is told before each wait; returning `false` (the caller is gone) stops the retries. A network failure throws, as `fetch` does; an unreadable body is null.
 */
export async function fetchRetrying(
  path: string,
  onRetrying?: () => void | boolean,
  delays: readonly number[] = RETRY_DELAYS_MS,
  /** SR-5b: a route whose own 503 code also means "try again" (`SITE_RANGE_OVERVIEW_UNAVAILABLE`) widens this. */
  retryable: (status: number, body: unknown) => boolean = isTemporarilyUnavailable,
): Promise<{ response: Response; body: unknown }> {
  for (let attempt = 0; ; attempt += 1) {
    const response = await fetch(path, { headers: { Accept: "application/json" } });
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      body = null;
    }
    if (!retryable(response.status, body) || attempt >= delays.length) return { response, body };
    if (onRetrying?.() === false) return { response, body }; // the caller unmounted: no further attempts
    await wait(delays[attempt]);
  }
}
