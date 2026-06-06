# C4 Conventions & Grid Layout

How this skill decides *what* goes in an architecture diagram (C4 levels) and *where*
each element sits (the grid). Coordinates are computed from grid position, never guessed —
that is what keeps output overlap-free.

## C4 levels

- **System Context** — the people (actors) who use the system, the one software system in
  scope, and the external systems it talks to. No internals.
- **Container** — the applications, services, and datastores *inside* the system in scope,
  drawn within a boundary, plus the actors/externals that touch them.
- **Component** — the parts inside a single container. Rarely needed.

This skill targets **System Context** and **Container** primarily. Pick one level per
diagram; if you need both, produce two diagrams (a Context overview and a Container
drill-down).

## The grid system — exact math

Lay elements out in **tiers** (rows), top → bottom, in dependency order:

```
users → edge/web → services/app → data → external
```

Constants:

```
NODE_W = 160
NODE_H = 80
H_GAP  = 80
V_GAP  = 120
MARGIN = 40
```

For an element at **column `c`** (0-based, left→right within a tier) and **tier `t`**
(0-based, top→bottom):

```
x = MARGIN + c * (NODE_W + H_GAP)   ->  40, 280, 520, 760, ...
y = MARGIN + t * (NODE_H + V_GAP)   ->  40, 240, 440, 640, ...
```

**Boundaries:** compute the bounding box of the children that belong to the boundary, then
expand by `BOUNDARY_PAD = 24` on each side. Emit the boundary cell *before* its children so
it renders behind them. Children use coordinates **relative to the boundary origin** (see
`mxgraph-primer.md`).

### Worked coordinate example

A single column (c=0) of four stacked tiers:

- Person at (c=0, t=0) → `x=40,  y=40`
- Web app at (c=0, t=1) → `x=40,  y=240`
- API at (c=0, t=2) → `x=40,  y=440`
- Database at (c=0, t=3) → `x=40,  y=640`

## Enforced rules

- **Every relationship edge must have a verb label** (`reads from`, `calls`,
  `publishes to`). Unlabeled arrows are the #1 architecture-diagram smell.
- **One dominant flow direction.** Default top → bottom.
- **Max ~12 elements per diagram.** Beyond that, split into a Context view plus a Container
  drill-down.
- **Add a legend cell** when non-obvious styling is used.

## Pointers

- Role style strings live in `../assets/styles.md`.
- XML syntax (wrapper, vertex, edge, boundary) lives in `mxgraph-primer.md`.
