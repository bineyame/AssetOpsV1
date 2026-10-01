import type {
  SldConnectionSlotContent,
  SldNodeSlotContent,
  SldSlotContent,
} from "../sites/SiteSingleLineDiagram";
import type {
  SiteDetailReadModel,
  SiteDetailResult,
} from "../sites/siteReadModel";
import {
  abs,
  type Exact,
  exactText,
  negate,
  parseExact,
  readable,
  sign,
  sum,
} from "./exactArithmetic";
import type {
  RunHistory,
  RunHistoryBoundAttachment,
  RunHistoryDrawingContext,
  RunHistoryFlow,
  RunHistoryInterval,
} from "./runHistory";

/**
 * The run-bound drawing of one recorded interval (T025d, Lab cockpit C1).
 *
 * Two jobs, both pure. `bindDrawing` decides whether this run's recorded values
 * may be put on the Site drawing the screen has read: only when the history's
 * attachments are the frozen ones (the backend's `VERIFIED`) AND the Site read
 * now is the Site and Foundation version the run froze AND every frozen
 * attachment and connection is still in that topology. Anything else is a
 * stated unavailable drawing - old values are never put on a substituted
 * diagram. `drawingSlots` then fills the shared drawing's neutral slots from the
 * history at one selected boundary.
 *
 * Timing is named, never implied. The selected boundary T selects the interval
 * that ENDED at T, `[T - dt, T)`, the same one the charts' interval readings
 * describe: stocks and discrete state are shown at the instant T (after its
 * events), flows as the mean over that interval, and the discrete state that
 * governed the interval as the state for the step that began at `T - dt`.
 */

/**
 * How the mini-grid model family's named flows are drawn.
 *
 * Keyed by this model family's flow vocabulary, as T025c's charts are keyed by
 * its state keys. A flow id not listed here is not drawn and is listed as such.
 *
 * - `BRANCH`: a transfer between a branch and the shared bus side.
 * - `CONVERTER`: a transfer between a component and its own converter.
 * - `ACCOUNTING`: a value the model accounts for that is not a wire transfer -
 *   potential, curtailed and clipped PV, conversion losses, demand, unserved.
 */
const FLOW_ROLES: Record<string, "BRANCH" | "CONVERTER" | "ACCOUNTING"> = {
  pv_to_load: "BRANCH",
  pv_to_battery: "BRANCH",
  generator_to_load: "BRANCH",
  generator_to_battery: "BRANCH",
  battery_to_load: "BRANCH",
  battery_charge_stored: "CONVERTER",
  battery_discharge_taken: "CONVERTER",
  pv_potential: "ACCOUNTING",
  inverter_clipping: "ACCOUNTING",
  curtailed_pv: "ACCOUNTING",
  generator_output: "ACCOUNTING",
  charge_loss: "ACCOUNTING",
  discharge_loss: "ACCOUNTING",
  load_demand: "ACCOUNTING",
  unserved_load: "ACCOUNTING",
};

export function flowRole(
  flowId: string,
): "BRANCH" | "CONVERTER" | "ACCOUNTING" | null {
  if (flowId.startsWith("served:")) return "BRANCH";
  if (flowId.startsWith("demand:") || flowId.startsWith("unserved:")) {
    return "ACCOUNTING";
  }
  return FLOW_ROLES[flowId] ?? null;
}

/** The resolved interval that ended at a boundary, or null when none did. */
export function completedIntervalAt(
  history: Pick<RunHistory, "intervals">,
  offset: number,
): RunHistoryInterval | null {
  return history.intervals.find((i) => i.to_offset === offset) ?? null;
}

export type DrawingBinding =
  | {
      status: "bound";
      site: SiteDetailReadModel;
      attachments: RunHistoryBoundAttachment[];
    }
  | { status: "unavailable"; code: string; statement: string };

/**
 * Whether this run's values may be drawn on the Site drawing just read.
 *
 * `site` is the current Site read (null while it is in flight). The Site
 * detail read serves the current Foundation only, so a Site whose Foundation
 * version is not the frozen one has no drawing for this run, stated.
 */
