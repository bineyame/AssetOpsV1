import { afterEach, describe, expect, it } from "vitest";

import { applyReviewLabels, REVIEW_LABELS_KEY } from "../reviewLabels";

/** Vitest serves imported CSS (even `?raw`) as empty text, so the stylesheet is read from disk (paths from `frontend/`). */
async function readDisk(path: string): Promise<string> {
  const fs = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
  const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
  return fs.readFileSync(`${cwd}/${path}`, "utf8");
}

/** An in-memory session store; `fail` makes every call throw, as a blocked or private-mode store does. */
function store(initial: Record<string, string> = {}, fail = false) {
  const data = new Map(Object.entries(initial));
  const guard = () => {
    if (fail) throw new Error("storage blocked");
  };
  return {
    data,
    getItem: (k: string) => (guard(), data.get(k) ?? null),
    setItem: (k: string, v: string) => (guard(), void data.set(k, v)),
    removeItem: (k: string) => (guard(), void data.delete(k)),
  };
}

describe("review mode for MOCK DEVIATION labels (POLISH §2)", () => {
  afterEach(() => {
    delete document.documentElement.dataset.reviewLabels;
  });

  it("is off by default: no parameter and nothing stored", () => {
    const s = store();
    expect(applyReviewLabels("", () => s)).toBe(false);
    expect(document.documentElement.dataset.reviewLabels).toBeUndefined();
  });

  it("?review=labels turns it on for the session and sets the root attribute", () => {
    const s = store();
    expect(applyReviewLabels("?review=labels", () => s)).toBe(true);
    expect(s.data.get(REVIEW_LABELS_KEY)).toBe("on");
    expect(document.documentElement.getAttribute("data-review-labels")).toBe("on");
  });

  it("stays on across later page loads in the same session", () => {
    const s = store({ [REVIEW_LABELS_KEY]: "on" });
    expect(applyReviewLabels("?date=2026-10-01", () => s)).toBe(true);
    expect(document.documentElement.dataset.reviewLabels).toBe("on");
  });

  it("?review=off removes the session flag and the root attribute", () => {
    const s = store({ [REVIEW_LABELS_KEY]: "on" });
    document.documentElement.dataset.reviewLabels = "on";
    expect(applyReviewLabels("?review=off", () => s)).toBe(false);
    expect(s.data.has(REVIEW_LABELS_KEY)).toBe(false);
    expect(document.documentElement.dataset.reviewLabels).toBeUndefined();
  });

  it("ignores any other review value", () => {
    const s = store();
    expect(applyReviewLabels("?review=on", () => s)).toBe(false);
    expect(document.documentElement.dataset.reviewLabels).toBeUndefined();
  });

  it("with storage failing, the parameter alone decides for that page load", () => {
    const failing = store({}, true);
    expect(applyReviewLabels("?review=labels", () => failing)).toBe(true);
    expect(document.documentElement.dataset.reviewLabels).toBe("on");
    expect(applyReviewLabels("", () => failing)).toBe(false);
    expect(document.documentElement.dataset.reviewLabels).toBeUndefined();
    expect(applyReviewLabels("?review=off", () => failing)).toBe(false);
  });

  it("with the storage accessor itself throwing, it still decides from the parameter", () => {
    const thrower = () => {
      throw new Error("SecurityError");
    };
    expect(applyReviewLabels("?review=labels", thrower)).toBe(true);
    expect(applyReviewLabels("", thrower)).toBe(false);
  });

  it("the stylesheet hides every tagged label outside review mode", async () => {
    expect(await readDisk("src/ui/mock-deviation.css")).toContain(':root:not([data-review-labels="on"]) [data-mock-deviation] { display: none !important; }');
  });
});
