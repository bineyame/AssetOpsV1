import type { ReactNode } from "react";

import { DataTable } from "../ui";
import type { SiteDetailReadModel } from "./siteReadModel";
import {
  CONNECTION_MEDIUM_LABELS,
  NO_RATING_DECLARED,
  TOPOLOGY_NODE_ROLE_LABELS,
  label,
} from "./siteViewModel";
import {
  deriveSiteSldView,
  type SiteSldView,
  type SldConnectionView,
  type SldDiagramView,
  type SldNodeView,
  type SldUnavailableReason,
} from "./sldViewModel";

/**
 * The configured Single Line Diagram, drawn inside Foundation.
 *
 * This is the renderer T015 deliberately did not write. It reads
 * `deriveSiteSldView` and nothing else: it holds no topology of its own, looks
 * up no component, resolves no device, and derives no signal. Every identity
 * it draws came out of the view model, which is itself tested to introduce
 * nothing the Foundation did not declare. That chain is the whole of why a
 * diagram on this screen can be trusted to be a picture of the record.
 *
 * ## What is drawn, and what is only positioned
 *
 * The document decides what exists. The archetype decides where it sits and
 * which shape stands for it. This module decides how many pixels a lane is
 * wide, and that is the only decision it makes.
 *
 * So there is no fallback here. If the view model says `unavailable`, this
 * draws no nodes at all - not the ones it understood, not a faded outline, not
 * an empty frame with a message over it. A partial diagram presented as whole
 * is the failure the unavailable state exists to prevent, and it is a failure
 * a renderer is uniquely able to commit by being helpful.
 *
 * ## The archetype's own vocabulary never becomes text
 *
 * `BUSBAR`, `TERMINAL`, `SOLID`, `COLUMN_FIRST` are presentation keys. They
 * are carried into the DOM as `data-` attributes so a test can bind to them
 * and a stylesheet can reach them, and they are never rendered as a word a
 * reader sees. A screen that showed one would be showing a reader the inside
 * of the archetype, which is not vocabulary the product has.
 *
 * ## The two slots stay empty, visibly
 *
 * Every drawn node carries one line reading `Awaiting runtime/evidence`. That
 * is the whole of what the slots say in this build. It is rendered rather than
 * left blank because a blank space next to a component reads as a value that
 * failed to load, and this is not a failure: no run has produced a runtime
 * value and no evidence has been accepted, so there is nothing that could be
 * there yet.
 *
 * ## Two questions this screen asks rather than answers
 *
 * `SldOpenQuestions` below is not documentation. It is the M1A user-review
 * checkpoint rendered where the thing being decided is visible: whether a
 * breaker is a device, component state or both and what its control
 * vocabulary is, and how a cold room's process symbol relates to an electrical
 * single line. Both are stated as undecided, on the screen, so that the review
 * is a decision rather than a ratification of something already shipped.
 */

/** The heading that names the diagram section. */
export const SITE_SLD_HEADING_ID = "foundation-single-line-diagram-heading";

/** The heading that names the diagram's contents, in text. */
export const SITE_SLD_CONTENTS_ID = "foundation-diagram-contents-heading";

/** The heading that names the open review questions. */
export const SITE_SLD_QUESTIONS_ID = "foundation-sld-open-questions-heading";

/** The heading of the diagram section, as v6.9 and the task name it. */
export const SITE_SLD_HEADING = "Single Line Diagram (Configured)";

/**
 * What a value slot says while it holds nothing.
 *
 * One string, exported, so the diagram, the contents table and every test read
 * the same words. Two surfaces spelling this differently would be two answers
 * to what an empty slot means.
 */
export const AWAITING_RUNTIME_OR_EVIDENCE = "Awaiting runtime/evidence";

/** What the diagram is, stated above it in both states. */
export const SITE_SLD_INTRODUCTION =
  "This is the configured single line diagram: the components this site's " +
  "foundation declares, arranged by the hybrid mini-grid archetype, with the " +
  "connections the document declares between them. It is a picture of the " +
  "configuration and never of the site's behaviour - no reading has arrived, " +
  "and every value slot on it is empty.";

