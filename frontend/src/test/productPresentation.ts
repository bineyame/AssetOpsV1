/**
 * The W1-UX shared acceptance check (W1-UX-01): with the exact-reference
 * disclosure closed, the plain state sentence, its scope and the "as of"
 * bound stay visible outside it. Every W1 consumer repeats this for its
 * non-positive states.
 */
import { expect } from "vitest";

/**
 * The only two forms an "as of" bound may take (`asOfText`): a formatted UTC
 * instant, or the honest "time not recorded" when the read returned none.
 * Mirrored by `AS_OF_PATTERN` in `tools/evidence-checks.mjs` for the browser
 * evidence scripts.
 */
export const AS_OF_PATTERN = /^As of(?: \d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4}, \d{2}:\d{2} UTC|: time not recorded)$/;

/** True when `el` is rendered outside the body of any closed disclosure. */
export function visibleOutsideClosedDisclosure(el: Element): boolean {
  let details: HTMLDetailsElement | null = el.closest("details");
  while (details !== null) {
    const summary: Element | null = details.querySelector(":scope > summary");
    if (!details.open && !(summary !== null && summary.contains(el))) return false;
    details = details.parentElement === null ? null : details.parentElement.closest("details");
  }
  return true;
}

/**
 * Assert the state line inside `within` carries a non-empty state sentence,
 * scope and "as of" bound, every exact-reference disclosure there is closed,
 * and the three stay visible outside it. Returns the state label.
 */
export function expectStateLineVisible(within: Element): string {
  const status = within.querySelector("[data-product-status]");
  expect(status, "a shared state line is rendered").not.toBeNull();
  for (const details of Array.from(within.querySelectorAll<HTMLDetailsElement>("details[data-exact-references]"))) {
    expect(details.open, "the exact-reference disclosure is closed").toBe(false);
  }
  const label = status!.querySelector("[data-product-status-label]");
  const sentence = status!.querySelector(".product-status__sentence");
  const scope = status!.querySelector("[data-product-status-scope]");
  const asOf = status!.querySelector("[data-product-status-as-of]");
  for (const [name, el] of [["state", label], ["sentence", sentence], ["scope", scope], ["as of", asOf]] as const) {
    expect(el, name).not.toBeNull();
    expect((el!.textContent ?? "").trim().length, `${name} has text`).toBeGreaterThan(0);
    expect(visibleOutsideClosedDisclosure(el!), `${name} is outside the closed disclosure`).toBe(true);
  }
  expect(asOf!.textContent).toMatch(AS_OF_PATTERN);
  return label!.textContent ?? "";
}
