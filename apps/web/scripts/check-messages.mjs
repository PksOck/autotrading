// Fails when sl.json and en.json do not have the same keys (VOICE.md §6, BL-008).
import { readFileSync } from "node:fs";

const load = (name) => JSON.parse(readFileSync(new URL(`../messages/${name}.json`, import.meta.url)));
const keys = (obj, prefix = "") =>
  Object.entries(obj).flatMap(([k, v]) =>
    v && typeof v === "object" ? keys(v, `${prefix}${k}.`) : [`${prefix}${k}`],
  );

const sl = new Set(keys(load("sl")));
const en = new Set(keys(load("en")));
const missingEn = [...sl].filter((k) => !en.has(k));
const missingSl = [...en].filter((k) => !sl.has(k));

if (missingEn.length || missingSl.length) {
  if (missingEn.length) console.error("Manjka v en.json:", missingEn.join(", "));
  if (missingSl.length) console.error("Manjka v sl.json:", missingSl.join(", "));
  process.exit(1);
}
console.log(`i18n OK: ${sl.size} ključev`);
