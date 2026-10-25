import { describe, expect, it } from "vitest";

/** Node's fs has no types in this DOM-only tsconfig, so it is loaded untyped; paths are relative to `frontend/`. */
async function readDisk(path: string): Promise<string> {
  const fs = (await import(/* @vite-ignore */ `node:${"fs"}`)) as { readFileSync: (p: string, e: string) => string };
  const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
  return fs.readFileSync(`${cwd}/${path}`, "utf8");
}

describe("mock-deviation line styling is not owned by a Mini page stylesheet", () => {
  it("defines .mock-deviation-line in ui/mock-deviation.css only", async () => {
    expect(await readDisk("src/ui/mock-deviation.css")).toContain(".mock-deviation-line {");
    expect(await readDisk("src/sites/w4-mini-decisions.css")).not.toContain("mock-deviation-line");
  });

  it("is imported by every component that renders a data-mock-deviation line of this class", async () => {
    for (const file of ["src/shell/SiteAnalyticsFrames.tsx", "src/sites/SiteActionVerification.tsx"]) {
      const source = await readDisk(file);
      expect(source).toContain('className="mock-deviation-line"');
      expect(source).toContain('import "../ui/mock-deviation.css";');
    }
  });
});
