import ast
import json

import build_kaggle_notebook as b


def test_notebook_is_up_to_date():
    assert b.NOTEBOOK.read_text(encoding="utf-8") == b.render(), (
        "notebook is stale: run python scripts/data/build_kaggle_notebook.py")


def test_code_cells_are_valid_python():
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


def test_embedded_files_match_repository():
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
