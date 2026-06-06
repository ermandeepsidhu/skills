# drawio-architecture Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `drawio-architecture` skill — a self-contained skill that produces editable, C4-inspired solution-architecture diagrams as native `.drawio` (mxGraph) XML, with deterministic grid layout and graceful-degradation verification.

**Architecture:** A skill directory (`SKILL.md` + `references/` + `assets/` + `examples/`) plus one real piece of code: `references/validate.py`, a zero-dependency Python validator (well-formedness + reference integrity + node-collision + negative-coordinate checks). The validator is the always-available verification tier; drawio-CLI rendering is the optional preferred tier. The mxGraph primer and verification reference are written to be reused verbatim by the later workflow/sequence/UML skills.

**Tech Stack:** Markdown (skill content), Python 3 stdlib (`xml.etree.ElementTree`, `unittest`) for the validator, optional `drawio` desktop CLI for rendering. No third-party packages.

**Repo conventions observed:** Public skills repo, currently only `README.md`. Each skill is a top-level directory at the repo root. The skill being built lives at `drawio-architecture/`.

---

## File Structure

```
drawio-architecture/
  SKILL.md                      # frontmatter + workflow + compressed conventions (Task 8)
  references/
    mxgraph-primer.md           # reusable .drawio XML primer (Task 3)
    c4-conventions.md           # C4 levels + grid math + style application (Task 5)
    verification.md             # CLI render + degradation tiers (Task 7)
    validate.py                 # zero-dep structural + collision validator (Task 2)
    tests/
      test_validate.py          # unittest for validate.py (Task 2)
      fixtures/
        good.drawio             # valid sample (Task 2)
        bad_overlap.drawio      # two overlapping nodes (Task 2)
        bad_dangling.drawio     # edge with unresolved target (Task 2)
  assets/
    styles.md                   # named C4 role style strings (Task 4)
  examples/
    context.drawio             # worked C4 System Context (Task 6)
    container.drawio            # worked C4 Container view (Task 6)
```

Build order is dependency-driven: scaffold → validator (it is the gate everything else is checked against) → primer → styles → conventions → examples (validated by the validator) → verification doc → SKILL.md → skill smoke test.

---

## Task 1: Scaffold the skill directory and SKILL.md frontmatter

**Files:**
- Create: `drawio-architecture/SKILL.md`
- Create: `drawio-architecture/references/`, `drawio-architecture/references/tests/fixtures/`, `drawio-architecture/assets/`, `drawio-architecture/examples/` (directories)

- [ ] **Step 1: Create directories**

Run:
```bash
cd /Users/mandeepsidhu/workspace/skills
mkdir -p drawio-architecture/references/tests/fixtures drawio-architecture/assets drawio-architecture/examples
```

- [ ] **Step 2: Write the SKILL.md frontmatter stub**

Write `drawio-architecture/SKILL.md` with ONLY the frontmatter and a title for now (the body is filled in Task 8). The `description` follows the superpowers convention of "Use when…" with concrete trigger phrases:

```markdown
---
name: drawio-architecture
description: Use when asked to create, draw, or update a solution/software architecture diagram, system context diagram, or C4 diagram as an editable draw.io file — produces native .drawio (mxGraph) XML with deterministic grid layout, C4-inspired vendor-neutral styling, labeled relationships, and built-in verification.
---

# drawio-architecture

<!-- body added in Task 8 -->
```

- [ ] **Step 3: Verify frontmatter is valid YAML**

Run:
```bash
cd /Users/mandeepsidhu/workspace/skills
python3 -c "import sys; d=open('drawio-architecture/SKILL.md').read(); fm=d.split('---')[1]; import yaml" 2>/dev/null || python3 -c "
d=open('drawio-architecture/SKILL.md').read().split('---')
assert d[1].strip().startswith('name:'), 'frontmatter missing name'
assert 'description:' in d[1], 'frontmatter missing description'
print('frontmatter OK')
"
```
Expected: `frontmatter OK`

- [ ] **Step 4: Commit**

