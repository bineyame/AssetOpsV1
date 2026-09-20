import { describe, expect, it } from "vitest";

import type { SiteDetailReadModel } from "../siteReadModel";
import {
  type SldValueSlot,
  HYBRID_MINI_GRID_ARCHETYPE,
  SLD_UNAVAILABLE_CODES,
  SLD_UNAVAILABLE_STATEMENTS,
  deriveSiteSldView,
} from "../sldViewModel";
import type {
  SldNodeView,
  SldUnavailableCode,
  SiteSldView,
} from "../sldViewModel";

import {
  HYBRID_MINI_GRID_SITE,
  UNDECLARED_TOPOLOGY_SITE,
  withReorderedTopology,
} from "./sldFixtures";

/**
 * The SLD view model, tested against records.
 *
 * This slice renders nothing, and that is the reason this file can be strict.
 * A view model with no renderer can be compared to the document it came from
 * field by field, with no screen in between to argue about, so every rule the
 * archetype has to obey is an assertion here rather than a convention.
 */

function compatible(site: SiteDetailReadModel) {
  const result = deriveSiteSldView(site);

  expect(result.status).toBe("compatible");
  if (result.status !== "compatible") {
    throw new Error(`expected a compatible view model, got ${result.status}`);
  }
  return result.diagram;
}

function node(site: SiteDetailReadModel, nodeId: string): SldNodeView {
  const found = compatible(site).nodes.find((entry) => entry.nodeId === nodeId);
  if (found === undefined) throw new Error(`no node ${nodeId}`);
  return found;
}

/**
 * Every key, at every depth, as a dotted path with array indices elided.
 *
 * Paths rather than bare keys because two of the names a field ban has to
 * catch are legitimate in exactly one position and nowhere else: `value` is
 * legitimate under `rating`, where it is the declared nameplate number the
 * document carries, and `evidence` is legitimate under `slots`, where it is
 * the name of the empty slot. A ban written against bare keys has to be
 * loosened to let those through, and loosening it is how it stops catching
 * `node.value` and `slots.evidence.value`.
 */
function allPaths(value: unknown, prefix = "", paths: string[] = []): string[] {
  if (Array.isArray(value)) {
    for (const entry of value) allPaths(entry, prefix, paths);
    return paths;
  }
  if (value !== null && typeof value === "object") {
    for (const [key, child] of Object.entries(value)) {
      const path = prefix === "" ? key : `${prefix}.${key}`;
      paths.push(path);
      allPaths(child, path, paths);
    }
  }
  return paths;
}

/** The last segment of each path: the field names, without their position. */
function allKeys(value: unknown): string[] {
  return allPaths(value).map((path) => path.split(".").slice(-1)[0]);
}

/** Every string, at every depth, in a plain object graph. */
function allStrings(value: unknown, strings: string[] = []): string[] {
  if (typeof value === "string") {
    strings.push(value);
    return strings;
  }
  if (Array.isArray(value)) {
    for (const entry of value) allStrings(entry, strings);
    return strings;
  }
  if (value !== null && typeof value === "object") {
    for (const child of Object.values(value)) allStrings(child, strings);
  }
  return strings;
}

/**
 * Canonical topology authority.
 *
 * The one assertion this whole slice is built around: the archetype owns
 * presentation and nothing else, so every node and connection it produces
 * traces to a Foundation identity, and no Foundation identity goes missing.
 * If this holds, the archetype cannot have become a second topology model.
 */
