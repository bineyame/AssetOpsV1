/**
 * Shared UI primitives: the one visual vocabulary both shells and the shared
 * Site substrate render with.
 *
 * This module is a leaf. It imports no shell code, no simulator code, and no
 * feature flag, which is enforced by `tools/checks/ui-primitives.ps1`. That
 * matters for two seams at once: a primitive that could read the gate would be
 * a back door around it, and a primitive that could import the Site substrate
 * would be a second place for Site presentation to live.
 *
 * It also declares no Site read model, no Site view-model derivation, and no
 * Site presentation component. Those resolve in `frontend/src/sites/` only, and
 * the substrate's single-definition guard still proves it. What lives here is
 * vocabulary: a table, not a Site table.
 */
export { AppHeader, type AppHeaderProps } from "./AppHeader";
export { Badge, type BadgeProps, type BadgeTone } from "./Badge";
export { Breadcrumbs, type BreadcrumbsProps, type Crumb } from "./Breadcrumbs";
export {
  DataTable,
  type DataTableProps,
  Fact,
  FactList,
  type FactListProps,
  type FactProps,
} from "./DataTable";
export { Disclosure, type DisclosureProps } from "./Disclosure";
export {
  NAV_RAIL_UNAVAILABLE_STATUS,
  NavRail,
  type NavRailItem,
  type NavRailLiveItem,
  type NavRailProps,
  type NavRailUnavailableItem,
} from "./NavRail";
export { RailIcon, type RailIconName } from "./RailIcon";
export { PageHeader, type PageHeaderProps } from "./PageHeader";
export { Panel, type PanelProps } from "./Panel";
export {
  AttentionList,
  type AttentionItem,
  ChartNote,
  KeyValues,
  MetricCard,
  type MetricCardProps,
  MetricCards,
  type MetricTone,
  CausalTimeline,
  type TimelineEvent,
  StatusBar,
  V69Notice,
  SITE_SCREEN_DESCRIPTIONS,
  SitePageHeader,
  type SitePageHeaderProps,
} from "./V69Layout";
export {
  ReviewProposal,
  type ReviewProposalProps,
  REVIEW_PROPOSAL_STATUS,
} from "./ReviewProposal";
export { MissingClaim, MissingClaimSvg, type MissingClaimProps, type MissingClaimSvgProps } from "./MissingClaim";
export { isKnownGapPlacement, UI_GAP_CATALOGUE, type GapId, type GapPlacement } from "./gapCatalogue";
export {
  asOfText,
  currentnessWords,
  DEMONSTRATION_OUTCOME_NOTE,
  limitationWords,
  moneyWords,
  outcomeWords,
  plainTime,
  readResultWords,
  REASON_GUARDRAIL_FAIL,
  sourceQualification,
  UNRECOGNISED_SENTENCE,
  type OutcomeWords,
  type ProductTone,
  type ProductWords,
  type ReadResultKind,
  type SourceQualification,
} from "./productWords";
export {
  ExactReferences,
  HeadlineVisualCard,
  ProductLimitation,
  ProductOutcome,
  ProductStatus,
  StepStrip,
  ValueBars,
  type Step,
  type StepState,
  type ExactReference,
  type ExactReferencesProps,
  type FailedLimit,
  type HeadlineVisualCardProps,
  type ProductLimitationProps,
  type ProductOutcomeProps,
  type ProductStatusProps,
  type ValueBarItem,
  type ValueBarsProps,
} from "./ProductStatus";