export function bindDrawing(
  context: RunHistoryDrawingContext | null,
  site: SiteDetailResult | null,
): DrawingBinding {
  if (context === null) {
    return {
      status: "unavailable",
      code: "NO_CONTEXT",
      statement:
        "The history read carries no run-bound drawing context, so no drawing is bound to it.",
    };
  }
  if (context.status !== "VERIFIED") {
    return {
      status: "unavailable",
      code: context.status,
      statement: context.statement,
    };
  }
  if (site === null) {
    return {
      status: "unavailable",
      code: "SITE_PENDING",
      statement: `Reading Site ${context.site_id} to check it is the Foundation this run froze.`,
    };
  }
  if (site.status !== "loaded") {
    return {
      status: "unavailable",
      code: "SITE_UNREADABLE",
      statement: `Site ${context.site_id} could not be read, so the Foundation this run froze cannot be confirmed and nothing is drawn.`,
    };
  }
  const current = site.site;
  if (current.site_id !== context.site_id) {
    return {
      status: "unavailable",
      code: "OTHER_SITE",
      statement: `The Site read is ${current.site_id}, not ${context.site_id}, the Site this run froze.`,
    };
  }
  if (current.foundation.version !== context.foundation_version) {
    return {
      status: "unavailable",
      code: "FOUNDATION_CHANGED",
      statement:
        `Site ${context.site_id} is now at Foundation version ${current.foundation.version}; ` +
        `this run froze version ${context.foundation_version}. Its values are not drawn ` +
        "on a different Foundation's diagram.",
    };
  }
  const topology = current.foundation.topology;
  if (topology === null) {
    return {
      status: "unavailable",
      code: "NO_TOPOLOGY",
      statement: `Site ${context.site_id}'s Foundation declares no topology to draw on.`,
    };
  }
  const nodeComponent = new Map(
    topology.nodes.map((node) => [node.node_id, node.component_id]),
  );
  const components = new Set(nodeComponent.values());
  const connections = new Map(
    topology.connections.map((c) => [c.connection_id, c]),
  );
  for (const attachment of context.attachments) {
    const members = [
      attachment.component_id,
      attachment.via_component_id,
      attachment.bus_component_id,
    ].filter((id): id is string => id !== null);
    const missing = members.find((id) => !components.has(id));
    if (missing !== undefined) {
      return {
        status: "unavailable",
        code: "TOPOLOGY_DIFFERS",
        statement: `The Site's topology has no node for ${missing}, which this run executed against.`,
      };
    }
    for (const connectionId of attachment.connection_ids) {
      const connection = connections.get(connectionId);
      const ends =
        connection === undefined
          ? []
          : [
              nodeComponent.get(connection.from_node),
              nodeComponent.get(connection.to_node),
            ];
      if (
        connection === undefined ||
        !ends.every((end) => end !== undefined && members.includes(end))
      ) {
        return {
          status: "unavailable",
          code: "TOPOLOGY_DIFFERS",
          statement: `The Site's topology does not carry connection ${connectionId} between the components this run froze for ${attachment.component_id}.`,
        };
      }
    }
  }
  return { status: "bound", site: current, attachments: context.attachments };
}

function componentOf(address: string): string | null {
  const at = address.lastIndexOf("@");
  return at < 0 ? null : address.slice(at + 1);
}

function exact(text: string): Exact {
  return parseExact(text) ?? { n: 0n, d: 1n };
}

function flowLine(flow: RunHistoryFlow): string {
  return `${flow.flow_id}: ${flow.from_address} -> ${flow.to_address}, ${flow.mean_power} kW mean, ${flow.energy} kWh`;
}

/** What the drawing's values are, stated on it. */
export function drawingStatement(offset: number, interval: RunHistoryInterval | null): string {
  const span =
    interval === null
      ? "No resolved interval ended at this boundary, so no flow is shown."
      : `Flows are the mean power in kW over the interval [${interval.from_offset}, ${interval.to_offset}) min that ended at this boundary.`;
  return (
    `Values are this run's recorded private truth at the selected boundary, offset ${offset} min. ` +
    `Stocks and discrete states are at that instant, after its events. ${span} ` +
    "An arrow on a connection to the shared bus is the aggregate transfer of that branch, " +
    "not a source-specific path. Battery power follows the existing convention: " +
    "positive discharging, negative charging. No voltage, frequency, breaker state or weather is modeled."
  );
}

/** The component name to use in a label: the Site's display name, or the id. */
function namer(site: SiteDetailReadModel): (id: string) => string {
  const names = new Map(
    site.foundation.components.map((c) => [c.component_id, c.display_name]),
  );
  return (id) => names.get(id) ?? id;
}

/**
 * The shared drawing's slot content for one selected boundary of a bound run.
 */
