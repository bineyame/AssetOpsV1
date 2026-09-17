import type { ReactNode } from "react";

/**
 * The one table pattern.
 *
 * It supplies the table element and its styling and nothing else: the caller
 * owns its own columns and rows, because which columns a screen has is that
 * screen's information architecture and not a shared decision. This slice adds
 * no column anywhere.
 *
 * `labelledBy` keeps the existing `aria-labelledby` pattern, so a table stays
 * named by the heading of the panel it sits in.
 */
export interface DataTableProps {
  /** The id of the heading that names this table. */
  labelledBy?: string;
  children: ReactNode;
}

export function DataTable({ labelledBy, children }: DataTableProps) {
  return (
    <table className="data-table" aria-labelledby={labelledBy}>
      {children}
    </table>
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
