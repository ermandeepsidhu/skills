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
            if cid is None:
                problems.append("a vertex is missing its required id attribute")
            r = _rect(c)
            if r is not None:
                if r[0] < 0 or r[1] < 0:
                    problems.append(f"vertex {cid!r} has negative coordinates {r[:2]}")
                if cid is not None:
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