/** What the unavailable state must not be read as saying. */
export const SITE_SLD_UNAVAILABLE_NOTE =
  "This is a statement about the drawing, not about the site. Nothing is " +
  "hidden: every component, device and signal this site's foundation declares " +
  "is still listed in the tables in this section. An arrangement the " +
  "archetype has no lane for is not evidence that the site has no configured " +
  "assets.";

/** The layout lattice, in CSS pixels. The one thing this module decides. */
const PADDING = 28;
const COLUMN_PITCH = 260;
const ROW_PITCH = 140;
const NODE_WIDTH = 200;
const NODE_HEIGHT = 108;
const GLYPH = 26;

/**
 * Where the text in a box starts, and how much of it fits on a line.
 *
 * SVG text does not wrap and does not clip, so a name longer than its box runs
 * out of the side of it and across whatever is drawn there - which is how
 * `Battery power conversion system` came to have a connection running through
 * it. The name is wrapped instead of shortened: a truncated component name is
 * a fact hidden to make a layout tidy, and this surface refuses that
 * everywhere else.
 */
const TEXT_LEFT = 14 + GLYPH + 10;
const NAME_LINE_BUDGET = 18;
const NAME_LINES = 2;

/** The empty space between two lanes, which is where a run turns. */
const LANE_GAP = COLUMN_PITCH - NODE_WIDTH;

interface Box {
  x: number;
  y: number;
}

function boxFor(node: SldNodeView): Box {
  return {
    x: PADDING + node.position.column * COLUMN_PITCH,
    y: PADDING + node.position.row * ROW_PITCH,
  };
}

/**
 * A display name broken onto at most two lines, on word boundaries.
 *
 * The remainder goes on the last line whole rather than being cut: a name too
 * long for two lines overflows its box, which is visible and fixable, where a
 * name with its end removed looks deliberate and is not.
 */
function wrapName(name: string): string[] {
  const words = name.split(/\s+/).filter((word) => word.length > 0);
  const lines: string[] = [];
  let current = "";

  for (const word of words) {
    const candidate = current === "" ? word : `${current} ${word}`;

    if (candidate.length <= NAME_LINE_BUDGET || current === "") {
      current = candidate;
      continue;
    }
    if (lines.length === NAME_LINES - 1) {
      current = candidate;
      continue;
    }
    lines.push(current);
    current = word;
  }

  if (current !== "") lines.push(current);
  return lines.length === 0 ? [name] : lines;
}

function ratingText(node: SldNodeView): string {
  return node.rating === null
    ? NO_RATING_DECLARED
    : `${node.rating.value} ${node.rating.unit}`;
}

/**
 * How a connection runs between two boxes.
 *
 * Orthogonal, and the turn is the view model's. Two nodes in one lane are
 * joined vertically; everything else leaves the right edge, turns at the
 * midpoint of the gap, and arrives at the left edge. There is no routing
 * search here and there is not meant to be: the archetype is a fixed
 * arrangement, and a router would be the auto-layout this slice must not
 * build.
 */
function runPoints(from: Box, to: Box, turn: SldConnectionView["route"]["turn"]): string {
  const fromMidY = from.y + NODE_HEIGHT / 2;
  const toMidY = to.y + NODE_HEIGHT / 2;

  if (turn === "ROW_FIRST") {
    const x = from.x + NODE_WIDTH / 2;
    const startY = from.y < to.y ? from.y + NODE_HEIGHT : from.y;
    const endY = from.y < to.y ? to.y : to.y + NODE_HEIGHT;
    return `${x},${startY} ${x},${endY}`;
  }

  // The turn happens in the gap immediately before the destination lane, not
  // at the midpoint of the whole run. A run that skips a lane - the generator
  // reaching the bus past the conversion lane - turns at the midpoint straight
  // through whatever that lane is holding, and a line crossing a component box
  // reads as a connection to it.
  const rightward = to.x >= from.x;
  const startX = rightward ? from.x + NODE_WIDTH : from.x;
  const endX = rightward ? to.x : to.x + NODE_WIDTH;
  const turnX = rightward ? endX - LANE_GAP / 2 : endX + LANE_GAP / 2;

  return `${startX},${fromMidY} ${turnX},${fromMidY} ${turnX},${toMidY} ${endX},${toMidY}`;
}

