# tests

The pytest suite. It needs no GPU and no KiTS23 data: it builds small fake scans on the fly.

```bash
.venv/Scripts/python -m pytest -q
```

The folders mirror [src/](../src/README.md) and [scripts/](../scripts/README.md): `data/`, `eval/`,
`training/`, `inference/`, `report/`, `gallery/`, `space/` and `ops/`. Two more files are shared:

- `conftest.py`: fixtures such as `fake_kits` (a tiny KiTS23-like folder) and `fake_eval`.
- `helpers.py`: small functions for writing fake NIfTI files.

`notebooks/test_notebooks.py` fails if a notebook in [notebooks/](../notebooks/README.md) is out of
date with the scripts it embeds. Tests that need nnU-Net or PyTorch skip themselves when those are
not installed.
