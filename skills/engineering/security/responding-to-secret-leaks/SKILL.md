---
name: responding-to-secret-leaks
description: Use when an API key has been compromised, billing shows unexpected spikes (dollars, requests, tokens), secrets appear in client-side JavaScript bundles (NEXT_PUBLIC_, VITE_, NG_APP_, REACT_APP_, PUBLIC_), or you suspect provider credentials leaked into a deployed web app. Covers detection, triage, revocation, server-side migration, and defense-in-depth.
---

# Responding to Secret Leaks

## Overview

Web apps routinely leak provider API keys (Gemini, Anthropic, OpenAI, Stripe, LinkedIn OAuth secrets) by bundling them into the client JavaScript at build time. The framework even gives them a friendly-sounding prefix (`NEXT_PUBLIC_*`, `VITE_*`, `NG_APP_*`, etc.) that hides what's actually happening: those values get inlined as string literals and shipped to every browser. Attackers grep the bundle and walk out with the key.

**Core principle: prove the leak, then triage by blast radius, then fix architecture — not the other way around.** Don't propose a revocation plan before you've shown the key really is in the public bundle. Don't write code before you know which keys are bleeding right now.

## When to use

- User reports unexpected API spend or rate-limit errors that don't match their usage.
- User asks "did my key leak?" or "is my API key in the bundle?"
- User mentions a billing/spend cap was hit overnight.
- Reviewing a web app and you see `dangerouslyAllowBrowser`, `apiKey:` in client code, or env vars prefixed `NEXT_PUBLIC_*` / `VITE_*` / `NG_APP_*` holding what looks like a real key.
- Provider notification: "Your key was used from an unfamiliar IP."

## When NOT to use

- Server-side-only leaks (e.g., a key checked into git but never bundled to a client). Use a general incident-response playbook instead — revocation steps apply but the architecture-fix phase is different.
- Phishing or stolen credentials unrelated to a bundler. Different threat model.

## The five phases

```
1. Detect      — Prove the keys are in the public bundle. No claims without `curl + grep`.
2. Triage      — Identify which keys, where they bill, what caps exist, what's still bleeding.
3. Stop        — Revoke / rotate. Destructive — confirm before each step.
4. Fix         — Move provider calls server-side behind auth + rate limits.
5. Harden      — Budgets, post-build leak detector, audit logs, key restrictions.
```

Never skip Phase 1. A user "thinking" the key leaked is not the same as the key being in `dist/`. Many false alarms turn out to be Firebase Browser keys (public by design) or look-alike strings.

---

## Phase 1 — Detection

### What to scan

Run all of these. They're cheap.

```bash
# 1. Local build output (if present)
grep -rohE "AIza[A-Za-z0-9_-]{30,}|sk-ant-[A-Za-z0-9_-]{40,}|sk-(proj-)?[A-Za-z0-9]{30,}|xox[bp]-[0-9-]+-[A-Za-z0-9]+|AKIA[A-Z0-9]{16}|gh[psouar]_[A-Za-z0-9]{30,}|glpat-[A-Za-z0-9_-]{20,}" dist/ build/ out/ .next/ 2>/dev/null | sort -u

# 2. The local .env vs the bundle — does anything in .env appear in dist/?
for v in $(grep -oE '^[A-Z_]+=.+' .env 2>/dev/null | cut -d= -f2 | grep -v '^$' | head -20); do
  prefix=$(echo "$v" | head -c 12)
  [ ${#prefix} -lt 12 ] && continue
  if grep -rq "$prefix" dist/ build/ 2>/dev/null; then
    echo "LEAK: prefix $prefix... found in build output"
  fi
done

# 3. THE ONE THAT MATTERS — fetch the LIVE production bundle and grep it
SITE="https://your-site.example.com"
mkdir -p /tmp/live-bundle && cd /tmp/live-bundle
curl -sL "$SITE/" | grep -oE 'main-[A-Za-z0-9]+\.js|chunk-[A-Za-z0-9]+\.js|[A-Za-z0-9._-]+\.bundle\.js' | sort -u | \
  xargs -I{} curl -sL "$SITE/{}" -o "{}"
grep -roh "AIza[A-Za-z0-9_-]\{20,\}\|sk-ant-[A-Za-z0-9_-]\{20,\}\|sk-[A-Za-z0-9]\{30,\}" . | sort -u
```

The live-bundle scan is the source of truth. Local `dist/` may be stale or may not have had build-time secrets injected.

### Common provider key prefixes

