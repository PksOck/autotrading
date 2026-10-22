import { decodeEntity, encodeEntity } from "./entities";

describe("entity refs", () => {
  it("round-trips", () => {
    const ref = { kind: "instrument" as const, id: "MSFT" };
    expect(decodeEntity(encodeEntity(ref))).toEqual(ref);
  });

  it("rejects unknown kinds and empty ids", () => {
    expect(decodeEntity("order:1")).toBeNull();
    expect(decodeEntity("instrument:")).toBeNull();
    expect(decodeEntity(null)).toBeNull();
  });
});
