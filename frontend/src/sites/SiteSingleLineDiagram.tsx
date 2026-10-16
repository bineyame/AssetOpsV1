import { useId, type KeyboardEvent, type ReactNode } from "react";

import { Badge, DataTable, MissingClaim, MissingClaimSvg } from "../ui";
import { COMPONENT_ICON_HEIGHT, COMPONENT_ICON_WIDTH, ComponentIconShape } from "./componentIcons";
import type { SiteDetailReadModel } from "./siteReadModel";
import {
  COMPONENT_TYPE_LABELS,
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
 * Every drawn node carries one line reading `Readings not assessed here`.
 * That is the whole of what the slots say in this build. It is rendered rather
 * than left blank because a blank space next to a component reads as a value
 * that failed to load. V-01a round 2 (Architect item 4): it says this view
 * does not assess readings, not that none has arrived - the former wording,
 * "Awaiting runtime/evidence", read as a statement that nothing had.
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
 * to what an empty slot means. The exported name is kept from S1 so every
 * reader of it stays one search away.
 */
export const AWAITING_RUNTIME_OR_EVIDENCE = "Readings not assessed here";

/** What the diagram is, stated above it in both states. */
export const SITE_SLD_INTRODUCTION_SCOPE =
  "This is the configured single line diagram: the components this site's " +
  "foundation declares, arranged by the hybrid mini-grid archetype, with the " +
  "connections the document declares between them. It is a picture of the " +
  "configuration and never of the site's behaviour.";

/** The introduction's one absent-readings claim (G-sld-reporting-status). */
export const SITE_SLD_INTRODUCTION_READINGS =
  "Whether any reading has arrived is not assessed in this view, so every " +
  "value slot on it is empty.";

function SiteSldIntroduction() {
  return (
    <p>
      {SITE_SLD_INTRODUCTION_SCOPE}{" "}
      <MissingClaim gapId="G-sld-reporting-status" placement="sld.intro.readings-status">
        {SITE_SLD_INTRODUCTION_READINGS}
      </MissingClaim>
    </p>
  );
}

/** What the unavailable state must not be read as saying. */
export const SITE_SLD_UNAVAILABLE_NOTE =
  "This is a statement about the drawing, not about the site. Nothing is " +
  "hidden: every component, device and signal this site's foundation declares " +
  "is still listed in the tables in this section. An arrangement the " +
  "archetype has no lane for is not evidence that the site has no configured " +
  "assets.";

/**
 * Which way a value slot on a connection says something moved along it,
 * relative to the connection's declared `from` and `to` nodes. `NONE` is a
 * stated zero or an undirected value, never an absent one: an absent value is
 * no slot content at all.
 */
export type SldSlotDirection = "ALONG" | "AGAINST" | "NONE";

/** Content for one component's slot: a short line on the box, the rest in the table. */
export interface SldNodeSlotContent {
  text: string;
  detail: string[];
}

/**
 * Content for one connection's slot: a direction, its statement and detail,
 * and optionally the few characters drawn on the line itself.
 *
 * `label` is kept short on purpose: the lattice's gaps are 32 px between rows
 * and 60 px between columns, and a sentence drawn there overlaps the boxes it
 * connects (measured, T025d). The full `text` is the line's accessible title
 * and its row in the contents table. Without a `label` nothing is drawn on the
 * line, and the table still says what the slot holds.
 */
export interface SldConnectionSlotContent {
  direction: SldSlotDirection;
  text: string;
  detail: string[];
  label?: string;
}

/**
 * Content a caller puts in the drawing's neutral value slots.
 *
 * The drawing does not know what the content is or where it came from: the
 * caller states that in `statement`, which replaces the drawing's own
 * "nothing on it is a measurement" description, and says in `unfilled` what a
 * slot it left empty means. Keys are component ids and connection ids from
 * the Site's own topology; a key the drawing does not have is ignored, and a
 * drawn item without a key shows `unfilled`.
 */
export interface SldSlotContent {
  statement: string;
  unfilled: string;
  nodes: ReadonlyMap<string, SldNodeSlotContent>;
  connections: ReadonlyMap<string, SldConnectionSlotContent>;
}

/**
 * The layout, in CSS pixels. The one thing this module decides.
 *
 * V-01a round 2 (Architect item 4, owner Q1): the v6.9 bus-bar grammar.
 * Supplies sit in the lanes left of the bus, the one declared bus is drawn as
 * a vertical bar spanning the rows, and what the bus feeds sits to its right.
 * Each component is an icon block with its declared name, declared rating and
 * slot underneath. Only declared nodes and connections are drawn: no breaker,
 * meter, monitoring link, status dot or voltage appears unless the selected
 * Foundation declares it as a component.
 */
const PADDING = 24;
/** The band above the rows where the bus is named. */
const HEADER = 64;
/** A lane's width: the icon and the name under it. */
const NODE_WIDTH = 156;
const NODE_HEIGHT = 126;
const ROW_PITCH = 144;
const LANE_GAP = 64;
/** How far a run between two nodes of one lane steps out to their left. */
const BRACKET = 14;
const ICON_W = COMPONENT_ICON_WIDTH;
const ICON_H = COMPONENT_ICON_HEIGHT;

/**
 * Where the text under an icon wraps.
 *
 * SVG text does not wrap and does not clip, so a name longer than its lane
 * runs into the next one. The name is wrapped instead of shortened: a
 * truncated component name is a fact hidden to make a layout tidy, and this
 * surface refuses that everywhere else.
 */
const NAME_LINE_BUDGET = 20;
const NAME_LINES = 2;

interface Box {
  x: number;
  y: number;
}

interface Placed {
  box: Box;
  bus: boolean;
}

interface Lattice {
  columnX: number[];
  width: number;
  height: number;
  busTop: number;
  busBottom: number;
}

/** Lane positions: a bus lane is a line, every other lane an icon's width. */
function latticeFor(diagram: SldDiagramView): Lattice {
  const busColumns = new Set(
    diagram.nodes.filter((node) => node.visualRole === "BUSBAR").map((node) => node.position.column),
  );
  const columnX: number[] = [];
  let x = PADDING;
  for (let column = 0; column < diagram.extent.columns; column += 1) {
    columnX.push(x);
    x += (busColumns.has(column) ? 0 : NODE_WIDTH) + LANE_GAP;
  }
  const rows = Math.max(1, diagram.extent.rows);
  const busTop = PADDING + HEADER - 10;
  const busBottom = PADDING + HEADER + (rows - 1) * ROW_PITCH + ICON_H + 10;
  return {
    columnX,
    width: x - LANE_GAP + PADDING,
    height: PADDING * 2 + HEADER + (rows - 1) * ROW_PITCH + NODE_HEIGHT,
    busTop,
    busBottom,
  };
}

function boxFor(node: SldNodeView, lattice: Lattice): Box {
  return {
    x: lattice.columnX[node.position.column] ?? PADDING,
    y: PADDING + HEADER + node.position.row * ROW_PITCH,
  };
}

/**
 * A display name broken onto at most two lines, on word boundaries.
 *
 * The remainder goes on the last line whole rather than being cut: a name too
 * long for two lines overflows its lane, which is visible and fixable, where a
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

const left = (box: Box) => ({ x: box.x, y: box.y + ICON_H / 2 });
const right = (box: Box) => ({ x: box.x + ICON_W, y: box.y + ICON_H / 2 });

/**
 * How a connection runs, in the bus-bar grammar.
 *
 * A run into or out of the bus meets the bar at the other end's own height,
 * so a supply's line goes straight across to the bus and a feeder leaves it
 * straight across to its load. Between two lanes the run turns in the gap
 * before the destination lane; between two nodes of one lane (a fuel tank
 * under the generator it feeds) it steps out to their left. There is no
 * routing search: the archetype is a fixed arrangement, and a router would be
 * the auto-layout this slice must not build.
 */
function runPoints(from: Placed, to: Placed, turn: SldConnectionView["route"]["turn"]): string {
  if (to.bus) {
    const start = from.box.x < to.box.x ? right(from.box) : left(from.box);
    return `${start.x},${start.y} ${to.box.x},${start.y}`;
  }
  if (from.bus) {
    const end = to.box.x > from.box.x ? left(to.box) : right(to.box);
    return `${from.box.x},${end.y} ${end.x},${end.y}`;
  }
  if (turn === "ROW_FIRST" || from.box.x === to.box.x) {
    const a = left(from.box);
    const b = left(to.box);
    const x = a.x - BRACKET;
    return `${a.x},${a.y} ${x},${a.y} ${x},${b.y} ${b.x},${b.y}`;
  }
  const rightward = to.box.x > from.box.x;
  const start = rightward ? right(from.box) : left(from.box);
  const end = rightward ? left(to.box) : right(to.box);
  if (start.y === end.y) return `${start.x},${start.y} ${end.x},${end.y}`;
  const turnX = rightward ? end.x - LANE_GAP / 2 : end.x + LANE_GAP / 2;
  return `${start.x},${start.y} ${turnX},${start.y} ${turnX},${end.y} ${end.x},${end.y}`;
}

/** A configured part chosen by stable component ID (V-01a round 2, item 3). */
export interface SldSelection {
  selected: string | null;
  onSelect: (componentId: string | null) => void;
}

/** What makes a drawn part a toggle, when the caller supplies a selection. */
function choiceProps(node: SldNodeView, selection: SldSelection | null, labelId: string) {
  if (selection === null) return {};
  const pressed = selection.selected === node.componentId;
  const toggle = () => selection.onSelect(pressed ? null : node.componentId);
  return {
    tabIndex: 0,
    role: "button",
    "aria-pressed": pressed,
    "aria-labelledby": labelId,
    "data-selected": pressed ? "" : undefined,
    onClick: toggle,
    onKeyDown: (event: KeyboardEvent<SVGGElement>) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        toggle();
      }
    },
  };
}