describe("the archetype introduces no topology of its own", () => {
  const site = HYBRID_MINI_GRID_SITE;

  it("produces exactly the nodes the Foundation declares", () => {
    const declared = (site.foundation.topology?.nodes ?? []).map(
      (entry) => entry.node_id,
    );

    expect(
      [...compatible(site).nodes.map((entry) => entry.nodeId)].sort(),
    ).toEqual([...declared].sort());
  });

  it("produces exactly the connections the Foundation declares", () => {
    const declared = (site.foundation.topology?.connections ?? []).map(
      (entry) => entry.connection_id,
    );

    expect(
      [...compatible(site).connections.map((entry) => entry.connectionId)].sort(),
    ).toEqual([...declared].sort());
  });

  it("points every connection at nodes the Foundation declares", () => {
    const diagram = compatible(site);
    const nodeIds = new Set(diagram.nodes.map((entry) => entry.nodeId));

    for (const connection of diagram.connections) {
      expect(nodeIds.has(connection.fromNodeId)).toBe(true);
      expect(nodeIds.has(connection.toNodeId)).toBe(true);
    }
  });

  it("names on every node the component the topology node names", () => {
    const declared = new Map(
      (site.foundation.topology?.nodes ?? []).map((entry) => [
        entry.node_id,
        entry.component_id,
      ]),
    );

    for (const entry of compatible(site).nodes) {
      expect(entry.componentId).toBe(declared.get(entry.nodeId));
    }
  });

  it("introduces no device, signal, or mapping of its own", () => {
    const diagram = compatible(site);

    const declaredDevices = new Set(
      (site.foundation.devices ?? []).map((device) => device.device_id),
    );
    const declaredMappings = (site.foundation.signal_mappings ?? []).map(
      (mapping) => mapping.mapping_id,
    );

    const producedDevices = [
      ...diagram.nodes.flatMap((entry) =>
        entry.attachedDevices.map((device) => device.deviceId),
      ),
      ...diagram.unplaced.devices.map((device) => device.deviceId),
    ];
    const producedMappings = [
      ...diagram.nodes.flatMap((entry) =>
        entry.availableSignals.map((signal) => signal.mappingId),
      ),
      ...diagram.unplaced.signals.map((signal) => signal.mappingId),
    ];

    for (const deviceId of producedDevices) {
      expect(declaredDevices.has(deviceId)).toBe(true);
    }
    // Every declared mapping appears exactly once: none invented, none
    // silently dropped, and none counted twice.
    expect([...producedMappings].sort()).toEqual([...declaredMappings].sort());
  });

  it("states a declared component the topology does not place", () => {
    // Not dropped. A component with no topology node is not in the topology,
    // but it is still something the document declares, and a diagram that
    // quietly omitted it would be hiding part of its own source.
    const withSpare: SiteDetailReadModel = {
      ...site,
      foundation: {
        ...site.foundation,
        components: [
          ...site.foundation.components,
          {
            component_id: "c-spare-meter",
            component_type: "METER",
            display_name: "Feeder meter",
            rating: null,
          },
        ],
      },
    };

    const diagram = compatible(withSpare);

    expect(diagram.nodes.map((entry) => entry.componentId)).not.toContain(
      "c-spare-meter",
    );
    expect(diagram.unplaced.components.map((entry) => entry.componentId)).toEqual(
      ["c-spare-meter"],
    );
  });
});

describe("labels, ratings and units come from the record", () => {
  it("carries the Foundation's display name, not the archetype's", () => {
    // The fixture calls its array `Rooftop PV array`; the shipped template
    // calls the same archetype component `PV array`. A view model carrying a
    // literal from the archetype would read `PV array` here and would be
    // wrong for every site that renamed anything.
    expect(node(HYBRID_MINI_GRID_SITE, "n-solar").displayName).toBe(
      "Rooftop PV array",
    );
    expect(node(HYBRID_MINI_GRID_SITE, "n-genset").displayName).toBe(
      "Diesel generator",
    );
  });

  it("carries the declared rating with its declared unit", () => {
    expect(node(HYBRID_MINI_GRID_SITE, "n-solar").rating).toEqual({
      value: 100,
      unit: "kW",
    });
    expect(node(HYBRID_MINI_GRID_SITE, "n-storage").rating).toEqual({
      value: 215,
      unit: "kWh",
    });
  });

  it("carries no rating where the document declares none", () => {
    // `null`, not a zero and not a formatted absence. No rating and a rating
    // of zero are different facts and the document states only the first.
    expect(node(HYBRID_MINI_GRID_SITE, "n-meter").rating).toBeNull();
  });

  it("carries the signal's declared name and unit from its device", () => {
    const load = node(HYBRID_MINI_GRID_SITE, "n-load");
    const power = load.availableSignals.find(
      (signal) => signal.mappingId === "m-load-power",
    );

    expect(power).toEqual({
      mappingId: "m-load-power",
      deviceId: "d-meter-unit",
      deviceName: "Site meter",
      signalId: "active-power",
      signalName: "Active power through the meter",
      unit: "kW",
    });
  });
});

