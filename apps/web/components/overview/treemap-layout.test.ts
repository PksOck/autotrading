import { computeTreemap } from "./treemap-layout";

describe("computeTreemap", () => {
  it("sizes tiles by weight and skips positions that are not held", () => {
    const tiles = computeTreemap(
      [
        { id: "a", weight: 60 },
        { id: "b", weight: 40 },
        { id: "c", weight: 0 },
      ],
      100,
      100,
      0,
    );
    expect(tiles.map((t) => t.item.id)).toEqual(["a", "b"]);
    const area = (id: string) => {
      const t = tiles.find((x) => x.item.id === id)!;
      return t.width * t.height;
    };
    expect(area("a") / (area("a") + area("b"))).toBeCloseTo(0.6, 1);
  });

  it("returns nothing before the container has a size", () => {
    expect(computeTreemap([{ weight: 1 }], 0, 100)).toEqual([]);
  });
});