```bash
cd /Users/mandeepsidhu/workspace/skills
git add drawio-architecture/SKILL.md
git commit -m "scaffold drawio-architecture skill directory and frontmatter"
```

---

## Task 2: Build the validator (TDD)

This is the only executable code in the skill and the always-on verification tier. Build it test-first.

**Files:**
- Create: `drawio-architecture/references/tests/fixtures/good.drawio`
- Create: `drawio-architecture/references/tests/fixtures/bad_overlap.drawio`
- Create: `drawio-architecture/references/tests/fixtures/bad_dangling.drawio`
- Create: `drawio-architecture/references/tests/test_validate.py`
- Create: `drawio-architecture/references/validate.py`

- [ ] **Step 1: Write the three fixtures**

`drawio-architecture/references/tests/fixtures/good.drawio` — two non-overlapping nodes and a resolving edge:
```xml
<mxfile><diagram name="good"><mxGraphModel><root>
  <mxCell id="0"/>
  <mxCell id="1" parent="0"/>
  <mxCell id="a" value="A" style="rounded=1;" vertex="1" parent="1"><mxGeometry x="40" y="40" width="160" height="80" as="geometry"/></mxCell>
  <mxCell id="b" value="B" style="rounded=1;" vertex="1" parent="1"><mxGeometry x="40" y="240" width="160" height="80" as="geometry"/></mxCell>
  <mxCell id="e1" value="calls" style="endArrow=open;" edge="1" parent="1" source="a" target="b"><mxGeometry relative="1" as="geometry"/></mxCell>
</root></mxGraphModel></diagram></mxfile>
```

`drawio-architecture/references/tests/fixtures/bad_overlap.drawio` — B's box overlaps A's:
```xml
<mxfile><diagram name="bad_overlap"><mxGraphModel><root>
  <mxCell id="0"/>
  <mxCell id="1" parent="0"/>
  <mxCell id="a" value="A" style="rounded=1;" vertex="1" parent="1"><mxGeometry x="40" y="40" width="160" height="80" as="geometry"/></mxCell>
  <mxCell id="b" value="B" style="rounded=1;" vertex="1" parent="1"><mxGeometry x="100" y="60" width="160" height="80" as="geometry"/></mxCell>
</root></mxGraphModel></diagram></mxfile>
```

`drawio-architecture/references/tests/fixtures/bad_dangling.drawio` — edge targets a missing id:
```xml
<mxfile><diagram name="bad_dangling"><mxGraphModel><root>
  <mxCell id="0"/>
  <mxCell id="1" parent="0"/>
  <mxCell id="a" value="A" style="rounded=1;" vertex="1" parent="1"><mxGeometry x="40" y="40" width="160" height="80" as="geometry"/></mxCell>
  <mxCell id="e1" value="calls" style="endArrow=open;" edge="1" parent="1" source="a" target="ZZZ"><mxGeometry relative="1" as="geometry"/></mxCell>
</root></mxGraphModel></diagram></mxfile>
```

- [ ] **Step 2: Write the failing test**

`drawio-architecture/references/tests/test_validate.py`:
```python
import os
import unittest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from validate import validate_drawio  # noqa: E402

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


class TestValidateDrawio(unittest.TestCase):
    def test_good_file_has_no_problems(self):
        self.assertEqual(validate_drawio(os.path.join(FIX, "good.drawio")), [])

    def test_overlap_is_detected(self):
        problems = validate_drawio(os.path.join(FIX, "bad_overlap.drawio"))
        self.assertTrue(any("overlap" in p for p in problems), problems)

    def test_dangling_edge_is_detected(self):
        problems = validate_drawio(os.path.join(FIX, "bad_dangling.drawio"))
        self.assertTrue(any("does not resolve" in p for p in problems), problems)

    def test_malformed_xml_is_reported(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".drawio", delete=False) as f:
            f.write("<mxfile><diagram>")  # unclosed
            path = f.name
        problems = validate_drawio(path)
        os.unlink(path)
        self.assertTrue(any("well-formed" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the test to confirm it fails**

Run:
```bash
cd /Users/mandeepsidhu/workspace/skills/drawio-architecture/references
python3 -m unittest tests.test_validate -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'validate'` (validate.py does not exist yet).

- [ ] **Step 4: Implement the validator**

`drawio-architecture/references/validate.py`:
```python
#!/usr/bin/env python3
"""Zero-dependency structural + collision validator for .drawio (mxGraph) files.

Checks performed:
  - XML is well-formed
  - <mxGraphModel> and its <root> exist
  - every cell's parent resolves to a real id
  - every edge's source/target resolves to a real id
  - no vertex has negative x/y
  - no two sibling, non-container, non-boundary nodes overlap

Returns a list of human-readable problem strings (empty list == valid).
"""
import sys
import xml.etree.ElementTree as ET


