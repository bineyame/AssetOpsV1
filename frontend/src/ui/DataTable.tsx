import type { ReactNode } from "react";

/**
 * The one table pattern.
 *
 * It supplies the table element, its styling and the region that owns its
 * overflow, and nothing else: the caller owns its own columns and rows,
 * because which columns a screen has is that screen's information architecture
 * and not a shared decision. No slice adds a column here.
 *
 * `labelledBy` keeps the existing `aria-labelledby` pattern, so a table stays
 * named by the heading of the panel it sits in.
 *
 * ## Why the table is wrapped
 *
 * A `<table>` will not shrink below its min-content width. The Sites index has
 * nine columns with unbreakable headers, so it has a floor of roughly a
 * thousand pixels, and before T011B that floor pushed the operator shell
 * sideways: the overflow escaped the content area, reached the document, and
 * took the rail and the workspace bar with it. Chrome that slides away when a
 * table is wide is chrome that is not chrome.
 *
 * So every table in the product sits in a region that owns its own horizontal
 * overflow. The table keeps every column it renders - the M1 viewport policy
 * is explicit that a column is never dropped because the viewport is narrow,
 * because that would be a fourth state beside not rendered, labelled in place
 * and disabled - and the region scrolls instead.
 *
 * The region is wrapped here rather than left to each caller so that no screen
 * can render a bare table by forgetting to. A guard holds the other half of
 * that: the `data-table` class is spelled in this module and nowhere else.
 *
 * ## Why it is focusable
 *
 * A scrollable region that only a mouse can scroll hides content from a
 * keyboard. `tabIndex={0}` makes it a focus stop so the arrow keys reach it,
 * and `role="region"` with the panel heading's id gives that stop a name
 * instead of announcing an anonymous group. The name is the heading the table
 * already answers to, so nothing new is claimed.
 *
 * When no heading names the table there is nothing to call the region, so it
 * takes neither the role nor the focus stop: an unnamed focus stop is worse
 * than none.
 */
export interface DataTableProps {
  /** The id of the heading that names this table. */
  labelledBy?: string;
  children: ReactNode;
}

export function DataTable({ labelledBy, children }: DataTableProps) {
  return (
    <div
      className="data-table__scroll"
      role={labelledBy === undefined ? undefined : "region"}
      aria-labelledby={labelledBy}
      tabIndex={labelledBy === undefined ? undefined : 0}
    >
      <table className="data-table" aria-labelledby={labelledBy}>
        {children}
      </table>
    </div>
  );
}

/**
 * A description list of record facts, used where a screen shows one subject's
 * fields rather than a list of rows. Same vocabulary, different shape.
 */
export interface FactListProps {
  children: ReactNode;
}

export function FactList({ children }: FactListProps) {
  return <dl className="fact-list">{children}</dl>;
}

export interface FactProps {
  term: ReactNode;
  children: ReactNode;
}

export function Fact({ term, children }: FactProps) {
  return (
    <>
      <dt className="fact-list__term">{term}</dt>
      <dd className="fact-list__value">{children}</dd>
    </>
  );
}
