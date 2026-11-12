// After a static export, copy each prefetch file from out/x/__next.a/b/__PAGE__.txt to
// out/x/__next.a.b.__PAGE__.txt, which is the name the browser asks for. Without this, a static host
// answers those prefetches with 404s; links still work, but the console fills with errors.
import { copyFileSync, readdirSync } from "node:fs";
import { join, relative, sep } from "node:path";

const out = process.argv[2] ?? "out";
let copied = 0;

function walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name.startsWith("__next.")) flatten(dir, path);
      else if (entry.name !== "_next") walk(path);
    }
  }
}

function flatten(parent, segmentDir) {
  for (const entry of readdirSync(segmentDir, { withFileTypes: true, recursive: true })) {
    if (!entry.isFile()) continue;
    const file = join(entry.parentPath, entry.name);
    copyFileSync(file, join(parent, relative(parent, file).split(sep).join(".")));
    copied += 1;
  }
}

walk(out);
console.log(`copied ${copied} prefetch files`);