def _rect(cell):
    geo = cell.find("mxGeometry")
    if geo is None:
        return None
    try:
        return (
            float(geo.get("x", "0")),
            float(geo.get("y", "0")),
            float(geo.get("width", "0")),
            float(geo.get("height", "0")),
        )
    except ValueError:
        return None


def _overlap(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def validate_drawio(path):
    problems = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        return [f"XML not well-formed: {e}"]

    root_el = tree.getroot()
    model = root_el if root_el.tag == "mxGraphModel" else root_el.find(".//mxGraphModel")
    if model is None:
        return ["missing <mxGraphModel> element"]
    graph_root = model.find("root")
    if graph_root is None:
        return ["missing <root> element inside <mxGraphModel>"]

    cells = graph_root.findall("mxCell")
    ids = {c.get("id") for c in cells}

    vertices = {}      # id -> (cell, rect, parent)
    parents_used = set()
    for c in cells:
        cid = c.get("id")
        parent = c.get("parent")
        if parent is not None:
            parents_used.add(parent)
            if parent not in ids:
                problems.append(f"cell {cid!r} has parent {parent!r} which does not exist")
        if c.get("vertex") == "1":
            r = _rect(c)
            if r is not None:
                if r[0] < 0 or r[1] < 0:
                    problems.append(f"vertex {cid!r} has negative coordinates {r[:2]}")
                vertices[cid] = (c, r, parent)
        if c.get("edge") == "1":
            for end in ("source", "target"):
                ref = c.get(end)
                if ref is not None and ref not in ids:
                    problems.append(f"edge {cid!r} {end} {ref!r} does not resolve")

    # Collision check: group non-container, non-boundary vertices by parent
    # (children of a container share its coordinate space). A vertex that is the
    # parent of any other cell is treated as a container and skipped.
    by_parent = {}
    for cid, (c, r, parent) in vertices.items():
        style = c.get("style") or ""
        if cid in parents_used or "boundary" in style or "container=1" in style:
            continue
        by_parent.setdefault(parent, []).append((cid, r))

    for items in by_parent.values():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if _overlap(items[i][1], items[j][1]):
                    problems.append(f"nodes {items[i][0]!r} and {items[j][0]!r} overlap")

    return problems


def main(argv):
    if len(argv) != 2:
        print("usage: validate.py <file.drawio>", file=sys.stderr)
        return 2
    problems = validate_drawio(argv[1])
    if problems:
        print(f"INVALID: {argv[1]}")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"VALID: {argv[1]} (structural + collision checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 5: Run the test to confirm it passes**

Run:
```bash
cd /Users/mandeepsidhu/workspace/skills/drawio-architecture/references
python3 -m unittest tests.test_validate -v
```
Expected: PASS — 4 tests OK.

- [ ] **Step 6: Sanity-check the CLI entrypoint**

Run:
```bash
cd /Users/mandeepsidhu/workspace/skills/drawio-architecture/references
python3 validate.py tests/fixtures/good.drawio; echo "exit=$?"
python3 validate.py tests/fixtures/bad_overlap.drawio; echo "exit=$?"
```
Expected: first prints `VALID: ... exit=0`; second prints `INVALID:` with an overlap line and `exit=1`.

- [ ] **Step 7: Commit**

```bash
cd /Users/mandeepsidhu/workspace/skills
git add drawio-architecture/references/validate.py drawio-architecture/references/tests/
git commit -m "add zero-dep .drawio structural + collision validator with tests"
```

---

## Task 3: Write the mxGraph primer (reusable spine)

**Files:**
- Create: `drawio-architecture/references/mxgraph-primer.md`

- [ ] **Step 1: Write the primer**

Write `drawio-architecture/references/mxgraph-primer.md` covering the minimal mxGraph XML an author needs. It MUST contain these concrete, copy-pasteable blocks plus brief prose explaining each:

The file wrapper (note the mandatory `id="0"` root cell and `id="1"` default layer):
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

A vertex (node) — `vertex="1"`, absolute `x/y/width/height`:
```xml
<mxCell id="web" value="Web App" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="1">
  <mxGeometry x="40" y="40" width="160" height="80" as="geometry"/>
</mxCell>
```

An edge (relationship) — `edge="1"`, `source`/`target` reference vertex ids, `value` is the label:
```xml
<mxCell id="e_web_api" value="makes API calls to" style="endArrow=open;html=1;" edge="1" parent="1" source="web" target="api">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

A boundary/container — children set `parent` to the boundary id, and their `x/y` become **relative to the boundary**:
```xml
<mxCell id="bnd_aws" value="AWS" style="rounded=1;dashed=1;fillColor=none;verticalAlign=top;container=1;" vertex="1" parent="1">
  <mxGeometry x="600" y="40" width="360" height="300" as="geometry"/>
</mxCell>
<mxCell id="lambda" value="Lambda" style="rounded=1;whiteSpace=wrap;html=1;" vertex="1" parent="bnd_aws">
  <mxGeometry x="20" y="40" width="160" height="80" as="geometry"/>
</mxCell>
```

The primer MUST state these rules explicitly:
- Every cell needs a unique `id` and a `parent`; top-level cells use `parent="1"`.
- `id="0"` and `id="1"` are reserved (root + default layer) and must always be present.
- Coordinates for children of a container are relative to that container's origin.
- Open the result by saving with a `.drawio` extension; it opens in draw.io / the VS Code Draw.io Integration extension with no import step.

Close with one line: "This primer is reused unchanged across the drawio-* skills."

- [ ] **Step 2: Validate the wrapper example actually parses**

Run (extracts nothing automatically — just confirm well-formedness of a hand-copy if needed). Skip if no standalone file; the canonical check happens on real examples in Task 6.

- [ ] **Step 3: Commit**

```bash
cd /Users/mandeepsidhu/workspace/skills
git add drawio-architecture/references/mxgraph-primer.md
git commit -m "add reusable mxGraph XML primer"
```

---

## Task 4: Write the named C4 role styles

**Files:**
- Create: `drawio-architecture/assets/styles.md`

- [ ] **Step 1: Write the style catalog**

Write `drawio-architecture/assets/styles.md` as a table mapping each C4 role to an exact, valid draw.io style string. Use these verbatim (they are valid mxGraph styles and form a coherent C4 palette):

| Role | `style=` string |
|---|---|
| Person / actor | `rounded=1;whiteSpace=wrap;html=1;fillColor=#08427B;strokeColor=#052E56;fontColor=#FFFFFF;` |
| Software system (in scope) | `rounded=1;whiteSpace=wrap;html=1;fillColor=#1168BD;strokeColor=#0B4884;fontColor=#FFFFFF;` |
| Container (app/service) | `rounded=1;whiteSpace=wrap;html=1;fillColor=#438DD5;strokeColor=#2E6295;fontColor=#FFFFFF;` |
| Datastore (database) | `shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;fillColor=#438DD5;strokeColor=#2E6295;fontColor=#FFFFFF;` |
| External system | `rounded=1;whiteSpace=wrap;html=1;fillColor=#999999;strokeColor=#6B6B6B;fontColor=#FFFFFF;` |
| Boundary (grouping) | `rounded=1;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 4;fillColor=none;strokeColor=#444444;fontColor=#444444;verticalAlign=top;container=1;` |
| Relationship (edge) | `endArrow=open;html=1;rounded=0;fontSize=10;fontColor=#404040;strokeColor=#707070;` |

The file MUST also state the labeling convention for each role:
- Person value: `Name\n[Person]` plus an optional description line.
- Container value: `Name\n[Container: technology]` (e.g. `[Container: Node.js]`).
- Datastore value: `Name\n[Container: database tech]`.
- Use `&#10;` or literal `\n` rendering via `html=1` for multi-line labels; in XML attribute values a real newline or `&#xa;` works — prefer `&#10;` for portability.

- [ ] **Step 2: Commit**

```bash
cd /Users/mandeepsidhu/workspace/skills
git add drawio-architecture/assets/styles.md
git commit -m "add named C4 role style strings"
```

---

## Task 5: Write the C4 conventions (grid layout system)

**Files:**
- Create: `drawio-architecture/references/c4-conventions.md`

- [ ] **Step 1: Write the conventions doc**

Write `drawio-architecture/references/c4-conventions.md`. It MUST contain:

**C4 levels** (brief): System Context (people + the system + external systems), Container (apps/services/datastores inside the system), Component (inside one container). The skill targets Context and Container primarily.

**The grid system — exact math** (copy verbatim):
- Tiers (rows), top → bottom, in dependency order: `users → edge/web → services/app → data → external`.
- Constants: `NODE_W = 160`, `NODE_H = 80`, `H_GAP = 80`, `V_GAP = 120`, `MARGIN = 40`.
- For an element at column `c` (0-based) and tier `t` (0-based):
  - `x = MARGIN + c * (NODE_W + H_GAP)`  → `40, 280, 520, 760, …`
  - `y = MARGIN + t * (NODE_H + V_GAP)`  → `40, 240, 440, 640, …`
- Boundaries: compute the bounding box of the children that belong to the boundary, then expand by `BOUNDARY_PAD = 24` on each side; emit the boundary cell BEFORE its children so it renders behind. Children use coordinates relative to the boundary origin.

**Worked coordinate example** (must appear so the engineer can verify the math):
> Person at (c=0,t=0) → x=40,y=40. Web app at (c=0,t=1) → x=40,y=240. API at (c=0,t=2) → x=40,y=440. Database at (c=0,t=3) → x=40,y=640.

**Enforced rules** (restate from spec):
- Every relationship edge MUST have a verb label.
- One dominant flow direction; default top→bottom.
- Max ~12 elements; beyond that, split into a Context view + a Container drill-down.
- Add a legend cell when non-obvious styling is used.

**Pointer:** "Role style strings live in `../assets/styles.md`. XML syntax lives in `mxgraph-primer.md`."

- [ ] **Step 2: Commit**

```bash
cd /Users/mandeepsidhu/workspace/skills
git add drawio-architecture/references/c4-conventions.md
git commit -m "add C4 grid layout conventions"
```

---

## Task 6: Create and validate the worked examples

The examples are the skill's proof and its few-shot reference. They MUST pass the Task 2 validator.

**Files:**
- Create: `drawio-architecture/examples/context.drawio`
- Create: `drawio-architecture/examples/container.drawio`

- [ ] **Step 1: Write `context.drawio` (C4 System Context)**

A person, the system in scope, and one external system, laid out on the grid with labeled edges. Coordinates follow the Task 5 math.
```xml
<mxfile host="app.diagrams.net">
  <diagram name="System Context">
    <mxGraphModel dx="800" dy="600" grid="1" gridSize="10" guides="1" page="1" pageWidth="1169" pageHeight="826">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="user" value="Customer&#10;[Person]" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#08427B;strokeColor=#052E56;fontColor=#FFFFFF;" vertex="1" parent="1"><mxGeometry x="40" y="40" width="160" height="80" as="geometry"/></mxCell>
        <mxCell id="sys" value="Ordering System&#10;[Software System]" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1168BD;strokeColor=#0B4884;fontColor=#FFFFFF;" vertex="1" parent="1"><mxGeometry x="40" y="240" width="160" height="80" as="geometry"/></mxCell>
        <mxCell id="pay" value="Payment Gateway&#10;[External System]" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#999999;strokeColor=#6B6B6B;fontColor=#FFFFFF;" vertex="1" parent="1"><mxGeometry x="280" y="240" width="160" height="80" as="geometry"/></mxCell>
        <mxCell id="e1" value="places orders using" style="endArrow=open;html=1;rounded=0;fontSize=10;fontColor=#404040;strokeColor=#707070;" edge="1" parent="1" source="user" target="sys"><mxGeometry relative="1" as="geometry"/></mxCell>
        <mxCell id="e2" value="requests payment via" style="endArrow=open;html=1;rounded=0;fontSize=10;fontColor=#404040;strokeColor=#707070;" edge="1" parent="1" source="sys" target="pay"><mxGeometry relative="1" as="geometry"/></mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

- [ ] **Step 2: Write `container.drawio` (C4 Container view with a boundary + datastore)**

```xml
<mxfile host="app.diagrams.net">
  <diagram name="Container">
    <mxGraphModel dx="800" dy="600" grid="1" gridSize="10" guides="1" page="1" pageWidth="1169" pageHeight="826">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="user" value="Customer&#10;[Person]" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#08427B;strokeColor=#052E56;fontColor=#FFFFFF;" vertex="1" parent="1"><mxGeometry x="40" y="40" width="160" height="80" as="geometry"/></mxCell>
        <mxCell id="bnd" value="Ordering System" style="rounded=1;whiteSpace=wrap;html=1;dashed=1;dashPattern=8 4;fillColor=none;strokeColor=#444444;fontColor=#444444;verticalAlign=top;container=1;" vertex="1" parent="1"><mxGeometry x="16" y="216" width="408" height="528" as="geometry"/></mxCell>
        <mxCell id="web" value="Web App&#10;[Container: React]" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#438DD5;strokeColor=#2E6295;fontColor=#FFFFFF;" vertex="1" parent="bnd"><mxGeometry x="24" y="48" width="160" height="80" as="geometry"/></mxCell>
        <mxCell id="api" value="API&#10;[Container: Node.js]" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#438DD5;strokeColor=#2E6295;fontColor=#FFFFFF;" vertex="1" parent="bnd"><mxGeometry x="24" y="248" width="160" height="80" as="geometry"/></mxCell>
        <mxCell id="db" value="Orders DB&#10;[Container: PostgreSQL]" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;fillColor=#438DD5;strokeColor=#2E6295;fontColor=#FFFFFF;" vertex="1" parent="bnd"><mxGeometry x="24" y="424" width="160" height="80" as="geometry"/></mxCell>
        <mxCell id="e1" value="uses [HTTPS]" style="endArrow=open;html=1;rounded=0;fontSize=10;fontColor=#404040;strokeColor=#707070;" edge="1" parent="1" source="user" target="web"><mxGeometry relative="1" as="geometry"/></mxCell>
        <mxCell id="e2" value="makes API calls to [JSON/HTTPS]" style="endArrow=open;html=1;rounded=0;fontSize=10;fontColor=#404040;strokeColor=#707070;" edge="1" parent="1" source="web" target="api"><mxGeometry relative="1" as="geometry"/></mxCell>
        <mxCell id="e3" value="reads from and writes to" style="endArrow=open;html=1;rounded=0;fontSize=10;fontColor=#404040;strokeColor=#707070;" edge="1" parent="1" source="api" target="db"><mxGeometry relative="1" as="geometry"/></mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

- [ ] **Step 3: Validate both examples with the Task 2 validator**

Run:
```bash
cd /Users/mandeepsidhu/workspace/skills/drawio-architecture/references
python3 validate.py ../examples/context.drawio; echo "exit=$?"
python3 validate.py ../examples/container.drawio; echo "exit=$?"
```
Expected: both print `VALID: ...` and `exit=0`. If either reports overlap, adjust the offending `x/y` per the Task 5 grid math and re-run until clean.

- [ ] **Step 4: Confirm well-formedness with xmllint as a second check**

Run:
```bash
cd /Users/mandeepsidhu/workspace/skills
xmllint --noout drawio-architecture/examples/context.drawio drawio-architecture/examples/container.drawio && echo "xmllint OK"
```
Expected: `xmllint OK`

- [ ] **Step 5: Commit**

```bash
cd /Users/mandeepsidhu/workspace/skills
git add drawio-architecture/examples/
git commit -m "add validated C4 context and container example diagrams"
```

---

## Task 7: Write the verification reference (degradation tiers)

**Files:**
- Create: `drawio-architecture/references/verification.md`

- [ ] **Step 1: Write the verification doc**

Write `drawio-architecture/references/verification.md` documenting the two tiers. It MUST include exact commands.

**Tier 2 — structural validation (ALWAYS run; the only check when no CLI):**
```bash
python3 references/validate.py <your-file>.drawio
```
Explain: exit 0 = pass; exit 1 = problems listed (unresolved refs, overlaps, negative coords, malformed XML). Fix and re-run until exit 0. Note it is zero-dependency (Python 3 stdlib) so it always works.

**Tier 1 — render & inspect (PREFERRED when the drawio CLI is installed):**
```bash
# detect
command -v drawio || command -v drawio-desktop
# export to PNG (add --no-sandbox on Linux/CI)
drawio --export --format png --output preview.png <your-file>.drawio
```
Explain: after export, read `preview.png` and visually check for overlapping nodes, edges routed through boxes, clipped labels, and off-canvas elements; fix coordinates and re-render until clean.

The doc MUST state: "Always run Tier 2. Run Tier 1 additionally when a drawio CLI is available. Report to the user which tier(s) ran." And note: "This reference is reused unchanged across the drawio-* skills."

- [ ] **Step 2: Verify the documented Tier 2 command works end-to-end**

Run:
```bash
cd /Users/mandeepsidhu/workspace/skills/drawio-architecture
python3 references/validate.py examples/context.drawio; echo "exit=$?"
```
Expected: `VALID: examples/context.drawio ...` and `exit=0`.

- [ ] **Step 3: Commit**

```bash
cd /Users/mandeepsidhu/workspace/skills
git add drawio-architecture/references/verification.md
git commit -m "add verification reference with graceful degradation tiers"
```

---

## Task 8: Write the SKILL.md body (the workflow)

**Files:**
- Modify: `drawio-architecture/SKILL.md`

- [ ] **Step 1: Replace the body stub with the full workflow**

Keep the Task 1 frontmatter. Replace the `<!-- body added in Task 8 -->` line with a body containing these sections:

1. **Overview** — one paragraph: produces editable native `.drawio` C4 architecture diagrams with deterministic grid layout and built-in verification.

2. **When to use / not use** — use for solution/software architecture, system context, C4 diagrams. Not for sequence/workflow/UML (point to the sibling skills when they exist).

3. **Workflow (numbered, the load-bearing part):**
   - **1. Clarify** — ask which C4 level (Context vs Container), the actors, the system(s) in scope, external systems, and the key relationships. List elements before drawing.
   - **2. Plan the grid** — assign every element a `(column, tier)` using the tier order `users → edge/web → services/app → data → external`. Compute `x/y` with the formulas in `references/c4-conventions.md`. Do this before emitting XML.
   - **3. Emit XML** — build the `.drawio` using the wrapper and node/edge syntax in `references/mxgraph-primer.md` and the role style strings in `assets/styles.md`. Emit boundaries before their children. Every edge gets a verb label.
   - **4. Verify** — run `python3 references/validate.py <file>.drawio` (always); if a drawio CLI is present, also export a PNG and visually inspect per `references/verification.md`. Fix and re-verify until clean.
   - **5. Deliver** — give the user the `.drawio` path (and PNG if rendered), and state which verification tier(s) ran.

4. **Compressed conventions** (so the skill works without opening references): the grid constants (`NODE_W=160, NODE_H=80, H_GAP=80, V_GAP=120, MARGIN=40`), the `x/y` formulas, and the three hard rules (every edge labeled; ≤12 elements or split; boundaries emitted first).

5. **References** — bullet list pointing to `references/mxgraph-primer.md`, `references/c4-conventions.md`, `assets/styles.md`, `references/verification.md`, and `examples/`.

The SKILL.md MUST cross-reference files by their real relative paths (verified to exist from Tasks 2–7).

- [ ] **Step 2: Verify all referenced paths exist**

Run:
```bash
cd /Users/mandeepsidhu/workspace/skills/drawio-architecture
for f in references/mxgraph-primer.md references/c4-conventions.md references/verification.md references/validate.py assets/styles.md examples/context.drawio examples/container.drawio; do
  test -f "$f" && echo "OK $f" || echo "MISSING $f"
done
```
Expected: every line starts with `OK`.

- [ ] **Step 3: Commit**

```bash
cd /Users/mandeepsidhu/workspace/skills
git add drawio-architecture/SKILL.md
git commit -m "write drawio-architecture SKILL.md workflow body"
```

---

## Task 9: Skill smoke test with a subagent

Validate that the skill actually drives correct behavior, using the testing-skills-with-subagents approach.

**Files:**
- No new files unless the test surfaces a fix.

- [ ] **Step 1: Dispatch a subagent given only the skill**

Use the Agent tool (general-purpose). Prompt the subagent to act as if it discovered and is following `drawio-architecture/SKILL.md`, and to produce a C4 Container diagram for a small described system (e.g. "a URL shortener: user → web app → API → Redis cache + Postgres") saved to `/tmp/smoketest.drawio`. Instruct it to follow the skill's workflow including verification.

- [ ] **Step 2: Validate the subagent's output**

Run:
```bash
cd /Users/mandeepsidhu/workspace/skills/drawio-architecture
python3 references/validate.py /tmp/smoketest.drawio; echo "exit=$?"
xmllint --noout /tmp/smoketest.drawio && echo "well-formed"
```
Expected: `VALID: ...`, `exit=0`, `well-formed`. Every edge in the file should have a non-empty `value`.

- [ ] **Step 3: Fix any gaps the test exposed**

If the subagent produced overlaps, unlabeled edges, or missed the grid/styles, the SKILL.md or a reference was ambiguous. Tighten the wording (e.g. make a rule more imperative, add a worked step), commit the doc fix, and re-run the smoke test. Iterate until a fresh subagent reliably produces a valid, well-labeled diagram.

- [ ] **Step 4: Final commit**

```bash
cd /Users/mandeepsidhu/workspace/skills
git add -A
git commit -m "tighten drawio-architecture skill after subagent smoke test" || echo "no changes needed"
```

---

## Self-Review

**Spec coverage:**
- Native `.drawio` output → Tasks 3, 6, 8 (primer, examples, workflow emit XML). ✓
- Standalone self-contained skill → Task 1 directory + all content inside it. ✓
- Reusable spine (primer + verification) → Tasks 3, 7 explicitly mark files "reused unchanged." ✓
- C4-inspired vendor-neutral style → Tasks 4, 5 (styles + C4 levels). ✓
- Deterministic grid layout → Task 5 (exact math), enforced in Task 8 workflow + compressed conventions. ✓
- Mandatory labeled edges / ≤12 elements / boundaries-first → Tasks 5, 8 rules; Task 6 examples demonstrate. ✓
- Verification with graceful degradation → Task 2 (validator), Task 7 (tiers doc), Task 8 step 4 (workflow invokes it), Task 9 (proves it). ✓
- Render via drawio CLI if available → Task 7 Tier 1 commands. ✓
- Generalizes to the next three skills → primer + verification authored as reusable (Tasks 3, 7). ✓

**Placeholder scan:** No "TBD"/"TODO"/"handle edge cases" left; all code blocks and commands are concrete. ✓

**Type/name consistency:** Validator exposes `validate_drawio(path)` (Task 2) and is invoked as `python3 references/validate.py <file>` everywhere (Tasks 6, 7, 8, 9). Grid constants `NODE_W/NODE_H/H_GAP/V_GAP/MARGIN` are identical in Tasks 5 and 8. Style strings in Task 4 match those used in the Task 6 example XML. ✓
