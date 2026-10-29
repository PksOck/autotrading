import { normalizePreferences } from "./view-state";

it("recovers corrupt preferences and retains required identity and action columns", () => {
  const defs = [
    { id: "identity", required: true },
    { id: "pe" },
    { id: "actions", required: true },
  ];
  expect(normalizePreferences("broken", defs).columns).toEqual(["identity", "pe", "actions"]);
  const prefs = normalizePreferences(
    JSON.stringify({
      version: 1,
      columns: ["unknown"],
      column_order: ["pe", "unknown"],
      density: "compact",
      column_widths: { pe: -5 },
    }),
    defs,
  );
  expect(prefs.columns).toEqual(["identity", "actions"]);
  expect(prefs.column_order).toEqual(["pe", "identity", "actions"]);
  expect(prefs.column_widths.pe).toBe(64);
  expect(prefs.density).toBe("compact");
});

it("rejects future schemas and malformed collection fields without crashing", () => {
  const defs = [{ id: "symbol", required: true }, { id: "price" }];
  expect(normalizePreferences('{"version":99,"columns":[]}', defs).columns).toEqual([
    "symbol",
    "price",
  ]);
  expect(
    normalizePreferences('{"version":1,"columns":"bad","column_order":null}', defs).columns,
  ).toEqual(["symbol", "price"]);
});