/**
 * W1-UX-05: a drawn part's accessible name, "<name>, <type>", held in a
 * non-drawn element the part points at, so the person-entered name is marked
 * user-owned one value at a time and the type word stays product wording.
 */
function SldNodeName({ id, node, selection }: { id: string; node: SldNodeView; selection: SldSelection | null }) {
  if (selection === null) return null;
  return (
    <text id={id} className="sld-node__name" display="none">
      <tspan data-vocabulary-exempt="user-owned">{`${node.displayName},`}</tspan>
      {` ${label(node.componentType, COMPONENT_TYPE_LABELS)}`}
    </text>
  );
}

/** The one declared bus: a bar spanning the rows, named above it. */
function SldBus({
  node,
  box,
  lattice,
  slots,
  selection,
}: {
  node: SldNodeView;
  box: Box;
  lattice: Lattice;
  slots: SldSlotContent | null;
  selection: SldSelection | null;
}) {
  const content = slots?.nodes.get(node.componentId) ?? null;
  const labelId = useId();
  const top = PADDING + 14;
  return (
    <>
      <g
        className="sld-node sld-node--bus"
        data-sld-node={node.nodeId}
        data-sld-component={node.componentId}
        data-sld-visual-role={node.visualRole}
        data-component-icon={node.symbol}
        {...choiceProps(node, selection, labelId)}
      >
        <rect
          className="sld-node__halo"
          x={box.x - 80}
          y={PADDING}
          width={160}
          height={lattice.busBottom - PADDING + 6}
          rx={6}
        />
        <text className="sld-node__name sld-node__name--bus" x={box.x} y={top} textAnchor="middle">
          {wrapName(node.displayName).map((line, index) => (
            <tspan key={line} x={box.x} dy={index === 0 ? 0 : 15} data-vocabulary-exempt="user-owned">
              {line}
            </tspan>
          ))}
        </text>
        <text className="sld-node__rating" x={box.x} y={top + 16} textAnchor="middle">
          {ratingText(node)}
        </text>
        {slots === null ? (
          <MissingClaimSvg
            gapId="G-sld-reporting-status"
            placement="sld.diagram.bus-slot"
            className="sld-node__slot"
            data-sld-slot="unfilled"
            x={box.x}
            y={top + 31}
            textAnchor="middle"
          >
            {AWAITING_RUNTIME_OR_EVIDENCE}
          </MissingClaimSvg>
        ) : (
          <text
            className="sld-node__slot"
            data-sld-slot={content === null ? "unfilled" : "filled"}
            x={box.x}
            y={top + 31}
            textAnchor="middle"
          >
            {content?.text ?? slots.unfilled}
          </text>
        )}
        <line
          className="sld-node__bar"
          x1={box.x}
          x2={box.x}
          y1={lattice.busTop}
          y2={lattice.busBottom}
        />
      </g>
      <SldNodeName id={labelId} node={node} selection={selection} />
    </>
  );
}