export function drawingSlots(
  binding: Extract<DrawingBinding, { status: "bound" }>,
  history: Pick<RunHistory, "intervals" | "samples">,
  offset: number,
): SldSlotContent {
  const { site, attachments } = binding;
  const name = namer(site);
  const interval = completedIntervalAt(history, offset);
  const span =
    interval === null ? "" : `[${interval.from_offset}, ${interval.to_offset})`;
  const flows = interval?.flows ?? [];

  const buses = new Set(attachments.map((a) => a.bus_component_id));
  const modeled = new Set<string>(buses);
  for (const a of attachments) {
    modeled.add(a.component_id);
    if (a.via_component_id !== null) modeled.add(a.via_component_id);
  }

  const storages = new Set(
    attachments.filter((a) => a.role === "STORAGE").map((a) => a.component_id),
  );

  // --- Components -----------------------------------------------------------
  const nodes = new Map<string, SldNodeSlotContent>();
  for (const bus of buses) {
    nodes.set(bus, {
      text: "Shared bus: aggregate transfer only",
      detail: [
        "Arrows on its connections are each branch's aggregate transfer over the interval, not source-specific electron paths.",
        "No voltage, frequency or breaker state is modeled.",
      ],
    });
  }
  for (const componentId of modeled) {
    if (buses.has(componentId)) continue;
    const detail: string[] = [];
    let text: string | null = null;

    for (const sample of history.samples) {
      if (sample.offset_minutes !== offset || sample.phase !== "POST_EVENT") continue;
      if (componentOf(sample.address) !== componentId) continue;
      const line = `${sample.state_key} ${sample.value}${sample.unit === "state" ? "" : ` ${sample.unit}`} at ${offset} min (state at the instant)`;
      detail.push(line);
      text ??= `${sample.state_key} ${sample.value}${sample.unit === "state" ? "" : ` ${sample.unit}`}`;
    }
    if (interval !== null) {
      for (const sample of history.samples) {
        if (
          sample.offset_minutes !== interval.from_offset ||
          sample.phase !== "FOR_STEP" ||
          componentOf(sample.address) !== componentId
        ) {
          continue;
        }
        detail.push(
          `${sample.state_key} ${sample.value} during ${span} (state for the step)`,
        );
        text = `${sample.value} during ${span}`;
      }
      for (const load of interval.loads) {
        if (componentOf(load.address) !== componentId) continue;
        text = `served ${load.served_power} of ${load.demand_power} kW`;
        detail.push(
          `demand ${load.demand_power} kW, served ${load.served_power} kW, unserved ${load.unserved_power} kW, mean over ${span}`,
          `energy: demand ${load.demand_energy}, served ${load.served_energy}, unserved ${load.unserved_energy} kWh`,
        );
      }
      // Charge direction is a storage component's, read off the accepted
      // flow endpoints between it and its converter; its converter shows none.
      const storage = storages.has(componentId);
      const stored = flows.filter(
        (f) =>
          storage &&
          flowRole(f.flow_id) === "CONVERTER" &&
          f.to_address === componentId,
      );
      const taken = flows.filter(
        (f) =>
          storage &&
          flowRole(f.flow_id) === "CONVERTER" &&
          f.from_address === componentId,
      );
      if (stored.length + taken.length > 0) {
        const net = sum([
          ...stored.map((f) => exact(f.mean_power)),
          ...taken.map((f) => negate(exact(f.mean_power))),
        ]);
        const direction =
          sign(net) > 0 ? "charging" : sign(net) < 0 ? "discharging" : "idle";
        const move = `${direction}${sign(net) === 0 ? " (0 kW)" : ` ${readable(abs(net))} kW`} over ${span}`;
        detail.push(
          `${move}, from the accepted flow endpoints (${[...stored, ...taken].map((f) => f.flow_id).join(", ")})`,
        );
        text = text === null ? move : `${direction}; ${text}`;
      }
      for (const flow of flows) {
        if (flowRole(flow.flow_id) !== "ACCOUNTING") continue;
        if (flow.from_address !== componentId) continue;
        detail.push(
          `${flow.flow_id}: ${flow.mean_power} kW mean over ${span} - an accounting value, not a wire`,
        );
      }
    }
    nodes.set(
      componentId,
      detail.length === 0
        ? {
            text: "Modeled; no value recorded here",
            detail: [
              "This component is part of the run, and the history records no value for it at this boundary.",
            ],
          }
        : { text: text ?? detail[0], detail },
    );
  }

  // --- Connections ------------------------------------------------------------
  const topology = site.foundation.topology;
  const nodeComponent = new Map(
    (topology?.nodes ?? []).map((node) => [node.node_id, node.component_id]),
  );
  const declared = new Map(
    (topology?.connections ?? []).map((c) => [c.connection_id, c]),
  );
  const connections = new Map<string, SldConnectionSlotContent>();
  const unclassified = flows.filter((f) => flowRole(f.flow_id) === null);

  for (const attachment of attachments) {
    for (const connectionId of attachment.connection_ids) {
      if (connections.has(connectionId)) continue;
      const connection = declared.get(connectionId);
      if (connection === undefined) continue;
      const fromComponent = nodeComponent.get(connection.from_node) ?? "";
      const toComponent = nodeComponent.get(connection.to_node) ?? "";
      // The branch a connection belongs to is the attachment whose own
      // component is one of its ends; the generator-to-bus connection is the
      // generator's, not the fuel supply's that passes through it.
      const owner =
        attachments.find(
          (a) =>
            a.connection_ids.includes(connectionId) &&
            (a.component_id === fromComponent || a.component_id === toComponent),
        ) ?? attachment;
      connections.set(
        connectionId,
        connectionSlot(owner, fromComponent, toComponent, flows, interval, name, buses),
      );
    }
  }
  if (unclassified.length > 0) {
    for (const bus of buses) {
      const content = nodes.get(bus);
      if (content === undefined) continue;
      content.detail.push(
        `Not drawn, no drawing rule for: ${unclassified.map((f) => f.flow_id).join(", ")}`,
      );
    }
  }

  return {
    statement: drawingStatement(offset, interval),
    unfilled: "Not modeled in this run",
    nodes,
    connections,
  };
}