/**
 * The shape that stands for a component type.
 *
 * Geometry only: no text, no digit, no letter. A glyph that spelled its own
 * name would put the archetype's vocabulary on the screen through the back
 * door, and a glyph carrying a number would put a number on a diagram that has
 * none.
 */
function Glyph({ symbol, x, y }: { symbol: SldNodeView["symbol"]; x: number; y: number }) {
  const shape = (): ReactNode => {
    switch (symbol) {
      case "PV_ARRAY":
        return (
          <>
            <rect x={0} y={4} width={GLYPH} height={GLYPH - 8} rx={2} />
            <line x1={0} y1={12} x2={GLYPH} y2={12} />
            <line x1={9} y1={4} x2={9} y2={GLYPH - 4} />
            <line x1={17} y1={4} x2={17} y2={GLYPH - 4} />
          </>
        );
      case "INVERTER":
      case "POWER_CONVERSION_SYSTEM":
        return (
          <>
            <rect x={1} y={1} width={GLYPH - 2} height={GLYPH - 2} rx={2} />
            <line x1={1} y1={GLYPH - 1} x2={GLYPH - 1} y2={1} />
          </>
        );
      case "BATTERY":
        return (
          <>
            <rect x={1} y={6} width={GLYPH - 6} height={GLYPH - 12} rx={2} />
            <rect x={GLYPH - 5} y={10} width={4} height={6} rx={1} />
          </>
        );
      case "GENERATOR":
        return (
          <>
            <circle cx={GLYPH / 2} cy={GLYPH / 2} r={GLYPH / 2 - 1} />
            <path
              d={`M4,${GLYPH / 2} q4,-7 8,0 q4,7 8,0`}
              fill="none"
            />
          </>
        );
      case "FUEL_TANK":
        return (
          <>
            <rect x={2} y={5} width={GLYPH - 4} height={GLYPH - 9} rx={6} />
            <line x1={2} y1={GLYPH - 8} x2={GLYPH - 2} y2={GLYPH - 8} />
          </>
        );
      case "BUSBAR":
        return (
          <>
            <rect x={0} y={GLYPH / 2 - 4} width={GLYPH} height={8} rx={2} />
          </>
        );
      case "METER":
        return (
          <>
            <circle cx={GLYPH / 2} cy={GLYPH / 2} r={GLYPH / 2 - 1} />
            <line x1={GLYPH / 2} y1={GLYPH / 2} x2={GLYPH - 5} y2={6} />
          </>
        );
      case "LOAD":
        return (
          <>
            <path d={`M${GLYPH / 2},${GLYPH - 2} L2,4 L${GLYPH - 2},4 Z`} />
          </>
        );
      case "COLD_ROOM":
        return (
          <>
            <rect x={1} y={1} width={GLYPH - 2} height={GLYPH - 2} rx={2} />
            <line x1={GLYPH / 2} y1={5} x2={GLYPH / 2} y2={GLYPH - 5} />
            <line x1={5} y1={GLYPH / 2} x2={GLYPH - 5} y2={GLYPH / 2} />
            <line x1={7} y1={7} x2={GLYPH - 7} y2={GLYPH - 7} />
            <line x1={GLYPH - 7} y1={7} x2={7} y2={GLYPH - 7} />
          </>
        );
    }
  };

  return (
    <g
      className={`sld-glyph sld-glyph--${symbol.toLowerCase().replace(/_/g, "-")}`}
      data-sld-symbol={symbol}
      transform={`translate(${x} ${y})`}
    >
      {shape()}
    </g>
  );
}

