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
const COLD_CSS = NODE_FS.readFileSync(`${CWD}/src/sites/w1f4-changes-work.css`, "utf8");
const GREY = "rgb(248, 250, 253)";

afterEach(() => {
  cleanup();
  document.head.querySelectorAll("style[data-test-primitives]").forEach((n) => n.remove());
});

const TOKENS = NODE_FS.readFileSync(`${CWD}/src/ui/tokens.css`, "utf8");
const TOKEN_VALUES = new Map(Array.from(TOKENS.matchAll(/(--[a-z0-9-]+):\s*([^;]+);/g)).map((m) => [m[1], m[2].trim()]));
/** jsdom does not resolve `var()`, so each `var(--token)` is replaced by its `tokens.css` value before injection. */
const resolveTokens = (css: string) => css.replace(/var\((--[a-z0-9-]+)\)/g, (all, name: string) => TOKEN_VALUES.get(name) ?? all);
function mount(sticky: boolean, wrapperClass?: string) {
  for (const text of [CSS, COLD_CSS]) {
    const style = document.createElement("style");
    style.setAttribute("data-test-primitives", "");
    style.textContent = resolveTokens(text);
    document.head.appendChild(style);
  }
  const table = (
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
    </DataTable>
  );
  return render(wrapperClass === undefined ? table : <div className={wrapperClass}>{table}</div>);
}

describe("DataTable sticky header", () => {
  it("sticky mode keeps the class and a uniformly grey header; the body first cell keeps the raised token", () => {
    const { container } = mount(true);
    expect(container.querySelector(".data-table__scroll--sticky")).not.toBeNull();
    const heads = Array.from(container.querySelectorAll("thead th"));
    expect(heads).toHaveLength(2);
    expect(getComputedStyle(heads[0]).backgroundColor).toBe(GREY);
    expect(getComputedStyle(heads[1]).backgroundColor).toBe(GREY);
    expect(getComputedStyle(container.querySelector("tbody th")!).backgroundColor).toBe("rgb(255, 255, 255)");
  });

  it("the cold Actions wrapper (w1f4-changes-work cold-work-actions) has one uniform #f8fafd header row (RR-M1)", () => {
    const { container } = mount(true, "w1f4-changes-work cold-work-actions");
    const heads = Array.from(container.querySelectorAll("thead th"));
    expect(heads.map((h) => getComputedStyle(h).backgroundColor)).toEqual([GREY, GREY]);
    expect(COLD_CSS).not.toMatch(/thead th:first-child\s*\{[^}]*background/);
  });

  it("non-sticky mode has no sticky class and its header is not given the sticky grey rule", () => {
    const { container } = mount(false);
    expect(container.querySelector(".data-table__scroll--sticky")).toBeNull();
    expect(container.querySelector(".data-table__scroll")).not.toBeNull();
    const bg = getComputedStyle(container.querySelector("thead th")!).backgroundColor;
    expect(bg).toBe("rgb(241, 244, 249)"); // the shared `--surface-sunken` head, not the sticky #f8fafd
  });
});