describe("the archetype binds by canonical type and role", () => {
  it("decides nothing from the order of the document's arrays", () => {
    // The proof that no placement is a consequence of array position: the same
    // site with every list reversed draws the same picture.
    const straight = compatible(HYBRID_MINI_GRID_SITE);
    const reversed = compatible(withReorderedTopology(HYBRID_MINI_GRID_SITE));

    const placement = (diagram: typeof straight) =>
      [...diagram.nodes]
        .map((entry) => ({
          nodeId: entry.nodeId,
          column: entry.position.column,
          row: entry.position.row,
          symbol: entry.symbol,
          visualRole: entry.visualRole,
        }))
        .sort((left, right) => (left.nodeId < right.nodeId ? -1 : 1));

    expect(placement(reversed)).toEqual(placement(straight));
    expect(reversed.extent).toEqual(straight.extent);

    // And the nodes still come out in the document's own order, which is a
    // canonical fact worth preserving even though nothing is decided from it.
    expect(reversed.nodes.map((entry) => entry.nodeId)).toEqual(
      [...straight.nodes.map((entry) => entry.nodeId)].reverse(),
    );
  });

  it("decides nothing from a display name", () => {
    const renamed: SiteDetailReadModel = {
      ...HYBRID_MINI_GRID_SITE,
      display_name: "Some Other Site",
      site_id: "MG-001",
      foundation: {
        ...HYBRID_MINI_GRID_SITE.foundation,
        components: HYBRID_MINI_GRID_SITE.foundation.components.map(
          (component) => ({ ...component, display_name: "Renamed" }),
        ),
      },
    };

    const before = compatible(HYBRID_MINI_GRID_SITE).nodes.map((entry) => ({
      nodeId: entry.nodeId,
      position: entry.position,
      symbol: entry.symbol,
      visualRole: entry.visualRole,
    }));
    const after = compatible(renamed).nodes.map((entry) => ({
      nodeId: entry.nodeId,
      position: entry.position,
      symbol: entry.symbol,
      visualRole: entry.visualRole,
    }));

    expect(after).toEqual(before);
  });

  it("puts each topology role in the lane the archetype gives that role", () => {
    const columns = Object.fromEntries(
      compatible(HYBRID_MINI_GRID_SITE).nodes.map((entry) => [
        entry.nodeId,
        entry.position.column,
      ]),
    );

    expect(columns["n-solar"]).toBe(columns["n-genset"]);
    expect(columns["n-solar-inverter"]).toBe(columns["n-storage-pcs"]);
    expect(columns["n-solar"]).toBeLessThan(columns["n-solar-inverter"]);
    expect(columns["n-solar-inverter"]).toBeLessThan(columns["n-bus"]);
    expect(columns["n-bus"]).toBeLessThan(columns["n-meter"]);
    expect(columns["n-meter"]).toBeLessThan(columns["n-load"]);
  });

  it("gives each component type the archetype's symbol and visual role", () => {
    const bus = node(HYBRID_MINI_GRID_SITE, "n-bus");

    expect(bus.symbol).toBe("BUSBAR");
    expect(bus.visualRole).toBe("BUSBAR");
    expect(node(HYBRID_MINI_GRID_SITE, "n-solar").symbol).toBe("PV_ARRAY");
    expect(node(HYBRID_MINI_GRID_SITE, "n-solar").visualRole).toBe("TERMINAL");
    expect(node(HYBRID_MINI_GRID_SITE, "n-meter").visualRole).toBe("INLINE");
  });

  it("gives no two nodes in one lane the same row", () => {
    const seen = new Set<string>();

    for (const entry of compatible(HYBRID_MINI_GRID_SITE).nodes) {
      const cell = `${entry.position.column}/${entry.position.row}`;

      expect(seen.has(cell)).toBe(false);
      seen.add(cell);
    }
  });

  it("routes a connection from its declared medium", () => {
    const diagram = compatible(HYBRID_MINI_GRID_SITE);
    const strokes = Object.fromEntries(
      diagram.connections.map((entry) => [entry.connectionId, entry.route.stroke]),
    );

    expect(strokes["k-solar-dc"]).toBe("DASHED");
    expect(strokes["k-solar-ac"]).toBe("SOLID");
    expect(strokes["k-fuel"]).toBe("DOTTED");
  });

  it("names the archetype that drew it", () => {
    expect(compatible(HYBRID_MINI_GRID_SITE).archetype).toBe(
      HYBRID_MINI_GRID_ARCHETYPE,
    );
  });
});