/** One drawn component: its shape, its declared name and rating, its slot. */
function SldNode({ node }: { node: SldNodeView }) {
  const box = boxFor(node);

  return (
    <g
      className="sld-node"
      data-sld-node={node.nodeId}
      data-sld-component={node.componentId}
      data-sld-visual-role={node.visualRole}
      data-sld-candidate={node.candidate === null ? undefined : "unsettled"}
    >
      <rect
        className="sld-node__box"
        x={box.x}
        y={box.y}
        width={NODE_WIDTH}
        height={NODE_HEIGHT}
        rx={6}
      />
      <Glyph symbol={node.symbol} x={box.x + 14} y={box.y + 14} />
      {/*
        * One `text` element holding the whole name, wrapped into `tspan`
        * lines. One element per line would put the name on the screen as two
        * separate strings, and an assertion comparing a label to the record
        * would then have to know how this component chose to break it.
        */}
      <text className="sld-node__name" x={box.x + TEXT_LEFT} y={box.y + 26}>
        {wrapName(node.displayName).map((line, index) => (
          <tspan
            key={line}
            x={box.x + TEXT_LEFT}
            dy={index === 0 ? 0 : 16}
          >
            {line}
          </tspan>
        ))}
      </text>
      <text className="sld-node__rating" x={box.x + TEXT_LEFT} y={box.y + 64}>
        {ratingText(node)}
      </text>
      {node.candidate === null ? null : (
        // Inside the box, on its own line. Over the corner it sat on top of
        // the component's name, which put the marking in the way of the thing
        // it is a marking about.
        <text
          className="sld-node__candidate"
          x={box.x + TEXT_LEFT}
          y={box.y + 82}
        >
          Proposed treatment
        </text>
      )}
      <text className="sld-node__slot" x={box.x + 14} y={box.y + NODE_HEIGHT - 10}>
        {AWAITING_RUNTIME_OR_EVIDENCE}
      </text>
    </g>
  );
}

/** One declared connection, drawn as the archetype routes it. */
function SldRun({
  connection,
  boxes,
}: {
  connection: SldConnectionView;
  boxes: Map<string, Box>;
}) {
  const from = boxes.get(connection.fromNodeId);
  const to = boxes.get(connection.toNodeId);
  if (from === undefined || to === undefined) return null;

  return (
    <polyline
      className={`sld-run sld-run--${connection.medium.toLowerCase()}`}
      data-sld-connection={connection.connectionId}
      data-sld-stroke={connection.route.stroke}
      data-sld-turn={connection.route.turn}
      points={runPoints(from, to, connection.route.turn)}
      fill="none"
    />
  );
}

/**
 * The drawing itself.
 *
 * `role="img"` with a title and a description, because the shapes and the
 * routing carry no meaning a screen reader can take from them. The description
 * does not try to narrate the topology: the same facts are in the tables
 * immediately below, in a form that can actually be read row by row, and
 * duplicating them into one long sentence would be worse for the reader who
 * needs them most.
 */
function SldDrawing({ diagram, siteName }: { diagram: SldDiagramView; siteName: string }) {
  const boxes = new Map<string, Box>();
  for (const node of diagram.nodes) {
    boxes.set(node.nodeId, boxFor(node));
  }

  const width = PADDING * 2 + (diagram.extent.columns - 1) * COLUMN_PITCH + NODE_WIDTH;
  const height = PADDING * 2 + (diagram.extent.rows - 1) * ROW_PITCH + NODE_HEIGHT;

  const titleId = "foundation-sld-title";
  const descriptionId = "foundation-sld-description";

  const media = [...new Set(diagram.connections.map((run) => run.medium))];

  return (
    <>
      <div
        className="sld__scroll"
        role="region"
        aria-labelledby={SITE_SLD_HEADING_ID}
        tabIndex={0}
      >
        <svg
          className="sld"
          role="img"
          aria-labelledby={`${titleId} ${descriptionId}`}
          data-sld-archetype={diagram.archetype}
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
        >
          <title id={titleId}>
            Configured single line diagram for {siteName}
          </title>
          <desc id={descriptionId}>
            Drawn from this site&apos;s declared topology. Every component,
            connection, device and signal it draws is listed in the tables in
            this section; nothing on it is a measurement.
          </desc>
          {diagram.connections.map((connection) => (
            <SldRun
              key={connection.connectionId}
              connection={connection}
              boxes={boxes}
            />
          ))}
          {diagram.nodes.map((node) => (
            <SldNode key={node.nodeId} node={node} />
          ))}
        </svg>
      </div>

      <ul className="sld-legend">
        {media.map((medium) => (
          <li className="sld-legend__item" key={medium}>
            <span
              className={`sld-legend__run sld-legend__run--${medium.toLowerCase()}`}
              aria-hidden="true"
            />
            {label(medium, CONNECTION_MEDIUM_LABELS)}
          </li>
        ))}
      </ul>
    </>
  );
}

