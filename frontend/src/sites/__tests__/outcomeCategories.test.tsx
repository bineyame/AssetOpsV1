/**
 * OUT-A A4: the outcome category pills (list form) and the Affects line (page form), against the
 * `outcome-map/1` wire (build spec §1.3, A4, A.3, A.4).
 */
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { AffectsLine, CategoryTags, lowerFirst, OutcomeIcon } from "../outcomeCategories";
import { F104, F118, F119, F130, GROW, NOT_MAPPED, OPT, PRO } from "./outcomeFixtures";

afterEach(cleanup);

const fs = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
const CWD = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();

const squash = (s: string | null | undefined) => (s ?? "").replace(/\s+/g, " ").trim();

function pills(container: HTMLElement) {
  return Array.from(container.querySelectorAll<HTMLElement>(".oc-affects")).map((el) => ({
    label: squash(Array.from(el.childNodes).filter((n) => n.nodeType === Node.TEXT_NODE).map((n) => n.textContent).join("")),
    quiet: el.classList.contains("quiet"),
    name: squash(el.textContent),
  }));
}

function expectClean(container: HTMLElement, page: string) {
  const scan = scanProductVocabulary(container, page, { set: "w1" });
  expect(scan.scanned).toBeGreaterThan(0);
  expect(describeViolations(scan.violations)).toBe("");
  expect(container.textContent ?? "").not.toMatch(/\b(MG|CC|EV)-\d\b|outcome-map|MOVES|CHECKED|NOT_MAPPED|[A-Z]+_[A-Z]+/);
}

describe("CategoryTags (list form)", () => {
  it("f104_one_solid_and_one_outlined_pill_with_accessible_names", () => {
    const { container } = render(<CategoryTags categories={F104} />);
    expect(pills(container)).toEqual([
      { label: OPT, quiet: false, name: `Affects ${OPT}` },
      { label: PRO, quiet: true, name: `Also checked under ${PRO}` },
    ]);
    // The role word is visually hidden text, not a title alone.
    expect(container.querySelectorAll(".oc-affects .visually-hidden")).toHaveLength(2);
    expectClean(container, "list pills");
  });

  it("f118_checked_category_already_moving_is_not_outlined", () => {
    const { container } = render(<CategoryTags categories={F118} />);
    expect(pills(container)).toEqual([
      { label: PRO, quiet: false, name: `Affects ${PRO}` },
      { label: OPT, quiet: true, name: `Also checked under ${OPT}` },
    ]);
  });

  it("f130_wire_order_protect_then_grow_and_no_outlined_pill", () => {
    const { container } = render(<CategoryTags categories={F130} />);
    expect(pills(container).map((p) => [p.label, p.quiet])).toEqual([
      [PRO, false],
      [GROW, false],
    ]);
    expect(container.querySelectorAll(".oc-affects.quiet")).toHaveLength(0);
  });

  it("f119_only_one_solid_pill", () => {
    const { container } = render(<CategoryTags categories={F119} />);
    expect(pills(container).map((p) => [p.label, p.quiet])).toEqual([[PRO, false]]);
  });

  it("not_mapped_reads_category_not_mapped_as_a_quiet_pill", () => {
    const { container } = render(<CategoryTags categories={NOT_MAPPED} />);
    const only = container.querySelectorAll(".oc-affects");
    expect(only).toHaveLength(1);
    expect(only[0].classList.contains("quiet")).toBe(true);
    expect(squash(only[0].textContent)).toBe("Category not mapped");
    expectClean(container, "list pills not mapped");
  });

  it("absent_key_renders_nothing", () => {
    const { container } = render(<CategoryTags categories={undefined} />);
    expect(container.innerHTML).toBe("");
  });
});

