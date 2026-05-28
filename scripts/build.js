#!/usr/bin/env node
// Bundles CodeMirror 6 packages into a single ESM file for local/offline use.
// Output: ../static/vendor/codemirror-bundle.js
// Run: node scripts/build.js  (from repo root)  OR  npm run build (from scripts/)

const path = require("path");
const esbuild = require("esbuild");

const outFile = path.resolve(__dirname, "../static/vendor/codemirror-bundle.js");

esbuild
  .build({
    entryPoints: [path.resolve(__dirname, "codemirror-entry.js")],
    bundle: true,
    format: "esm",
    minify: true,
    outfile: outFile,
    logLevel: "info",
  })
  .then(() => {
    console.log(`[vendor] CodeMirror bundle written → ${outFile}`);
  })
  .catch((err) => {
    console.error(err);
    process.exit(1);
  });
