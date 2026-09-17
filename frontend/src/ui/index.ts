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
export { NavRail, type NavRailItem, type NavRailProps } from "./NavRail";
export { PageHeader, type PageHeaderProps } from "./PageHeader";
export { Panel, type PanelProps } from "./Panel";