describe("signal availability comes from the declared mappings", () => {
  it("attaches a signal to the component its mapping names", () => {
    // The case the whole rule exists for. The site meter is attached to the
    // metering point and describes the load and the bus. A view model taking
    // the device's own component instead would look right on every other node
    // and would put the load's power on the meter.
    const meter = node(HYBRID_MINI_GRID_SITE, "n-meter");
    const load = node(HYBRID_MINI_GRID_SITE, "n-load");
    const bus = node(HYBRID_MINI_GRID_SITE, "n-bus");

    expect(meter.attachedDevices.map((device) => device.deviceId)).toEqual([
      "d-meter-unit",
    ]);
    expect(meter.availableSignals).toEqual([]);

    expect(load.attachedDevices).toEqual([]);
    expect(load.availableSignals.map((signal) => signal.mappingId)).toEqual([
      "m-load-power",
      "m-load-energy",
    ]);
    expect(bus.availableSignals.map((signal) => signal.mappingId)).toEqual([
      "m-bus-voltage",
      "m-bus-frequency",
    ]);
  });

  it("keeps a device's attachment separate from what it describes", () => {
    const diagram = compatible(HYBRID_MINI_GRID_SITE);
    const attachedTo = (deviceId: string) =>
      diagram.nodes
        .filter((entry) =>
          entry.attachedDevices.some((device) => device.deviceId === deviceId),
        )
        .map((entry) => entry.nodeId);

    expect(attachedTo("d-meter-unit")).toEqual(["n-meter"]);
  });
});

describe("the signal selector stays inert", () => {
  it("exposes available signals and chooses none of them", () => {
    const diagram = compatible(HYBRID_MINI_GRID_SITE);

    expect(
      diagram.nodes.flatMap((entry) => entry.availableSignals).length,
    ).toBeGreaterThan(0);

    // No field selects, defaults, prefers, or highlights one. A selector is a
    // control with a choice behind it, and neither exists yet.
    expect(allKeys(diagram).join(" ")).not.toMatch(
      /select|selected|default|preferred|primary|chosen|highlight|focus/i,
    );
  });
});

describe("the runtime and evidence slots carry nothing", () => {
  it("gives every node and every connection both named slots", () => {
    const diagram = compatible(HYBRID_MINI_GRID_SITE);

    expect(diagram.nodes.length).toBeGreaterThan(0);
    expect(diagram.connections.length).toBeGreaterThan(0);

    for (const slots of [
      ...diagram.nodes.map((entry) => entry.slots),
      ...diagram.connections.map((entry) => entry.slots),
    ]) {
      expect(Object.keys(slots).sort()).toEqual(["evidence", "runtime"]);
    }
  });

  it("leaves both slots with no field at all", () => {
    const diagram = compatible(HYBRID_MINI_GRID_SITE);

    for (const slots of [
      ...diagram.nodes.map((entry) => entry.slots),
      ...diagram.connections.map((entry) => entry.slots),
    ]) {
      // Not "no value set". No field, so there is nothing named for a value,
      // a timestamp, or a quality to be absent from.
      expect(Object.keys(slots.runtime)).toEqual([]);
      expect(Object.keys(slots.evidence)).toEqual([]);
      expect(Object.getOwnPropertyNames(slots.runtime)).toEqual([]);
      expect(Object.getOwnPropertyNames(slots.evidence)).toEqual([]);
    }
  });

  it("freezes them, so this build cannot fill one by accident", () => {
    const first = compatible(HYBRID_MINI_GRID_SITE).nodes[0];

    expect(Object.isFrozen(first.slots)).toBe(true);
    expect(Object.isFrozen(first.slots.runtime)).toBe(true);
    expect(Object.isFrozen(first.slots.evidence)).toBe(true);
  });

  it("gives each node and connection its own slots", () => {
    const diagram = compatible(HYBRID_MINI_GRID_SITE);

    expect(diagram.nodes[0].slots).not.toBe(diagram.nodes[1].slots);
    expect(diagram.nodes[0].slots).not.toBe(diagram.connections[0].slots);
  });

  it("carries no runtime, evidence, or health field anywhere in the model", () => {
    // Against the whole graph, not only the slots. The slots are the obvious
    // place for one of these to appear; a field called `lastReading` on a node
    // beside them would be the same claim in a less obvious place.
    //
    // Two paths are exempt by their exact position, not by their name.
    // `rating.value` is the declared nameplate number the document carries;
    // `slots.runtime` and `slots.evidence` are the empty slots themselves. A
    // `value` anywhere else, or anything under a slot, is a claim.
    const exempt = ["rating.value", "slots.runtime", "slots.evidence"];
    const paths = allPaths(compatible(HYBRID_MINI_GRID_SITE));
    const banned =
      /\b\w*(value|reading|timestamp|freshness|quality|health|staleness|latest|observed|measured|run|evidence|envelope|ingest|telemetry|replay|finding)\w*$/i;

    expect(paths.length).toBeGreaterThan(0);
    expect(
      paths.filter(
        (path) =>
          banned.test(path) &&
          !exempt.some((allowed) => path.endsWith(allowed)),
      ),
    ).toEqual([]);
  });
});

