#!/usr/bin/env node
// Compile MDX files with @mdx-js/mdx, remark-gfm and remark-math, and report parse errors.
//
// The packages are not a dependency of this repository; point --modules at a directory
// where they are installed:
//
//   npm install --prefix /tmp/mdxcheck @mdx-js/mdx remark-gfm remark-math
//   scripts/check_mdx.mjs --modules /tmp/mdxcheck en/**/*.mdx
//
// Prints one JSON object per line: {"file", "ok", "line", "column", "message"}.
// With --stdin, reads newline-separated file paths from standard input.

import { readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const args = process.argv.slice(2);
let modules = process.env.MDX_MODULES;
let fromStdin = false;
const files = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--modules") modules = args[++i];
  else if (args[i] === "--stdin") fromStdin = true;
  else files.push(args[i]);
}
if (!modules) {
  console.error("check_mdx.mjs: pass --modules DIR (or set MDX_MODULES)");
  process.exit(2);
}
if (fromStdin) {
  files.push(...readFileSync(0, "utf8").split("\n").filter(Boolean));
}

const load = async (name) => {
  // The packages are ESM-only; import the entry point from their package directory.
  const pkgDir = join(resolve(modules), "node_modules", name);
  const pkg = JSON.parse(readFileSync(join(pkgDir, "package.json"), "utf8"));
  const exp = pkg.exports;
  const entry = typeof exp === "string" ? exp : exp?.["."]?.default ?? exp?.default ?? pkg.main ?? "index.js";
  return import(pathToFileURL(join(pkgDir, entry)).href);
};
const { compile } = await load("@mdx-js/mdx");
const remarkGfm = (await load("remark-gfm")).default;
const remarkMath = (await load("remark-math")).default;

// Pages compile even with expressions like {boost}, but fail when rendered: the
// identifier is undefined. Converted pages should only contain {/* comments */}, so
// report every other expression, and every component Mintlify does not provide.
const MINTLIFY_COMPONENTS = new Set(
  ("Accordion AccordionGroup Callout Card CardGroup Check CodeGroup Columns Danger Expandable Frame Icon Info " +
    "Note ParamField RequestExample ResponseExample ResponseField Snippet Step Steps Tab Tabs Tip Tooltip Update " +
    "Warning Badge Tile Tree Panel Color View").split(" "),
);
// Literals are safe: a template string without ${...}, a quoted string, a number or boolean.
const isLiteral = (v) =>
  /^\s*(`(?:[^`\\$]|\\.|\$(?!\{))*`|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|-?\d+(\.\d+)?|true|false)\s*$/.test(v);
let problems = [];
const collect = () => (tree) => {
  const walk = (node) => {
    if (node.type === "mdxFlowExpression" || node.type === "mdxTextExpression") {
      if (!/^\s*\/\*[\s\S]*\*\/\s*$/.test(node.value) && !isLiteral(node.value)) problems.push([node, `expression {${node.value.slice(0, 60)}}`]);
    }
    if ((node.type === "mdxJsxFlowElement" || node.type === "mdxJsxTextElement") && node.name) {
      if (/^[A-Z]/.test(node.name) && !MINTLIFY_COMPONENTS.has(node.name)) problems.push([node, `unknown component <${node.name}>`]);
      for (const a of node.attributes ?? []) {
        if (a.type === "mdxJsxExpressionAttribute" || (a.value && typeof a.value === "object" && !isLiteral(a.value.value)))
          problems.push([node, `expression attribute on <${node.name}>`]);
      }
    }
    for (const c of node.children ?? []) walk(c);
  };
  walk(tree);
};

let failed = 0;
for (const file of files) {
  problems = [];
  let text = readFileSync(file, "utf8").replace(/^﻿/, "");
  // Replace the frontmatter with blank lines so reported line numbers match the file.
  const fm = text.match(/^---\n[\s\S]*?\n---\n/);
  if (fm) text = "\n".repeat(fm[0].split("\n").length - 1) + text.slice(fm[0].length);
  try {
    await compile(text, { remarkPlugins: [remarkGfm, remarkMath, collect] });
    if (problems.length) {
      failed++;
      for (const [node, message] of problems) {
        const p = node.position?.start ?? {};
        console.log(JSON.stringify({ file, ok: false, line: p.line, column: p.column, message }));
      }
    } else {
      console.log(JSON.stringify({ file, ok: true }));
    }
  } catch (e) {
    failed++;
    const place = e.place?.start ?? e.place ?? {};
    console.log(JSON.stringify({ file, ok: false, line: place.line ?? e.line, column: place.column ?? e.column, message: e.reason ?? e.message }));
  }
}
process.exit(failed ? 1 : 0);
