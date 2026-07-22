import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const fixturePath = fileURLToPath(
  new URL("../src/data/fixtures/amzn.json", import.meta.url),
);
const startDate = "2021-07-22T20:00:00Z";
const endDate = "2026-07-22T20:00:00Z";
const seed = 0x5a17c9e3;

function createRandom(seedValue) {
  let state = seedValue;
  return () => {
    state = (state * 1_664_525 + 1_013_904_223) >>> 0;
    return state / 2 ** 32;
  };
}

function businessDayPoints() {
  const random = createRandom(seed);
  const dates = [];
  const current = new Date(startDate);
  const finalDate = new Date(endDate);

  while (current <= finalDate) {
    const day = current.getUTCDay();
    if (day !== 0 && day !== 6) dates.push(new Date(current));
    current.setUTCDate(current.getUTCDate() + 1);
  }

  let close = 135;
  const rawPoints = dates.map((date, index) => {
    const dailyReturn = 0.00035 + (random() - 0.5) * 0.03;
    close = Math.max(25, close * (1 + dailyReturn));

    return {
      timestamp: date.toISOString().replace(".000", ""),
      close,
      volume:
        index % 47 === 0
          ? null
          : Math.round(18_000_000 + random() * 30_000_000),
    };
  });
  const scale = 217.35 / rawPoints[rawPoints.length - 1].close;

  return rawPoints.map((point, index) => ({
    ...point,
    close:
      index === rawPoints.length - 1
        ? 217.35
        : Number((point.close * scale).toFixed(2)),
  }));
}

const fixture = JSON.parse(readFileSync(fixturePath, "utf8"));
const output = `${JSON.stringify(
  { ...fixture, priceHistory: businessDayPoints() },
  null,
  2,
)}\n`;

if (process.argv.includes("--check")) {
  if (readFileSync(fixturePath, "utf8") !== output) {
    console.error("AMZN price history fixture is not generated from the fixed seed.");
    process.exitCode = 1;
  } else {
    console.log("AMZN price history fixture is deterministic.");
  }
} else {
  writeFileSync(fixturePath, output);
  console.log("Wrote deterministic AMZN price history fixture.");
}
