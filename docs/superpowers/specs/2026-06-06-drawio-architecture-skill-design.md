# drawio-architecture Skill — Design

**Date:** 2026-06-06
**Status:** Approved (brainstorming)
**Scope:** First skill in a public, vendor-neutral library of software-engineering diagramming skills built around draw.io.

## Context & Goal

Build a public, shareable library of high-quality software-engineering skills. The first
batch covers diagramming with draw.io: solution architecture, workflows, sequence, and UML.

This spec covers **only the first skill**, `drawio-architecture`. It is built first as the
*template* — its structure, XML conventions, and verification approach establish the
reusable pattern that the other three skills (`drawio-workflow`, `drawio-sequence`,
`drawio-uml`) will replicate in later sessions.

## Decisions (locked during brainstorming)

| Decision | Choice | Rationale |
|---|---|---|
| Output artifact | Native `.drawio` XML (mxGraph) | Editable, drawio-faithful, no GUI import steps |
| Packaging | One standalone skill per diagram type | Each is self-contained and independently discoverable |
| Build order | One excellent template skill first | Lowest risk of baking a mistake into all four |
| First skill | Solution architecture | Highest value; forces strong layout conventions |
| Verification | Render via drawio CLI if available, degrade gracefully | Catches visual overlaps; still works with no tooling |
| Architectural style | C4-inspired, vendor-neutral | Ages well, stack-agnostic; cloud icons are a later add-on |

## Skill Structure

```
drawio-architecture/
  SKILL.md              # frontmatter + workflow + compressed core conventions
  references/
    mxgraph-primer.md   # reusable .drawio XML primer (shapes, edges, file wrapper)
    c4-conventions.md   # C4 levels, grid/tier layout system, spacing, styling rules
    verification.md     # drawio CLI export + graceful degradation tiers
  examples/
    context.drawio      # worked C4 System Context example
    container.drawio     # worked C4 Container example
    container.png        # rendered reference image
  assets/
    styles.md           # named style strings per role
```

**Reusable spine:** `references/mxgraph-primer.md` and `references/verification.md` carry
over to the other three skills almost unchanged. Only `c4-conventions.md` is swapped per
diagram type. This keeps "standalone per skill" consistent without reinventing the XML
basics four times.

## Runtime Workflow (encoded in SKILL.md)

1. **Clarify intent** — which C4 level (Context / Container / Component); the actors,
   systems, and key relationships.
2. **Plan layout on a grid** — assign every element to a tier (row) and column *before*
   emitting XML. This is the step that prevents freeform overlap.
3. **Emit native `.drawio` XML** — using named role styles + computed grid coordinates.
4. **Verify** — render via drawio CLI if present and inspect; always run structural +
   collision checks. Fix and re-verify until clean.
5. **Hand back** — the editable `.drawio` file plus the rendered image when available,
   stating which verification tier ran.

## Layout & Styling Conventions

The quality engine. Coordinates are *computed from grid position*, never guessed.

### Grid system
- **Tiers (rows)** run top→bottom in dependency order:
  `users → edge/web → services/app → data → external`.
- **Cell math:** node `width=160, height=80`; horizontal gap `80`; vertical tier gap `120`.
  Element at column `c`, tier `t`:
  - `x = 40 + c * (160 + 80)`
  - `y = 40 + t * (80 + 120)`
- **Boundaries** (e.g. "AWS", "Internal network") are container cells drawn as a padded
  rectangle around their children, emitted *first* so they render behind.

### C4 element styles (named, in `assets/styles.md`, applied by role)

| Role | Look |
|---|---|
| Person / actor | rounded, accent fill, person glyph |
| Software system | solid rounded box, primary fill |
| Container (app/service/db) | rounded box, lighter fill, tech label in italics |
| Datastore | cylinder shape |
| External system | grey / dashed — signals "not ours" |
| Boundary | dashed large rectangle, label top-left, no fill |
| Relationship | labeled edge, open arrow, verb required |

### Enforced rules
- **Every relationship edge must carry a label** — a verb ("reads from", "calls",
  "publishes to"). Unlabeled arrows are the #1 architecture-diagram smell.
- One dominant flow direction (top→bottom or left→right), chosen up front.
- Max ~12 elements per diagram; beyond that, split into a higher-level Context view plus a
  drill-down Container/Component view.
- Add a legend cell when non-obvious styling is used.

The full conventions live in `references/c4-conventions.md`; SKILL.md carries a compressed
version inline so the skill is usable without always opening the reference.

## Verification (graceful degradation)

Encoded in `references/verification.md`.

### Tier 1 — render & inspect (preferred; when drawio CLI available)
- Detect the CLI (`drawio` / `drawio-desktop`, or a VS Code extension binary).
- Export headless:
  `drawio --export --format png --output <out>.png <file>.drawio`
  (with `--no-sandbox` fallback for Linux/CI).
- Read the rendered PNG and check for: overlapping nodes, edges routed through boxes,
  clipped labels, off-canvas elements. Fix coordinates and re-render until clean.

### Tier 2 — structural validation (always runs; sole check when no CLI)
- XML well-formedness (parse it).
- Schema sanity: every `mxCell` has a valid `parent`; every edge `source`/`target`
  resolves to a real id; the `mxfile / diagram / mxGraphModel / root` wrapper is intact.
- **Coordinate-collision check:** programmatically confirm no two node bounding boxes
  overlap and nothing sits at negative coordinates.

The skill always states which tier ran, so the user knows whether the diagram was visually
verified or only structurally validated.

## Out of Scope (this spec)

- The other three skills (`drawio-workflow`, `drawio-sequence`, `drawio-uml`) — replicated
  from this template in later sessions.
- Cloud-vendor icon stencils (AWS/Azure/GCP) — possible later add-on.
- Mermaid authoring path — explicitly not used; native XML only.

## Success Criteria

- `drawio-architecture` produces a valid, editable `.drawio` file that opens cleanly in
  draw.io with no overlapping elements and every relationship labeled.
- Output follows C4 levels and the grid layout deterministically.
- Verification runs and reports its tier on every invocation.
- The structure cleanly generalizes: the primer + verification references are reusable for
  the next three skills with only conventions swapped.
