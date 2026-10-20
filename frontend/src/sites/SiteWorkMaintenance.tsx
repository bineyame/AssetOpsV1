/**
 * W4-01 commit 5 (`I-maintenance-ui`): Site > Work > Maintenance, the v69
 * `sitework-maintenance` screen over `GET /api/sites/{site}/work/maintenance`.
 * Completed work is activity only: the Outcome column stays "Unverified" until
 * a reviewed outcome evaluator exists. The shared body is `siteWorkCases.tsx`.
 */
import { SiteWorkCases, type SiteWorkCasesProps } from "./siteWorkCases";

export function SiteWorkMaintenance(props: SiteWorkCasesProps) {
  return <SiteWorkCases kind="maintenance" {...props} />;
}
