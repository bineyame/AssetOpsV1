/**
 * The single-line-diagram view model: canonical Foundation topology, bound to
 * the hybrid mini-grid archetype, as something a renderer can draw.
 *
 * Nothing here renders. This module is a pure function over a
 * `SiteDetailReadModel` and has no React import, no element, and no string a
 * screen shows today. The renderer is a later slice, and keeping the boundary
 * at a record rather than at a component is what makes the rules below
 * testable without a screen to argue about.
 *
 * ## The one rule this module must not break
 *
 * The archetype is presentation and nothing else. It decides visual roles,
 * approximate positions, symbols, connection routing, and where later value
 * slots hang. It may not create, remove, rename, reorder or reinterpret a
 * single canonical component, connection, device, signal, mapping or rating.
 *
 * Concretely: every node and every connection it produces carries a Foundation
 * identity, and no Foundation identity is missing from the output. If that
 * holds, the archetype cannot have become a second topology model, which is
 * the failure this boundary exists to prevent. A diagram that quietly knows a
 * different topology from the record is a diagram nobody can check.
 *
 * ## Binding is by canonical type and role
 *
 * Nothing below binds by `site_id`, by a component identity, by a display
 * name, by a mockup label, or by a position in an array. The lane a node sits
 * in comes from its `node_role`; its symbol and visual role come from its
 * component's `component_type`; a connection's stroke comes from its declared
 * `medium`. A site that declares the same shape with different identities, in
 * a different order, gets the same drawing.
 *
 * The one place identity is touched is the tiebreak between two nodes that
 * share a lane AND a component type, where the component identity orders them.
 * That is a tiebreak, not a binding: it decides which of two identical-looking
 * siblings is drawn above the other and decides nothing else. Without it the
 * only available tiebreak would be document order, which is exactly what must
 * not decide anything.
 *
 * ## Unsupported topology is a refusal, not a smaller drawing
 *
 * When the archetype meets something it cannot place, the whole result is
 * unavailable with a stable reason. It does not drop the node, skip the
 * connection, fall back to a generic graph, or draw the part it understood as
 * though it were the site. A partial diagram presented as complete is the
 * worst outcome available here: it is wrong and it looks right.
 *
 * Every reason in `SLD_UNAVAILABLE_CODES` is reachable, and a test builds a
 * document for each one. A refusal nothing can trigger is not a refusal.
 *
 * ## Two vocabularies this module deliberately does not settle
 *
 * Whether a breaker is a device, component state, or both - and what the
 * control-state vocabulary is - is undecided, and the T016 review owns it.
 * This module therefore carries no control field at all: not a state, not a
 * mode, not a position, and not a declared control assumption. The Foundation
 * screen already states the declared assumptions in words; carrying them into
 * a diagram model would be the first place a control vocabulary could appear
 * by accident.
 *
 * How a cold room relates to mini-grid electrical topology is undecided too.
 * The archetype reserves a symbol for a declared cold room, and marks it as a
 * candidate carrying the question it does not answer, so T016 reviews a
 * proposal rather than inheriting a decision.
 *
 * ## The value slots carry nothing
 *
 * Every node and every connection has named, empty runtime and evidence slots.
 * Empty means empty: no value, no timestamp, no freshness, no quality, no
 * health, no source, no run, and no evidence metadata - not even a `null`
 * field named for a reading, because a field named for a reading is already a
 * claim that a reading is what belongs there. They are frozen, so this build
 * cannot fill one by accident.
 */

import type {
  FoundationDeviceReadModel,
  SignalMappingReadModel,
  SiteComponentReadModel,
  SiteDetailReadModel,
  SiteRatingReadModel,
  TopologyConnectionReadModel,
  TopologyNodeReadModel,
} from "./siteReadModel";

/** Which archetype produced a compatible view model. */
export const HYBRID_MINI_GRID_ARCHETYPE = "hybrid-mini-grid";

/**
 * Where a node sits on the archetype's lattice.
 *
 * Approximate, and deliberately unitless. A column is a lane in the archetype,
 * a row is a position within it. Turning these into pixels is the renderer's
 * job and a later slice's decision; a view model that carried pixels would be
 * making layout decisions with no viewport in front of it.
 */
export interface SldPosition {
  column: number;
  row: number;
}

/**
 * How a node is drawn, as distinct from where.
 *
 * A presentation concept, not a topology one. `TERMINAL` is drawn as an end
 * block, `INLINE` sits in a run between two things, `BUSBAR` is drawn as a
 * bar. Two components with different topology roles can share a visual role,
 * and that is the point of having one.
 */
