import { fireEvent, within } from "@testing-library/react";
import { expect } from "vitest";

/**
 * W1-F5b (D-2026-10-17-f5-subtabs-and-contact): the shared assertions for an unbuilt in-page tab or lens chip.
 * It is announced and shown as "Not available yet", sits in its row as text, and is not a control: no link,
 * button, href, tab stop, handler, disabled or aria-disabled; Enter and Space on it change nothing.
 */
export const UNAVAILABLE_STATUS = "Not available yet";

export function expectUnavailableEntry(row: HTMLElement, label: string): HTMLElement {
  const entry = within(row).getByRole("listitem", { name: `${label}, ${UNAVAILABLE_STATUS}` });
  expect(entry.textContent).toContain(label);
  expect(entry.textContent).toContain(UNAVAILABLE_STATUS);
  expect(within(row).queryByRole("link", { name: new RegExp(`^${label}\\b`) })).toBeNull();
  expect(within(row).queryByRole("button", { name: new RegExp(`^${label}\\b`) })).toBeNull();
  for (const el of [entry, ...Array.from(entry.querySelectorAll("*"))]) {
    expect(el.tagName, `${label}: ${el.outerHTML}`).not.toMatch(/^(A|BUTTON|INPUT|SELECT)$/);
    for (const attr of ["href", "tabindex", "disabled", "aria-disabled", "onclick", "role"]) {
      expect(el.hasAttribute(attr), `${label}: ${attr}`).toBe(false);
    }
  }
  // Keyboard: it cannot take focus, and Enter or Space on it does not navigate or change the row.
  entry.focus();
  expect(document.activeElement).not.toBe(entry);
  const before = `${window.location.href}|${row.innerHTML}`;
  fireEvent.keyDown(entry, { key: "Enter" });
  fireEvent.keyDown(entry, { key: " " });
  fireEvent.click(entry);
  expect(`${window.location.href}|${row.innerHTML}`).toBe(before);
  return entry;
}

/** The row's entries in DOM order, live or not, by visible label. */
export function rowLabels(row: HTMLElement): string[] {
  return Array.from(row.querySelectorAll(":scope li")).map((li) =>
    li.hasAttribute("data-tab-unavailable") || li.hasAttribute("data-chip-unavailable")
      ? `${li.getAttribute("data-tab-unavailable") ?? li.getAttribute("data-chip-unavailable")} (${UNAVAILABLE_STATUS})`
      : (li.textContent ?? "").trim(),
  );
}
