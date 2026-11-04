/**
 * CH-5a2a test helper: the `link_refs` sibling of a hand-written fixture `links` dict (CH5a2-R4(c)).
 *
 * The client renders links only from Refs, so a fixture written with legacy hrefs needs the Ref of each one.
 * `refOfHref` reads the few fixture shapes and refuses anything else; every Ref it returns must route back to the
 * exact same text through `routeFor`, so a fixture whose href the shared builder would not emit fails loudly
 * instead of passing on a guessed Ref. Product code never parses an href; this is test-only.
 */
import { routeFor, type Ref, type RefWindow } from "../shell/operatorSiteRoutes";

const seg = (s: string) => decodeURIComponent(s);

function windowOf(q: URLSearchParams): RefWindow | undefined {
  const from = q.get("from");
  const to = q.get("to");
  if (!from || !to) return undefined;
  const known = q.get("known_at");
  return known ? { from, to, known_at: known } : { from, to };
}

function parse(href: string): Ref | null {
  const [path, query = ""] = href.split("?", 2);
  const q = new URLSearchParams(query);
  let m: RegExpMatchArray | null;
  if ((m = path.match(/^\/sites\/([^/]+)$/))) return { kind: "SITE", site: seg(m[1]) };
  if ((m = path.match(/^\/sites\/([^/]+)\/ev$/))) return { kind: "SITE", site: seg(m[1]), view: "ev" };
  if ((m = path.match(/^\/sites\/([^/]+)\/findings\/([^/]+)$/))) {
    const window = windowOf(q);
    if (window) return { kind: "FINDING", site: seg(m[1]), id: seg(m[2]), window };
    const revision = q.get("revision_id") ?? undefined;
    return { kind: "FINDING", site: seg(m[1]), id: seg(m[2]), ...(revision ? { revision } : {}) };
  }
  if ((m = path.match(/^\/sites\/([^/]+)\/actions\/([^/]+)(?:\/(verification|plan|history))?$/))) {
    const event = q.get("event_id") ?? undefined;
    const view = m[3] as "verification" | "plan" | "history" | undefined;
    return { kind: "ACTION", site: seg(m[1]), id: seg(m[2]), ...(view ? { view } : {}), ...(event ? { event_id: event } : {}) };
  }
  if ((m = path.match(/^\/sites\/([^/]+)\/performance\/([^/]+)$/))) {
    const window = windowOf(q);
    return { kind: "EVIDENCE", site: seg(m[1]), capability: seg(m[2]), ...(window ? { window } : {}) };
  }
  return null;
}

/** The Ref whose `routeFor` is exactly `href`; throws for an unsupported or non-round-tripping fixture href. */
export function refOfHref(href: string): Ref {
  const ref = parse(href);
  if (!ref) throw new Error(`linkRefs: unsupported fixture href ${href}`);
  const back = routeFor(ref);
  if (back !== href) throw new Error(`linkRefs: fixture href ${href} is not what the shared builder emits (${back})`);
  return ref;
}

/** `row` with `link_refs` set from its `links` (same keys; a null href is a null Ref). */
export function withLinkRefs<T extends { links: Record<string, string | null> }>(row: T): T {
  const link_refs: Record<string, Ref | null> = {};
  for (const [key, href] of Object.entries(row.links)) {
    if (key.endsWith("_label")) continue;
    link_refs[key] = href === null ? null : refOfHref(href);
  }
  return { ...row, link_refs };
}
