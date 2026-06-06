# mxGraph (.drawio) XML Primer

A `.drawio` file is plain XML in the mxGraph format. Everything is an `mxCell`: nodes, edges, and containers alike. This primer covers the four building blocks you need to hand-author a diagram.

## 1. File wrapper

Every diagram is wrapped in `mxfile` → `diagram` → `mxGraphModel` → `root`. The `root` must contain two reserved cells: `id="0"` is the invisible root, and `id="1"` is the default layer (its `parent` is `0`). All your content lives below them and sets `parent="1"` (or the id of a boundary). Omitting either reserved cell produces a file draw.io cannot open.

```xml
<mxfile host="app.diagrams.net">
  <diagram name="Page-1">
    <mxGraphModel dx="800" dy="600" grid="1" gridSize="10" guides="1" connect="1" arrows="1" page="1" pageWidth="1169" pageHeight="826">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- nodes and edges go here, parent="1" (or a boundary id) -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## 2. Vertex (node)

A node is an `mxCell` with `vertex="1"`. Its `mxGeometry` gives an absolute position and size on the page: `x`/`y` are the top-left corner, `width`/`height` the box dimensions. The `value` is the visible label; `style` is a semicolon-separated list of shape properties.

```xml
<mxCell id="web" value="Web App" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
  <mxGeometry x="40" y="40" width="160" height="80" as="geometry"/>
</mxCell>
```

## 3. Edge (relationship)

An edge is an `mxCell` with `edge="1"`. Its `source` and `target` reference the `id`s of two vertices, and draw.io routes the connector between them — you do not specify coordinates. The `value` is the visible label on the edge. The geometry is `relative="1"` with no fixed points, letting the layout engine handle routing.

```xml
<mxCell id="e_web_api" value="makes API calls to" style="endArrow=open;html=1;" edge="1" parent="1" source="web" target="api">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

## 4. Boundary / container

A container is a vertex with `container=1` in its style. Place children inside it by setting their `parent` to the container's `id`. A child's `x`/`y` are then **relative to the container's origin**, not the page — `x="20" y="40"` below means 20px right and 40px down from the boundary's top-left corner.

```xml
<mxCell id="bnd_aws" value="AWS" style="rounded=1;dashed=1;fillColor=none;verticalAlign=top;container=1;" vertex="1" parent="1">
  <mxGeometry x="600" y="40" width="360" height="300" as="geometry"/>
</mxCell>
<mxCell id="lambda" value="Lambda" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="bnd_aws">
  <mxGeometry x="20" y="40" width="160" height="80" as="geometry"/>
</mxCell>
```

## Rules

- Every cell needs a unique `id` and a `parent`; top-level cells use `parent="1"`.
- `id="0"` and `id="1"` are reserved (root + default layer) and must always be present.
- Coordinates for children of a container are relative to that container's origin.
- Save the result with a `.drawio` extension; it opens in draw.io / the VS Code Draw.io Integration extension with no import step.

This primer is reused unchanged across the drawio-* skills.
