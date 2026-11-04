import { createContext, useContext } from "react";

/**
 * CH-5a2a (B1, CH5a2-R4(b)): the screen-link reference the server sends beside a legacy `href` as `link_ref`,
 * mirroring `backend/assetops_backend/chain/refs.py`.
 *
 * The types live in the Site substrate because the substrate renders them and is a leaf (it imports no shell code,
 * `tools/checks/site-substrate.ps1` rule 8). `routeFor` in `shell/operatorSiteRoutes.ts` stays the ONLY client
 * builder of a rendered link (`__fixtures__/route-refs.json`, read by a vitest and a pytest, pins it to the
 * server's `href_for`); the shell hands it to the substrate through `RefLinkProvider`, never the reverse.
 */

/**
 * S4-03: the named child views of the canonical Finding root (`/sites/{site}/findings/{finding}/{view}`), re-exported
 * by `shell/operatorSiteRoutes.ts`, which owns their routes. W4-03 unit 6b adds `alternatives`.
 */
export const FINDING_CHILD_VIEWS = ["evidence", "history", "recommendation", "alternatives"] as const;
export type FindingChildView = (typeof FINDING_CHILD_VIEWS)[number];

export interface RefWindow {
  from: string;
  to: string;
  known_at?: string;
}
export const REF_SITE_VIEWS = [
  "home", "foundation", "foundation_changes", "findings", "financials", "financial_assumptions", "financial_scenarios",
  "ev", "ev_evidence", "ev_analysis", "ev_financials", "ev_assumptions", "ev_scenarios",
  "work", "work_incidents", "work_maintenance", "health", "assets",
] as const;
export type RefSiteView = (typeof REF_SITE_VIEWS)[number];
export const REF_ESTATE_VIEWS = [
  "portfolio", "findings", "findings_cost", "findings_risks", "findings_opportunities", "actions", "evidence",
  "financials", "incidents", "maintenance", "maintenance_preventive", "operational_records",
] as const;
export type RefEstateView = (typeof REF_ESTATE_VIEWS)[number];
export type RefActionView = "verification" | "plan" | "history";

export type Ref =
  | { kind: "THREAD"; site: string; id: string }
  | { kind: "FINDING"; site: string; id: string; revision?: string; view?: FindingChildView; window?: RefWindow }
  | { kind: "ACTION"; site: string; id: string; view?: RefActionView; event_id?: string; recorded_at?: string }
  | { kind: "OPPORTUNITY"; site: string; id: string; known_at?: string }
  | { kind: "CASE"; site: string; id: string }
  | { kind: "EVIDENCE"; site: string; capability?: string; window?: RefWindow }
  | { kind: "SITE"; site: string; view?: RefSiteView; window?: RefWindow }
  | { kind: "ESTATE"; view: RefEstateView };

/** The shell's `linkFor`: a Ref's screen path, or null when the Ref has no screen (or is absent). */
export type LinkFor = (ref: Ref | null | undefined) => string | null;

const RefLinkContext = createContext<LinkFor | null>(null);

/** The shell provides `linkFor` (`App.tsx`); tests provide it with `test/refLinks.tsx`. */
export const RefLinkProvider = RefLinkContext.Provider;

/**
 * The rendered-link builder of a substrate component. Outside a `RefLinkProvider` it throws: a forgotten provider
 * must fail loudly, never render every link as "no link".
 */
export function useLinkFor(): LinkFor {
  const linkFor = useContext(RefLinkContext);
  if (!linkFor) throw new Error("A Site component that renders links needs a RefLinkProvider (the shell's linkFor).");
  return linkFor;
}
