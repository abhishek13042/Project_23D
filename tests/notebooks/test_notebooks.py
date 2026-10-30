import ast
import json

import pytest

import build_eval_notebook
import build_prepare_notebook
import build_preprocess_notebook
import build_stage_notebook
import build_train_notebook

BUILDERS = pytest.mark.parametrize(
    "b", [build_stage_notebook, build_prepare_notebook, build_preprocess_notebook, build_train_notebook,
          build_eval_notebook],
    ids=["00_stage_data", "01_prepare_data", "01b_preprocess", "02_train", "03_evaluate"])


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


def test_every_stage_shard_notebook_is_up_to_date():
    for k in range(1, build_stage_notebook.N_SHARDS + 1):
        nb = build_stage_notebook.path(k)
        assert nb.read_text(encoding="utf-8") == build_stage_notebook.render(k), (
            f"notebook is stale: run python {build_stage_notebook.__file__}")
        sources = ["".join(c["source"]) for c in json.loads(nb.read_text(encoding="utf-8"))["cells"]]
        assert any(s.startswith(f"SHARD = {k}\n") for s in sources)


def test_every_preprocess_shard_notebook_is_up_to_date():
    for k in range(1, build_preprocess_notebook.N_SHARDS + 1):
        nb = build_preprocess_notebook.path(k)
        assert nb.read_text(encoding="utf-8") == build_preprocess_notebook.render(k), (
            f"notebook is stale: run python {build_preprocess_notebook.__file__}")
        sources = ["".join(c["source"]) for c in json.loads(nb.read_text(encoding="utf-8"))["cells"]]
        assert any(s.startswith(f"SHARD = {k}\n") for s in sources)


def test_pilot_notebook_is_up_to_date():
    for run, cfg in build_train_notebook.RUNS.items():
        assert cfg["path"].read_text(encoding="utf-8") == build_train_notebook.render(run), (
            f"notebook is stale: run python {build_train_notebook.__file__}")
        sources = "".join("".join(c["source"]) for c in build_train_notebook.build(run)["cells"])
        assert f'TRAINER = "{cfg["trainer"]}"' in sources
