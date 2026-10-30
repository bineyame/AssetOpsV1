/**
 * W3-03 run 2: the Portfolio page's literal copy (`.agent/W3-03-build-spec.md` mock ledger as amended by closures
 * 1-5, r1a, r1b, r1b2 and r1b4). The page never invents a value: every slot without a reviewed source keeps its
 * mock position and says so.
 */
import type {
  EstateDomain,
  EstatePortfolioBody,
  EstatePortfolioExclusion,
  EstatePortfolioStatus,
  EstateSiteState,
  EstateValueCardKey,
} from "./estateClient";
import { hasReasonWord, reasonText } from "./estateFinancialsWords";

export const PORTFOLIO_PATH = "/portfolio";
export const PORTFOLIO_TITLE = "Portfolio Value & Operations";
export const PORTFOLIO_SUBTITLE = "Operating decisions across the estate: cost, service, productive use and asset value";
export const PORTFOLIO_PAGE_SIZE = 50;

export const PRIORITY_PANEL = "Where management should act first";
/**
 * CC-R2-Q3 ruling. MOCK DEVIATION: v69 (`index.html:133`) says "ranked by consequence and urgency"; groups are not a
 * value ranking (the placement policy footer says so).
 */
export const PRIORITY_SUBTITLE =
  "Selected Findings across accessible Sites, grouped by where to look first, with evidence confidence alongside.";
/** CC-R2-Q3 ruling. MOCK DEVIATION: v69 (`index.html:135`) says "Priority"; the column is now "Placement". */
export const PRIORITY_BOTTOM_LINE = "Placement and confidence answer different questions.";
/** CC-R2 (D5, build spec "CC-R2 Frontend"): placement group labels, in the server's group order. */
export const PLACEMENT_GROUP_LABEL = {
  NEEDS_INVESTIGATION: "Needs investigation first",
  ACT_NOW: "Act now",
  COMPARE_VALUE: "Compare value",
  UNPRICED_RISK: "Unpriced risk",
  MONITOR: "Monitor",
} as const;
export const PLACEMENT_CONFIDENCE_WORDS: Record<string, string> = {
  SUPPORTED_SOURCE_COHERENT: "Supported, coherent source",
  LIMITED: "Limited",
  UNKNOWN: "Unknown",
};
export const PLACEMENT_POLICY_SUMMARY = "How placement works";
export const PLACEMENT_POLICY_LINES = [
  "Needs investigation first: the evidence source is mixed or unresolved, the Finding is unconfirmed, or its cost is withheld.",
  "Act now: the episode is open, returned or reopened, and no Action is underway or its resolution was withdrawn.",
  "Monitor (checked next): a change was applied or verified.",
  "Compare value: the Finding has a priced cost exposure.",
  "Unpriced risk: the Finding has no price basis.",
] as const;
export const PLACEMENT_POLICY_FOOTER =
  "Groups say where to look first; they are not a value ranking. Within a group, most recent first. Policy estate-placement/1.";
export const EVIDENCE_ASIDE = "Evidence that would change a decision";
export const OPPORTUNITY_PANEL = "An opportunity beyond reducing cost";
export const PROGRESS_PANEL = "What changed in this review";

export const LENS_LABELS = [
  ["all", "All findings"],
  ["cost", "Cost"],
  ["risks", "Risks"],
  ["opportunities", "Opportunities"],
] as const;

export const DOMAIN_WORD: Readonly<Record<EstateDomain, string>> = {
  MINIGRID: "Mini-grid",
  COLDCHAIN: "Cold-chain",
  EV_CHARGING: "EV charging",
};

export const CARD_LABEL: Readonly<Record<EstateValueCardKey, string>> = {
  OPERATING_COST: "Operating-cost exposure",
  SERVICE_PRODUCT_RISK: "Service & product risk",
  PRODUCTIVE_USE: "Productive-use opportunity",
  ASSET_LIFE: "Asset-life exposure",
  VERIFIED_RECOVERY: "Verified value recovered",
};

/** Closure 1: display strings the API leaves null for the unsupported/unknown card states. */
export const CARD_VALUE: Readonly<Record<string, string>> = {
  UNPRICED: "Unpriced",
  WITHHELD: "Not comparable for this selection",
  NO_LINE: "No supported value",
  UNKNOWN: "Not assessed",
  UNSUPPORTED: "Not established",
  NOT_ESTABLISHED: "Not established",
};

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** `d MMM yyyy · HH:mm UTC` for one wire instant. */
export function dayMinute(wire: string): string {
  return `${Number(wire.slice(8, 10))} ${MONTHS[Number(wire.slice(5, 7)) - 1] ?? "?"} ${wire.slice(0, 4)} · ${wire.slice(11, 16)} UTC`;
}

/** Closure 1 Q19: the context badge, its tone, and the separate status sentence, by status precedence. */
export function contextWords(status: EstatePortfolioStatus, knownAt: string): { badge: string; tone: string; sentence: string } {
  switch (status) {
    case "EMPTY_SCOPE":
      return { badge: "No accessible Sites", tone: "neutral", sentence: "Portfolio: No accessible Sites" };
    case "HISTORICAL":
      return { badge: `Historical as of ${dayMinute(knownAt)}`, tone: "blue", sentence: "Portfolio: Historical selection" };
    case "PENDING":
      return { badge: "Updating selected Sites", tone: "amber", sentence: "Portfolio: Some Sites unavailable" };
    case "UNKNOWN":
      return { badge: "Some Sites cannot be compared yet", tone: "amber", sentence: "Portfolio: Some Sites unavailable" };
    default:
      return { badge: "Selected Site records", tone: "blue", sentence: "Portfolio: Review selected Sites" };
  }
}