export type SldVisualRole = "TERMINAL" | "INLINE" | "BUSBAR";

/** The symbol the archetype draws for a component. A presentation key. */
export type SldSymbol =
  | "PV_ARRAY"
  | "INVERTER"
  | "BATTERY"
  | "POWER_CONVERSION_SYSTEM"
  | "GENERATOR"
  | "FUEL_TANK"
  | "BUSBAR"
  | "METER"
  | "LOAD"
  | "COLD_ROOM";

/** How a connection's run is drawn, from its declared medium. */
export type SldStroke = "SOLID" | "DASHED" | "DOTTED";

/**
 * A presentational treatment the archetype proposes and does not settle.
 *
 * `settled` is the literal `false` so nothing in this build can mark one
 * decided. The question travels with the treatment, so the slice that renders
 * it renders the question with it.
 */
export interface SldCandidateTreatment {
  question: string;
  settled: false;
}

/**
 * The cold-room question, carried rather than answered.
 *
 * The archetype needs some symbol for a declared cold room or it could not
 * draw a site that has one. Choosing one quietly would settle how a process
 * asset relates to an electrical single line, which is a domain decision this
 * slice is not entitled to make.
 */
export const COLD_ROOM_TREATMENT_CANDIDATE: SldCandidateTreatment = {
  question:
    "How a cold room's process symbol relates to mini-grid electrical " +
    "topology is not decided. The archetype draws it in the lane its declared " +
    "topology role puts it in, which is a proposal for review and not a " +
    "statement that a process asset and an electrical asset are the same kind " +
    "of thing.",
  settled: false,
};

/**
 * A named place a later runtime or evidence overlay may bind to.
 *
 * `Record<string, never>` is not a stylistic choice: it makes a slot with a
 * field in it a type error rather than a code review question. The slot's name
 * is its position on the node - `slots.runtime`, `slots.evidence` - and that
 * is the whole of what this slice commits to.
 */
export type SldValueSlot = Record<string, never>;

/**
 * The two overlay boundaries, named and empty.
 *
 * They are two rather than one because they are different boundaries with
 * different rules. Runtime values arrive from a Simulator Lab run and are
 * never product evidence; evidence values arrive only from accepted AssetOps
 * evidence and are never simulator truth. One shared slot would be the seam
 * between them collapsing into a field.
 */
export interface SldValueSlots {
  runtime: SldValueSlot;
  evidence: SldValueSlot;
}

/** A canonical component, referenced rather than restated. */
export interface SldComponentRefView {
  componentId: string;
  componentType: string;
  displayName: string;
}

/** A declared device, at the component its document attaches it to. */
export interface SldAttachedDeviceView {
  deviceId: string;
  deviceType: string;
  displayName: string;
}

/**
 * One signal that is available about a component, from a declared mapping.
 *
 * Availability, never a reading. The mapping is what says which component a
 * signal describes, and it is deliberately not the device's own component: a
 * meter attached at the metering point describes the load and the bus, and
 * taking the device's component instead would look right on every other row.
 *
 * Every field traces to the document: the mapping declares the identity, the
 * device declares the signal's name and unit.
 */
export interface SldAvailableSignalView {
  mappingId: string;
  deviceId: string;
  deviceName: string;
  signalId: string;
  signalName: string;
  unit: string;
}

/**
 * One node of the diagram.
 *
 * The first block is canonical and copied, not derived. The second block is
 * the archetype's, and is the only thing in this file the archetype decides.
 */
export interface SldNodeView {
  nodeId: string;
  componentId: string;
  componentType: string;
  nodeRole: string;
  displayName: string;
  rating: SiteRatingReadModel | null;

  visualRole: SldVisualRole;
  symbol: SldSymbol;
  position: SldPosition;
  candidate: SldCandidateTreatment | null;

  attachedDevices: SldAttachedDeviceView[];
  availableSignals: SldAvailableSignalView[];
  slots: SldValueSlots;
}

/** Where a connection runs, on the archetype's lattice. */
export interface SldRouteView {
  from: SldPosition;
  to: SldPosition;
  /** Which axis the run turns on first. */
  turn: "COLUMN_FIRST" | "ROW_FIRST";
  stroke: SldStroke;
}

/**
 * One connection of the diagram.
 *
 * The direction is the document's declared direction. It is not flow, nothing
 * has flowed, and no slot below says otherwise.
 */