/** One drawn component: its icon, its declared name and rating, its slot. */
function SldNode({
  node,
  box,
  slots,
  selection,
}: {
  node: SldNodeView;
  box: Box;
  slots: SldSlotContent | null;
  selection: SldSelection | null;
}) {
  const content = slots?.nodes.get(node.componentId) ?? null;
  const labelId = useId();
  const text = box.y + ICON_H + 17;
  const nameLines = wrapName(node.displayName);
  // The lines under the name follow it, so a one-line name leaves no gap.
  const rating = text + 15 * (nameLines.length - 1) + 16;

  return (
    <>
      <g
        className="sld-node"
        data-sld-node={node.nodeId}
        data-sld-component={node.componentId}
        data-sld-visual-role={node.visualRole}
        data-sld-candidate={node.candidate === null ? undefined : "unsettled"}
        {...choiceProps(node, selection, labelId)}
      >
        <rect
          className="sld-node__halo"
          x={box.x - 6}
          y={box.y - 6}
          width={NODE_WIDTH + 12}
          height={NODE_HEIGHT + 6}
          rx={6}
        />
        <g transform={`translate(${box.x} ${box.y})`}>
          {/* The frame keeps `sld-node__box`: the Lab drawing's label-collision
              measurement reads it as the part's drawn extent on the line. */}
          <ComponentIconShape symbol={node.symbol} frameClassName="sld-node__box" />
        </g>
        {/*
          * One `text` element holding the whole name, wrapped into `tspan`
          * lines. One element per line would put the name on the screen as two
          * separate strings, and an assertion comparing a label to the record
          * would then have to know how this component chose to break it.
          */}
        <text className="sld-node__name" x={box.x} y={text}>
          {nameLines.map((line, index) => (
            <tspan key={line} x={box.x} dy={index === 0 ? 0 : 15} data-vocabulary-exempt="user-owned">
              {line}
            </tspan>
          ))}
        </text>
        <text className="sld-node__rating" x={box.x} y={rating}>
          {ratingText(node)}
        </text>
        {node.candidate === null ? null : (
          <text className="sld-node__candidate" x={box.x} y={rating + 15}>
            Proposed treatment
          </text>
        )}
        {slots === null ? (
          <MissingClaimSvg
            gapId="G-sld-reporting-status"
            placement="sld.diagram.node-slot"
            className="sld-node__slot"
            data-sld-slot="unfilled"
            x={box.x}
            y={rating + (node.candidate === null ? 15 : 30)}
          >
            {AWAITING_RUNTIME_OR_EVIDENCE}
          </MissingClaimSvg>
        ) : (
          <text
            className="sld-node__slot"
            data-sld-slot={content === null ? "unfilled" : "filled"}
            x={box.x}
            y={rating + (node.candidate === null ? 15 : 30)}
          >
            {content?.text ?? slots.unfilled}
          </text>
        )}
      </g>
      <SldNodeName id={labelId} node={node} selection={selection} />
    </>
  );
}

