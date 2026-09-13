/**
 * Read-only client for the gated Site Templates API.
 *
 * The client is created with its base path rather than importing one, so this
 * module never spells a simulator URL: `tools/check-architecture.ps1` allows
 * that only in `simulatorLabRoutes.tsx`, which is where the path lives and
 * where this client is constructed.
 *
 * It reads. There is no create, instantiate, copy, upload, import, edit, save,
 * publish, delete, or rename method, so no screen built on it can offer one.
 *
 * Failures are returned as named states rather than thrown or swallowed. A
 * template that is not in the catalog is `not_found`; a catalog that could not
 * be read is `unavailable`. Neither is allowed to degrade into an empty list,
 * because "no templates ship" and "the catalog could not be read" are
 * different facts and a screen must not state the first when the second is
 * true.
 */

export interface SiteTemplateRating {
  value: number;
  unit: string;
}

/** What a template is, in its own identity space. Note the absent fields:
 *  no `site_id`, no lifecycle status, no location, no timezone, no source
 *  mode. A template has none of those, so this shape has nowhere to put one. */
export interface SiteTemplateSummary {
  template_id: string;
  template_version: number;
  display_name: string;
  site_type: string;
  summary: string;
}

export interface SiteTemplateComponent {
  component_id: string;
  component_type: string;
  display_name: string;
  rating: SiteTemplateRating | null;
}

export interface SiteTemplateDetail extends SiteTemplateSummary {
  components: SiteTemplateComponent[];
}

export type SiteTemplateListResult =
  | { status: "loaded"; templates: SiteTemplateSummary[] }
  | { status: "unavailable" };

export type SiteTemplateDetailResult =
  | { status: "loaded"; template: SiteTemplateDetail }
  | { status: "not_found" }
  | { status: "unavailable" };

export interface SiteTemplateCatalogClient {
  listTemplates(): Promise<SiteTemplateListResult>;
  getTemplate(templateId: string): Promise<SiteTemplateDetailResult>;
}

function isRating(value: unknown): value is SiteTemplateRating {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const rating = value as Record<string, unknown>;
  return typeof rating.value === "number" && typeof rating.unit === "string";
}

function isSummary(value: unknown): value is SiteTemplateSummary {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const template = value as Record<string, unknown>;
  return (
    typeof template.template_id === "string" &&
    typeof template.template_version === "number" &&
    typeof template.display_name === "string" &&
    typeof template.site_type === "string" &&
    typeof template.summary === "string"
  );
}

function isDetail(value: unknown): value is SiteTemplateDetail {
  if (!isSummary(value)) {
    return false;
  }
  const components = (value as unknown as Record<string, unknown>).components;
  return (
    Array.isArray(components) &&
    components.every((component) => {
      if (component === null || typeof component !== "object") {
        return false;
      }
      const entry = component as Record<string, unknown>;
      return (
        typeof entry.component_id === "string" &&
        typeof entry.component_type === "string" &&
        typeof entry.display_name === "string" &&
        (entry.rating === null || isRating(entry.rating))
      );
    })
  );
}

/**
 * Build a catalog client over an API base path.
 *
 * A response that does not match the expected shape is `unavailable`, not a
 * partially rendered template: a screen must not display half a document and
 * imply the rest is missing from the configuration.
 */
export function createSiteTemplateCatalogClient(
  basePath: string,
): SiteTemplateCatalogClient {
  return {
    async listTemplates(): Promise<SiteTemplateListResult> {
      try {
        const response = await fetch(basePath);
        if (!response.ok) {
          return { status: "unavailable" };
        }
        const body: unknown = await response.json();
        const templates = (body as Record<string, unknown>)?.templates;
        if (!Array.isArray(templates) || !templates.every(isSummary)) {
          return { status: "unavailable" };
        }
        return { status: "loaded", templates };
      } catch {
        return { status: "unavailable" };
      }
    },

    async getTemplate(templateId: string): Promise<SiteTemplateDetailResult> {
      try {
        const response = await fetch(
          `${basePath}/${encodeURIComponent(templateId)}`,
        );
        if (response.status === 404) {
          return { status: "not_found" };
        }
        if (!response.ok) {
          return { status: "unavailable" };
        }
        const body: unknown = await response.json();
        if (!isDetail(body)) {
          return { status: "unavailable" };
        }
        return { status: "loaded", template: body };
      } catch {
        return { status: "unavailable" };
      }
    },
  };
}