export interface SldConnectionView {
  connectionId: string;
  fromNodeId: string;
  toNodeId: string;
  medium: string;
  route: SldRouteView;
  slots: SldValueSlots;
}

/**
 * What the Foundation declares that the diagram has no place for.
 *
 * Stated rather than dropped. A component with no topology node is not in the
 * topology, and a mapping about it has nowhere on the drawing to hang - but
 * both are declared facts, and a diagram that quietly omitted them would be
 * hiding part of the document it claims to draw.
 */
export interface SldUnplacedView {
  components: SldComponentRefView[];
  devices: SldAttachedDeviceView[];
  signals: SldAvailableSignalView[];
}

/** How far the lattice extends, so a renderer can scale it. */
export interface SldExtent {
  columns: number;
  rows: number;
}

export interface SldDiagramView {
  archetype: string;
  extent: SldExtent;
  nodes: SldNodeView[];
  connections: SldConnectionView[];
  unplaced: SldUnplacedView;
}

/**
 * Why the archetype cannot draw this site.
 *
 * Every code is reachable and a test builds a document for each. The checks
 * run in the order listed, so a document that trips two reports the first.
 */
export const SLD_UNAVAILABLE_CODES = [
  "SITE_TYPE_NOT_SUPPORTED",
  "NO_TOPOLOGY_DECLARED",
  "REFERENCE_UNRESOLVED",
  "UNSUPPORTED_NODE_ROLE",
  "UNSUPPORTED_COMPONENT_TYPE",
  "BUS_CARDINALITY_UNSUPPORTED",
  "UNSUPPORTED_CONNECTION_MEDIUM",
] as const;

export type SldUnavailableCode = (typeof SLD_UNAVAILABLE_CODES)[number];

/**
 * A refusal a screen can render.
 *
 * `code` is stable and is what a test or a later screen branches on.
 * `statement` is the same sentence every time that code is produced, so two
 * surfaces cannot explain the same refusal differently. `detail` is what in
 * this particular document produced it, in the document's own words, because
 * a refusal that does not say which node it choked on leaves a reader with
 * nothing to act on.
 */
export interface SldUnavailableReason {
  code: SldUnavailableCode;
  statement: string;
  detail: string;
}

export const SLD_UNAVAILABLE_STATEMENTS: Record<SldUnavailableCode, string> = {
  SITE_TYPE_NOT_SUPPORTED:
    "The hybrid mini-grid archetype draws mini-grid sites. This site is " +
    "configured as another kind of site, so the archetype has no drawing for " +
    "it.",
  NO_TOPOLOGY_DECLARED:
    "This site's foundation document declares no topology, so there is " +
    "nothing to draw. The components it declares are listed on the " +
    "foundation; how they connect is a separate declaration this document " +
    "does not make.",
  REFERENCE_UNRESOLVED:
    "This site's foundation refers to something it does not declare, so the " +
    "archetype cannot resolve what to draw. Nothing is drawn rather than a " +
    "drawing with a gap in it.",
  UNSUPPORTED_NODE_ROLE:
    "This site's topology places a component in a role the hybrid mini-grid " +
    "archetype has no lane for. The archetype has a fixed arrangement and " +
    "does not invent a place for a role it does not know.",
  UNSUPPORTED_COMPONENT_TYPE:
    "This site declares a component the hybrid mini-grid archetype has no " +
    "symbol for. Drawing it as something else would misname an asset, so " +
    "nothing is drawn.",
  BUS_CARDINALITY_UNSUPPORTED:
    "The hybrid mini-grid archetype is arranged around exactly one AC bus. " +
    "This site's topology does not declare exactly one, so the arrangement " +
    "does not apply to it.",
  UNSUPPORTED_CONNECTION_MEDIUM:
    "This site declares a connection carrying something the hybrid mini-grid " +
    "archetype cannot route. The connection is not dropped and the rest is " +
    "not drawn without it.",
};

/**
 * Either a diagram the archetype can draw, or the reason it cannot.
 *
 * Two states, and neither degrades into the other. There is no partial
 * diagram, no empty diagram, and no diagram flagged as incomplete.
 */
export type SiteSldView =
  | { status: "compatible"; diagram: SldDiagramView }
  | { status: "unavailable"; reason: SldUnavailableReason };