/** One declared connection, drawn as the archetype routes it. */
function SldRun({
  connection,
  placed,
  slot,
  markerId,
}: {
  connection: SldConnectionView;
  placed: Map<string, Placed>;
  slot: SldConnectionSlotContent | null;
  markerId: string;
}) {
  const from = placed.get(connection.fromNodeId);
  const to = placed.get(connection.toNodeId);
  if (from === undefined || to === undefined) return null;

  const points = runPoints(from, to, connection.route.turn);
  const marker = `url(#${markerId})`;
  const line = (
    <polyline
      className={`sld-run sld-run--${connection.medium.toLowerCase()}`}
      data-sld-connection={connection.connectionId}
      data-sld-stroke={connection.route.stroke}
      data-sld-turn={connection.route.turn}
      points={points}
      fill="none"
      markerEnd={slot?.direction === "ALONG" ? marker : undefined}
      markerStart={slot?.direction === "AGAINST" ? marker : undefined}
    />
  );
  if (slot === null || slot.label === undefined) return line;

  // A short label centred on the line's midpoint, where the route runs in a
  // gap of the lattice. Its title is the full statement, which says the
  // direction in words, and the contents table repeats it with the direction
  // column: no reading depends on the marker or its colour.
  const middle = midpointOf(points);
  return (
    <>
      {line}
      <text
        className="sld-run__value"
        data-sld-connection-value={connection.connectionId}
        data-sld-direction={slot.direction}
        x={middle.x}
        y={middle.y}
        textAnchor="middle"
        dominantBaseline="central"
      >
        <title>{`${slot.text} (${SLOT_DIRECTION_WORDS[slot.direction]})`}</title>
        {slot.label}
      </text>
    </>
  );
}

