// @vitest-environment jsdom
/**
 * W5-03b ruling 25: a sticky-first-column DataTable shows one uniform mock-grey header (#f8fafd), first cell included.
 * jsdom computes the cascade from the real `primitives.css` text injected here; the browser-computed values at 1440
 * and 390 are checked by the capture run (`.agent/W5-03b-ui-evidence/capture.mjs`, `headerBackgrounds`).
 */
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { DataTable } from "../DataTable";

const NODE_FS = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
const CWD = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
const CSS = NODE_FS.readFileSync(`${CWD}/src/ui/primitives.css`, "utf8");
const GREY = "rgb(248, 250, 253)";

afterEach(() => {
  cleanup();
  document.head.querySelectorAll("style[data-test-primitives]").forEach((n) => n.remove());
});

function mount(sticky: boolean) {
  const style = document.createElement("style");
  style.setAttribute("data-test-primitives", "");
  style.textContent = CSS;
  document.head.appendChild(style);
  return render(
    <DataTable stickyFirstColumn={sticky}>
      <thead>
        <tr>
          <th scope="col">Asset</th>
          <th scope="col">Supported assessment</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th scope="row">c1</th>
          <td>x</td>
        </tr>
      </tbody>
    </DataTable>,
  );
}

describe("DataTable sticky header", () => {
  for (const width of [1440, 390]) {
    it(`sticky mode keeps the class and a uniformly grey header at ${width}px; body first cell stays raised`, () => {
      Object.defineProperty(window, "innerWidth", { configurable: true, value: width });
      const { container } = mount(true);
      expect(container.querySelector(".data-table__scroll--sticky")).not.toBeNull();
      const heads = Array.from(container.querySelectorAll("thead th"));
      expect(heads).toHaveLength(2);
      expect(getComputedStyle(heads[0]).backgroundColor).toBe(GREY);
      expect(getComputedStyle(heads[1]).backgroundColor).toBe(GREY);
      const bodyFirst = container.querySelector("tbody th")!;
      expect(getComputedStyle(bodyFirst).backgroundColor).not.toBe(GREY);
    });
  }

  it("non-sticky mode has no sticky class and the sticky header rule does not apply", () => {
    const { container } = mount(false);
    expect(container.querySelector(".data-table__scroll--sticky")).toBeNull();
    expect(container.querySelector(".data-table__scroll")).not.toBeNull();
    expect(getComputedStyle(container.querySelector("thead th")!).backgroundColor).not.toBe(GREY);
  });
});
