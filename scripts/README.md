# scripts: command-line entry points

One folder per stage of the project. Each script has a `--help`, and the docstring at the top of
each file shows an example. Heavy steps run on Kaggle through the generated
[notebooks](../notebooks/README.md).

| Folder | Scripts | Stage |
|---|---|---|
| `data/` | `stage_kits23.py`, `prepare_kits23.py`, `preprocess_shard.py` | Download and check KiTS23, split it, preprocess it |
| `training/` | `train.py` | Train nnU-Net within one Kaggle session's time budget, resuming across sessions |
| `eval/` | `postprocess.py`, `evaluate.py`, `case_analysis.py` | Score the locked test set and analyse where the model fails |
| `report/` | `build_report.py` | Build [reports/evaluation/results.md](../reports/evaluation/results.md) from the saved records |
| `release/` | `export_model.py` | Package the trained model with a checksum for every file |
| `inference/` | `predict.py`, `benchmark.py` | Segment one scan, and compare inference settings |
| `gallery/` | `select_cases.py`, `build_gallery.py` | Pick the public sample cases by a fixed rule and crop them |
| `space/` | `package_space.py` | Assemble the Hugging Face Space folder |
| `ops/` | `health_check.py`, `scan_history.py` | Check the live site, and scan the git history for data or secrets |
| `notebooks/` | `build_all.py` and one builder per notebook | Generate the Kaggle notebooks from these scripts |

Each script puts `src/` on `sys.path` itself, on purpose, so it runs on Kaggle as a plain file.
After changing a script that a notebook embeds, run:

```bash
.venv/Scripts/python scripts/notebooks/build_all.py
```
