#!/usr/bin/env node
// Post-build secret leak detector. Fails the build if any well-known
// provider-key prefix shows up in the build output. Allowlist
// public-by-design keys (Firebase Browser key, Maps JS API with referrer
// restriction, etc.) by FULL string match in the ALLOWED set below —
// never by prefix.
//
// Wire into package.json:
//   "build": "<framework build> && npm run verify:no-secrets",
//   "verify:no-secrets": "node scripts/check-no-secrets.mjs"
//
// Copy this file to scripts/check-no-secrets.mjs in your project, edit
// the ALLOWED set, and you're done.

import { readdirSync, readFileSync, statSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const PATTERNS = [
  { name: 'Google API key', re: /AIza[A-Za-z0-9_-]{30,}/g },
  { name: 'Anthropic API key', re: /sk-ant-[A-Za-z0-9_-]{40,}/g },
  { name: 'OpenAI API key', re: /sk-(proj-)?[A-Za-z0-9]{30,}/g },
  { name: 'Slack token', re: /xox[bpaors]-[0-9A-Za-z-]{10,}/g },
  { name: 'AWS access key', re: /AKIA[A-Z0-9]{16}/g },
  { name: 'GitHub token', re: /gh[psouar]_[A-Za-z0-9]{30,}/g },
  { name: 'GitLab PAT', re: /glpat-[A-Za-z0-9_-]{20,}/g },
  { name: 'Stripe live secret', re: /sk_live_[A-Za-z0-9]{24,}/g }
];

// Public-by-design keys. ALLOWLIST BY FULL STRING ONLY — never by prefix.
// Example: Firebase Browser keys are intentionally public (security comes
// from Firestore Rules + App Check). Maps JS API keys with referrer
// restrictions are also fine.
const ALLOWED = new Set([
  // 'AIzaSyDKDTpVDT2r7DdCm8Z3rjMt91ikVm3kdSQ', // Example: Firebase Browser key for project foo
]);

// Where to scan. Add to this list if your build emits elsewhere.
const DIST_DIRS = ['dist', 'build', 'out', '.next', 'public', '.svelte-kit'];
const FILE_EXTS = /\.(js|mjs|cjs|html|css|json|map|txt)$/;

function walk(dir, out = []) {
  if (!existsSync(dir)) return out;
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    let s;
    try { s = statSync(p); } catch { continue; }
    if (s.isDirectory()) walk(p, out);
    else if (FILE_EXTS.test(entry)) out.push(p);
  }
  return out;
}

const targets = DIST_DIRS.filter(d => existsSync(d));
if (targets.length === 0) {
  console.log('[check-no-secrets] No build output directory found — skipping.');
  process.exit(0);
}

const violations = [];
let scanned = 0;
for (const dir of targets) {
  for (const file of walk(dir)) {
    scanned++;
    const content = readFileSync(file, 'utf8');
    for (const { name, re } of PATTERNS) {
      const matches = content.match(re) || [];
      for (const m of matches) {
        if (ALLOWED.has(m)) continue;
        violations.push({ file, kind: name, fingerprint: m.slice(0, 12) + '…' });
      }
    }
  }
}

if (violations.length) {
  console.error(`\n[check-no-secrets] FAIL — secret-like strings found in build output:\n`);
  for (const v of violations) {
    console.error(`  ${v.kind.padEnd(20)}  ${v.fingerprint.padEnd(16)}  ${v.file}`);
  }
  console.error(`\nIf any of these are intentionally public (e.g., Firebase Browser key),`);
  console.error(`add the FULL string to the ALLOWED set in scripts/check-no-secrets.mjs.`);
  console.error(`Otherwise, the build is leaking secrets.\n`);
  process.exit(1);
}
console.log(`[check-no-secrets] OK — scanned ${scanned} files in ${targets.join(', ')}, no leaked secrets detected.`);