/** The point half way along a polyline, where its value label sits. */
function midpointOf(points: string): { x: number; y: number } {
  const vertices = points
    .split(" ")
    .map((pair) => pair.split(",").map(Number) as [number, number]);
  const lengths = vertices
    .slice(1)
    .map(([x, y], index) =>
      Math.hypot(x - vertices[index][0], y - vertices[index][1]),
    );
  let remaining = lengths.reduce((sum, length) => sum + length, 0) / 2;
  for (let index = 0; index < lengths.length; index += 1) {
    const [x0, y0] = vertices[index];
    const [x1, y1] = vertices[index + 1];
    if (remaining <= lengths[index] || index === lengths.length - 1) {
      const t =
        lengths[index] === 0 ? 0 : Math.min(1, remaining / lengths[index]);
      return { x: x0 + (x1 - x0) * t, y: y0 + (y1 - y0) * t };
    }
    remaining -= lengths[index];
  }
  return { x: vertices[0][0], y: vertices[0][1] };
}

/** What the Foundation's drawing says it is, above it (Architect item 4). */
export const SLD_CONFIGURED_NOT_LIVE = "Configured, not live";

/**
 * The drawing itself.
 *
 * `role="img"` with a title and a description when nothing on it can be
 * chosen, because the shapes and the routing carry no meaning a screen reader
 * can take from them. When the caller passes a selection, the drawing is a
 * named `group` instead and each part is a toggle button named by its declared
 * name and type, because an image's children are hidden from assistive
 * technology and a control nobody can reach is not a control.
 */
