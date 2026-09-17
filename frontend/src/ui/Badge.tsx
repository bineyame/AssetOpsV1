import type { ReactNode } from "react";

/**
 * The badge and pill vocabulary, defined once.
 *
 * `tone` names which vocabulary the value belongs to, and the four do not
 * share a tone. Provenance, lifecycle, configuration origin and source health
 * are separate concepts that this project forbids collapsing into one status
 * pill, and a shared tone is how that separation quietly dies: two vocabularies
 * that look identical are read as one.
 *
 * Defining a tone for a concept does not make it appear. A badge renders only
 * where a record supplies its value; there is no default, no placeholder, and
 * no empty badge. `Unknown` is not a badge value, it is the absence of one, and
 * a caller with nothing to show renders nothing.
 *
 * The value is always the visible text. The tone reinforces it and never
 * replaces it, so meaning survives without colour.
 */
export type BadgeTone = "provenance" | "lifecycle" | "origin" | "neutral";

export interface BadgeProps {
  tone: BadgeTone;
  /** The value from the record. */
  children: ReactNode;
}

export function Badge({ tone, children }: BadgeProps) {
  return <span className={`badge badge--${tone}`}>{children}</span>;
}