| Prefix | Provider |
|---|---|
| `AIza...` (length 39) | Google API keys (Gemini, Maps, Firebase, etc.) |
| `sk-ant-api03-...` | Anthropic |
| `sk-` / `sk-proj-` | OpenAI |
| `xoxb-` / `xoxp-` / `xoxa-` | Slack |
| `AKIA...` (length 20) | AWS Access Keys |
| `ghp_` / `gho_` / `ghu_` / `ghs_` | GitHub PATs |
| `glpat-` | GitLab PATs |
| `pk_live_` / `sk_live_` | Stripe |

### Public-by-design keys

Some `AIza...` keys are SUPPOSED to be in client code. Don't raise the alarm on these:

- **Firebase Browser key** — restricted to Firebase APIs. Security comes from Firestore Rules + App Check, not key secrecy. Verify by inspecting the key's `restrictions.apiTargets` in GCP API Keys console — if it's only `firebase*.googleapis.com`, it's safe.
- Maps JS API keys with HTTP-referrer restrictions to your domain — usually intentional.

To confirm what each leaked key does:
```bash
gcloud services api-keys list --project=PROJECT_ID --format="table(uid,displayName,restrictions.apiTargets[].service)"
# Then resolve the prefix to a UID:
for proj in PROJECT_A PROJECT_B; do
  gcloud services api-keys list --project=$proj --format="value(uid)" 2>/dev/null | while read uid; do
    prefix=$(gcloud services api-keys get-key-string "$uid" --project=$proj --format="value(keyString)" 2>/dev/null | cut -c1-15)
    echo "  $prefix  $uid  $proj"
  done
done
```

### Output of Phase 1

A table the user can act on:

| Key fingerprint | Provider | Where billed | Public by design? | Status |
|---|---|---|---|---|
| `AIzaSyXY...` | Gemini | project foo | NO | LEAKED |
| `sk-ant-...` | Anthropic | console.anthropic.com | NO | LEAKED |
| `AIzaSyDK...` | Firebase Browser | project foo | YES | keep, allowlist |

---

## Phase 2 — Triage

Find out *which key is still bleeding right now.* The order matters: revoke the one with no brake first.

For each leaked key, answer:
1. **What's the cap?** Anthropic, OpenAI — usually no per-project cap, so unbounded.
2. **Has the cap been hit?** If yes, the bleeding has paused.
3. **What's the rate ceiling?** Tier 3 Gemini = thousands of RPM. Anthropic Tier 1 = much less. A higher ceiling = a faster bleed.

Provider spend caps are usually labeled `Experimental` or have minute-level lag. They're soft brakes, not circuit breakers — assume an attacker can punch through by an order of magnitude before the cap evaluator catches up.

Priority order (highest urgency first):
1. Uncapped providers (Anthropic, OpenAI)
2. Capped providers where cap hasn't been hit yet
3. Capped providers where cap already hit (durability fix, no acute bleed)

---

## Phase 3 — Stop the bleeding

**Destructive. Confirm each action with the user before executing.** Revoking a key in production typically breaks the live app for legitimate users. Sometimes that's already broken (cap hit) and revocation is free; sometimes it's not.

Pattern:
```
"I'm about to <revoke X>. This is irreversible and will break <Y>. Proceed?"
```

### Per provider

| Provider | How to revoke | Can Claude do via CLI? |
|---|---|---|
| Google API Key (managed) | `gcloud services api-keys delete <UID> --project=...` | Yes |
| Gemini key from AI Studio | https://aistudio.google.com/apikey?project=... → delete | Yes via gcloud if it's a managed API key |
| Anthropic | console.anthropic.com/settings/keys → Disable | No — user must click |
| OpenAI | platform.openai.com/api-keys → Delete | No — user must click |
| LinkedIn OAuth | linkedin.com/developers → app → Auth → Regenerate secret | No — user must click |
| AWS Access Key | `aws iam delete-access-key --access-key-id AKIA...` | Yes |
| GitHub PAT | https://github.com/settings/tokens → Revoke | Yes via `gh api -X DELETE /user/keys/<id>` if creds work |

### Spend-cap drop (defense-in-depth, do same session)

While revoking, drop any available spend cap to its floor. Even an experimental cap helps if it catches the next leak before you notice.

---

## Phase 4 — Architecture fix

**The leak will reappear on next deploy unless you change the architecture.**

The root cause is always one of:

1. **Bundler env-var inlining.** Frameworks like Next.js, Vite, Angular, CRA, Astro, Nuxt, Remix, SvelteKit have a "public" prefix that's documented as build-time but is *actually* "shipped to the client." Anything set there is exposed.
2. **Build-time string injection.** Dockerfiles / Cloud Build that `printf` or `sed` a secret into a `.ts` / `.js` source file before bundling. Same outcome.
3. **Direct SDK use in browser code.** `new OpenAI({...})`, `new Anthropic({apiKey, dangerouslyAllowBrowser: true})`, `new GoogleGenAI({apiKey})` all assume server-side. The `dangerouslyAllowBrowser` flag is a SIREN.

### The fix pattern (universal)

```
Browser  ──HTTPS + Bearer <user-auth-token>──▶  Your server  ──(holds the keys)──▶  Provider
```

Three pieces:
1. **Server endpoint** that wraps each provider call. Accepts the prompt/payload, calls the SDK with the secret-bearing client, returns the response.
2. **Auth middleware** on every server endpoint. Verify the user's session (Firebase ID token, Clerk JWT, NextAuth session, etc.). 401 on miss.
3. **Per-user rate limit** on every endpoint. Even with auth, a single compromised account can spend hundreds of dollars in minutes. Cap requests/hour/user.

### Framework-specific cleanup

For each framework, the cleanup has two parts: stop bundling the secret, and route the call through your server.

| Framework | Bad env var | Bundler behavior | Server file pattern |
|---|---|---|---|
| Next.js | `NEXT_PUBLIC_*` | Inlined into client + server | Move to `process.env.MY_KEY` (server-only), call from `/api/...` route handler |
| Vite | `VITE_*` | Inlined into client | Move to non-prefixed env var, call from any Node server backend |
| Angular (vite-plugin) | `NG_APP_*` | Inlined into client | Move to backend service, call from Express/Cloud Run endpoint |
| CRA | `REACT_APP_*` | Inlined into client | Same as Vite |
| Astro | `PUBLIC_*` | Inlined into client | Move to non-`PUBLIC_` var, use in Astro server endpoints |
| Nuxt | `NUXT_PUBLIC_*` (in `runtimeConfig.public`) | Sent to client | Move to `runtimeConfig` (non-public), use in `/server/api/` routes |
| SvelteKit | `PUBLIC_*` | Inlined into client | Move to `$env/static/private`, use in `+page.server.ts` / `+server.ts` |
| Remix | (no prefix — `loader` returns) | Returned to client | Use server-only `process.env`, never include in `loader` JSON |

### Build-pipeline cleanup

```bash
# Look for build-time secret injection patterns:
grep -rnE "ARG (GEMINI|ANTHROPIC|OPENAI|API)|printf .*API_KEY|envsubst|sed.*API_KEY" Dockerfile* cloudbuild.yaml .github/ .gitlab-ci.yml 2>/dev/null
```

If you find a `printf` or `sed` writing a key into a source file: delete it. Move the secret to a runtime env var on the server (Cloud Run `--set-secrets`, Kubernetes Secret, Fly.io secret, Vercel server env, etc.).

### Verify after refactor

```bash
# Local build
npm run build
grep -rohE "AIza[A-Za-z0-9_-]{30,}|sk-ant-[A-Za-z0-9_-]{40,}" dist/ build/ out/ | sort -u
# Should return only allowlisted public keys (Firebase Browser, etc.)
```

Then re-fetch the live URL after deploy and run the same scan.

---

## Phase 5 — Defense in depth

Do all of these. Each is cheap individually; together they catch the next leak before it costs anything.

### 5.1 Post-build leak detector (high ROI)

Add `scripts/check-no-secrets.mjs` and wire it into `npm run build`. A copy-paste-ready version of the script lives next to this skill at `check-no-secrets.mjs`. It scans `dist/` (and common alternatives) for known provider-key prefixes, allowlists public-by-design keys, and fails the build if anything else matches.

```json
{
  "scripts": {
    "build": "next build && npm run verify:no-secrets",
    "verify:no-secrets": "node scripts/check-no-secrets.mjs"
  }
}
```

Also run it in CI so PRs that re-introduce the pattern fail before merge.

### 5.2 Real billing circuit breaker

Provider spend caps are usually lagged and experimental. Set a real one at the cloud-billing layer:

```bash
# GCP example — $25/month project budget with alerts at 50%, 90%, 100%, 120%
gcloud services enable billingbudgets.googleapis.com --project=PROJECT_ID

BILLING_ID=$(gcloud billing projects describe PROJECT_ID --format="value(billingAccountName)" | sed 's|billingAccounts/||')
PROJECT_NUMBER=$(gcloud projects describe PROJECT_ID --format="value(projectNumber)")

cat > /tmp/budget.json <<EOF
{
  "displayName": "PROJECT_ID-circuit-breaker",
  "amount": {"specifiedAmount": {"currencyCode": "USD", "units": "25"}},
  "budgetFilter": {
    "projects": ["projects/${PROJECT_NUMBER}"],
    "calendarPeriod": "MONTH",
    "creditTypesTreatment": "INCLUDE_ALL_CREDITS"
  },
  "thresholdRules": [
    {"thresholdPercent": 0.5, "spendBasis": "CURRENT_SPEND"},
    {"thresholdPercent": 0.9, "spendBasis": "CURRENT_SPEND"},
    {"thresholdPercent": 1.0, "spendBasis": "CURRENT_SPEND"},
    {"thresholdPercent": 1.2, "spendBasis": "CURRENT_SPEND"}
  ]
}
EOF

curl -sS -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "x-goog-user-project: PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d @/tmp/budget.json \
  "https://billingbudgets.googleapis.com/v1/billingAccounts/${BILLING_ID}/budgets"
```

For a true *kill switch* (not just alerts), wire the 100% threshold to a Pub/Sub topic and a Cloud Function that calls `gcloud billing projects unlink`. Document this; don't auto-set without explicit user approval — it can take a project offline.

Equivalents:
- AWS Budgets + EventBridge + Lambda that detaches IAM roles
- Stripe usage-based alerts + automated downgrade
- Render / Fly.io / Vercel: provider-specific spend alerts

### 5.3 Key restrictions

For any new key, restrict it at the provider:
- **Google API keys**: HTTP referrer restriction (`*.your-domain.com/*`) + API restriction (single-service allowlist). Referrers can be spoofed but every layer adds friction.
- **OpenAI**: project-scoped keys with usage limits.
- **AWS**: IAM policies with explicit resource ARNs and `aws:SourceIp` conditions.

**Even better: drop API keys entirely** where possible. Use workload identity / OIDC / Application Default Credentials. The Cloud Run service account can call Gemini directly without an API key — Anthropic SDK supports `GOOGLE_APPLICATION_CREDENTIALS` for Vertex.

### 5.4 Audit logs

If your cloud supports it, enable data-access audit logs on sensitive APIs *before* the next incident. They cost almost nothing and provide caller-IP-level forensics the next time something looks off.

```bash
# GCP: enable Data Access logs for all services on a project
gcloud projects get-iam-policy PROJECT_ID --format=json > /tmp/policy.json
python3 -c "
import json
p = json.load(open('/tmp/policy.json'))
p['auditConfigs'] = [{'service': 'allServices', 'auditLogConfigs': [
  {'logType': 'ADMIN_READ'}, {'logType': 'DATA_READ'}, {'logType': 'DATA_WRITE'}
]}]
json.dump(p, open('/tmp/new-policy.json', 'w'))
"
gcloud projects set-iam-policy PROJECT_ID /tmp/new-policy.json
```

Caveat: some services (notably AI Studio Generative Language API) don't emit data-access logs. Document the gap.

### 5.5 Git history scan

Even if the leaked key was build-time only, *verify* it was never committed:

```bash
# Quick targeted scan
git log --all -p 2>/dev/null | grep -oE "AIza[A-Za-z0-9_-]{30,}|sk-ant-[A-Za-z0-9_-]{40,}" | sort -u

# Full scan (slower, more thorough) — needs Docker or local install
docker run --rm -v "$(pwd)":/pwd trufflesecurity/trufflehog:latest git file:///pwd --no-update --only-verified
```

If anything else turns up: rotate THAT key too. A key in git history is forever — anyone who cloned the repo at any commit has it.

### 5.6 CORS

After moving keys server-side, tighten the server CORS policy on the new authenticated routes:
- Static assets: `Access-Control-Allow-Origin: *` is usually fine.
- Authenticated API routes: restrict to your origin(s) only. Otherwise an attacker can call your proxy endpoints from any site after exfiltrating a Firebase ID token via XSS.

---

## Generalized audit checklist (apply to any web project)

Copy this into the project's README or CONTRIBUTING:

- [ ] No third-party API keys in client-side env files. If you need to call OpenAI / Anthropic / Gemini / Stripe / etc., do it from a server you control.
- [ ] No env var prefix that suggests "public" should hold a secret. `NEXT_PUBLIC_*`, `VITE_*`, `NG_APP_*`, `REACT_APP_*` are for analytics IDs and feature flags. Never for keys that grant spend.
- [ ] Post-build leak detector wired into `npm run build` AND CI.
- [ ] Real billing circuit breaker on every project that touches a paid API. Provider caps are not enough.
- [ ] API keys restricted to specific HTTP referrers / IPs / API services at the provider.
- [ ] Prefer service-identity over API keys (ADC on GCP, IAM roles on AWS, OIDC federation).
- [ ] Data-access audit logs enabled on sensitive APIs.
- [ ] `trufflehog git file://. --only-verified` clean on every repo before going public.
- [ ] Treat `dangerouslyAllowBrowser: true` (and equivalent flags) as a bug to fix, not a workaround to keep.
- [ ] Per-user rate limits on all AI endpoints. Even auth alone is not enough.
- [ ] Test the leak detector by intentionally committing `AIzaSyTESTBADKEYDOTNOTUSE0123456789ABC` once, watch CI fail, revert.

