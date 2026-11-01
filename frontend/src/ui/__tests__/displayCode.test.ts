import { describe, expect, it } from "vitest";

import { displayCode } from "../displayCode";

describe("POLISH §3 displayCode", () => {
  it("pads the number to at least three digits after the prefix", () => {
    expect(displayCode("ACT-000001")).toBe("ACT-001");
    expect(displayCode("WR-000006")).toBe("WR-006");
    expect(displayCode("INC-000005")).toBe("INC-005");
    expect(displayCode("PM-000013")).toBe("PM-013");
    expect(displayCode("REC-000204")).toBe("REC-204");
    expect(displayCode("ACT-001234")).toBe("ACT-1234");
  });

  it("returns other text and absent codes unchanged", () => {
    expect(displayCode("Battery reserve trial")).toBe("Battery reserve trial");
    expect(displayCode("act-000001")).toBe("act-000001");
    expect(displayCode("ACT-")).toBe("ACT-");
    expect(displayCode(null)).toBeNull();
    expect(displayCode(undefined)).toBeUndefined();
  });
});
