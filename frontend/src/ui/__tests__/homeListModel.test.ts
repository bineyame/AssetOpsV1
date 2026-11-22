import { describe, expect, it } from "vitest";

import { HOME_LIST_CAP, homeListHref, homeListModel, type ListDefModel } from "../homeListModel";

/** IA-2b §8 Block A on a synthetic store: 25 items in 3 groups (a: 13, b: 7, c: 5), every figure a literal. */
interface Item {
  id: string;
  g: "a" | "b" | "c";
  state: "open" | "done";
  name: string;
  site: string;
  rank: number;
  hot: boolean;
}

function store(n: number): Item[] {
  const groups: Item["g"][] = ["a", "b", "c"];
  const out: Item[] = [];
  for (let i = 0; i < n; i += 1) {
    // a: i % 25 < 13, b: 13 to 19, c: 20 to 24, so the store order is a, b, c blocks; the sort below mixes them.
    const g = i < 13 ? groups[0] : i < 20 ? groups[1] : groups[2];
    out.push({ id: `i${i + 1}`, g, state: i % 2 === 0 ? "open" : "done", name: `Item ${i + 1} <b>tag</b>`, site: `S${(i % 5) + 1}`, rank: i % 4, hot: i === 24 });
  }
  return out;
}

const DEF: ListDefModel<Item> = {
  key: "things",
  plural: "things",
  facets: [
    {
      key: "state",
      label: "State",
      options: [
        { value: "open", word: "Open" },
        { value: "done", word: "Done" },
      ],
      all: "All states",
      of: (i) => i.state,
    },
  ],
  sorts: [
    { key: "priority", label: "Priority" },
    { key: "rank", label: "Rank", compare: (a, b) => a.rank - b.rank },
  ],
  text: (i) => i.name,
  site: (i) => i.site,
  keep: (i) => i.hot,
};
const GROUPED: ListDefModel<Item> = { ...DEF, group: (i) => i.g };

describe("homeListModel: the tier", () => {
  it.each([
    [2, 0],
    [3, 1],
    [10, 1],
    [11, 2],
    [25, 2],
  ])("%i items is tier %i", (n, tier) => {
    expect(homeListModel(DEF, store(n), {}, "all").tier).toBe(tier);
  });
  it("the tier is set by the items in scope, not the rows left", () => {
    const m = homeListModel(DEF, store(25), { q: "nothing-matches" }, "all");
    expect(m.tier).toBe(2);
    expect(m.n).toBe(0);
  });
});

describe("homeListModel: filters, search, sort, cap", () => {
  it("the cap is 10 and Show all lifts it", () => {
    expect(HOME_LIST_CAP).toBe(10);
    const m = homeListModel(DEF, store(25), {}, "all");
    expect([m.shown.length, m.hidden.length, m.n]).toEqual([10, 15, 25]);
    const all = homeListModel(DEF, store(25), { show: "all" }, "all");
    expect([all.shown.length, all.hidden.length]).toEqual([25, 0]);
  });
  it("a facet keeps the matching items; n is after filters and before the cap", () => {
    const m = homeListModel(DEF, store(25), { state: "open" }, "all");
    expect(m.n).toBe(13);
    expect(m.rows.every((r) => r.state === "open")).toBe(true);
    expect(m.ns).toBe(25);
  });
  it("a value that is not an option is ignored", () => {
    expect(homeListModel(DEF, store(25), { state: "bogus" }, "all").n).toBe(25);
  });
  it("search words are ANDed, lower-cased, with tags stripped", () => {
    expect(homeListModel(DEF, store(25), { q: "ITEM 7" }, "all").rows.map((r) => r.id)).toEqual(["i7", "i17"]);
    expect(homeListModel(DEF, store(25), { q: "item tag" }, "all").n).toBe(25);
    expect(homeListModel(DEF, store(25), { q: "b" }, "all").n).toBe(0);
  });
  it("the sort is stable, with ties in store order, and an unknown sort is the first", () => {
    const m = homeListModel(DEF, store(25), { sort: "rank", show: "all" }, "all");
    const ids = m.rows.map((r) => r.id);
    expect(ids.slice(0, 7)).toEqual(["i1", "i5", "i9", "i13", "i17", "i21", "i25"]);
    expect(homeListModel(DEF, store(25), { sort: "bogus", show: "all" }, "all").rows[1].id).toBe("i2");
  });
  it("keep-first: a kept item is shown inside the cap but displayed in sort order", () => {
    const m = homeListModel(DEF, store(25), {}, "all");
    expect(m.shown.map((r) => r.id)).toEqual(["i1", "i2", "i3", "i4", "i5", "i6", "i7", "i8", "i9", "i25"]);
    expect(m.hidden.map((r) => r.id)[0]).toBe("i10");
    expect(m.hidden.map((r) => r.id)).not.toContain("i25");
  });
  it("a cap override is honoured", () => {
    expect(homeListModel(DEF, store(25), {}, "all", 6).shown).toHaveLength(6);
  });
});

