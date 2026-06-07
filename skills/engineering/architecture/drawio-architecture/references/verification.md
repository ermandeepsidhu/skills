# Verifying a .drawio Diagram

Two tiers, designed to degrade gracefully. **Always run Tier 2.** Additionally run Tier 1
when a draw.io CLI is installed. Tell the user which tier(s) ran.

## Tier 2 — structural validation (ALWAYS run)

Zero-dependency, Python 3 standard library only — works on any machine with `python3`,
including CI with no GUI:

```bash
python3 references/validate.py <your-file>.drawio
```

- **Exit 0** → `VALID`: well-formed XML, `mxGraphModel`/`root` present, every cell's parent
  resolves, every edge's `source`/`target` resolves, no negative coordinates, and no two
  sibling nodes overlap.
- **Exit 1** → `INVALID`: each problem is listed (unresolved reference, overlap, negative
  coordinate, missing id, or malformed XML). Fix the offending cell and re-run until exit 0.

This is the dependable floor: even with no rendering tools available, it catches the worst
structural and layout failures.

## Tier 1 — render & inspect (PREFERRED, when the draw.io CLI is installed)

Detect the CLI:

```bash
command -v drawio || command -v drawio-desktop
```

If present, export the diagram to an image (add `--no-sandbox` on Linux/CI where the
sandbox is unavailable):

```bash
drawio --export --format png --output preview.png <your-file>.drawio
# Linux/CI fallback:
drawio --no-sandbox --export --format png --output preview.png <your-file>.drawio
```

Then **read `preview.png`** and check visually for things the structural checker cannot see:

- nodes overlapping or touching awkwardly,
- edges routed *through* boxes instead of around them,
- labels clipped or spilling outside their node,
- elements pushed off the page/canvas.

Fix coordinates and re-render until the image is clean.

## Reporting

State the outcome explicitly, e.g. *"Verified: Tier 2 structural checks passed; Tier 1
render skipped (no draw.io CLI found)."* — so the user knows whether the diagram was
visually inspected or only structurally validated.

---

This reference is reused unchanged across the drawio-* skills.
