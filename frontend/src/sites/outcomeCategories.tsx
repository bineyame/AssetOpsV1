import { Fragment } from "react";

import { OutcomeGlyph, type OutcomeGlyphName } from "./componentIcons";
import "./outcomes.css";

/**
 * OUT-A A4: the outcome categories a Finding (or an Action) belongs to, as the server's outcome map
 * (policy `outcome-map/1`) states them. The wire's item order is final: the categories the record moves, in
 * first-appearance order, then the ones it must be checked against. Wire keys carry codes; nothing here puts
 * a code on screen.
 */
export type OutcomeCategoryKey = "GROW_REVENUE" | "OPTIMIZE_COST" | "PROTECT_ASSET" | "ASSURE_PERFORMANCE";

export interface OutcomeCategoryItem {
  category: OutcomeCategoryKey | string;
  label: string;
  role: "MOVES" | "CHECKED";
  outcomes: { key: string; label: string }[];
}

export interface OutcomeCategories {
  policy_version: string;
  state: "MAPPED" | "NOT_MAPPED";
  items: OutcomeCategoryItem[];
}

export const NOT_MAPPED_TEXT = "Category not mapped";

const GLYPH_OF_CATEGORY: Record<OutcomeCategoryKey, OutcomeGlyphName> = {
  GROW_REVENUE: "grow",
  OPTIMIZE_COST: "cost",
  PROTECT_ASSET: "protect",
  ASSURE_PERFORMANCE: "assure",
};

/** The category's icon, named by `label` (mock `catIcon`). Returns nothing for a category it has no glyph for. */
export function OutcomeIcon({
  icon,
  label,
  className,
  size,
}: {
  icon: OutcomeCategoryKey | string;
  label: string;
  className?: string;
  size?: number;
}) {
  const name = GLYPH_OF_CATEGORY[icon as OutcomeCategoryKey];
  if (name === undefined) return null;
  const classes = ["oc-cat", `oc-cat-${name}`, className].filter(Boolean).join(" ");
  return <OutcomeGlyph name={name} label={label} className={classes} size={size} />;
}

/** Ruling A-Q4: lower-case the first character only, so units stay correct ("supply cost per kWh"). */
export function lowerFirst(text: string): string {
  return text.length === 0 ? text : text.charAt(0).toLowerCase() + text.slice(1);
}

function mapped(categories: OutcomeCategories | null | undefined): categories is OutcomeCategories {
  return categories !== null && categories !== undefined && typeof categories === "object";
}

/**
 * The list-row form (mock `affectsPill`, `outcomes.js:29-30`): a solid pill per category the record moves, an
 * outlined pill per category it is only checked against, and none for a checked category already shown as
 * moved. An absent `categories` (an older body) renders nothing.
 */
export function CategoryTags({ categories }: { categories?: OutcomeCategories | null }) {
  if (!mapped(categories)) return null;
  if (categories.state !== "MAPPED") {
    return (
      <span className="oc-affectwrap" data-outcome-tags="">
        <span className="oc-affects quiet" data-outcome-role="NOT_MAPPED">
          {NOT_MAPPED_TEXT}
        </span>
      </span>
    );
  }
  const moves: OutcomeCategoryItem[] = [];
  const checked: OutcomeCategoryItem[] = [];
  for (const item of categories.items) {
    if (item.role === "MOVES") {
      if (!moves.some((seen) => seen.category === item.category)) moves.push(item);
    }
  }
  for (const item of categories.items) {
    if (item.role !== "CHECKED") continue;
    if (moves.some((seen) => seen.category === item.category)) continue;
    if (!checked.some((seen) => seen.category === item.category)) checked.push(item);
  }
  if (moves.length === 0 && checked.length === 0) return null;
  return (
    <span className="oc-affectwrap" data-outcome-tags="">
      {moves.map((item) => (
        <span
          key={`m-${item.category}`}
          className="oc-affects"
          data-outcome-role="MOVES"
          title={`Affects ${item.label}`}
        >
          <span className="visually-hidden">Affects </span>
          {item.label}
        </span>
      ))}
      {checked.map((item) => (
        <span
          key={`c-${item.category}`}
          className="oc-affects quiet"
          data-outcome-role="CHECKED"
          title={`Also checked under ${item.label}`}
        >
          <span className="visually-hidden">Also checked under </span>
          {item.label}
        </span>
      ))}
    </span>
  );
}

function Pill({ item, quiet }: { item: OutcomeCategoryItem; quiet: boolean }) {
  const names = item.outcomes.map((outcome) => lowerFirst(outcome.label)).join(", ");
  return (
    <span className={quiet ? "oc-pill quiet" : "oc-pill"} data-outcome-role={item.role}>
      {item.label}{" "}
      <small>{names}</small>
    </span>
  );
}

/**
 * The page form (mock `affectsLine`, `outcomes.js:33-34`): every item on the wire, the moved categories with
 * their outcome names, then "Also check" (a Finding) or "Safeguards checked" (an Action) and the checked ones.
 */
export function AffectsLine({
  categories,
  subject,
}: {
  categories?: OutcomeCategories | null;
  /** What the line belongs to; it names the second key ("Also check" for a Finding, "Safeguards checked" for an Action). */
  subject: "finding" | "action";
}) {
  if (!mapped(categories)) return null;
  if (categories.state !== "MAPPED") {
    return (
      <div className="oc-affectsline" data-affects-line="">
        <span className="oc-k">Affects</span>{" "}
        <span className="oc-pill quiet" data-outcome-role="NOT_MAPPED">
          {NOT_MAPPED_TEXT}
        </span>
      </div>
    );
  }
  const moves = categories.items.filter((item) => item.role === "MOVES");
  const checked = categories.items.filter((item) => item.role === "CHECKED");
  if (moves.length === 0 && checked.length === 0) return null;
  return (
    <div className="oc-affectsline" data-affects-line="">
      <span className="oc-k">Affects</span>{" "}
      {moves.map((item) => (
        <Fragment key={`m-${item.category}`}>
          <Pill item={item} quiet={false} />{" "}
        </Fragment>
      ))}
      {checked.length > 0 ? (
        <>
          <span className="oc-k">{subject === "action" ? "Safeguards checked" : "Also check"}</span>{" "}
          {checked.map((item) => (
            <Fragment key={`c-${item.category}`}>
              <Pill item={item} quiet />{" "}
            </Fragment>
          ))}
        </>
      ) : null}
    </div>
  );
}
