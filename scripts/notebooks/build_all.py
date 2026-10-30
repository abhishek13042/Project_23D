"""Regenerate every notebook in notebooks/. Run this after changing an embedded file."""

from __future__ import annotations

import runpy
from pathlib import Path

for builder in sorted(Path(__file__).parent.glob("build_*_notebook.py")):
    runpy.run_path(str(builder), run_name="__main__")
