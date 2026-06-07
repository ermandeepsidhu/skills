#!/usr/bin/env python3
"""Maintain the skills repo: sync per-IDE symlink farms and check README is current.

Canonical skills live at:   skills/<domain>/<category>/<skill>/SKILL.md
Each supported AI coding tool discovers skills as direct children of its own skills
directory, so we expose every canonical skill as a flat symlink inside each tool's dir:

    .claude/skills/<skill>   -> ../../skills/<domain>/<category>/<skill>
    .cursor/skills/<skill>   -> ...
    .github/skills/<skill>   -> ...
    .agent/skills/<skill>    -> ...   (Antigravity, singular)
    .agents/skills/<skill>   -> ...   (emerging cross-client standard)

Usage:
    python3 scripts/skills.py sync     # create/refresh/prune the symlinks (idempotent)
    python3 scripts/skills.py check    # verify symlinks + README list are in sync (CI gate)

Zero third-party dependencies (standard library only).
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "skills"
README = REPO_ROOT / "README.md"

# Per-tool skills directories (relative to repo root).
IDE_SKILL_DIRS = [
    ".claude/skills",
    ".cursor/skills",
    ".github/skills",
    ".agent/skills",
    ".agents/skills",
]


def _frontmatter_name(skill_md: Path):
    """Return the `name:` value from a SKILL.md YAML frontmatter block, or None."""
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    for line in parts[1].splitlines():
        if line.strip().startswith("name:"):
            return line.split(":", 1)[1].strip()
    return None


def discover_skills():
    """Find every canonical skill. Returns list of (name, skill_dir, problems)."""
    skills = []
    for skill_md in sorted(SKILLS_ROOT.glob("**/SKILL.md")):
        skill_dir = skill_md.parent
        fm_name = _frontmatter_name(skill_md)
        dir_name = skill_dir.name
        problems = []
        if fm_name is None:
            problems.append(f"{skill_md}: missing `name:` in frontmatter")
        elif fm_name != dir_name:
            problems.append(
                f"{skill_md}: frontmatter name {fm_name!r} != directory {dir_name!r}"
            )
        skills.append((dir_name, skill_dir, problems))
    return skills


def desired_links(skills):
    """Map each tool's skills dir -> {skill_name: relative_symlink_target}."""
    plan = {}
    for ide_rel in IDE_SKILL_DIRS:
        ide_dir = REPO_ROOT / ide_rel
        plan[ide_dir] = {}
        for name, skill_dir, _ in skills:
            link = ide_dir / name
            target = os.path.relpath(skill_dir, start=ide_dir)
            plan[ide_dir][name] = (link, target)
    return plan


def cmd_sync():
    skills = discover_skills()
    problems = [p for _, _, probs in skills for p in probs]
    if problems:
        print("Refusing to sync — fix these skill problems first:")
        for p in problems:
            print(f"  - {p}")
        return 1

    plan = desired_links(skills)
    valid_names = {name for name, _, _ in skills}
    changes = 0
    for ide_dir, links in plan.items():
        ide_dir.mkdir(parents=True, exist_ok=True)
        # Prune stale symlinks (point into skills/ but skill no longer exists).
        for entry in ide_dir.iterdir():
            if entry.is_symlink() and entry.name not in valid_names:
                target = os.readlink(entry)
                if "skills" in target:
                    entry.unlink()
                    print(f"pruned  {entry.relative_to(REPO_ROOT)}")
                    changes += 1
        # Create or fix each desired link.
        for name, (link, target) in links.items():
            if link.is_symlink():
                if os.readlink(link) == target:
                    continue
                link.unlink()
            elif link.exists():
                print(f"SKIP    {link.relative_to(REPO_ROOT)} exists and is not a symlink")
                continue
            os.symlink(target, link)
            print(f"linked  {link.relative_to(REPO_ROOT)} -> {target}")
            changes += 1
    print(f"sync complete: {len(valid_names)} skill(s), {changes} change(s).")
    return 0


def cmd_check():
    skills = discover_skills()
    errors = [p for _, _, probs in skills for p in probs]

    plan = desired_links(skills)
    for ide_dir, links in plan.items():
        for name, (link, target) in links.items():
            if not link.is_symlink():
                errors.append(f"missing symlink: {link.relative_to(REPO_ROOT)} (run: scripts/skills.py sync)")
            elif os.readlink(link) != target:
                errors.append(f"wrong symlink: {link.relative_to(REPO_ROOT)} -> {os.readlink(link)} (want {target})")
            elif not link.resolve().exists():
                errors.append(f"broken symlink: {link.relative_to(REPO_ROOT)}")

    readme_text = README.read_text(encoding="utf-8") if README.exists() else ""
    for name, _, _ in skills:
        if name not in readme_text:
            errors.append(f"README.md does not mention skill '{name}'")

    if errors:
        print("check FAILED:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"check OK: {len(skills)} skill(s), all symlinks and README references present.")
    return 0


def main(argv):
    if len(argv) != 2 or argv[1] not in ("sync", "check"):
        print(__doc__)
        return 2
    return cmd_sync() if argv[1] == "sync" else cmd_check()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
