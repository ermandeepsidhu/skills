# skills

A public library of high-quality, reusable **agent skills** for engineering teams.

Each skill is a self-contained directory that teaches an AI coding agent how to perform one
task well — with an ordered workflow, reference docs, copyable assets, validated examples,
and built-in verification. Skills use the open [Agent Skills](https://agentskills.io)
`SKILL.md` format, so the **same skill works across Claude Code, Cursor, GitHub Copilot, and
Google Antigravity** (see [Using these skills](#using-these-skills)).

## Skill catalog

Skills are grouped by **domain / category** under [`skills/`](skills/).

### Engineering

| Category | Skill | What it does | Examples |
|---|---|---|---|
| Architecture | [`drawio-architecture`](skills/engineering/architecture/drawio-architecture/) | Produce editable, C4-inspired solution-architecture diagrams as native `.drawio` (mxGraph) XML, with deterministic grid layout and built-in verification. | [showcase](skills/engineering/architecture/drawio-architecture/EXAMPLES.md) |
| Security | [`responding-to-secret-leaks`](skills/engineering/security/responding-to-secret-leaks/) | Incident response for leaked API keys: prove the leak in the live bundle, triage by blast radius, revoke/rotate, move calls server-side, and harden with budgets + a post-build leak detector. | — |

<p align="center">
  <img src="skills/engineering/architecture/drawio-architecture/examples/container.png" alt="Example C4 container diagram produced by drawio-architecture" width="280">
</p>

_More diagramming skills (workflow, sequence, UML) are planned, following the
`drawio-architecture` template._

## Using these skills

As of 2026, Claude Code, Cursor, GitHub Copilot, and Google Antigravity all discover skills
in the same `SKILL.md` directory format. The canonical copy of every skill lives once under
[`skills/`](skills/); each tool finds them through a flat symlink directory that is already
committed to this repo:

| Tool | Looks in | Notes |
|---|---|---|
| Claude Code | `.claude/skills/` | Native. |
| Cursor | `.cursor/skills/` (also reads `.claude/skills/`, `.agents/skills/`) | Cursor 2.4+. |
| GitHub Copilot | `.github/skills/` (also reads `.claude/skills/`, `.agents/skills/`) | VS Code ≥ 1.108. |
| Google Antigravity | `.agent/skills/` | Path provided as `.agent` and `.agents`. |

**To use a skill, clone this repo and point your tool at it** — either open the repo
directly, or copy/symlink a skill directory into your own project's tool directory (e.g.
`.claude/skills/`). The skills are vendor-neutral and have no install step.

> **Windows:** the per-tool links are git symlinks. Windows checkouts need
> `git config core.symlinks true` (plus Developer Mode/admin), or run
> `python3 scripts/skills.py sync` after cloning to materialize them. macOS/Linux work out
> of the box.

## Repository layout

```text
skills/<domain>/<category>/<skill>/   ← canonical skills (source of truth)
  SKILL.md           workflow + frontmatter (the skill's contract)
  references/        deep-dive docs + executable tooling (loaded on demand)
  assets/            verbatim material the agent copies into output
  examples/          worked, validated outputs (+ rendered previews)
  EXAMPLES.md        prompt → output showcase

.claude/skills/  .cursor/skills/  .github/skills/  .agent/skills/  .agents/skills/
                   ← flat symlink farms into skills/, one per tool (generated)

scripts/skills.py            sync the symlink farms + check this README is current
scripts/render-examples.py   build draw.io-viewer HTML to render example previews
docs/superpowers/            design specs + implementation plans for each skill
AGENTS.md / CLAUDE.md        house rules for agents working IN this repo
```

## Contributing a skill

1. Create the skill under `skills/<domain>/<category>/<name>/` with a `SKILL.md` whose
   frontmatter `name` matches the directory name. Follow the
   [`drawio-architecture`](skills/engineering/architecture/drawio-architecture/) template:
   an ordered workflow, `references/`, `assets/`, and **validated** `examples/`.
2. Add a row to the [Skill catalog](#skill-catalog) above (every skill must appear here).
3. Regenerate the per-tool symlinks and verify everything is in sync:

   ```bash
   python3 scripts/skills.py sync     # create/refresh the per-tool symlinks
   python3 scripts/skills.py check    # CI gate: symlinks + README references present
   ```

`scripts/skills.py check` fails if a skill is missing its symlinks or is not mentioned in
this README — that is what keeps this README up to date.
