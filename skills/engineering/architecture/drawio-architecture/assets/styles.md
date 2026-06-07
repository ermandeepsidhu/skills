# C4 Role Styles

Named draw.io style strings for each C4 role. Apply them verbatim to the `style="..."`
attribute of an `mxCell`. They form a coherent, vendor-neutral C4 palette (people darkest,
systems mid, containers lighter, externals grey).

| Role | `style=` string |
|---|---|
| Person / actor | `rounded=1;whiteSpace=wrap;html=1;fillColor=#08427B;strokeColor=#052E56;fontColor=#FFFFFF;` |
| Software system (in scope) | `rounded=1;whiteSpace=wrap;html=1;fillColor=#1168BD;strokeColor=#0B4884;fontColor=#FFFFFF;` |
| Container (app/service) | `rounded=1;whiteSpace=wrap;html=1;fillColor=#438DD5;strokeColor=#2E6295;fontColor=#FFFFFF;` |
| Datastore (database) | `shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;fillColor=#438DD5;strokeColor=#2E6295;fontColor=#FFFFFF;` |
| External system | `rounded=1;whiteSpace=wrap;html=1;fillColor=#999999;strokeColor=#6B6B6B;fontColor=#FFFFFF;` |
| Boundary (grouping) | `rounded=1;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 4;fillColor=none;strokeColor=#444444;fontColor=#444444;verticalAlign=top;container=1;` |
| Relationship (edge) | `endArrow=open;html=1;rounded=0;fontSize=10;fontColor=#404040;strokeColor=#707070;` |

## Labeling convention

The `value="..."` attribute carries the label. Use a typed second line so every element
announces its kind (this is the C4 convention):

- **Person** → `Name&#10;[Person]`, optionally a third line describing the role.
- **Software system** → `Name&#10;[Software System]`.
- **Container** → `Name&#10;[Container: technology]`, e.g. `API&#10;[Container: Node.js]`.
- **Datastore** → `Name&#10;[Container: database tech]`, e.g. `Orders DB&#10;[Container: PostgreSQL]`.
- **External system** → `Name&#10;[External System]`.
- **Relationship (edge)** → a verb phrase, e.g. `makes API calls to`, `reads from and writes to`.

## Multi-line labels

These styles set `html=1`, so a label renders multiple lines when the line break is encoded
in the XML attribute. Use the numeric entity `&#10;` (a newline) between lines — it is the
most portable form inside an attribute value and survives round-tripping through draw.io.