/**
 * The lane each topology role occupies, left to right.
 *
 * Closed. A role with no entry here is a role the archetype cannot place, and
 * that is a refusal rather than a default lane, because a default lane is how
 * a diagram comes to show a component somewhere meaningless.
 *
 * Generation, storage and fuel storage share the left lane: they are the
 * things that supply the bus or supply the things that supply it. Conversion
 * sits between them and the bus, metering after it, load at the end.
 */
const ARCHETYPE_LANES: Record<string, number> = {
  GENERATION: 0,
  STORAGE: 0,
  FUEL_STORAGE: 0,
  CONVERSION: 1,
  BUS: 2,
  METERING: 3,
  LOAD: 4,
};

/**
 * The symbol drawn for each component type. Closed, for the same reason.
 *
 * Kept separate from `component_type` even where the two spell the same word.
 * A symbol is a presentation key: two component types may come to share one,
 * or one may be drawn differently, and neither should require touching the
 * canonical component vocabulary.
 */
const ARCHETYPE_SYMBOLS: Record<string, SldSymbol> = {
  PV_ARRAY: "PV_ARRAY",
  INVERTER: "INVERTER",
  BATTERY: "BATTERY",
  POWER_CONVERSION_SYSTEM: "POWER_CONVERSION_SYSTEM",
  GENERATOR: "GENERATOR",
  FUEL_TANK: "FUEL_TANK",
  AC_BUS: "BUSBAR",
  METER: "METER",
  LOAD: "LOAD",
  COLD_ROOM: "COLD_ROOM",
};

/** How each component type is drawn, as opposed to which symbol it gets. */
const ARCHETYPE_VISUAL_ROLES: Record<string, SldVisualRole> = {
  PV_ARRAY: "TERMINAL",
  INVERTER: "INLINE",
  BATTERY: "TERMINAL",
  POWER_CONVERSION_SYSTEM: "INLINE",
  GENERATOR: "TERMINAL",
  FUEL_TANK: "TERMINAL",
  AC_BUS: "BUSBAR",
  METER: "INLINE",
  LOAD: "TERMINAL",
  COLD_ROOM: "TERMINAL",
};

/** How a run is drawn, by what the document says it carries. */
const ARCHETYPE_STROKES: Record<string, SldStroke> = {
  AC: "SOLID",
  DC: "DASHED",
  FUEL: "DOTTED",
};

/**
 * The order same-lane component types stack in.
 *
 * This is what makes a row a decision of the archetype rather than a
 * consequence of where a node happened to appear in the document.
 */
const ARCHETYPE_STACK_ORDER: string[] = [
  "PV_ARRAY",
  "INVERTER",
  "BATTERY",
  "POWER_CONVERSION_SYSTEM",
  "GENERATOR",
  "FUEL_TANK",
  "AC_BUS",
  "METER",
  "LOAD",
  "COLD_ROOM",
];

/** The component types the archetype treats as a reviewable candidate only. */
const ARCHETYPE_CANDIDATES: Record<string, SldCandidateTreatment> = {
  COLD_ROOM: COLD_ROOM_TREATMENT_CANDIDATE,
};

/**
 * Named, empty, and frozen.
 *
 * A fresh pair per node and per connection rather than one shared object, so
 * nothing downstream can discover that two nodes share a slot and start
 * treating that as meaningful. Frozen so this build cannot fill one: the rule
 * is not "these happen to be unset", it is "these carry nothing".
 */
function emptyValueSlots(): SldValueSlots {
  return Object.freeze({
    runtime: Object.freeze({}),
    evidence: Object.freeze({}),
  });
}

function unavailable(
  code: SldUnavailableCode,
  detail: string,
): SiteSldView {
  return {
    status: "unavailable",
    reason: { code, statement: SLD_UNAVAILABLE_STATEMENTS[code], detail },
  };
}

function indexComponents(
  components: SiteComponentReadModel[],
): Map<string, SiteComponentReadModel> {
  const byId = new Map<string, SiteComponentReadModel>();
  for (const component of components) {
    byId.set(component.component_id, component);
  }
  return byId;
}

/**
 * The row a node takes within its lane.
 *
 * Computed from the lane's membership under the archetype's stack order, with
 * the component identity as the tiebreak between two members that share a
 * component type. Document order is not consulted, which is the property the
 * reordering test exists to hold.
 */
