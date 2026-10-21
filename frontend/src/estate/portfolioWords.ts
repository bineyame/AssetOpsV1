/**
 * W3-03 run 2: the Portfolio page's literal copy (`.agent/W3-03-build-spec.md` mock ledger as amended by closures
 * 1-5, r1a, r1b, r1b2 and r1b4). The page never invents a value: every slot without a reviewed source keeps its
 * mock position and says so.
 */
import type {
  EstateDomain,
  EstatePortfolioBody,
  EstatePortfolioStatus,
  EstateValueCardKey,
} from "./estateClient";

export const PORTFOLIO_PATH = "/portfolio";
export const PORTFOLIO_TITLE = "Portfolio Value & Operations";
export const PORTFOLIO_SUBTITLE = "Operating decisions across the estate: cost, service, productive use and asset value";
export const PORTFOLIO_PAGE_SIZE = 50;

export const PRIORITY_PANEL = "Where management should act first";
export const PRIORITY_SUBTITLE = "Selected Findings across accessible Sites; priority and confidence appear when assessed.";
export const OBJECTIVES_PANEL = "Objectives across the estate";
export const OBJECTIVES_SUBTITLE = "Operating condition, not a composite health score";
export const OBJECTIVES_FOOTNOTE =
  "Site-owned assessments · Unknown is not healthy. N/A means the objective is not configured. Select a linked cell for context.";
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
  NO_LINE: "No supported value for this window",
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
