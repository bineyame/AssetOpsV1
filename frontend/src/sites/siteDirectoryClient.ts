/**
 * Read-only client for the operator Sites API.
 *
 * The Sites index is an operator capability and is never gated, so this client
 * spells an operator path and is built with no reference to the feature flag.
 * It reads. There is no create, edit, save, publish, rename, duplicate, or
 * delete method here, so no screen built on it can offer one; creating a site
 * is a Simulator Lab capability with its own gated client.
 *
 * Failures are returned as named states rather than thrown or swallowed. A
 * response that does not match the expected shape is `unavailable`, not a
 * partially rendered row: a screen must not show half a site and imply the
 * rest is missing from the configuration.
 */

import type {
  SiteDetailReadModel,
  SiteDetailResult,
  SiteListResult,
  SiteSummary,
} from "./siteReadModel";

/** The operator Sites API. Not a simulator path, and never gated. */
export const SITES_API_PATH = "/api/sites";

export interface SiteDirectoryClient {
  listSites(): Promise<SiteListResult>;
}

/**
 * Reading one site by its identity.
 *
 * A second interface rather than a second method on the one above, so that a
 * screen declares which capability it needs and a caller that only lists
 * sites cannot reach a lookup it never uses. Both are satisfied by the one
 * client built below, and both are read-only: there is still no create, edit,
 * save, publish, rename, duplicate, or delete method anywhere in this module.
 *
 * A site is addressed by `site_id` and by nothing else. The display name and
 * the template a site was created from are not identity and never appear in a
 * request path.
 */
export interface SiteDetailClient {
  getSite(siteId: string): Promise<SiteDetailResult>;
}

function isTemplateProvenance(value: unknown): boolean {
  if (value === null) {
    return true;
  }
  if (typeof value !== "object") {
    return false;
  }
  const provenance = value as Record<string, unknown>;
  return (
    typeof provenance.template_id === "string" &&
    typeof provenance.template_version === "number"
  );
}

export function isSiteSummary(value: unknown): value is SiteSummary {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const site = value as Record<string, unknown>;
  const location = site.location as Record<string, unknown> | undefined;
  const source = site.source as Record<string, unknown> | undefined;

  return (
    typeof site.site_id === "string" &&
    typeof site.display_name === "string" &&
    typeof site.site_type === "string" &&
    typeof site.timezone === "string" &&
    typeof site.lifecycle_status === "string" &&
    typeof site.origin === "string" &&
    location !== undefined &&
    typeof location.country === "string" &&
    typeof location.locality === "string" &&
    source !== undefined &&
    typeof source.mode === "string" &&
    isTemplateProvenance(site.template)
  );
}

/**
 * A declared design rating, or the absence of one.
 *
 * `null` is the document saying a component declares no rating, and it is the
 * only absence this accepts. A missing key is not that statement: it is a
 * response that does not carry the field, and letting it through here would
 * put `undefined` where a view model reads `rating.value`.
 */
function isSiteRating(value: unknown): boolean {
  if (value === null) {
    return true;
  }
  if (typeof value !== "object") {
    return false;
  }
  const rating = value as Record<string, unknown>;
  return typeof rating.value === "number" && typeof rating.unit === "string";
}

function isSiteComponent(value: unknown): boolean {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const component = value as Record<string, unknown>;
  return (
    typeof component.component_id === "string" &&
    typeof component.component_type === "string" &&
    typeof component.display_name === "string" &&
    isSiteRating(component.rating)
  );
}

/**
 * A declared section, or the absence of one.
 *
 * `null` is the document declaring none, and it is the only absence accepted.
 * A missing key is not that statement - it is a response that does not carry
 * the field - and letting it through would put `undefined` where a view model
 * asks whether the site declares any devices, which is a question `undefined`
 * answers wrongly.
 */
function isDeclaredOrNull(
  value: unknown,
  entry: (candidate: unknown) => boolean,
): boolean {
  if (value === null) {
    return true;
  }
  // Also refused: an empty array. The backend never sends one, because `[]`
  // and `null` would be two spellings of one fact and a screen could not tell
  // "declares none" from "has none". A response carrying one is a response
  // from something that is not this contract.
  return Array.isArray(value) && value.length > 0 && value.every(entry);
}

function isTopologyNode(value: unknown): boolean {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const node = value as Record<string, unknown>;
  return (
    typeof node.node_id === "string" &&
    typeof node.component_id === "string" &&
    typeof node.node_role === "string"
  );
}

function isTopologyConnection(value: unknown): boolean {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const connection = value as Record<string, unknown>;
  return (
    typeof connection.connection_id === "string" &&
    typeof connection.from_node === "string" &&
    typeof connection.to_node === "string" &&
    typeof connection.medium === "string"
  );
}

