"""Check every relative link in the repo's Markdown files, including #heading anchors.

Web links are not fetched; the live site has its own health check. Example::

    python scripts/ops/check_links.py
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE_RE = re.compile(r"^(```|~~~).*?^\1", re.MULTILINE | re.DOTALL)
CODE_RE = re.compile(r"`[^`\n]*`")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
EXTERNAL = ("http://", "https://", "mailto:")


def slug(heading: str) -> str:
    """GitHub's anchor for a heading: lower case, punctuation dropped, spaces to hyphens."""
    text = re.sub(r"[`*_]|\[([^\]]*)\]\([^)]*\)", r"\1", heading).strip().lower()
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


def anchors(markdown: str) -> set[str]:
    """Every heading anchor in a Markdown text, numbered the way GitHub numbers repeats."""
    seen: dict[str, int] = {}
    found = set()
    for heading in HEADING_RE.findall(FENCE_RE.sub("", markdown)):
        base = slug(heading)
        count = seen.get(base, 0)
        seen[base] = count + 1
        found.add(base if count == 0 else f"{base}-{count}")
    return found


def links(markdown: str) -> list[str]:
    """Link targets in a Markdown text, ignoring code blocks and inline code."""
    return LINK_RE.findall(CODE_RE.sub("", FENCE_RE.sub("", markdown)))


def broken_links(files: list[Path], root: Path = ROOT) -> list[str]:
    """One line per relative link whose file or heading does not exist."""
    problems = []
    for source in files:
        text = source.read_text(encoding="utf-8")
        for target in links(text):
            if target.startswith(EXTERNAL):
                continue
            path_part, _, anchor = target.partition("#")
            path = (source.parent / path_part).resolve() if path_part else source
            where = f"{source.relative_to(root).as_posix()}: {target}"
            if not path.exists():
                problems.append(f"{where} (no such file)")
            elif anchor and path.suffix == ".md" and anchor not in anchors(path.read_text(encoding="utf-8")):
                problems.append(f"{where} (no such heading)")
    return problems


def tracked_markdown(root: Path = ROOT) -> list[Path]:
    """Markdown files tracked by git."""
    out = subprocess.run(["git", "ls-files", "*.md"], cwd=root, capture_output=True, check=True, text=True).stdout
    return [root / line for line in out.splitlines()]


def main(argv: list[str] | None = None) -> int:
    """Print every broken link and exit with 1 if there are any."""
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    files = tracked_markdown()
    problems = broken_links(files)
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"{len(problems)} broken links in {len(files)} Markdown files")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