describe("the archetype settles no undecided vocabulary", () => {
  it("uses no control-state word in a key or a value", () => {
    // The backend keeps the same territory clear: T014 scans every closed
    // vocabulary in `models.py` for these, so that whether a breaker is a
    // device, component state, or both stays open until the T016 review. A
    // diagram model is the other place that decision could be made by
    // accident, in a slot name or a symbol.
    const diagram = compatible(HYBRID_MINI_GRID_SITE);
    const text = [...allKeys(diagram), ...allStrings(diagram)].join(" ");

    expect(text.length).toBeGreaterThan(0);
    expect(text).not.toMatch(/\b(OPEN|CLOSED|TRIPPED|AUTO|MANUAL|BREAKER)\b/);
    expect(text).not.toMatch(/\bbreaker\b/i);
  });

  it("offers a cold room a symbol and marks the treatment unsettled", () => {
    const withColdRoom: SiteDetailReadModel = {
      ...HYBRID_MINI_GRID_SITE,
      foundation: {
        ...HYBRID_MINI_GRID_SITE.foundation,
        components: [
          ...HYBRID_MINI_GRID_SITE.foundation.components,
          {
            component_id: "c-cold-room",
            component_type: "COLD_ROOM",
            display_name: "Vaccine cold room",
            rating: { value: 12, unit: "kW" },
          },
        ],
        topology: {
          nodes: [
            ...(HYBRID_MINI_GRID_SITE.foundation.topology?.nodes ?? []),
            {
              node_id: "n-cold-room",
              component_id: "c-cold-room",
              node_role: "LOAD",
            },
          ],
          connections: [
            ...(HYBRID_MINI_GRID_SITE.foundation.topology?.connections ?? []),
            {
              connection_id: "k-meter-cold-room",
              from_node: "n-meter",
              to_node: "n-cold-room",
              medium: "AC",
            },
          ],
        },
      },
    };

    const coldRoom = node(withColdRoom, "n-cold-room");

    expect(coldRoom.symbol).toBe("COLD_ROOM");
    // Carried as a proposal with the question it does not answer, so the slice
    // that renders it renders the question with it.
    expect(coldRoom.candidate?.settled).toBe(false);
    expect(coldRoom.candidate?.question).toMatch(/not decided/i);

    // And no electrical node inherits the candidate marking.
    expect(node(withColdRoom, "n-bus").candidate).toBeNull();
    expect(node(withColdRoom, "n-load").candidate).toBeNull();
  });
});

/**
 * Unsupported topology is a refusal, not a smaller drawing.
 *
 * The reachability table below is the shape T014 landed for cardinality caps
 * and for the same reason: a refusal nothing can trigger is not a refusal, and
 * it is invisible precisely because the suite stays green. Every code in
 * `SLD_UNAVAILABLE_CODES` has a document here that produces it, and adding a
 * code without adding a document fails the last test in this block.
 */
