// Compile styles/site.css from every published .html file.
//   node _build/build-css.mjs
// Uses the Tailwind v4 compiler already installed in the app repo's
// frontend (../Retirology_App/frontend/node_modules) — no npm here.
import { createRequire } from "node:module";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const site = join(here, "..");
const appFrontend = join(site, "..", "Retirology_App", "frontend");
const require = createRequire(join(appFrontend, "package.json"));
const { compile, optimize } = require("@tailwindcss/node");
const { Scanner } = require("@tailwindcss/oxide");

const input = readFileSync(join(here, "site.src.css"), "utf8");
const compiler = await compile(input, { base: appFrontend, onDependency: () => {} });
const scanner = new Scanner({
  sources: [{ base: site, pattern: "**/*.html", negated: false }],
});
const candidates = scanner.scan().filter(Boolean);
const css = optimize(compiler.build(candidates), { minify: true });
writeFileSync(join(site, "styles", "site.css"), css.code ?? css);
console.log(`styles/site.css: ${(css.code ?? css).length} bytes from ${candidates.length} candidates`);