describe("homeListModel: scope", () => {
  it("a Site scope keeps that Site's items and ns counts them", () => {
    const m = homeListModel(DEF, store(25), {}, "site:S1");
    expect([m.ns, m.n]).toEqual([5, 5]);
    expect(m.tier).toBe(1);
  });
  it("a list with no site ignores the scope", () => {
    const m = homeListModel({ ...DEF, site: undefined }, store(25), {}, "site:S1");
    expect(m.ns).toBe(25);
  });
});

describe("homeListModel: groups", () => {
  it("only above 10 rows in more than one group; n_g sums to n, before the cap", () => {
    const m = homeListModel(GROUPED, store(25), {}, "all");
    expect(m.groups).toEqual([
      { g: "a", n_g: 13 },
      { g: "b", n_g: 7 },
      { g: "c", n_g: 5 },
    ]);
    expect(m.groups.reduce((s, g) => s + g.n_g, 0)).toBe(m.n);
    expect(m.shown.map((r) => r.g)).toEqual(["a", "a", "a", "a", "a", "a", "a", "a", "a", "c"]);
  });
  it("10 rows or fewer, or one group, draw none", () => {
    expect(homeListModel(GROUPED, store(10), {}, "all").groups).toEqual([]);
    expect(homeListModel(GROUPED, store(25), { state: "open", q: "item 1" }, "all").groups).toEqual([]);
    expect(homeListModel(GROUPED, store(13), {}, "all").groups).toEqual([]);
  });
  it("a group with no shown row keeps its head", () => {
    const m = homeListModel(GROUPED, store(25), { sort: "rank" }, "all");
    expect(m.groups.map((g) => g.g)).toEqual(["a", "b", "c"]);
  });
});

describe("homeListHref: the canonical address", () => {
  it("writes range, scope, facets, sort, q, show, each only when not its default", () => {
    const params = new URLSearchParams("known_at=2026-10-01T00:00:00Z&to=2026-10-31&from=2026-10-01&zzz=1");
    expect(homeListHref(DEF, "/things", params, {})).toBe("/things?from=2026-10-01&to=2026-10-31&known_at=2026-10-01T00%3A00%3A00Z");
    expect(homeListHref(DEF, "/things", params, { show: "all", q: "a b", sort: "rank", state: "open", scope: "site:S1" })).toBe(
      "/things?from=2026-10-01&to=2026-10-31&known_at=2026-10-01T00%3A00%3A00Z&scope=site%3AS1&state=open&sort=rank&q=a+b&show=all",
    );
  });
  it("defaults are omitted: scope all, the first sort, an empty q, an invalid facet", () => {
    const params = new URLSearchParams("scope=all&sort=priority&q=&state=bogus");
    expect(homeListHref(DEF, "/things", params, {})).toBe("/things");
  });
  it("a facet or search change drops show; a sort change keeps it", () => {
    const params = new URLSearchParams("show=all&sort=rank");
    expect(homeListHref(DEF, "/things", params, { state: "done" })).toBe("/things?state=done&sort=rank");
    expect(homeListHref(DEF, "/things", params, { q: "x" })).toBe("/things?sort=rank&q=x");
    expect(homeListHref(DEF, "/things", params, { sort: "priority" })).toBe("/things?show=all");
  });
  it("a change to the empty value clears the parameter", () => {
    expect(homeListHref(DEF, "/things", new URLSearchParams("state=open"), { state: "" })).toBe("/things");
  });
});
