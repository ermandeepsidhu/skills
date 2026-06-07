---
name: drawio-architecture
description: Use when asked to create, draw, or update a solution/software architecture diagram, system context diagram, or C4 diagram as an editable draw.io file — produces native .drawio (mxGraph) XML with deterministic grid layout, C4-inspired vendor-neutral styling, labeled relationships, and built-in verification.
---

# drawio-architecture

Produce editable, professional **solution-architecture diagrams** as native `.drawio`
(mxGraph) XML. Layout is computed on a deterministic grid (so diagrams never come out
overlapping), styling follows a C4-inspired vendor-neutral palette, every relationship is
labeled, and output is verified before you hand it over.

## When to use

Use for: solution/software architecture diagrams, system context diagrams, container
diagrams, C4 diagrams — anything where you show systems, services, datastores, and how they
relate, as an editable draw.io file.

Not for: sequence diagrams, flowcharts/workflows, or UML class diagrams (sibling
`drawio-*` skills cover those). If the request is one of those, stop and use the matching
skill.

## Workflow

Follow these steps in order. Do not emit XML before you have planned the grid.

### 1. Clarify

Establish, asking the user only if it is genuinely ambiguous:
- **C4 level** — System Context (people + the system + external systems) or Container
  (apps/services/datastores inside the system). One level per diagram.
- The **actors**, the **system(s) in scope**, the **external systems**, and the **key
  relationships** between them.

List the elements and relationships explicitly before drawing.

### 2. Plan the grid

Assign every element a `(column, tier)` position. Tiers run top → bottom in dependency
order: `users → edge/web → services/app → data → external`. Compute each element's `x/y`
with the formulas in `references/c4-conventions.md`. Do this before emitting any XML — it is
what keeps the diagram overlap-free.

### 3. Emit the `.drawio` XML

Build the file using the wrapper and node/edge syntax in `references/mxgraph-primer.md` and
the role style strings in `assets/styles.md`. Rules:
- Emit **boundaries before their children** (so they render behind); children use
  coordinates relative to the boundary origin.
- **Every edge gets a verb label** (`reads from`, `calls`, `publishes to`).
- Save with a `.drawio` extension.

### 4. Verify

Run the always-on structural + collision check:

```bash
python3 references/validate.py <file>.drawio
```

Fix anything it reports and re-run until it prints `VALID`. If a draw.io CLI is installed,
additionally export a PNG and visually inspect it. Full procedure (both tiers, with
commands) is in `references/verification.md`.

### 5. Deliver

Give the user the `.drawio` file path (and the PNG if you rendered one), and state which
verification tier(s) ran.

## Core conventions (quick reference)

Grid constants — `x = MARGIN + c*(NODE_W+H_GAP)`, `y = MARGIN + t*(NODE_H+V_GAP)`:

```
NODE_W = 160   NODE_H = 80   H_GAP = 80   V_GAP = 120   MARGIN = 40
```

Hard rules:
- Every relationship edge carries a verb label.
- Max ~12 elements per diagram; beyond that, split into a Context view plus a Container
  drill-down.
- Emit boundaries before the children they contain.

## References

- `references/mxgraph-primer.md` — the `.drawio` XML syntax (wrapper, vertex, edge, boundary).
- `references/c4-conventions.md` — C4 levels, the full grid math, and enforced rules.
- `assets/styles.md` — named C4 role style strings + labeling convention.
- `references/verification.md` — the two-tier verification procedure.
- `examples/context.drawio`, `examples/container.drawio` — worked, validated diagrams to
  pattern-match against.
