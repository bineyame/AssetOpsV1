import type { ReactNode } from "react";

/**
 * A closed-by-default disclosure: secondary content kept on the page, one
 * click away (T025e AC10). The content stays mounted while closed, so every
 * hook and heading inside it survives and nothing remounts when it opens.
 *
 * `name` is on `data-disclosure`, so a browser measurement can open every
 * disclosure before it measures (a closed one measures as zero).
 */
export interface DisclosureProps {
  /** The one-line summary a reader clicks. */
  summary: ReactNode;
  /** A stable name for the disclosure, on `data-disclosure`. */
  name: string;
  /** Open on first render. Closed unless a surface says otherwise. */
  defaultOpen?: boolean;
  /** W1-F3 height phase (additive): "inline" renders the summary as one small link on a row's link line. */
  variant?: "inline";
  children: ReactNode;
}

export function Disclosure({
  summary,
  name,
  defaultOpen = false,
  variant,
  children,
}: DisclosureProps) {
  return (
    <details className={variant === "inline" ? "disclosure disclosure--inline" : "disclosure"} data-disclosure={name} open={defaultOpen}>
      <summary className="disclosure__summary">{summary}</summary>
      <div className="disclosure__body">{children}</div>
    </details>
  );
}

/**
 * W1-F3 height phase (additive): the mock shows the latest few rows of a list;
 * the rest stay on the page behind one plain "Show all N" expander. Closed
 * unless `defaultOpen` (a selected row that would otherwise be hidden). The
 * content stays mounted, so every row is still in the document and reachable.
 */
export interface ShowAllProps {
  /** The plain expander words, e.g. "Show all 205 versions". */
  summary: ReactNode;
  /** A stable name, on `data-show-all`. */
  name: string;
  defaultOpen?: boolean;
  children: ReactNode;
}

export function ShowAll({ summary, name, defaultOpen = false, children }: ShowAllProps) {
  return (
    <details className="v69-show-all" data-show-all={name} open={defaultOpen}>
      <summary className="v69-show-all__summary">{summary}</summary>
      <div className="v69-show-all__body">{children}</div>
    </details>
  );
}
