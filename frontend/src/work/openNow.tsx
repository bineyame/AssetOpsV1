/**
 * OPEN-NOW: the line above each Work list that names what is open now, whatever the dates
 * (`.agent/architect-sequence-client-scope-2026-11-11.md`, card OPEN-NOW). The Work pages open on the last 7 full
 * days, so an older open item is outside the list; this line keeps it in view. The server writes the sentence
 * (`backend/assetops_backend/work/open_now.py`); the page never composes it from raw codes.
 */

/** The `open_now` object on the global and Site Work list responses (incidents and maintenance lists). */
export interface OpenNow {
  incidents: number;
  requests: number;
  line: string;
}

export function isOpenNow(value: unknown): value is OpenNow {
  if (typeof value !== "object" || value === null) return false;
  const v = value as Record<string, unknown>;
  return typeof v.incidents === "number" && typeof v.requests === "number" && typeof v.line === "string" && v.line !== "";
}

/** Renders nothing when the response carries no usable `open_now` (an older server, or a malformed value). */
export function OpenNowLine({ openNow }: { openNow: unknown }) {
  if (!isOpenNow(openNow)) return null;
  const nothing = openNow.incidents === 0 && openNow.requests === 0;
  return (
    <p className="work-open-now" data-work-open-now={nothing ? "none" : "some"}>
      {openNow.line}
    </p>
  );
}
