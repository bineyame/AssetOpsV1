/**
 * Post-W6 W6 caps ruling 4: in-cell progressive disclosure. The value shows plainly when it fits; when it overflows
 * its two-line preview a visible "Show full" button (column-and-row accessible name, native button, sibling of any
 * cell link) reveals the complete unchanged value inline and offers "Show less". The overflow check runs on mount,
 * on resize (ResizeObserver) and on content change.
 */
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Link } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { CellDisclosure } from "../CellDisclosure";
import { ResizeObserverStub, stubCellOverflow } from "./cellDisclosureStub";

const LONG = "Field maintenance supervisor team on rotation ".repeat(4).slice(0, 160);
let restore: () => void = () => {};

beforeEach(() => {
  ResizeObserverStub.instances = [];
  vi.stubGlobal("ResizeObserver", ResizeObserverStub);
  restore = stubCellOverflow();
});

afterEach(() => {
  cleanup();
  restore();
  vi.unstubAllGlobals();
});

const value = () => document.querySelector(".cell-disclosure__value") as HTMLElement;
const state = () => document.querySelector("[data-cell-disclosure]")?.getAttribute("data-cell-disclosure-state");

describe("caps ruling 4: CellDisclosure", () => {
  it("shows a value that fits plainly, with no disclosure button", () => {
    render(<CellDisclosure column="Owner" row="INC-0001">Ops team</CellDisclosure>);
    expect(value().textContent).toBe("Ops team");
    expect(value().className).toContain("global-work-clamp--two");
    expect(screen.queryByRole("button")).toBeNull();
    expect(state()).toBe("fits");
  });

  it("offers Show full / Show less with a column-and-row name for an overflowing value, keeping it unchanged", () => {
    render(
      <CellDisclosure column="Owner" row="INC-0001" data={{ "data-global-work-owner": "" }}>
        {LONG}
      </CellDisclosure>,
    );
    const button = screen.getByRole("button", { name: "Show full Owner for INC-0001" });
    expect(button.tagName).toBe("BUTTON");
    expect(button.getAttribute("type")).toBe("button");
    expect(button.textContent).toBe("Show full");
    expect(button.getAttribute("aria-expanded")).toBe("false");
    expect(button.getAttribute("aria-controls")).toBe(value().id);
    expect(value().hasAttribute("data-global-work-owner")).toBe(true);
    expect(state()).toBe("collapsed");
    // Keyboard: a native button takes focus and activates with Enter/Space; no hover-only path.
    button.focus();
    expect(document.activeElement).toBe(button);
    fireEvent.click(button);
    const less = screen.getByRole("button", { name: "Show less Owner for INC-0001" });
    expect(less).toBe(button);
    expect(less.textContent).toBe("Show less");
    expect(less.getAttribute("aria-expanded")).toBe("true");
    expect(value().getAttribute("data-cell-disclosure-expanded")).toBe("true");
    expect(value().textContent).toBe(LONG);
    expect(state()).toBe("expanded");
    fireEvent.click(less);
    expect(screen.getByRole("button", { name: "Show full Owner for INC-0001" }).getAttribute("aria-expanded")).toBe(
      "false",
    );
    expect(value().getAttribute("data-cell-disclosure-expanded")).toBe("false");
    expect(document.querySelector("[title]")).toBeNull();
  });

  it("keeps the button a sibling of a cell link, never nested in it", () => {
    render(
      <MemoryRouter>
        <CellDisclosure column="Site" row="INC-0002">
          <Link to="/sites/KOBO-001">{LONG}</Link>
        </CellDisclosure>
      </MemoryRouter>,
    );
    const button = screen.getByRole("button", { name: "Show full Site for INC-0002" });
    const link = screen.getByRole("link");
    expect(button.closest("a")).toBeNull();
    expect(link.contains(button)).toBe(false);
    expect(link.querySelector("button")).toBeNull();
  });

  it("re-measures on resize: a value that starts fitting gains the button when its box overflows", () => {
    let limit = 400;
    restore();
    restore = stubCellOverflow(limit);
    render(<CellDisclosure column="Feeds" row="REC-0003">{LONG}</CellDisclosure>);
    expect(screen.queryByRole("button")).toBeNull();
    // A narrower column: the same text now overflows two lines, which the resize observer reports.
    limit = 40;
    restore();
    restore = stubCellOverflow(limit);
    expect(ResizeObserverStub.instances.some((o) => o.targets.includes(value()))).toBe(true);
    act(() => ResizeObserverStub.fire());
    expect(screen.getByRole("button", { name: "Show full Feeds for REC-0003" })).toBeTruthy();
  });

  it("re-measures on a content change that keeps the box size", async () => {
    render(<CellDisclosure column="By" row="REC-0004">short</CellDisclosure>);
    expect(screen.queryByRole("button")).toBeNull();
    await act(async () => {
      value().firstChild!.textContent = LONG;
      await Promise.resolve();
    });
    expect(screen.getByRole("button", { name: "Show full By for REC-0004" })).toBeTruthy();
  });
});
