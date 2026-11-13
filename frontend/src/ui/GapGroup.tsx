import { Fragment, type ReactNode } from "react";
import { groupGaps, type GapItem } from "./gapGroup";

export interface GapGroupProps<T extends GapItem> {
  /** One section's gap statements, in the order the section shows them today. */
  items: readonly T[];
  /**
   * How a gap renders when it is the only one with its fact: exactly as the page renders it
   * today (D-UQFI.4, "a group with one subject renders exactly as today").
   */
  renderSingle: (item: T) => ReactNode;
  /** The subject's content inside its `<li>`; a MissingClaim-backed gap renders its MissingClaim here. */
  renderSubject?: (item: T) => ReactNode;
  className?: string;
  /** Inline form for a status strip, which holds inline elements only: spans in place of div/ul/li. */
  inline?: boolean;
}

/**
 * UQ-FI-2 (D-UQFI.4): one line per fact for a section: the fact once, then every subject it
 * applies to, each in its own node (separators are CSS). The component composes no words.
 * The line is a `div`, not the brief's `<p>`: a `<ul>` cannot sit inside a `<p>`.
 */
export function GapGroup<T extends GapItem>({ items, renderSingle, renderSubject, className, inline = false }: GapGroupProps<T>) {
  const [Line, List, Item] = inline ? (["span", "span", "span"] as const) : (["div", "ul", "li"] as const);
  const lines = groupGaps(items);
  // Each subject is matched back to its item (same fact, reason and subject, in order).
  const pool = [...items];
  const take = (fact: string, reason: string | undefined, subject: string): T => {
    const i = pool.findIndex((it) => it.fact === fact && it.reason === reason && it.subject === subject);
    return pool.splice(i, 1)[0];
  };
  return (
    <>
      {lines.map((line, n) => {
        const members = line.subjects.map((s) => take(line.fact, line.reason, s.subject));
        if (members.length === 1) return <Fragment key={n}>{renderSingle(members[0])}</Fragment>;
        return (
          <Line key={n} className={["gap-group", className].filter(Boolean).join(" ")} data-gap-group="">
            <span className="gap-group__fact">{line.fact}</span>
            <List className="gap-group__subjects">
              {members.map((item, k) => (
                <Item key={k} className="gap-group__subject" data-gap-id={renderSubject ? undefined : item.gapId}>
                  {renderSubject ? renderSubject(item) : item.subject}
                </Item>
              ))}
            </List>
          </Line>
        );
      })}
    </>
  );
}