function SldDrawing({
  diagram,
  siteName,
  slots = null,
  idPrefix = "foundation-sld",
  labelledBy = SITE_SLD_HEADING_ID,
  selection = null,
}: {
  diagram: SldDiagramView;
  siteName: string;
  slots?: SldSlotContent | null;
  idPrefix?: string;
  labelledBy?: string;
  selection?: SldSelection | null;
}) {
  const lattice = latticeFor(diagram);
  const placed = new Map<string, Placed>();
  for (const node of diagram.nodes) {
    placed.set(node.nodeId, { box: boxFor(node, lattice), bus: node.visualRole === "BUSBAR" });
  }

  const titleId = `${idPrefix}-title`;
  const descriptionId = `${idPrefix}-description`;
  const markerId = `${idPrefix}-direction`;

  const media = [...new Set(diagram.connections.map((run) => run.medium))];

  return (
    <>
      {slots === null ? (
        // A one-line label, not a paragraph: the drawing still leads the
        // section at phone width (S1-03 review m2).
        <div className="sld-status" data-sld-configured="">
          <Badge tone="neutral">{SLD_CONFIGURED_NOT_LIVE}</Badge>
          <MissingClaim gapId="G-sld-reporting-status" placement="sld.diagram.readings-status">
            Readings are not assessed in this view.
          </MissingClaim>
        </div>
      ) : null}
      <div
        className="sld__scroll"
        role="region"
        aria-labelledby={labelledBy}
        tabIndex={0}
      >
        <svg
          className="sld"
          role={selection === null ? "img" : "group"}
          aria-labelledby={`${titleId} ${descriptionId}`}
          data-sld-archetype={diagram.archetype}
          data-sld-layout="bus-bar"
          width={lattice.width}
          height={lattice.height}
          viewBox={`0 0 ${lattice.width} ${lattice.height}`}
        >
          <title id={titleId}>
            Configured single line diagram for {siteName}
          </title>
          <desc id={descriptionId}>
            {slots === null
              ? "Drawn from this site's declared topology. Every component, " +
                "connection, device and signal it draws is listed in the " +
                "tables in this section; nothing on it is a measurement."
              : `Drawn from this site's declared topology. ${slots.statement}`}
          </desc>
          {slots === null ? null : (
            <defs>
              <marker
                id={markerId}
                className="sld-run__arrow"
                viewBox="0 0 10 10"
                refX={9}
                refY={5}
                markerWidth={8}
                markerHeight={8}
                orient="auto-start-reverse"
              >
                <path d="M0,0 L10,5 L0,10 z" />
              </marker>
            </defs>
          )}
          {diagram.connections.map((connection) => (
            <SldRun
              key={connection.connectionId}
              connection={connection}
              placed={placed}
              slot={slots?.connections.get(connection.connectionId) ?? null}
              markerId={markerId}
            />
          ))}
          {diagram.nodes.map((node) =>
            node.visualRole === "BUSBAR" ? (
              <SldBus
                key={node.nodeId}
                node={node}
                box={(placed.get(node.nodeId) as Placed).box}
                lattice={lattice}
                slots={slots}
                selection={selection}
              />
            ) : (
              <SldNode
                key={node.nodeId}
                node={node}
                box={(placed.get(node.nodeId) as Placed).box}
                slots={slots}
                selection={selection}
              />
            ),
          )}
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
function SldContents({
  diagram,
  slots = null,
  headingId = SITE_SLD_CONTENTS_ID,
  boundDevices = null,
}: {
  diagram: SldDiagramView;
  slots?: SldSlotContent | null;
  headingId?: string;
  boundDevices?: ReadonlySet<string> | null;
}) {
  return (
    <>
      <h4 className="subsection__subheading" id={headingId}>
        What the diagram draws
      </h4>
      <DataTable labelledBy={headingId}>
        {slots === null ? (
          <caption>
            Every component the diagram draws, with the devices configured
            against it and the signals this site&apos;s foundation declares are
            available about it. The readings and evidence column is the slot
            each drawn component carries:{" "}
            <MissingClaim gapId="G-sld-reporting-status" placement="sld.contents.caption">
              both are empty in this build, for every component, and neither
              holds a reading.
            </MissingClaim>
          </caption>
        ) : (
          <caption>
            {"Every component the diagram draws, with the devices configured " +
              "against it and the signals this site's foundation declares are " +
              "available about it. The value column is the slot each drawn " +
              `component carries. ${slots.statement}`}
          </caption>
        )}
        <thead>
          <tr>
            <th scope="col">Component</th>
            <th scope="col">Role in topology</th>
            <th scope="col">Declared rating</th>
            <th scope="col">Devices attached</th>
            <th scope="col">Signals available</th>
            <th scope="col">{slots === null ? "Readings and evidence" : "Value"}</th>
            <th scope="col">Node ID</th>
          </tr>
        </thead>
        <tbody>
          {diagram.nodes.map((node) => (
            <tr key={node.nodeId} data-sld-row={node.nodeId}>
              <td>
                <span data-vocabulary-exempt="user-owned">{node.displayName}</span>
              </td>
              <td>{label(node.nodeRole, TOPOLOGY_NODE_ROLE_LABELS)}</td>
              <td>{ratingText(node)}</td>
              <td>
                {node.attachedDevices.length === 0 ? (
                  "None configured against this component"
                ) : (
                  <ul className="cell-list">
                    {node.attachedDevices.map((device) =>
                      boundDevices === null ? (
                        <li key={device.deviceId}>
                          <span data-vocabulary-exempt="user-owned">{device.displayName}</span>
                        </li>
                      ) : (
                        <li
                          key={device.deviceId}
                          data-sld-device-binding={boundDevices.has(device.deviceId) ? "bound" : "unbound"}
                        >
                          <span data-vocabulary-exempt="user-owned">{device.displayName}</span>
                          {boundDevices.has(device.deviceId) ? null : " - no bound channel"}
                        </li>
                      ),
                    )}
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
                        <span data-vocabulary-exempt="user-owned">{signal.signalName}</span> ({signal.unit})
                      </li>
                    ))}
                  </ul>
                )}
              </td>
              <td data-sld-row-slot={node.componentId}>
                {slots === null ? (
                  <MissingClaim gapId="G-sld-reporting-status" placement="sld.contents.readings-slot">
                    {AWAITING_RUNTIME_OR_EVIDENCE}
                  </MissingClaim>
                ) : (
                  <SlotCell content={slots.nodes.get(node.componentId) ?? null} unfilled={slots.unfilled} />
                )}
              </td>
              <td>
                <code data-vocabulary-exempt="source-reference">{node.nodeId}</code>
              </td>
            </tr>
          ))}
        </tbody>
      </DataTable>
      {slots === null ? null : (
        <SldConnectionContents
          diagram={diagram}
          slots={slots}
          headingId={`${headingId}-connections`}
        />
      )}
    </>
  );
}

