#!/usr/bin/env python3
"""Build draw.io-viewer HTML pages for every example .drawio in the repo.

For each `skills/**/examples/*.drawio`, writes a self-contained HTML file under
`build/render/` that renders the diagram with the official draw.io GraphViewer
(viewer.diagrams.net). Open each HTML in a browser — or drive it headless — and
screenshot it to produce a PNG preview next to the .drawio file.

The PNG previews are committed and shown in each skill's EXAMPLES.md. Regenerate
previews after changing an example by re-running this and re-screenshotting.

Zero third-party dependencies (standard library only).
"""
import html
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "build" / "render"

PAGE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>html,body{{margin:0;padding:0;background:#ffffff}}</style></head>
<body>
<div class="mxgraph" style="max-width:100%;" data-mxgraph="{config}"></div>
<script type="text/javascript" src="https://viewer.diagrams.net/js/viewer-static.min.js"></script>
</body>
</html>
"""


def build():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pages = []
    for drawio in sorted((REPO_ROOT / "skills").glob("**/examples/*.drawio")):
        xml = drawio.read_text(encoding="utf-8")
        config = json.dumps(
            {"xml": xml, "toolbar": None, "nav": False, "resize": True, "border": 24}
        )
        page = PAGE.format(config=html.escape(config, quote=True))
        out = OUT_DIR / (drawio.stem + ".html")
        out.write_text(page, encoding="utf-8")
        # PNG should be written next to the source .drawio by the screenshot step.
        png = drawio.with_suffix(".png")
        pages.append((out, png))
        print(f"{out.relative_to(REPO_ROOT)}  ->  screenshot to {png.relative_to(REPO_ROOT)}")
    if not pages:
        print("no example .drawio files found")
    return pages


if __name__ == "__main__":
    build()
    sys.exit(0)
