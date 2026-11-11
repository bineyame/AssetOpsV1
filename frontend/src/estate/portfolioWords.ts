/**
 * W3-03 run 2: the Portfolio page's literal copy (`.agent/W3-03-build-spec.md` mock ledger as amended by closures
 * 1-5, r1a, r1b, r1b2 and r1b4). The page never invents a value: every slot without a reviewed source keeps its
 * mock position and says so.
 */
import type {
  EstateCoverageDays,
  EstateDomain,
  EstatePortfolioBody,
  EstatePortfolioExclusion,
  EstatePortfolioStatus,
  EstateSiteState,
  EstateValueCardKey,
} from "./estateClient";
import { dayGapWords } from "../ui/productWords";
import { formatDayTime } from "../ui/time";
import { hasReasonWord, reasonText } from "./estateFinancialsWords";

export const PORTFOLIO_PATH = "/portfolio";
export const PORTFOLIO_TITLE = "Portfolio Value & Operations";
export const PORTFOLIO_SUBTITLE = "Operating decisions across the estate: cost, service, productive use and asset value";
export const PORTFOLIO_PAGE_SIZE = 50;

/**
 * PF-T: the Portfolio section tabs (owner-approved names, walkthrough item 5.1; proposal 2026-11-10 §6). Each tab is
 * an address under `/portfolio/:tab?`; Overview is the bare root. `scope` is the deep tab, set apart at the right.
 */
export type PortfolioTab = "overview" | "act-first" | "outcomes" | "opportunity" | "changes" | "scope";
export const PORTFOLIO_TABS: readonly { tab: PortfolioTab; label: string; segment: string | null }[] = [
  { tab: "overview", label: "Overview", segment: null },
  { tab: "act-first", label: "Act first", segment: "act-first" },
  { tab: "outcomes", label: "Outcomes by site", segment: "outcomes" },
  { tab: "opportunity", label: "Opportunity", segment: "opportunity" },
  { tab: "changes", label: "What changed", segment: "changes" },
  { tab: "scope", label: "Scope & coverage", segment: "scope" },
];
export const PORTFOLIO_TABS_LABEL = "Portfolio sections";
/** The tab a `:tab` segment names; `null` for a segment that names no tab (the page redirects to Overview). */
export function portfolioTabFrom(segment: string | undefined): PortfolioTab | null {
  if (segment === undefined || segment === "") return "overview";
  return PORTFOLIO_TABS.find((t) => t.segment === segment)?.tab ?? null;
}
export function portfolioTabPath(tab: PortfolioTab): string {
  const segment = PORTFOLIO_TABS.find((t) => t.tab === tab)?.segment ?? null;
  return segment === null ? PORTFOLIO_PATH : `${PORTFOLIO_PATH}/${segment}`;
}
export const TOP3_SEE_ALL = (n: number | null) => (n === null ? "See all findings →" : `See all ${n} findings →`);
export const TOP3_SUBTITLE = "The three highest-placed findings. Placement and confidence answer different questions.";

export const PRIORITY_PANEL = "Where management should act first";
/**
 * CC-R2-Q3 ruling. MOCK DEVIATION: v69 (`index.html:133`) says "ranked by consequence and urgency"; groups are not a
 * value ranking (the placement policy footer says so).
 */
export const PRIORITY_SUBTITLE =
  "Selected findings across accessible Sites, grouped by where to look first, with evidence confidence alongside.";
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
  SUPPORTED_SOURCE_COHERENT: "Well supported",
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