/** `{N} accessible Sites · {mini} mini-grid / {cold} cold-chain / {ev} EV charging`, zeros included. */
export function domainSummary(body: EstatePortfolioBody): string {
  const sites = body.scope_disclosure.sites;
  const count = (domain: EstateDomain) => sites.filter((s) => s.domain === domain).length;
  return `${body.scope.authorized_site_count} accessible Sites · ${count("MINIGRID")} mini-grid / ${count("COLDCHAIN")} cold-chain / ${count("EV_CHARGING")} EV charging`;
}

export const PULSE_NOTE = "Distinct consequence categories · no combined savings total";
export const OPPORTUNITY_NOTE = "A scenario needs reviewed physical headroom, demand and an authored economic assumption.";
export const OUTCOME_NOTE = "Observed change → comparable evidence → verified outcome → eligible financial value";
export const NO_SNAPSHOT_NOTICE =
  "No previous comparable Portfolio snapshot is selected; change deltas and recovered-value trends are withheld.";
export const PROGRESS_REFERENCE = "Counts use retained Action and verification records. Portfolio does not decide resolution.";
export const ACTION_WINDOW_NOTE =
  "Action counts cover only Actions created in the selected window; an earlier Action verified within 30 days is not counted.";
export const NO_ENERGY_TOTAL = "Cross-Site energy and tariff totals are not established.";
export const ENERGY_UNAVAILABLE = "Energy basis unavailable";
export const EV_COVERAGE_WARNING = "Other Sites may lack comparable full-window coverage.";
export const CATEGORIES_SEPARATE = "Categories and windows remain separate.";
export const CURRENT_SITE_VIEW = "Opens current Site view";
export const SCOPE_RULE =
  "Each Site keeps its own selected assessment and evidence limits. Portfolio does not create a combined site health score.";
export const VALUE_OWNERSHIP =
  "Each consequence remains owned by its source Site, category, period, currency and assumption. Exclusions and provenance are shown with the selected lines.";
export const SCOPE_NOTICE =
  "The selected windows share one request; their underlying event periods may differ. No monthly extrapolation or asset valuation is established.";

/**
 * Post-W6 W3-estate Q13 (R307): the scope disclosure's plain words. Coverage states follow the estate Site state
 * words (UNKNOWN reads `Not yet assessed`); an exclusion's reason codes use the money reason dictionary, and an
 * exclusion with any code outside it reads `Excluded from comparison` with the raw codes kept in a detail.
 */
export const ASSESSMENT_IDS = "Assessment IDs";
/** Q10: an EV Site has no Backup objective target; any other matrix cell without a destination. */
export const NO_SELECTED_ASSESSMENT = "No selected assessment";
export const EXCLUDED_FROM_COMPARISON = "Excluded from comparison";

export const COVERAGE_STATE_WORDS: Readonly<Record<EstateSiteState, string>> = {
  CURRENT: "Current",
  PENDING_RECOMPUTE: "New evidence is being assessed",
  STALE_SOURCE: "May miss newer readings",
  HISTORICAL: "Earlier evidence cutoff",
  UNKNOWN: "Not yet assessed",
  NOT_APPLICABLE: "Not applicable",
};

export function coverageStateWords(state: string): string {
  return COVERAGE_STATE_WORDS[state as EstateSiteState] ?? "Not yet assessed";
}

/** `{n} selected assessment(s)` or `No selected assessment`. */
export function selectedAssessmentWords(count: number): string {
  if (count === 0) return NO_SELECTED_ASSESSMENT;
  return `${count} selected ${count === 1 ? "assessment" : "assessments"}`;
}

export function exclusionReasonWords(exclusion: EstatePortfolioExclusion): string {
  const codes = exclusion.reason_codes;
  if (codes.length === 0 || !codes.every(hasReasonWord)) return EXCLUDED_FROM_COMPARISON;
  return reasonText(codes);
}

const LINE_DOMAIN_WORD: Readonly<Record<string, string>> = {
  mini_grid: "Mini-grid line",
  cold_chain: "Cold-chain line",
  ev_charging: "EV charging line",
};

/** The Site that owns an excluded line (from the selected lines), else its domain, else a plain fallback. */
export function exclusionLineLabel(lineKey: string, body: Pick<EstatePortfolioBody, "selected_lines">): string {
  const line = body.selected_lines.find((l) => l.line_key === lineKey);
  if (line !== undefined && line.site_name.trim() !== "") return line.site_name;
  return LINE_DOMAIN_WORD[lineKey.split(":")[0]] ?? "Consequence line";
}

export const MECHANISM_NOT_RECORDED = "Mechanism not recorded";
/**
 * CC-R2-F3 ruling. MOCK DEVIATION: v69 `#/portfolio` shows instance text such as "Automatic start failed; cooling
 * interrupted" and "30 min candidate; charging trade-off remains". The wire carries only the mechanism code, so these
 * generic words drop the figures and effects the row does not carry. Null or any other code falls back.
 */
export const MECHANISM_WORDS: Record<string, string> = {
  GENERATOR_SUPPORT_CANDIDATE: "Possible extended generator support",
  COLD_EXCURSION: "Chamber temperature above policy",
  COLD_START_FAILURE: "Automatic start failed",
  EV_INTERRUPTION: "Charging session interrupted",
};
export function mechanismWords(code: string | null | undefined): string {
  return (code != null && Object.prototype.hasOwnProperty.call(MECHANISM_WORDS, code) && MECHANISM_WORDS[code]) || MECHANISM_NOT_RECORDED;
}
