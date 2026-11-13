import { expect } from "vitest";

/**
 * UQ-FI-2 (D-UQFI.4, rev 6 6.3 "Tests"): a demo-path page has exactly one `h1`, it carries the headline
 * text, and it is the first element of its page header's title block (nothing above it but an eyebrow).
 * Call it after `settledScreen()`: a loading screen also has one `h1`.
 */
export function expectOneHeadline(text: string | RegExp): HTMLHeadingElement {
  const h1s = Array.from(document.querySelectorAll("h1"));
  expect(h1s.map((h) => h.textContent)).toHaveLength(1);
  const h1 = h1s[0];
  if (typeof text === "string") expect(h1.textContent).toBe(text);
  else expect(h1.textContent).toMatch(text);
  const header = h1.closest(".page-header");
  if (header !== null) {
    // The heading's title row is the first block in the header (an eyebrow is the only thing allowed above it).
    const block = h1.closest(".page-header__title");
    const before = block?.previousElementSibling ?? null;
    expect(before === null || before.classList.contains("page-header__eyebrow")).toBe(true);
  }
  return h1;
}

/**
 * Every registry gap id on the page, sorted, whether its gap renders as its own line or as a subject inside a
 * `GapGroup` line (both carry `data-gap-id`). A page test pins this list so a collapse cannot lose a gap (risk 4).
 */
export function gapIds(root: ParentNode = document): string[] {
  return Array.from(root.querySelectorAll("[data-gap-id]"))
    .map((el) => el.getAttribute("data-gap-id") ?? "")
    .sort();
}
