import ast
import json

import pytest

import build_eval_notebook
import build_kaggle_notebook

BUILDERS = pytest.mark.parametrize("b", [build_kaggle_notebook, build_eval_notebook],
                                   ids=["01_prepare_data", "03_evaluate"])


@BUILDERS
def test_notebook_is_up_to_date(b):
    assert b.NOTEBOOK.read_text(encoding="utf-8") == b.render(), (
        f"notebook is stale: run python {b.__file__}")


@BUILDERS
def test_code_cells_are_valid_python(b):
    nb = json.loads(b.render())
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        if src.startswith("%%writefile"):
            header, body = src.split("\n", 1)
            assert header.startswith("%%writefile /kaggle/working/project23d/")
            if header.endswith(".py"):
                ast.parse(body)
        else:
            ast.parse(src)


@BUILDERS
def test_embedded_files_match_repository(b):
    nb = json.loads(b.render())
    written = {}
    for cell in nb["cells"]:
        src = "".join(cell["source"])
        if src.startswith("%%writefile"):
            header, body = src.split("\n", 1)
            written[header.split("project23d/", 1)[1]] = body
    assert sorted(written) == sorted(b.EMBEDDED)
    for rel, body in written.items():
        assert body == (b.ROOT / rel).read_text(encoding="utf-8").replace("\r\n", "\n")


def test_eval_notebook_embeds_every_eval_module():
    """Everything evaluate.py / case_analysis.py import must be written on Kaggle."""
    root = build_eval_notebook.ROOT
    for py in (root / "src/project3d/eval").glob("*.py"):
        assert py.relative_to(root).as_posix() in build_eval_notebook.EMBEDDED
