import { NO_TEMPLATE_PROVENANCE } from "./siteViewModel";
import type { SiteSummary } from "./siteReadModel";
import {
  templateLineageNote,
  type SiteTemplateLineageReadModel,
} from "./siteTemplateLineage";

/**
 * The value of "Created from template", in every place a site shows it.
 *
 * The recorded template and version, then - only when a lineage answer says
 * the record is behind or no longer shipped - one plain secondary line saying
 * so. Plain text by design: it is provenance, not a status pill, a blocker or
 * an action, and nothing here offers to change the site.
 */
export function TemplateProvenanceText({
  site,
  provenance,
  lineage,
}: {
  site: SiteSummary;
  /** The view model's rendering of the recorded provenance. */
  provenance: string;
  lineage: SiteTemplateLineageReadModel | undefined;
}) {
  const note =
    provenance === NO_TEMPLATE_PROVENANCE ? null : templateLineageNote(site, lineage);

  return (
    <>
      {provenance}
      {note === null ? null : (
        <span className="cell-secondary" data-template-lineage-note="">
          {note}
        </span>
      )}
    </>
  );
}
