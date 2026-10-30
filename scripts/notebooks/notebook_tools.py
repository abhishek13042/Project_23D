"""Shared helpers for the notebook builders in this folder.

Each builder generates notebooks that embed the tested source files with
%%writefile cells, so Kaggle runs exactly the code the local tests cover.
tests/notebooks/test_notebooks.py fails if a notebook is stale; ``build_all.py``
regenerates them all.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NNUNET_VERSION = "2.8.1"
N_SHARDS = 4  # shard notebooks for the preprocessing (D-017)


def md_cell(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code_cell(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.splitlines(keepends=True)}


def writefile_cells(embedded: list[str]) -> list[dict]:
    cells = [md_cell("Write the project code (generated from the repository).")]
    for rel in embedded:
        body = (ROOT / rel).read_text(encoding="utf-8").replace("\r\n", "\n")
        cells.append(code_cell(f"%%writefile /kaggle/working/project23d/{rel}\n{body}"))
    return cells


def notebook(cells: list[dict]) -> dict:
    return {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
            "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3",
                                        "language": "python"},
                         "language_info": {"name": "python"}}}