function isFoundationTopology(value: unknown): boolean {
  if (value === null) {
    return true;
  }
  if (typeof value !== "object") {
    return false;
  }
  const topology = value as Record<string, unknown>;
  return (
    Array.isArray(topology.nodes) &&
    topology.nodes.length > 0 &&
    topology.nodes.every(isTopologyNode) &&
    Array.isArray(topology.connections) &&
    topology.connections.length > 0 &&
    topology.connections.every(isTopologyConnection)
  );
}

function isDeviceSignal(value: unknown): boolean {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const signal = value as Record<string, unknown>;
  return (
    typeof signal.signal_id === "string" &&
    typeof signal.display_name === "string" &&
    typeof signal.unit === "string"
  );
}

function isFoundationDevice(value: unknown): boolean {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const device = value as Record<string, unknown>;
  return (
    typeof device.device_id === "string" &&
    typeof device.device_type === "string" &&
    typeof device.display_name === "string" &&
    typeof device.component_id === "string" &&
    Array.isArray(device.signals) &&
    device.signals.length > 0 &&
    device.signals.every(isDeviceSignal)
  );
}

function isSignalMapping(value: unknown): boolean {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const mapping = value as Record<string, unknown>;
  return (
    typeof mapping.mapping_id === "string" &&
    typeof mapping.device_id === "string" &&
    typeof mapping.signal_id === "string" &&
    typeof mapping.component_id === "string"
  );
}

function isControlAssumption(value: unknown): boolean {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const assumption = value as Record<string, unknown>;
  return (
    typeof assumption.assumption_id === "string" &&
    typeof assumption.display_name === "string" &&
    (assumption.component_id === null ||
      typeof assumption.component_id === "string") &&
    typeof assumption.basis === "string" &&
    typeof assumption.statement === "string"
  );
}

/**
 * The detail shape, checked field by field down to a component's rating.
 *
 * Every field a site surface reads is checked here, because this guard is the
 * only thing between a response and a render. A check that stopped at the
 * foundation's metadata would accept a body with no `components` array and no
 * `summary`, and the screen that maps over the components would then fail
 * while rendering rather than state that the store could not be read. A
 * response that does not match the expected shape is `unavailable`; it is
 * never half a site.
 *
 * The guard grows with the read model. A field added to the foundation that is
 * not checked here is a field a malformed response can smuggle past. T014 adds
 * four, and all four are checked including their absence spelling: the four
 * sections are `null` or declared content, never a missing key and never an
 * empty array, because a screen that could not tell those apart would state
 * that a site has no devices on the strength of a truncated response.
 */
export function isSiteDetail(value: unknown): value is SiteDetailReadModel {
  if (!isSiteSummary(value)) {
    return false;
  }
  const foundation = (value as unknown as Record<string, unknown>).foundation as
    | Record<string, unknown>
    | undefined;

  return (
    foundation !== undefined &&
    foundation !== null &&
    typeof foundation.version === "number" &&
    typeof foundation.valid_from === "string" &&
    typeof foundation.summary === "string" &&
    Array.isArray(foundation.components) &&
    foundation.components.every(isSiteComponent) &&
    isFoundationTopology(foundation.topology) &&
    isDeclaredOrNull(foundation.devices, isFoundationDevice) &&
    isDeclaredOrNull(foundation.signal_mappings, isSignalMapping) &&
    isDeclaredOrNull(foundation.control_assumptions, isControlAssumption)
  );
}

export function createSiteDirectoryClient(
  basePath: string = SITES_API_PATH,
): SiteDirectoryClient & SiteDetailClient {
  return {
    async listSites(): Promise<SiteListResult> {
      try {
        const response = await fetch(basePath);
        if (!response.ok) {
          return { status: "unavailable" };
        }
        const body: unknown = await response.json();
        const sites = (body as Record<string, unknown>)?.sites;
        if (!Array.isArray(sites) || !sites.every(isSiteSummary)) {
          return { status: "unavailable" };
        }
        return { status: "loaded", sites };
      } catch {
        return { status: "unavailable" };
      }
    },

    async getSite(siteId: string): Promise<SiteDetailResult> {
      try {
        const response = await fetch(
          `${basePath}/${encodeURIComponent(siteId)}`,
        );
        if (response.status === 404) {
          return { status: "not_found" };
        }
        if (!response.ok) {
          return { status: "unavailable" };
        }
        const body: unknown = await response.json();
        if (!isSiteDetail(body)) {
          return { status: "unavailable" };
        }
        return { status: "loaded", site: body };
      } catch {
        return { status: "unavailable" };
      }
    },
  };
}
