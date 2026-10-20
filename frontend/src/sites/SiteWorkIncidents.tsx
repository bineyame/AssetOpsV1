/**
 * W4-01 commit 5 (`I-incident-ui`): Site > Work > Incidents, the v69
 * `sitework-incidents` screen over `GET /api/sites/{site}/work/incidents`.
 * Status strip, the one "Incidents at this site" panel, the context notice;
 * the shared body is `siteWorkCases.tsx`.
 */
import { SiteWorkCases, type SiteWorkCasesProps } from "./siteWorkCases";

export function SiteWorkIncidents(props: SiteWorkCasesProps) {
  return <SiteWorkCases kind="incidents" {...props} />;
}