describe("unsupported topology is explicit", () => {
  const coldChainSite: SiteDetailReadModel = {
    ...HYBRID_MINI_GRID_SITE,
    site_type: "COLDCHAIN",
  };

  const danglingComponentSite: SiteDetailReadModel = {
    ...HYBRID_MINI_GRID_SITE,
    foundation: {
      ...HYBRID_MINI_GRID_SITE.foundation,
      components: HYBRID_MINI_GRID_SITE.foundation.components.filter(
        (component) => component.component_id !== "c-fuel",
      ),
    },
  };

  const withNodeRole = (nodeId: string, role: string): SiteDetailReadModel => ({
    ...HYBRID_MINI_GRID_SITE,
    foundation: {
      ...HYBRID_MINI_GRID_SITE.foundation,
      topology: {
        nodes: (HYBRID_MINI_GRID_SITE.foundation.topology?.nodes ?? []).map(
          (entry) =>
            entry.node_id === nodeId ? { ...entry, node_role: role } : entry,
        ),
        connections:
          HYBRID_MINI_GRID_SITE.foundation.topology?.connections ?? [],
      },
    },
  });

  const unknownComponentTypeSite: SiteDetailReadModel = {
    ...HYBRID_MINI_GRID_SITE,
    foundation: {
      ...HYBRID_MINI_GRID_SITE.foundation,
      components: HYBRID_MINI_GRID_SITE.foundation.components.map((component) =>
        component.component_id === "c-load"
          ? { ...component, component_type: "HEAT_PUMP" }
          : component,
      ),
    },
  };

  // The bus removed, and every connection that touched it removed with it, so
  // the refusal that fires is about the bus and not about a dangling edge.
  const noBusSite: SiteDetailReadModel = {
    ...HYBRID_MINI_GRID_SITE,
    foundation: {
      ...HYBRID_MINI_GRID_SITE.foundation,
      topology: {
        nodes: (HYBRID_MINI_GRID_SITE.foundation.topology?.nodes ?? []).filter(
          (entry) => entry.node_id !== "n-bus",
        ),
        connections: (
          HYBRID_MINI_GRID_SITE.foundation.topology?.connections ?? []
        ).filter(
          (entry) => entry.from_node !== "n-bus" && entry.to_node !== "n-bus",
        ),
      },
    },
  };

  const twoBusSite: SiteDetailReadModel = {
    ...HYBRID_MINI_GRID_SITE,
    foundation: {
      ...HYBRID_MINI_GRID_SITE.foundation,
      components: [
        ...HYBRID_MINI_GRID_SITE.foundation.components,
        {
          component_id: "c-bus-b",
          component_type: "AC_BUS",
          display_name: "Second AC bus",
          rating: { value: 400, unit: "V" },
        },
      ],
      topology: {
        nodes: [
          ...(HYBRID_MINI_GRID_SITE.foundation.topology?.nodes ?? []),
          { node_id: "n-bus-b", component_id: "c-bus-b", node_role: "BUS" },
        ],
        connections:
          HYBRID_MINI_GRID_SITE.foundation.topology?.connections ?? [],
      },
    },
  };

  const unknownMediumSite: SiteDetailReadModel = {
    ...HYBRID_MINI_GRID_SITE,
    foundation: {
      ...HYBRID_MINI_GRID_SITE.foundation,
      topology: {
        nodes: HYBRID_MINI_GRID_SITE.foundation.topology?.nodes ?? [],
        connections: (
          HYBRID_MINI_GRID_SITE.foundation.topology?.connections ?? []
        ).map((entry) =>
          entry.connection_id === "k-fuel"
            ? { ...entry, medium: "HYDRAULIC" }
            : entry,
        ),
      },
    },
  };

  const REFUSALS: Record<SldUnavailableCode, SiteDetailReadModel> = {
    SITE_TYPE_NOT_SUPPORTED: coldChainSite,
    NO_TOPOLOGY_DECLARED: UNDECLARED_TOPOLOGY_SITE,
    REFERENCE_UNRESOLVED: danglingComponentSite,
    UNSUPPORTED_NODE_ROLE: withNodeRole("n-load", "SWITCHGEAR"),
    UNSUPPORTED_COMPONENT_TYPE: unknownComponentTypeSite,
    BUS_CARDINALITY_UNSUPPORTED: noBusSite,
    UNSUPPORTED_CONNECTION_MEDIUM: unknownMediumSite,
  };

  function refusal(site: SiteDetailReadModel) {
    const result: SiteSldView = deriveSiteSldView(site);

    expect(result.status).toBe("unavailable");
    if (result.status !== "unavailable") {
      throw new Error("expected an unavailable result");
    }
    return result;
  }

  it.each(SLD_UNAVAILABLE_CODES)("can refuse with %s", (code) => {
    // The reachability table. If a code has no document that produces it, the
    // code is decoration and a screen will never render it.
    expect(refusal(REFUSALS[code]).reason.code).toBe(code);
  });

  it("covers every declared code with a document", () => {
    expect(Object.keys(REFUSALS).sort()).toEqual([...SLD_UNAVAILABLE_CODES].sort());
  });

  it("gives every code a stable statement", () => {
    for (const code of SLD_UNAVAILABLE_CODES) {
      const reason = refusal(REFUSALS[code]).reason;

      expect(reason.statement).toBe(SLD_UNAVAILABLE_STATEMENTS[code]);
      expect(reason.statement.length).toBeGreaterThan(0);
    }
  });

  it("says which part of the document it choked on", () => {
    // A refusal that does not name what it could not place leaves a reader
    // with nothing to act on.
    expect(refusal(withNodeRole("n-load", "SWITCHGEAR")).reason.detail).toContain(
      "SWITCHGEAR",
    );
    expect(refusal(unknownMediumSite).reason.detail).toContain("HYDRAULIC");
    expect(refusal(danglingComponentSite).reason.detail).toContain("c-fuel");
    expect(refusal(twoBusSite).reason.detail).toContain("2");
  });

  it("refuses a second bus rather than drawing one of them", () => {
    expect(refusal(twoBusSite).reason.code).toBe("BUS_CARDINALITY_UNSUPPORTED");
  });

  it("returns no diagram at all, not a partial one", () => {
    // Not an empty diagram, not a diagram with a flag on it. There is no
    // `diagram` key on an unavailable result, so nothing downstream can render
    // the part the archetype understood as though it were the site.
    for (const code of SLD_UNAVAILABLE_CODES) {
      const result = deriveSiteSldView(REFUSALS[code]);

      expect(result).not.toHaveProperty("diagram");
      expect(allKeys(result).sort()).toEqual([
        "code",
        "detail",
        "reason",
        "statement",
        "status",
      ]);
    }
  });

  it("does not fall back to a generic graph for an unknown role", () => {
    const result = deriveSiteSldView(withNodeRole("n-load", "SWITCHGEAR"));

    expect(result.status).toBe("unavailable");
    // Every other node in that document is placeable. Drawing the eight it
    // understood would be the partial diagram this boundary exists to refuse.
    expect(allStrings(result).join(" ")).not.toContain("n-solar");
  });
});

/**
 * The value slots are empty at the type level, and that is checked here rather
 * than assumed.
 *
 * Every runtime assertion above passes if `SldValueSlot` is widened to permit
 * an optional field: the objects this build produces are still empty, still
 * frozen, still carry no key. What changes is the contract - the type would
 * then say a reading may be attached, which is the claim this slice exists not
 * to make. Proved by widening it: zero tests failed.
 *
 * `@ts-expect-error` closes that. While a slot may hold no field, the
 * assignment below is an error and the directive is used. Widen the type and
 * the error disappears, the directive becomes unused, and `tsc` fails with
 * "Unused '@ts-expect-error' directive" - which is the compile-time way of
 * saying the guarantee was removed.
 */
describe("a value slot cannot be widened without the compiler noticing", () => {
  it("rejects a field at the type level", () => {
    // @ts-expect-error a value slot may never carry a field, of any name
    const runtime: SldValueSlot = { lastReading: 1 };
    // @ts-expect-error nor may it carry evidence metadata
    const evidence: SldValueSlot = { acceptedAt: "2026-01-01T00:00:00Z" };

    expect(Object.keys(runtime)).toHaveLength(1);
    expect(Object.keys(evidence)).toHaveLength(1);
  });
});
