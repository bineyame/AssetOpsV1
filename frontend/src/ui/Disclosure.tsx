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
  children: ReactNode;
}

export function Disclosure({
  summary,
  name,
  defaultOpen = false,
  children,
}: DisclosureProps) {
  return (
    <details className="disclosure" data-disclosure={name} open={defaultOpen}>
      <summary className="disclosure__summary">{summary}</summary>
      <div className="disclosure__body">{children}</div>
    </details>
  );
}