/** The refusal, stated where the drawing would have been. */
function SldUnavailable({ reason }: { reason: SldUnavailableReason }) {
  return (
    <div className="sld-unavailable" data-sld-unavailable={reason.code}>
      <p className="sld-unavailable__statement">{reason.statement}</p>
      <p className="sld-unavailable__detail">{reason.detail}</p>
      <p className="sld-unavailable__note">{SITE_SLD_UNAVAILABLE_NOTE}</p>
    </div>
  );
}

/**
 * What the archetype has no place for, stated rather than dropped.
 *
 * A declared component with no topology node is not in the topology, so there
 * is nowhere on the drawing for it or for the devices and signals anchored to
 * it. All three are facts the document states, and a diagram that silently
 * left them out would be hiding part of what it claims to draw.
 */
function SldUnplaced({ diagram }: { diagram: SldDiagramView }) {
  const { components, devices, signals } = diagram.unplaced;
  if (components.length === 0 && devices.length === 0 && signals.length === 0) {
    return null;
  }

  return (
    <div className="sld-unplaced" data-sld-unplaced="">
      <p>
        This site&apos;s foundation declares more than the diagram has a place
        for. The diagram draws what the topology positions; what the topology
        does not position is listed here rather than left out.
      </p>
      <ul className="sld-unplaced__list">
        {components.map((component) => (
          <li key={component.componentId}>
            {component.displayName} is declared as a component and takes no
            position in the declared topology.
          </li>
        ))}
        {devices.map((device) => (
          <li key={device.deviceId}>
            {device.displayName} is attached to a component the topology does
            not position.
          </li>
        ))}
        {signals.map((signal) => (
          <li key={signal.mappingId}>
            {signal.signalName} describes a component the topology does not
            position.
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * The diagram's contents, in text.
 *
 * Not a second source and not a caption. Every row is one drawn node, and
 * every cell is read off the same view model the drawing is: the component
 * name on the box is the component name in this row, because there is one
 * string and it is used twice.
 *
 * This is also where declared signal availability lives. Names and units on
 * the drawing itself would either crowd it or be truncated, and a truncated
 * label is a hidden fact wearing a tidy layout.
 */
function SldContents({ diagram }: { diagram: SldDiagramView }) {
  return (
    <>
      <h4 className="subsection__subheading" id={SITE_SLD_CONTENTS_ID}>
        What the diagram draws
      </h4>
      <DataTable labelledBy={SITE_SLD_CONTENTS_ID}>
        <caption>
          Every component the diagram draws, with the devices configured
          against it and the signals this site&apos;s foundation declares are
          available about it. The runtime and evidence column is the slot each
          drawn component carries: both are empty in this build, for every
          component, and neither holds a reading.
        </caption>
        <thead>
          <tr>
            <th scope="col">Component</th>
            <th scope="col">Role in topology</th>
            <th scope="col">Declared rating</th>
            <th scope="col">Devices attached</th>
            <th scope="col">Signals available</th>
            <th scope="col">Runtime and evidence</th>
            <th scope="col">Node ID</th>
          </tr>
        </thead>
        <tbody>
          {diagram.nodes.map((node) => (
            <tr key={node.nodeId} data-sld-row={node.nodeId}>
              <td>{node.displayName}</td>
              <td>{label(node.nodeRole, TOPOLOGY_NODE_ROLE_LABELS)}</td>
              <td>{ratingText(node)}</td>
              <td>
                {node.attachedDevices.length === 0 ? (
                  "None configured against this component"
                ) : (
                  <ul className="cell-list">
                    {node.attachedDevices.map((device) => (
                      <li key={device.deviceId}>{device.displayName}</li>
                    ))}
                  </ul>
                )}
              </td>
              <td>
                {node.availableSignals.length === 0 ? (
                  "None declared about this component"
                ) : (
                  <ul className="cell-list">
                    {node.availableSignals.map((signal) => (
                      <li key={signal.mappingId}>
                        {signal.signalName} ({signal.unit})
                      </li>
                    ))}
                  </ul>
                )}
              </td>
              <td>{AWAITING_RUNTIME_OR_EVIDENCE}</td>
              <td>{node.nodeId}</td>
            </tr>
          ))}
        </tbody>
      </DataTable>
    </>
  );
}

/**
 * The two decisions this slice presents and does not take.
 *
 * Rendered on the screen rather than filed in a document, because both are
 * about what a reader would conclude from looking at this diagram, and a
 * reader cannot judge that from a task file. Each says plainly that it is
 * undecided, which is what stops the review being a ratification of something
 * already chosen.
 *
 * The control-vocabulary candidates are named as candidates. Naming none of
 * them would make the question unanswerable; naming one of them anywhere else
 * on this screen would answer it.
 */
function SldOpenQuestions({ diagram }: { diagram: SldDiagramView | null }) {
  const coldRoom = diagram?.nodes.find((node) => node.candidate !== null) ?? null;

  return (
    <div className="sld-questions" data-review-question="">
      <h4 className="subsection__subheading" id={SITE_SLD_QUESTIONS_ID}>
        Open for review: two things this diagram does not decide
      </h4>
      <p className="sld-questions__lede">
        Neither question below is decided, and nothing on this screen should be
        read as deciding one. They are here so that the review is a decision
        rather than agreement with something already shipped.
      </p>

      <dl className="sld-questions__list">
        <div className="sld-questions__item">
          <dt>Is a breaker a device, a component state, or both?</dt>
          <dd>
            <p>
              Nothing in this build draws a breaker or names a control
              position, and the foundation schema declares no vocabulary for
              one. Two answers are needed and neither has been given: whether a
              breaker is a configured device attached to a component, a state
              the component itself carries, or both at once; and what the words
              for that state are. Candidates the project has considered and not
              chosen are open, closed and tripped for position, and auto and
              manual for mode.
            </p>
            <p>
              Until it is settled, this site&apos;s foundation states how it is
              intended to be operated in words only, under Controls on this
              page. No column, symbol, label or class anywhere in this build
              carries a control state, deliberately.
            </p>
          </dd>
        </div>

        <div className="sld-questions__item">
          <dt>
            How should a cold room relate to mini-grid electrical topology?
          </dt>
          <dd>
            <p>
              A cold room is a process asset. A single line diagram is an
              electrical drawing. Whether the two belong on one picture at all,
              and what it means when they do, has not been decided.
            </p>
            <p>
              The proposal on offer is to draw a declared cold room in the lane
              its declared topology role puts it in, with its own shape, marked
              as a proposal rather than as settled practice. It claims nothing
              about refrigeration performance, temperature, cold-chain
              compliance or product condition, and this build holds no such
              fact to claim it with.
            </p>
            <p className="sld-questions__witness">
              {coldRoom === null
                ? "This site's foundation declares no cold room, so none is " +
                  "drawn above. The proposal is visible on a site whose " +
                  "foundation declares one."
                : `${coldRoom.displayName} is drawn above under that proposal, ` +
                  "marked as a proposed treatment."}
            </p>
            {coldRoom === null ? null : (
              <p className="sld-questions__candidate">{coldRoom.candidate?.question}</p>
            )}
          </dd>
        </div>
      </dl>
    </div>
  );
}

/**
 * The diagram section, in whichever of its two states this site is in.
 *
 * One entry point, so no caller has to know that the compatible and
 * unavailable branches exist, and neither branch can be rendered without the
 * other being considered.
 */
export function SiteSingleLineDiagram({ site }: { site: SiteDetailReadModel }) {
  const view: SiteSldView = deriveSiteSldView(site);

  return (
    <div className="subsection" data-sld-region="">
      <h3 className="subsection__heading" id={SITE_SLD_HEADING_ID}>
        {SITE_SLD_HEADING}
      </h3>
      <p>{SITE_SLD_INTRODUCTION}</p>

      {view.status === "compatible" ? (
        <>
          <SldDrawing diagram={view.diagram} siteName={site.display_name} />
          <SldUnplaced diagram={view.diagram} />
          <SldContents diagram={view.diagram} />
        </>
      ) : (
        <SldUnavailable reason={view.reason} />
      )}

      <SldOpenQuestions
        diagram={view.status === "compatible" ? view.diagram : null}
      />
    </div>
  );
}
