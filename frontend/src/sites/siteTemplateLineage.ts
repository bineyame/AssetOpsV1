/**
 * A site's recorded template lineage against the current shipped template
 * (T025f, `D-2026-10-01-run-binds-scenario-to-site`, Versioning).
 *
 * Advisory provenance. The backend computes it on every read from the site's
 * recorded `(template_id, template_version)` and the shipped catalog, and
 * stores nothing on the site. It is not a status, a blocker or an action: a
 * site created from an older template version keeps the content it was given,
 * because templates copy and never migrate an existing site.
 *
 * The catalog it compares against is a Simulator Lab surface, so the read is
 * gated. This module never names the Lab: the client is built with its base
 * path by the one gated module, and a composing shell passes it in only when
 * the gate is open. With no client, every surface renders exactly what it
 * rendered before - the recorded template and version, and nothing else.
 */

import { useEffect, useState } from "react";

import type { SiteSummary, SiteTemplateProvenanceReadModel } from "./siteReadModel";

export type SiteTemplateLineageState =
  | "NO_TEMPLATE"
  | "CURRENT"
  | "BEHIND"
  | "NOT_SHIPPED"
  | "UNRECOGNISED_VERSION";

export interface SiteTemplateLineageReadModel {
  site_id: string;
  /** The lineage the comparison was made against, as the site records it. */
  template: SiteTemplateProvenanceReadModel | null;
  state: string;
  current_template_version: number | null;
}

export type SiteTemplateLineageResult =
  | { status: "loaded"; sites: SiteTemplateLineageReadModel[] }
  | { status: "unavailable" };

export interface SiteTemplateLineageClient {
  listLineage(): Promise<SiteTemplateLineageResult>;
}

function isLineage(value: unknown): value is SiteTemplateLineageReadModel {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const entry = value as Record<string, unknown>;
  const template = entry.template as Record<string, unknown> | null | undefined;
  return (
    typeof entry.site_id === "string" &&
    typeof entry.state === "string" &&
    (entry.current_template_version === null ||
      typeof entry.current_template_version === "number") &&
    (template === null ||
      (typeof template === "object" &&
        template !== undefined &&
        typeof template.template_id === "string" &&
        typeof template.template_version === "number"))
  );
}

/** Build a lineage client over a base path the caller supplies. */
export function createSiteTemplateLineageClient(
  basePath: string,
): SiteTemplateLineageClient {
  return {
    async listLineage(): Promise<SiteTemplateLineageResult> {
      try {
        const response = await fetch(basePath);
        if (!response.ok) {
          return { status: "unavailable" };
        }
        const body: unknown = await response.json();
        const sites = (body as Record<string, unknown>)?.sites;
        if (!Array.isArray(sites) || !sites.every(isLineage)) {
          return { status: "unavailable" };
        }
        return { status: "loaded", sites };
      } catch {
        return { status: "unavailable" };
      }
    },
  };
}

/**
 * The advisory note beside "Created from template", or `null` for none.
 *
 * `null` when there is no lineage answer (no client, a read in flight, an
 * unavailable read), when the site came from no template (the provenance
 * already says so), and when the recorded version is current. An answer made
 * about a different recorded lineage than the record in hand is ignored rather
 * than applied to it.
 */
export function templateLineageNote(
  site: SiteSummary,
  lineage: SiteTemplateLineageReadModel | undefined,
): string | null {
  if (lineage === undefined || site.template === null) {
    return null;
  }
  if (
    lineage.template === null ||
    lineage.template.template_id !== site.template.template_id ||
    lineage.template.template_version !== site.template.template_version
  ) {
    return null;
  }

  const recorded = site.template.template_version;
  switch (lineage.state) {
    case "BEHIND":
      return `Created from v${recorded}; current template is v${lineage.current_template_version}`;
    case "NOT_SHIPPED":
      return "This template is no longer shipped";
    case "UNRECOGNISED_VERSION":
      return `Recorded v${recorded} is not a version this build ships; current is v${lineage.current_template_version}`;
    default:
      return null;
  }
}

/**
 * The lineage answers by `site_id`, or `null` while there is none to apply.
 *
 * `null` covers no client, a read in flight and an unavailable read alike: in
 * each case the surface shows the recorded provenance alone, which is what it
 * showed before this slice, and claims nothing about currency.
 */
export function useSiteTemplateLineage(
  client: SiteTemplateLineageClient | undefined,
): ReadonlyMap<string, SiteTemplateLineageReadModel> | null {
  const [answers, setAnswers] = useState<ReadonlyMap<
    string,
    SiteTemplateLineageReadModel
  > | null>(null);

  useEffect(() => {
    let active = true;
    setAnswers(null);
    if (client === undefined) {
      return undefined;
    }
    void client.listLineage().then((loaded) => {
      if (active && loaded.status === "loaded") {
        setAnswers(new Map(loaded.sites.map((entry) => [entry.site_id, entry])));
      }
    });
    return () => {
      active = false;
    };
  }, [client]);

  return answers;
}