describe("AffectsLine (page form)", () => {
  it("action_line_with_safeguards_checked_and_first_character_lower_cased", () => {
    const { container } = render(<AffectsLine categories={F104} variant="action" />);
    const lines = container.querySelectorAll("[data-affects-line]");
    expect(lines).toHaveLength(1);
    expect(squash(lines[0].textContent)).toBe(
      "Affects Optimize cost and efficiency supply cost per kWh Safeguards checked Protect asset and capital reliable service, battery and generator life",
    );
    expect(container.querySelectorAll(".oc-pill:not(.quiet)")).toHaveLength(1);
    expect(container.querySelectorAll(".oc-pill.quiet")).toHaveLength(1);
    expectClean(container, "action affects line");
  });

  it("f118_finding_line_shows_every_wire_item", () => {
    const { container } = render(<AffectsLine categories={F118} variant="finding" />);
    expect(squash(container.querySelector("[data-affects-line]")?.textContent)).toBe(
      "Affects Protect asset and capital cooling continuity, stock kept saleable Also check Protect asset and capital compressor life Optimize cost and efficiency cost per cooling unit",
    );
    expect(container.querySelectorAll(".oc-pill.quiet")).toHaveLength(2);
    expectClean(container, "finding affects line");
  });

  it("no_checked_items_omits_the_second_key", () => {
    const { container } = render(<AffectsLine categories={F119} variant="finding" />);
    expect(squash(container.textContent)).toBe("Affects Protect asset and capital stock kept saleable");
    expect(container.querySelectorAll(".oc-k")).toHaveLength(1);
  });

  it("not_mapped_and_absent", () => {
    const first = render(<AffectsLine categories={NOT_MAPPED} variant="finding" />);
    expect(squash(first.container.textContent)).toBe("Affects Category not mapped");
    first.unmount();
    const second = render(<AffectsLine categories={undefined} variant="action" />);
    expect(second.container.innerHTML).toBe("");
  });

  it("lower_first_changes_only_the_first_character", () => {
    expect(lowerFirst("Supply cost per kWh")).toBe("supply cost per kWh");
    expect(lowerFirst("")).toBe("");
  });
});

describe("OutcomeIcon", () => {
  it("is_an_image_named_by_its_label_and_unknown_categories_draw_nothing", () => {
    const { container } = render(
      <>
        <OutcomeIcon icon="GROW_REVENUE" label={GROW} />
        <OutcomeIcon icon="SOMETHING_ELSE" label="x" />
      </>,
    );
    const svgs = container.querySelectorAll("svg");
    expect(svgs).toHaveLength(1);
    expect(svgs[0].getAttribute("role")).toBe("img");
    expect(svgs[0].getAttribute("aria-label")).toBe(GROW);
    expect(svgs[0].querySelector("title")?.textContent).toBe(GROW);
    expect(svgs[0].classList.contains("oc-cat-grow")).toBe(true);
  });

  it("outcome_categories_module_draws_no_svg_itself", () => {
    const source = fs.readFileSync(`${CWD}/src/sites/outcomeCategories.tsx`, "utf8");
    expect(source).not.toContain("<svg");
  });
});

/* --- Contrast (guide §4): pill text pairs computed from the token hex values. --- */

function tokens(): Record<string, string> {
  const css = fs.readFileSync(`${CWD}/src/ui/tokens.css`, "utf8");
  const root = css.slice(css.indexOf(":root"));
  const out: Record<string, string> = {};
  for (const m of root.matchAll(/(--[a-z0-9-]+):\s*(#[0-9a-fA-F]{6})\s*;/g)) if (!(m[1] in out)) out[m[1]] = m[2];
  return out;
}

function rule(css: string, selector: string): string {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const m = css.match(new RegExp(`(?:^|\\n|\\})\\s*${escaped}\\s*\\{([^}]*)\\}`));
  if (!m) throw new Error(`no rule for ${selector}`);
  return m[1];
}

function decl(body: string, property: string): string | null {
  const m = body.match(new RegExp(`(?:^|;|\\s)${property}:\\s*var\\((--[a-z0-9-]+)\\)`));
  return m ? m[1] : null;
}

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string): number {
  const [x, y] = [luminance(a), luminance(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}

describe("pill contrast", () => {
  it("every_pill_text_pair_is_at_least_4_5_to_1", () => {
    const t = tokens();
    const css = fs.readFileSync(`${CWD}/src/sites/outcomes.css`, "utf8");
    const solid = rule(css, ".oc-affects");
    const quiet = rule(css, ".oc-affects.quiet");
    const pill = rule(css, ".oc-pill");
    const pillQuiet = rule(css, ".oc-pill.quiet");
    const small = rule(css, ".oc-pill small");
    const pairs: [string, string | null, string | null][] = [
      ["list pill", decl(solid, "color"), decl(solid, "background")],
      ["quiet list pill", decl(quiet, "color"), decl(quiet, "background")],
      ["page pill", decl(pill, "color"), decl(pill, "background")],
      ["page pill small", decl(small, "color"), decl(pill, "background")],
      ["quiet page pill", decl(pillQuiet, "color"), decl(pillQuiet, "background")],
      ["quiet page pill small", decl(small, "color"), decl(pillQuiet, "background")],
    ];
    expect(pairs.length).toBe(6);
    for (const [name, fg, bg] of pairs) {
      expect(fg, `${name} colour token`).not.toBeNull();
      expect(bg, `${name} background token`).not.toBeNull();
      const ratio = contrast(t[fg as string], t[bg as string]);
      expect(ratio, `${name}: ${fg} on ${bg}`).toBeGreaterThanOrEqual(4.5);
    }
  });
});