function assignRows(
  nodes: TopologyNodeReadModel[],
  components: Map<string, SiteComponentReadModel>,
): Map<string, number> {
  const lanes = new Map<string, TopologyNodeReadModel[]>();
  for (const node of nodes) {
    const lane = `${ARCHETYPE_LANES[node.node_role]}`;
    const members = lanes.get(lane) ?? [];
    members.push(node);
    lanes.set(lane, members);
  }

  const rows = new Map<string, number>();
  for (const members of lanes.values()) {
    const ordered = [...members].sort((left, right) => {
      const leftType = components.get(left.component_id)?.component_type ?? "";
      const rightType = components.get(right.component_id)?.component_type ?? "";
      const byType =
        ARCHETYPE_STACK_ORDER.indexOf(leftType) -
        ARCHETYPE_STACK_ORDER.indexOf(rightType);
      if (byType !== 0) return byType;
      return left.component_id < right.component_id ? -1 : 1;
    });

    ordered.forEach((node, row) => rows.set(node.node_id, row));
  }

  return rows;
}

function availableSignal(
  mapping: SignalMappingReadModel,
  devices: Map<string, FoundationDeviceReadModel>,
): SldAvailableSignalView | null {
  const device = devices.get(mapping.device_id);
  if (device === undefined) return null;

  const signal = device.signals.find(
    (candidate) => candidate.signal_id === mapping.signal_id,
  );
  if (signal === undefined) return null;

  return {
    mappingId: mapping.mapping_id,
    deviceId: device.device_id,
    deviceName: device.display_name,
    signalId: signal.signal_id,
    signalName: signal.display_name,
    unit: signal.unit,
  };
}

/**
 * The hybrid mini-grid view model for a site, or the reason there is none.
 *
 * Pure: it reads the record it is given and touches nothing else.
 */
