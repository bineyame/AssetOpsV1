import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { App } from "../../App";

const operatorRoutes = ["/", "/sites", "/site-details", "/site-configuration"];

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );
}

describe("operator route frames", () => {
  it("renders the Sites route frame", () => {
    renderAt("/sites");

    expect(
      screen.getByRole("heading", { level: 1, name: "Sites" }),
    ).toBeInTheDocument();
  });

  it("renders the Site Details route frame", () => {
    renderAt("/site-details");

    expect(
      screen.getByRole("heading", { level: 1, name: "Site details" }),
    ).toBeInTheDocument();
  });

  it("renders the Site Configuration route frame", () => {
    renderAt("/site-configuration");

    expect(
      screen.getByRole("heading", { level: 1, name: "Site configuration" }),
    ).toBeInTheDocument();
  });
});

describe("operator route frame empty states", () => {
  it("states that no sites are configured on the Sites frame", () => {
    renderAt("/sites");

    expect(
      screen.getByRole("heading", { level: 2, name: "No sites configured" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /No sites have been configured, so there is nothing to list/i,
      ),
    ).toBeInTheDocument();
  });

  it("states that the Site Details frame describes no site", () => {
    renderAt("/site-details");

    expect(
      screen.getByRole("heading", { level: 2, name: "No site to show" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /No site has been configured, so this frame describes no site/i,
      ),
    ).toBeInTheDocument();
  });

  it("states that site configuration is unavailable", () => {
    renderAt("/site-configuration");

    expect(
      screen.getByRole("heading", {
        level: 2,
        name: "Site configuration unavailable",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/No site configuration exists in this build/i),
    ).toBeInTheDocument();
  });

  it.each(operatorRoutes)(
    "shows no fabricated values, charts, health, analytics, Replay, or Findings at %s",
    (path) => {
      const { container } = renderAt(path);

      expect(container.querySelectorAll("table")).toHaveLength(0);
      expect(container.querySelectorAll("svg, canvas, img")).toHaveLength(0);
      expect(screen.queryAllByRole("figure")).toHaveLength(0);
      expect(
        within(screen.getByRole("main")).queryAllByText(/\d/),
      ).toHaveLength(0);
    },
  );

  it.each(["/site-details", "/site-configuration"])(
    "does not hard-code a site identifier at %s",
    (path) => {
      const { container } = renderAt(path);

      expect(container.textContent).not.toMatch(/MG-?\s*\d/i);
      expect(container.textContent).not.toMatch(/\bsite[-_\s]?id\b/i);
    },
  );
});

describe("operator route navigation", () => {
  it("navigates between operator route frames", () => {
    renderAt("/");

    const operatorNavigation = screen.getByRole("navigation", {
      name: "Operator routes",
    });

    fireEvent.click(within(operatorNavigation).getByRole("link", { name: "Sites" }));
    expect(
      screen.getByRole("heading", { level: 1, name: "Sites" }),
    ).toBeInTheDocument();

    fireEvent.click(
      within(operatorNavigation).getByRole("link", { name: "Site details" }),
    );
    expect(
      screen.getByRole("heading", { level: 1, name: "Site details" }),
    ).toBeInTheDocument();

    fireEvent.click(
      within(operatorNavigation).getByRole("link", {
        name: "Site configuration",
      }),
    );
    expect(
      screen.getByRole("heading", { level: 1, name: "Site configuration" }),
    ).toBeInTheDocument();
  });

  it.each(operatorRoutes)(
    "exposes no Simulator Lab entry point at %s",
    (path) => {
      const { container } = renderAt(path);

      expect(container.textContent).not.toMatch(/simulator/i);
      for (const link of Array.from(container.querySelectorAll("a"))) {
        expect(link.getAttribute("href")).not.toMatch(/simulator/i);
      }
    },
  );

  it("keeps Simulator Lab outside the operator navigation layout", () => {
    renderAt("/simulator-lab");

    expect(screen.queryByRole("navigation")).toBeNull();
  });
});
