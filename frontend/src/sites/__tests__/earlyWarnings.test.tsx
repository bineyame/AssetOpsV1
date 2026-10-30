import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { boardBody, fakeOutcomeBoard, outcomeWarning, planWarning } from "../../test/outcomeBoardFixture";
import { describeViolations, scanProductVocabulary } from "../../test/productVocabulary";
import { settledScreen } from "../../test/settled";
import { EarlyWarningList, miniBoardDay, SiteEarlyWarnings, WARNINGS_EXPLAIN } from "../EarlyWarnings";
import type { OutcomeWarning } from "../outcomeBoardClient";

const MONEY = /[$€£]|\b(USD|EUR|GBP|KES|ETB)\b/;

function renderList(warnings: OutcomeWarning[], props: { max?: number; showSite?: boolean } = {}) {
  return render(
    <MemoryRouter>
      <EarlyWarningList warnings={warnings} max={props.max} showSite={props.showSite ?? true} />
    </MemoryRouter>,
  );
}

const list = () => document.querySelector("[data-early-warnings]") as HTMLElement;

describe("OUT-C U5 early-warning list", () => {
  it("rendersTheMockStructureAndClasses", () => {
    renderList([outcomeWarning(), planWarning()]);
    const root = list();
    expect(root).toHaveClass("oc-warn");
    const head = root.querySelector(".oc-warn-head") as HTMLElement;
    expect(within(head).getByRole("heading", { level: 3 }).textContent).toBe("Early warnings · not priced yet");
    expect(within(head).getByRole("button", { name: "About early warnings" })).toHaveClass("oc-info");
    const items = Array.from(root.querySelectorAll("ul > li"));
    expect(items).toHaveLength(2);
    expect(items[0].querySelector(".oc-kind")?.className).toBe("oc-kind risk");
    expect(items[0].querySelector(".oc-kind")?.textContent).toBe("Risk");
    expect(items[1].querySelector(".oc-kind")?.className).toBe("oc-kind stress");
    expect(items[1].querySelector(".oc-kind")?.textContent).toBe("Early warning");
    const link = within(items[0] as HTMLElement).getByRole("link");
    expect(link).toHaveAttribute("href", "/maintenance/requests/case-3");
    expect(link.querySelector("strong")?.textContent).toBe("Repeated maintenance without a result");
    expect(items[0].querySelector("small")?.textContent).toBe(
      "GreenHarvest · Optimize cost and efficiency · generator-1 visited 3 times in 60 days (2 Oct, 14 Oct, 28 Oct); the linked finding is still open",
    );
  });

  it("dropsTheSiteWhenShowSiteIsFalseAndCapsAtMax", () => {
    renderList([outcomeWarning(), planWarning(), planWarning({ key: "PLAN_OVERDUE:p2", title: "Filter change overdue" })], {
      max: 2,
      showSite: false,
    });
    const items = Array.from(list().querySelectorAll("ul > li"));
    expect(items).toHaveLength(2);
    expect(items[1].querySelector("small")?.textContent).toBe("Protect asset and capital · Due 2 Nov");
    expect(list().textContent).not.toContain("Filter change overdue");
  });

  it("rendersNothingWhenEmpty", () => {
    const { container } = renderList([]);
    expect(container.innerHTML).toBe("");
  });

  it("explainerTakesFocusListsEachWarningClosesOnEscapeAndReturnsFocus", () => {
    renderList([outcomeWarning(), planWarning()]);
    const info = screen.getByRole("button", { name: "About early warnings" });
    info.focus();
    fireEvent.click(info);
    const dialog = document.querySelector("[data-warnings-explainer]") as HTMLDialogElement;
    expect(dialog).toHaveAttribute("open");
    expect(within(dialog).getByRole("heading", { level: 2 }).textContent).toBe("Early warnings");
    const close = within(dialog).getByRole("button", { name: "Close" });
    expect(document.activeElement).toBe(close);
    expect(dialog.querySelector("p.prose")?.textContent).toBe(WARNINGS_EXPLAIN);
    const heads = Array.from(dialog.querySelectorAll("thead th")).map((th) => th.textContent);
    expect(heads).toEqual(["Warning", "Outcome", "What would put a value on it"]);
    const cells = Array.from(dialog.querySelectorAll("tbody tr")).map((tr) => Array.from(tr.querySelectorAll("td")).map((td) => td.textContent));
    expect(cells).toEqual([
      ["Repeated maintenance without a result", "Optimize cost and efficiency", "A cost per visit is not set for this site"],
      ["Coil clean due soon", "Protect asset and capital", "Needs repair cost and wear history"],
    ]);
    fireEvent.keyDown(dialog, { key: "Tab" });
    expect(document.activeElement).toBe(close);
    fireEvent.keyDown(dialog, { key: "Escape" });
    expect(document.querySelector("[data-warnings-explainer]")).toBeNull();
    expect(document.activeElement).toBe(info);
  });

  it("showsNoCodeNoMoneyAndPassesTheW1VocabularyScan", () => {
    renderList([outcomeWarning(), planWarning()]);
    fireEvent.click(screen.getByRole("button", { name: "About early warnings" }));
    const root = list();
    const text = root.textContent ?? "";
    for (const code of ["REPEATED_MAINTENANCE_NO_RESULT", "PLAN_DUE_SOON", "CC-3", "CC-1", "NEEDS_ATTENTION", "RECURRING", "COST", "RISK"]) {
      expect(text).not.toContain(code);
    }
    expect(MONEY.test(text)).toBe(false);
    const scan = scanProductVocabulary(root, "site-findings", { set: "w1" });
    expect(scan.scanned).toBeGreaterThan(5);
    expect(describeViolations(scan.violations)).toBe("");
  });

  it("miniBoardDayIsTheUtcDayOfToOrThePreviousDayAtMidnight", () => {
    expect(miniBoardDay("2026-10-07T00:00:00Z")).toBe("2026-10-06");
    expect(miniBoardDay("2026-10-07T09:30:00Z")).toBe("2026-10-07");
    expect(miniBoardDay(null)).toBeNull();
    expect(miniBoardDay("not a time")).toBeNull();
  });

  it("siteListReadsTheBoardAndHidesWhenRefusedOrEmpty", async () => {
    const loaded = fakeOutcomeBoard({ status: "loaded", value: boardBody({ warnings: [planWarning()] }) });
    const first = render(
      <MemoryRouter>
        <SiteEarlyWarnings client={loaded.client} siteCode="GH-COLD-01" query={{ from: "a", to: "b", known_at: null }} />
      </MemoryRouter>,
    );
    await settledScreen();
    expect(loaded.calls).toEqual([{ siteCode: "GH-COLD-01", query: { from: "a", to: "b", known_at: null } }]);
    expect(list().querySelector("small")?.textContent).toBe("Protect asset and capital · Due 2 Nov");
    first.unmount();
    for (const read of [
      { status: "refused", httpStatus: 404, code: "SITE_NOT_FOUND" } as const,
      { status: "loaded", value: boardBody() } as const,
    ]) {
      const fake = fakeOutcomeBoard(read);
      const view = render(
        <MemoryRouter>
          <SiteEarlyWarnings client={fake.client} siteCode="GH-COLD-01" query={{ date: "2026-10-06" }} />
        </MemoryRouter>,
      );
      await settledScreen();
      // The read has no loading text: flush its promise so the absence is asserted on the answered read.
      await act(async () => {
        await new Promise((resolve) => setTimeout(resolve, 0));
      });
      expect(fake.calls).toHaveLength(1);
      expect(document.querySelector("[data-early-warnings]")).toBeNull();
      view.unmount();
    }
  });
});