/** `29 Oct 2026, 16:00` for one wire instant (POLISH §3 Times). */
export function dayMinute(wire: string): string {
  return formatDayTime(wire);
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
    case "PARTIAL":
      // PF-W (D-E5.46): the estate PARTIAL state is "incomplete days", never "not checked".
      return { badge: "Some days incomplete", tone: "amber", sentence: "Portfolio: Some sites have incomplete days" };
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
export const OPPORTUNITY_NOTE = "A what-if needs reviewed physical headroom, demand and an agreed cost assumption.";
export const OUTCOME_NOTE = "Observed change → comparable evidence → verified outcome → eligible financial value";
export const NO_SNAPSHOT_NOTICE =
  "No previous comparable Portfolio snapshot is selected; change deltas and recovered-value trends are withheld.";
export const PROGRESS_REFERENCE = "Counts use retained Action and verification records. Portfolio does not decide resolution.";
export const ACTION_WINDOW_NOTE =
  "Action counts cover only Actions created in the selected window; an earlier Action verified within 30 days is not counted.";
export const NO_ENERGY_TOTAL = "Cross-Site energy and tariff totals are not known yet.";
export const ENERGY_UNAVAILABLE = "Energy basis unavailable";
export const EV_COVERAGE_WARNING = "Other Sites may lack comparable full-window coverage.";
export const CATEGORIES_SEPARATE = "Categories and windows remain separate.";
export const CURRENT_SITE_VIEW = "Current view";
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
export const NO_SELECTED_ASSESSMENT = "No selected assessment";
export const EXCLUDED_FROM_COMPARISON = "Excluded from comparison";

export const COVERAGE_STATE_WORDS: Readonly<Record<EstateSiteState, string>> = {
  CURRENT: "Current",
  PENDING_RECOMPUTE: "New evidence is being assessed",
  STALE_SOURCE: "May miss newer readings",
  HISTORICAL: "Earlier evidence cutoff",
  UNKNOWN: "Not yet assessed",
  NOT_APPLICABLE: "Not applicable",
  PARTIAL: "Incomplete days",
};

export function coverageStateWords(state: string): string {
  return COVERAGE_STATE_WORDS[state as EstateSiteState] ?? "Not yet assessed";
}

const GAP_DAY = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", timeZone: "UTC" });

/** COV-PARTIAL: a Site's gap days as `26 Oct, 27 Oct` (UTC days, ascending as sent). */
export function gapDayList(days: EstateCoverageDays | null | undefined): string {
  return (days?.gaps ?? []).map((gap) => GAP_DAY.format(new Date(`${gap.day}T00:00:00Z`))).join(", ");
}

/*
 * PF-W (proposal §10.2; D-E5.46, owner-directed 2026-11-11): the readings term family. Data words say what arrived,
 * never whether anyone "checked"; "Not analysed yet" and "Still processing" are system work only. The backend
 * `chain/vocabulary.py` holds these strings byte for byte (`test_pfc_coverage_line.py`).
 * MOCK DEVIATION PF-C-1: 8 terms against the v71 mock's 6 (adds "Not enough readings" and "Conflicting readings", the
 * D-E5.46 data-gap reasons the Site rows name), and "Not analysed yet" uses the D-E5.46 definition, not the mock's
 * (`portfolio-tabs.html:178`).
 */

/** The "What these words mean" list: [term, one-line definition], in order. */
export const READINGS_TERMS: readonly (readonly [string, string])[] = [
  ["Complete readings", "Readings arrived for at least 80% of the hours the day needed (for spare solar: every daylight hour). The day is counted."],
  ["Partial readings", "Readings arrived for 25–80% of those hours. The day is shown, and named wherever it is used."],
  ["Too few readings", "Readings arrived for under 25% of those hours. The day is not counted."],
  ["No readings received", "Nothing arrived from the site for that day."],
  ["Not enough readings", "Some readings arrived, but not enough to analyse the day."],
  ["Conflicting readings", "Readings for the day conflict (duplicate or overlapping reports), so it can't be analysed."],
  ["Still processing", "Readings arrived and are being analysed; results follow."],
  ["Not analysed yet", "AssetOps has not analysed the day yet; it will, without any action from you."],
];
export const READINGS_GLOSSARY_NOTE = "AssetOps looks at every day. These words describe the data that arrived, not whether anyone looked.";

/** D-E5.46 table, one gap reason per day: the ONE table lives in `ui/productWords.ts` (`dayGapWords`, PB-4). */
function gapShort(reason: string): string | null {
  return dayGapWords(reason)?.short ?? null;
}
export const STILL_PROCESSING = "Still processing";
/** A gap whose reason has no words (an older body's `NO_ASSESSED_SELECTION`) reads as system work. */
const UNKNOWN_GAP_SHORT = "not analysed yet";
/** D-E5.46: more than 3 gap days read as one count. */
export const GAPS_LISTED_MAX = 3;

/** D-E5.46 (amends D-E5.26): the Site PARTIAL count, `{n} site(s) with incomplete days`. */
export function incompleteSites(n: number): string {
  return `${n} ${n === 1 ? "site with incomplete days" : "sites with incomplete days"}`;
}

/**
 * D-E5.46 short form of a Site's gap days: one group per reason, days sharing a reason grouped (`3, 4 Nov:
 * conflicting readings`), groups " · "-joined; more than 3 gap days read `{g} days without a usable result`.
 */
export function gapReasonClause(days: EstateCoverageDays | null | undefined, max: number = GAPS_LISTED_MAX): string {
  const gaps = days?.gaps ?? [];
  if (gaps.length === 0) return "";
  if (gaps.length > max) return `${gaps.length} days without a usable result`;
  const groups = new Map<string, Date[]>();
  for (const gap of gaps) {
    const short = gapShort(gap.reason) ?? UNKNOWN_GAP_SHORT;
    groups.set(short, [...(groups.get(short) ?? []), new Date(`${gap.day}T00:00:00Z`)]);
  }
  return Array.from(groups, ([short, list]) => `${dayGroup(list)}: ${short}`).join(" · ");
}

function dayGroup(list: Date[]): string {
  const month = (d: Date) => GAP_DAY.format(d).split(" ").slice(1).join(" ");
  if (list.every((d) => month(d) === month(list[0]))) return `${list.map((d) => d.getUTCDate()).join(", ")} ${month(list[0])}`;
  return list.map((d) => GAP_DAY.format(d)).join(", ");
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
  /** DIESEL-1-R3p (K8 coordinator ruling): the backend's approved SUPPORTED title, `site_outcomes/mini.py` FINDING_TITLE_BY_MECHANISM. */
  UNEXPLAINED_FUEL: "Unexplained fuel overnight",
};
export function mechanismWords(code: string | null | undefined): string {
  return (code != null && Object.prototype.hasOwnProperty.call(MECHANISM_WORDS, code) && MECHANISM_WORDS[code]) || MECHANISM_NOT_RECORDED;
}
