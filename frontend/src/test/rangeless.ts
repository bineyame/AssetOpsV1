/**
 * SR-4a (architect rev 8 §8.3 "compare the path part, as SR-2 did"): Site links and Site addresses now carry the shared
 * range (`RangeLink`, the shell's safety net). A test whose subject is not the range compares an href or address with
 * the range parameters (`from`, `to`, `known_at`) taken out; every other parameter keeps its order.
 */
const RANGE_KEYS = new Set(["from", "to", "known_at"]);

/** `rangeless` over a value: a string is stripped, an array element by element; anything else is returned as it is. */
export function rangeless<T>(value: T): T;
export function rangeless(value: unknown): unknown {
  if (typeof value === "string") return rangelessHref(value);
  if (Array.isArray(value)) return value.map((item) => rangeless(item));
  return value;
}

function rangelessHref(href: string): string {
  const hashAt = href.indexOf("#");
  const head = hashAt < 0 ? href : href.slice(0, hashAt);
  const hash = hashAt < 0 ? "" : href.slice(hashAt);
  const queryAt = head.indexOf("?");
  if (queryAt < 0) return href;
  const kept = head
    .slice(queryAt + 1)
    .split("&")
    .filter((pair) => pair !== "" && !RANGE_KEYS.has(decodeURIComponent(pair.split("=", 1)[0])));
  return `${head.slice(0, queryAt)}${kept.length ? `?${kept.join("&")}` : ""}${hash}`;
}
