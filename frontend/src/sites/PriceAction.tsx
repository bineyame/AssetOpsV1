import { Link, useLocation } from "react-router-dom";
import { useLinkFor, type Ref } from "./chainRef";
import "./priceAction.css";

/**
 * PR-1 (BL-68, architect-answer-price-it §4.1): the server-built link on an unpriced item. Two shapes; the words
 * (`label`, `text`) are the server's, and this component never decides which items are priceable. A missing action,
 * or a ref with no screen, renders nothing.
 */
export type PriceAction =
  | { kind: "SET_PRICE"; key: string; label: string; href: string | null; link_ref: Ref }
  | { kind: "NEEDS_MODEL"; need_key: string; text: string; label: string; href: string | null; link_ref: Ref };

/** The shared-range keys the price page keeps (SR), copied from the current address when present. */
const RANGE_KEYS = ["from", "to", "known_at"] as const;

/**
 * The link address: the server's path, the current shared range, and `return` (the current address), so the price
 * page can bring the reader back exactly where they were.
 */
export function priceActionTarget(path: string, current: { pathname: string; search: string }): string {
  const [base, query = ""] = path.split("?", 2);
  const params = new URLSearchParams(query);
  const here = new URLSearchParams(current.search);
  for (const key of RANGE_KEYS) {
    const value = here.get(key);
    if (value) params.set(key, value);
  }
  params.set("return", `${current.pathname}${current.search}`);
  return `${base}?${params.toString()}`;
}

export function PriceActionLink({ action }: { action: PriceAction | null | undefined }) {
  const linkFor = useLinkFor();
  const location = useLocation();
  if (!action) return null;
  const path = linkFor(action.link_ref);
  if (!path) return null;
  return (
    <Link className="price-action-link" to={priceActionTarget(path, location)} data-price-action={action.kind}>
      {action.label}
    </Link>
  );
}

/**
 * The `return` address the price page goes back to: only a same-app path ("/..."), never another origin
 * ("//host", "http:"), so a crafted link cannot send the reader elsewhere.
 */
export function safeReturn(value: string | null): string | null {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.startsWith("/\\")) return null;
  return value;
}
