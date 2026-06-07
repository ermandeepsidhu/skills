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

**Boundaries.** A boundary wraps a set of child elements. Compute it in three steps:

1. **Bounding box** of the children, in page coordinates. With children spanning columns
   `c` and tiers `t`, that is `min_x … max_x+NODE_W` by `min_y … max_y+NODE_H`.
2. **Pad** by `BOUNDARY_PAD = 24` on every side. So the boundary's page origin is
   `(min_x - 24, min_y - 24)`, its width is `(max_x + NODE_W) - min_x + 48`, and its height
   is `(max_y + NODE_H) - min_y + 48`. (The boundary intentionally extends ~24px left of and
   above the grid margin — that is expected, not an error.)
3. **Re-express each child relative to the boundary origin**, because draw.io child
   geometry is relative to the parent container (see `mxgraph-primer.md`):

   ```text
   child_relative_x = child_page_x - boundary_origin_x
   child_relative_y = child_page_y - boundary_origin_y
   ```

Emit the boundary cell *before* its children so it renders behind them.

**Worked two-column example.** Children at page coords Web(40,240), API(40,440),
Postgres(40,640), Redis(280,640):

- bounding box `40 … 280+160=440` by `240 … 640+80=720`
- padded boundary origin `(16, 216)`, size `(440-40+48) × (720-240+48) = 448 × 528`
- relative children: Web(24,24), API(24,224), Postgres(24,424), Redis(264,424).

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