function connectionSlot(
  owner: RunHistoryBoundAttachment,
  fromComponent: string,
  toComponent: string,
  flows: RunHistoryFlow[],
  interval: RunHistoryInterval | null,
  name: (id: string) => string,
  buses: Set<string>,
): SldConnectionSlotContent {
  if (interval === null) {
    return {
      direction: "NONE",
      text: "no interval ended here",
      detail: ["No resolved interval ended at this boundary, so no flow is shown."],
    };
  }
  const span = `[${interval.from_offset}, ${interval.to_offset})`;
  const busEnd = buses.has(fromComponent)
    ? fromComponent
    : buses.has(toComponent)
      ? toComponent
      : null;

  let contributing: RunHistoryFlow[];
  let net: Exact;
  let towards: string;
  let note: string;
  if (busEnd !== null) {
    const branchEnd = busEnd === fromComponent ? toComponent : fromComponent;
    const members = new Set(
      [owner.component_id, owner.via_component_id].filter(
        (id): id is string => id !== null,
      ),
    );
    const out = flows.filter(
      (f) =>
        flowRole(f.flow_id) === "BRANCH" &&
        members.has(f.from_address) &&
        !members.has(f.to_address),
    );
    const into = flows.filter(
      (f) =>
        flowRole(f.flow_id) === "BRANCH" &&
        members.has(f.to_address) &&
        !members.has(f.from_address),
    );
    contributing = [...out, ...into];
    net = sum([
      ...out.map((f) => exact(f.mean_power)),
      ...into.map((f) => negate(exact(f.mean_power))),
    ]);
    // Positive `net` leaves the branch for the bus.
    towards = busEnd;
    if (sign(net) < 0) {
      net = negate(net);
      towards = branchEnd;
    }
    note = `Aggregate transfer of the ${name(owner.component_id)} branch across the shared bus, not a source-specific path.`;
  } else {
    contributing = flows.filter(
      (f) =>
        flowRole(f.flow_id) === "CONVERTER" &&
        ((f.from_address === fromComponent && f.to_address === toComponent) ||
          (f.from_address === toComponent && f.to_address === fromComponent)),
    );
    net = sum(
      contributing.map((f) =>
        f.to_address === toComponent
          ? exact(f.mean_power)
          : negate(exact(f.mean_power)),
      ),
    );
    towards = toComponent;
    if (sign(net) < 0) {
      net = negate(net);
      towards = fromComponent;
    }
    note = "Transfer between a component and its own converter.";
  }

  if (contributing.length === 0) {
    return {
      direction: "NONE",
      text: "no modeled flow",
      detail: [
        "The model records no flow on this connection; it is drawn as configured, with no value.",
      ],
    };
  }
  const detail = [
    note,
    `Mean over ${span} from: ${contributing.map(flowLine).join("; ")}`,
  ];
  if (sign(net) === 0) {
    return { direction: "NONE", text: "0 kW", detail, label: "0 kW" };
  }
  return {
    direction: towards === toComponent ? "ALONG" : "AGAINST",
    text: `${readable(net)} kW to ${name(towards)}`,
    detail,
    label: `${drawnValue(net)} kW`,
  };
}

/**
 * The value drawn on a line: exact when it is a short decimal, otherwise
 * marked approximate to one decimal. A lattice gap is 60 px wide, and an
 * exact fraction drawn there overlaps the boxes either side (measured,
 * T025d). The exact value stays in the line's title and the contents table.
 */
export function drawnValue(a: Exact): string {
  const text = exactText(a);
  if (!text.includes("/") && text.length <= 5) return text;
  return `~${(Number(a.n) / Number(a.d)).toFixed(1)}`;
}
