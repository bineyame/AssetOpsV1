/**
 * The Site read model.
 *
 * One definition, here, for both shells. Where the operator shell and the
 * Simulator Lab both present a Site they present it from this substrate: one
 * read model, one view model, one set of presentation components. Neither
 * shell may declare a Site read-model type of its own, because two read models
 * with a translation layer between them is exactly the drift this directory
 * exists to prevent, and by the time anyone notices, both have users.
 *
 * `frontend/src/sites/**` is a leaf. It imports no shell code, no simulator
 * code, and no feature flag, and nothing here takes a shell, mode, variant, or
 * `isLab` discriminant. A branch inside the shared core is a fork with extra
 * steps and its branches drift independently.
 *
 * The shape mirrors the API, and the API keeps the provenance-and-status
 * concepts separate on purpose. `origin` is about the configuration document.
 * `source.mode` is about where evidence comes from. `lifecycle_status` is
 * about the site's own life. `template` is provenance about which template the
 * foundation was copied from. There is no `created_in_lab` or
 * `is_simulator_site` field, because which shell created a site is not a
 * property of the site.
 *
 * There is no evidence-derived field at all: no last-data timestamp, no source
 * health, no evidence availability, no analytics. Each arrives with the
 * evidence that fills it.
 */

export interface SiteLocationReadModel {
  country: string;
  locality: string;
}

export interface SiteTemplateProvenanceReadModel {
  template_id: string;
  template_version: number;
}

export interface SiteSourceReadModel {
  mode: string;
}

/** One configured site, as the Sites index reads it. */
export interface SiteSummary {
  site_id: string;
  display_name: string;
  site_type: string;
  location: SiteLocationReadModel;
  timezone: string;
  lifecycle_status: string;
  origin: string;
  source: SiteSourceReadModel;
  template: SiteTemplateProvenanceReadModel | null;
}

/**
 * "No sites are configured" and "the site store could not be read" are
 * different facts, so they are different states. Neither is allowed to degrade
 * into the other: an index that says nothing is configured when it simply
 * could not look is making a claim it cannot back.
 */
export type SiteListResult =
  | { status: "loaded"; sites: SiteSummary[] }
  | { status: "unavailable" };

/**
 * A declared design rating on a configured component.
 *
 * Nameplate intent from the configuration document, never a measurement. A
 * component that declares no rating carries `null` rather than a zero: no
 * rating and a rating of zero are different facts, and only one of them is
 * something the document says.
 */
export interface SiteRatingReadModel {
  value: number;
  unit: string;
}

/** One component a site's foundation declares. */
export interface SiteComponentReadModel {
  component_id: string;
  component_type: string;
  display_name: string;
  rating: SiteRatingReadModel | null;
}

/**
 * One position in a site's declared electrical topology.
 *
 * A node is not a component. It is the place a declared component occupies,
 * and `componentId` always names a component the same foundation declares -
 * the backend refuses a document where it does not, so nothing here has to
 * cope with a reference that dangles.
 */
export interface TopologyNodeReadModel {
  node_id: string;
  component_id: string;
  node_role: string;
}

/**
 * One declared connection between two topology nodes.
 *
 * The direction is the direction the document declares. It is not a
 * measurement, and nothing on a screen may present it as flow.
 */
export interface TopologyConnectionReadModel {
  connection_id: string;
  from_node: string;
  to_node: string;
  medium: string;
}

export interface FoundationTopologyReadModel {
  nodes: TopologyNodeReadModel[];
  connections: TopologyConnectionReadModel[];
}

/**
 * One signal a declared device is configured to be able to report.
 *
 * Availability, never a reading. There is no value field, no timestamp and no
 * cadence, so no screen can render a measurement out of this and no screen has
 * to decide what a missing one would mean.
 */
export interface DeviceSignalReadModel {
  signal_id: string;
  display_name: string;
  unit: string;
}

/**
 * One device the foundation declares.
 *
 * A configured asset awaiting runtime and evidence. It is never healthy,
 * online, offline, stale or degraded: this record carries no field that could
 * say so, which is what keeps a device table from becoming a status board.
 */
export interface FoundationDeviceReadModel {
  device_id: string;
  device_type: string;
  display_name: string;
  component_id: string;
  signals: DeviceSignalReadModel[];
}

/** One declared binding from a device signal to the component it describes. */
export interface SignalMappingReadModel {
  mapping_id: string;
  device_id: string;
  signal_id: string;
  component_id: string;
}

/**
 * One declared assumption about how a site is expected to be operated.
 *
 * `component_id` is `null` when the assumption is about the site rather than
 * one component. It is not a control model: there is no state, no setpoint and
 * no breaker position here, because that vocabulary is not decided.
 */
export interface ControlAssumptionReadModel {
  assumption_id: string;
  display_name: string;
  component_id: string | null;
  basis: string;
  statement: string;
}

/**
 * The foundation on a site record.
 *
 * The version and the start of the validity interval are metadata about the
 * configuration document; the summary and the components are the document's
 * content, and they arrive here with the surface that renders them.
 *
 * There is no `valid_to`. The validity interval is open-ended because a
 * foundation stays valid until a later version supersedes it, and M1 has no
 * mechanism that produces a later version. A field carrying an invented end
 * would state when this configuration stops being true.
 *
 * Topology, devices, signal mappings and control assumptions arrive with T014,
 * and each is `null` when this site's foundation declares none. `null` is the
 * only way that is said, because the backend refuses an empty list: `[]` would
 * let a screen state that this site HAS no devices, and what is true is
 * narrower - its configuration document declares none. A screen has to be able
 * to tell those apart, so the read model does.
 */
export interface SiteFoundationReadModel {
  version: number;
  valid_from: string;
  summary: string;
  components: SiteComponentReadModel[];
  topology: FoundationTopologyReadModel | null;
  devices: FoundationDeviceReadModel[] | null;
  signal_mappings: SignalMappingReadModel[] | null;
  control_assumptions: ControlAssumptionReadModel[] | null;
}

/**
 * One configured site, as a site page reads it.
 *
 * Everything the Sites index reads, plus foundation metadata. There is still
 * no evidence-derived field of any kind: no last-data timestamp, no source
 * health, no evidence availability, no analytics. A configuration-only site
 * has none of those, and a field carrying a zero or a plausible default would
 * be a claim the product cannot back.
 */
export interface SiteDetailReadModel extends SiteSummary {
  foundation: SiteFoundationReadModel;
}

/**
 * Three outcomes, and none may degrade into another.
 *
 * "This site is not configured", "the store could not be read", and "here is
 * the site" are different facts. An unknown site is `not_found`, which a page
 * states explicitly; it is never rendered as a site with empty fields, which
 * would claim the product knows a site it does not know.
 */
export type SiteDetailResult =
  | { status: "loaded"; site: SiteDetailReadModel }
  | { status: "not_found" }
  | { status: "unavailable" };