function SlotCell({
  content,
  unfilled,
}: {
  content: SldNodeSlotContent | SldConnectionSlotContent | null;
  unfilled: string;
}) {
  if (content === null) return <>{unfilled}</>;
  return (
    <ul className="cell-list">
      {[content.text, ...content.detail].map((line, index) => (
        <li key={`${index}-${line}`}>{line}</li>
      ))}
    </ul>
  );
}

/** The words for a connection slot's direction, so no reading needs the arrow. */
const SLOT_DIRECTION_WORDS: Record<SldSlotDirection, string> = {
  ALONG: "from -> to, in the declared order",
  AGAINST: "to -> from, against the declared order",
  NONE: "no direction",
};

/** What each drawn connection's slot holds, in text, when a caller filled any. */
function SldConnectionContents({
  diagram,
  slots,
  headingId,
}: {
  diagram: SldDiagramView;
  slots: SldSlotContent;
  headingId: string;
}) {
  const names = new Map(
    diagram.nodes.map((node) => [node.nodeId, node.displayName]),
  );
  return (
    <>
      <h4 className="subsection__subheading" id={headingId}>
        What each drawn connection carries
      </h4>
      <DataTable labelledBy={headingId}>
        <thead>
          <tr>
            <th scope="col">Connection</th>
            <th scope="col">Declared from</th>
            <th scope="col">Declared to</th>
            <th scope="col">Direction</th>
            <th scope="col">Value</th>
          </tr>
        </thead>
        <tbody>
          {diagram.connections.map((connection) => {
            const content =
              slots.connections.get(connection.connectionId) ?? null;
            return (
              <tr
                key={connection.connectionId}
                data-sld-connection-row={connection.connectionId}
                data-sld-direction={content?.direction ?? "UNFILLED"}
              >
                <th scope="row">{connection.connectionId}</th>
                <td>
                  {names.get(connection.fromNodeId) ?? connection.fromNodeId}
                </td>
                <td>{names.get(connection.toNodeId) ?? connection.toNodeId}</td>
                <td>
                  {content === null
                    ? "none stated"
                    : SLOT_DIRECTION_WORDS[content.direction]}
                </td>
                <td>
                  <SlotCell content={content} unfilled={slots.unfilled} />
                </td>
              </tr>
            );
          })}
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
              as a proposal rather than as settled practice. It says nothing
              about refrigeration performance, temperature, cold-chain
              compliance or product condition, and this build holds no such
              fact to say it with.
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
 * The configured drawing alone, with a caller's content in its value slots.
 *
 * The same view model, geometry and tables as the Foundation's diagram
 * section, without that section's heading, introduction or review questions:
 * the caller names what it is showing, states in `slots.statement` what the
 * values are, and composes whatever else belongs beside it. The drawing binds
 * nothing itself - which Site, which version and which values are the
 * caller's to establish before passing them in.
 */
export function ConfiguredSingleLineDrawing({
  site,
  slots,
  headingId,
  idPrefix,
}: {
  site: SiteDetailReadModel;
  slots: SldSlotContent;
  /** The caller's heading, which names the drawing's scroll region. */
  headingId: string;
  /** Distinguishes this drawing's element ids from any other on the page. */
  idPrefix: string;
}) {
  const view: SiteSldView = deriveSiteSldView(site);
  if (view.status !== "compatible") {
    return <SldUnavailable reason={view.reason} />;
  }
  return (
    <>
      <SldDrawing
        diagram={view.diagram}
        siteName={site.display_name}
        slots={slots}
        idPrefix={idPrefix}
        labelledBy={headingId}
      />
      <SldUnplaced diagram={view.diagram} />
      <SldContents
        diagram={view.diagram}
        slots={slots}
        headingId={`${idPrefix}-contents-heading`}
      />
    </>
  );
}

/**
 * The diagram section, in whichever of its two states this site is in.
 *
 * One entry point, so no caller has to know that the compatible and
 * unavailable branches exist, and neither branch can be rendered without the
 * other being considered.
 */
/** S1-02: what the SLD says when its signals are a published binding set. */
export const SITE_SLD_BINDINGS_STATEMENT =
  "For this stored Site, the signals listed are the channels bound in the " +
  "channel-link set in effect for the period shown. A device marked as having no " +
  "bound channel is registered, but nothing it could report is bound to a role.";

export function SiteSingleLineDiagram({
  site,
  boundDevices = null,
}: {
  site: SiteDetailReadModel;
  /**
   * S1-02: devices with a bound channel in the binding set in effect. When
   * given, every other attached device is shown as having no bound channel.
   */
  boundDevices?: ReadonlySet<string> | null;
}) {
  const view: SiteSldView = deriveSiteSldView(site);

  return (
    <div className="subsection" data-sld-region="">
      <h3 className="subsection__heading" id={SITE_SLD_HEADING_ID}>
        {SITE_SLD_HEADING}
      </h3>
      <SiteSldIntroduction />
      {boundDevices === null ? null : <p data-sld-bindings="">{SITE_SLD_BINDINGS_STATEMENT}</p>}

      {view.status === "compatible" ? (
        <>
          <SldDrawing diagram={view.diagram} siteName={site.display_name} />
          <SldUnplaced diagram={view.diagram} />
          <SldContents diagram={view.diagram} boundDevices={boundDevices} />
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

/**
 * S1-03: the configured drawing as the primary visual of the Foundation's
 * Single line diagram view, without the tables and review questions that
 * follow it as secondary detail (`SiteSldDetails`). The caller supplies the
 * panel and its heading; this names the drawing's scroll region by it.
 */
export function SiteSldPrimary({
  site,
  boundDevices,
  headingId,
  selection = null,
  strip = null,
}: {
  site: SiteDetailReadModel;
  boundDevices: ReadonlySet<string> | null;
  headingId: string;
  /** V-01a round 2: drawn parts become toggles that choose by component ID. */
  selection?: SldSelection | null;
  /** V-01a round 3: the in-context selected-part strip, below the drawing and outside its scroll area. */
  strip?: ReactNode;
}) {
  const view: SiteSldView = deriveSiteSldView(site);
  return (
    <div data-sld-region="">
      {/* The drawing leads (S1-03 review m2): at phone width the two
          explanatory paragraphs used to push it below the first screen. */}
      {view.status === "compatible" ? (
        <>
          <SldDrawing
            diagram={view.diagram}
            siteName={site.display_name}
            labelledBy={headingId}
            selection={selection}
          />
          <SldUnplaced diagram={view.diagram} />
        </>
      ) : (
        <SldUnavailable reason={view.reason} />
      )}
      {strip}
      <SiteSldIntroduction />
      {boundDevices === null ? null : <p data-sld-bindings="">{SITE_SLD_BINDINGS_STATEMENT}</p>}
    </div>
  );
}

/** S1-03: the diagram's contents table and open review questions, as secondary detail. */
export function SiteSldDetails({
  site,
  boundDevices,
}: {
  site: SiteDetailReadModel;
  boundDevices: ReadonlySet<string> | null;
}) {
  const view: SiteSldView = deriveSiteSldView(site);
  return (
    <>
      {view.status === "compatible" ? <SldContents diagram={view.diagram} boundDevices={boundDevices} /> : null}
      <SldOpenQuestions diagram={view.status === "compatible" ? view.diagram : null} />
    </>
  );
}