---

## Common mistakes

| Mistake | Fix |
|---|---|
| Proposing a revocation plan before `curl`-grepping the live bundle | Always Phase 1 first. False alarms are common (Firebase Browser key). |
| Revoking a key while user has uncommitted in-flight OAuth flows | Warn explicitly; user may need to coordinate with active users. |
| Moving keys to "Secret Manager" but leaving them as plaintext Cloud Run env vars | `--set-secrets` vs `--set-env-vars` — they're different. Verify with `gcloud run services describe`. |
| Allowlisting Firebase Browser key by regex (`AIzaSy*`) in the leak detector | Allowlist by FULL string match, never prefix. Otherwise a future leaked Google key with the same prefix slips through. |
| Skipping audit log enable because "we already fixed it" | Next incident, you'll wish you had them. Enable now. |
| Treating the experimental AI Studio spend cap as a circuit breaker | It's labeled experimental and has 10-minute lag. Use Cloud Billing budgets for real limits. |
| Forgetting `dist/` is cached by CDN + Wayback after rotation | A rotated key is no longer accepted but the bundle history is forever. Rotate, don't try to "scrub." |
| Rotating a Secret Manager / AWS Secrets Manager / k8s Secret version and assuming running services pick it up | They don't. See "Operational gotcha" section below. Force a revision restart on every consumer after rotation. |

## Operational gotcha: rotating a secret does NOT propagate to running services

Secrets are typically resolved at container/process startup. Adding a new version doesn't push it to anything — consumers keep serving the cached old value until they restart. This bites people during incidents because rotating a leaked key feels like it should be immediate, and the live app keeps using the old key for hours afterwards.

**Always force a restart on every consumer after rotation.**

| Platform | Symptom | Fix |
|---|---|---|
| Cloud Run with `--set-secrets` | Stale value in env until container restart | `gcloud run services update <name> --region=<r> --update-secrets=<VAR>=<secret>:latest` |
| AWS Lambda + Secrets Manager env vars | Stale value until next deploy | Publish new function version |
| ECS/Fargate with `secrets:` in task def | Stale value until next task replacement | `aws ecs update-service --force-new-deployment` |
| Kubernetes Secret mounted as env var | Stale until pod restart | `kubectl rollout restart deployment/<name>` |
| Kubernetes Secret mounted as file | Auto-refreshes after kubelet sync (~1-2 min) | Usually no action needed |
| GitHub Actions secret | Stale until next workflow run | No action — new runs read fresh |
| Fly.io `fly secrets set` | Triggers automatic redeploy | No action — Fly handles it |
| Vercel env vars | Need redeploy | `vercel --prod` after `vercel env add` |

Symptom to recognize: you rotated a key, the call still returns the old key's error (e.g., `API_KEY_INVALID` when you just generated a fresh valid key). The fix isn't to re-rotate — it's to restart the consumer.

## Red flags that mean STOP

If you find yourself doing any of these, restart Phase 1:
- Telling the user keys are leaked without showing them the `grep` output.
- Editing build/Dockerfile/cloudbuild before the user has revoked the leaked keys.
- "Quick fix" that keeps the keys client-side but adds restrictions. Restrictions are layered defense; they're not the fix.
- Modifying `dist/` directly to "remove" the key. That doesn't change what's already been served and cached.
- Skipping the live-bundle verification because the local dist looked clean.

## Related artifacts

- `check-no-secrets.mjs` (next to this SKILL.md) — copy-paste-ready post-build leak detector. Wire into `package.json` build script.

## To install this skill globally

This skill lives in the originating project at `.claude/skills/responding-to-secret-leaks/`. To make it available across all projects on your machine, symlink (or copy) it into `~/.claude/skills/`:

```bash
ln -s "$(pwd)/.claude/skills/responding-to-secret-leaks" ~/.claude/skills/responding-to-secret-leaks
# Or copy if you'd rather have an independent snapshot:
# cp -R .claude/skills/responding-to-secret-leaks ~/.claude/skills/
```