export function deriveSiteSldView(site: SiteDetailReadModel): SiteSldView {
  if (site.site_type !== "MINIGRID") {
    return unavailable(
      "SITE_TYPE_NOT_SUPPORTED",
      `The site is configured as ${site.site_type}.`,
    );
  }

  const topology = site.foundation.topology;
  if (topology === null) {
    return unavailable(
      "NO_TOPOLOGY_DECLARED",
      "The foundation declares no topology section.",
    );
  }

  const components = indexComponents(site.foundation.components);
  const devices = site.foundation.devices ?? [];
  const mappings = site.foundation.signal_mappings ?? [];

  const devicesById = new Map<string, FoundationDeviceReadModel>();
  for (const device of devices) {
    devicesById.set(device.device_id, device);
  }

  // --- References resolve, or nothing is drawn -----------------------------
  //
  // The backend refuses a document whose references dangle, so none of these
  // should be reachable from the store. They are checked anyway because the
  // alternative to checking is drawing a node with no component, an edge to
  // nowhere, or a signal with no name - three quiet ways for a diagram to
  // disagree with the record it is supposedly of.
  for (const node of topology.nodes) {
    if (!components.has(node.component_id)) {
      return unavailable(
        "REFERENCE_UNRESOLVED",
        `Topology node ${node.node_id} names component ` +
          `${node.component_id}, which the foundation does not declare.`,
      );
    }
  }

  const nodesById = new Map<string, TopologyNodeReadModel>();
  for (const node of topology.nodes) {
    nodesById.set(node.node_id, node);
  }

  for (const connection of topology.connections) {
    for (const endpoint of [connection.from_node, connection.to_node]) {
      if (!nodesById.has(endpoint)) {
        return unavailable(
          "REFERENCE_UNRESOLVED",
          `Connection ${connection.connection_id} names node ${endpoint}, ` +
            "which the topology does not declare.",
        );
      }
    }
  }

  for (const mapping of mappings) {
    if (availableSignal(mapping, devicesById) === null) {
      return unavailable(
        "REFERENCE_UNRESOLVED",
        `Mapping ${mapping.mapping_id} names signal ${mapping.signal_id} on ` +
          `device ${mapping.device_id}, which is not a signal that device ` +
          "declares.",
      );
    }
  }

  // --- Everything the archetype meets, it must be able to place ------------
  for (const node of topology.nodes) {
    if (!(node.node_role in ARCHETYPE_LANES)) {
      return unavailable(
        "UNSUPPORTED_NODE_ROLE",
        `Topology node ${node.node_id} has role ${node.node_role}.`,
      );
    }

    const componentType = components.get(node.component_id)?.component_type;
    if (componentType === undefined || !(componentType in ARCHETYPE_SYMBOLS)) {
      return unavailable(
        "UNSUPPORTED_COMPONENT_TYPE",
        `Topology node ${node.node_id} is a ${componentType} component.`,
      );
    }
  }

  const buses = topology.nodes.filter((node) => node.node_role === "BUS");
  if (buses.length !== 1) {
    return unavailable(
      "BUS_CARDINALITY_UNSUPPORTED",
      `The topology declares ${buses.length} nodes in the BUS role.`,
    );
  }

  for (const connection of topology.connections) {
    if (!(connection.medium in ARCHETYPE_STROKES)) {
      return unavailable(
        "UNSUPPORTED_CONNECTION_MEDIUM",
        `Connection ${connection.connection_id} carries ${connection.medium}.`,
      );
    }
  }

  // --- Placement ----------------------------------------------------------
  const rows = assignRows(topology.nodes, components);
  const positions = new Map<string, SldPosition>();
  for (const node of topology.nodes) {
    positions.set(node.node_id, {
      column: ARCHETYPE_LANES[node.node_role],
      row: rows.get(node.node_id) ?? 0,
    });
  }

  const placedComponents = new Set(
    topology.nodes.map((node) => node.component_id),
  );

  // Nodes come out in the document's own order. The document's order is a
  // canonical fact and preserving it costs nothing; what must not happen is
  // the archetype deciding anything FROM it, and it does not - every position
  // above was computed without consulting it.
  const nodes: SldNodeView[] = topology.nodes.map(
    (node: TopologyNodeReadModel) => {
      const component = components.get(node.component_id) as SiteComponentReadModel;
      const position = positions.get(node.node_id) as SldPosition;

      return {
        nodeId: node.node_id,
        componentId: component.component_id,
        componentType: component.component_type,
        nodeRole: node.node_role,
        displayName: component.display_name,
        rating: component.rating,

        visualRole: ARCHETYPE_VISUAL_ROLES[component.component_type],
        symbol: ARCHETYPE_SYMBOLS[component.component_type],
        position,
        candidate: ARCHETYPE_CANDIDATES[component.component_type] ?? null,

        attachedDevices: devices
          .filter((device) => device.component_id === component.component_id)
          .map((device) => ({
            deviceId: device.device_id,
            deviceType: device.device_type,
            displayName: device.display_name,
          })),
        // From the mappings, never from the devices attached here. Which
        // component a signal describes is the mapping's own declaration.
        availableSignals: mappings
          .filter((mapping) => mapping.component_id === component.component_id)
          .map(
            (mapping) =>
              availableSignal(mapping, devicesById) as SldAvailableSignalView,
          ),
        slots: emptyValueSlots(),
      };
    },
  );

  const connections: SldConnectionView[] = topology.connections.map(
    (connection: TopologyConnectionReadModel) => {
      const from = positions.get(connection.from_node) as SldPosition;
      const to = positions.get(connection.to_node) as SldPosition;

      return {
        connectionId: connection.connection_id,
        fromNodeId: connection.from_node,
        toNodeId: connection.to_node,
        medium: connection.medium,
        route: {
          from,
          to,
          turn: from.column === to.column ? "ROW_FIRST" : "COLUMN_FIRST",
          stroke: ARCHETYPE_STROKES[connection.medium],
        },
        slots: emptyValueSlots(),
      };
    },
  );

  const unplacedComponents = site.foundation.components.filter(
    (component) => !placedComponents.has(component.component_id),
  );

  const unplaced: SldUnplacedView = {
    components: unplacedComponents.map((component) => ({
      componentId: component.component_id,
      componentType: component.component_type,
      displayName: component.display_name,
    })),
    devices: devices
      .filter((device) => !placedComponents.has(device.component_id))
      .map((device) => ({
        deviceId: device.device_id,
        deviceType: device.device_type,
        displayName: device.display_name,
      })),
    signals: mappings
      .filter((mapping) => !placedComponents.has(mapping.component_id))
      .map(
        (mapping) =>
          availableSignal(mapping, devicesById) as SldAvailableSignalView,
      ),
  };

  const extent: SldExtent = {
    columns:
      nodes.length === 0
        ? 0
        : Math.max(...nodes.map((node) => node.position.column)) + 1,
    rows:
      nodes.length === 0
        ? 0
        : Math.max(...nodes.map((node) => node.position.row)) + 1,
  };

  return {
    status: "compatible",
    diagram: {
      archetype: HYBRID_MINI_GRID_ARCHETYPE,
      extent,
      nodes,
      connections,
      unplaced,
    },
  };
}
