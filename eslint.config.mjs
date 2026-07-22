import { FlatCompat } from "@eslint/eslintrc";
import { fileURLToPath } from "node:url";

const baseDirectory = fileURLToPath(new URL(".", import.meta.url));
const compat = new FlatCompat({ baseDirectory });

const eslintConfig = [
  ...compat.extends("next/core-web-vitals"),
  {
    ignores: [".next/**", "node_modules/**", "playwright-report/**", "test-results/**"],
  },
];

export default eslintConfig;
