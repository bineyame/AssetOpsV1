/**
 * The estate Findings words that outlived the lens roots. IA-P P2 (spec §5.2) retired the four lens tables: the
 * Findings list is `estate/homeLists.tsx` on the home-list component, and `/findings/cost|risks|opportunities` are
 * aliases of its `lens` facet. What stays here is reused: the consequence words, the lifecycle words and the
 * `findingLinkLive` rule (Post-W6 W3-estate Q4, R297; I8).
 */
import {
  type EstateConsequence,
  type EstateFindingRow,
  type EstateLens,
  type EstateLifecycle,
  type EstateStateFilter,
} from "./estateClient";
import { linkFor } from "../shell/operatorSiteRoutes";
import { utcInstant } from "./estateShared";

/** The four estate Finding lens routes (Lane A mounts them; this page links between them). */
export const ESTATE_FINDING_LENS_PATHS: Readonly<Record<EstateLens, string>> = {
  all: "/findings",
  cost: "/findings/cost",
  risks: "/findings/risks",
  opportunities: "/findings/opportunities",
};

export const LIFECYCLE_WORDS: Readonly<Record<EstateLifecycle, { text: string; tone: string; filter: EstateStateFilter }>> = {
  SUPPORTED: { text: "Confirmed", tone: "blue", filter: "supported" },
  UNCONFIRMED: { text: "Not yet confirmed", tone: "amber", filter: "unconfirmed" },
  NO_LONGER_SUPPORTED: { text: "No longer applies", tone: "neutral", filter: "no_longer_supported" },
  MERGED: { text: "Combined with another", tone: "neutral", filter: "merged" },
};

/**
 * The Main consequence cell (Run 6 Blocker 2, Run 8 rulings 3-4): a PRICED row shows its stored interval, never a
 * sum or point estimate; a withheld amount on a historical basis says `Historical as of {known_at}`; another
 * withheld amount says `Source not checked`; a stored unpriced row says `Unpriced`; no row says `No consequence
 * recorded`.
 */
export function consequenceWords(consequence: EstateConsequence, rowStatus: string, knownAt: string): string {
  if (consequence.state === "PRICED" && consequence.amount_low !== null && consequence.amount_high !== null) {
    return `${consequence.amount_low}–${consequence.amount_high} ${consequence.currency ?? ""}`.trim();
  }
  // COV-PARTIAL MOCK DEVIATION R622: a row of a Site with incomplete days never shows an amount (the backend sends
  // none). PF-W (D-E5.46): "incomplete days", never "checked".
  if (rowStatus === "PARTIAL") {
    return consequence.source_revision_id === null ? "No consequence recorded" : consequence.state === "UNPRICED" ? "Unpriced" : "Value not shown while this site has incomplete days";
  }
  if (consequence.source_revision_id === null) return "No consequence recorded";
  if (consequence.state === "UNPRICED") return "Unpriced";
  if (rowStatus === "HISTORICAL") return `Historical as of ${utcInstant(knownAt)}`;
  return "Source not checked";
}

/**
 * Post-W6 W3-estate Q4 (R297): whether a row's Finding title is live. A mini-grid row links its exact revision
 * link. A cold or EV row is live only when the server sends a provable row-local windowed link (one carrying its
 * own `from`, `to` and `known_at`; the server otherwise sends `null`); a null, absent or unwindowed link leaves the title inert with a labelled unavailable detail.
 */
export function findingLinkLive(row: Pick<EstateFindingRow, "link_refs" | "site_id">, miniGridIds: ReadonlySet<string>): boolean {
  // CH5a2-R4(c): the gate reads the Ref sibling, never the legacy href text.
  const ref = row.link_refs?.finding;
  // DIESEL-1-R3p: an unexplained-fuel Finding opens its own page (one address, no window or revision to prove).
  if (ref?.kind === "FUEL_FINDING") return Boolean(linkFor(ref));
  if (!ref || ref.kind !== "FINDING" || !linkFor(ref)) return false;
  if (miniGridIds.has(row.site_id)) return true;
  const w = ref.window;
  return Boolean(w?.from && w.to && w.known_at);
}

export const FINDING_DETAIL_UNAVAILABLE = "Finding detail unavailable";

