"""Generate notebooks/01_prepare_data.ipynb from the tested source files.

The notebook embeds the SPEC 002 code with %%writefile cells, so Kaggle runs
exactly the code the local tests cover. Re-run this script after any change to
the embedded files; tests/notebooks/test_notebooks.py fails if the notebook is stale.
"""

from __future__ import annotations

import json

from notebook_tools import N_SHARDS, NNUNET_VERSION, ROOT, code_cell, md_cell, notebook, writefile_cells

NOTEBOOK = ROOT / "notebooks" / "01_prepare_data.ipynb"
EMBEDDED = [
    "src/project3d/__init__.py",
    "src/project3d/data/__init__.py",
    "src/project3d/data/manifest.py",
    "src/project3d/data/features.py",
    "src/project3d/data/split.py",
    "src/project3d/data/nnunet_export.py",
    "src/project3d/data/preprocess_plan.py",
    "scripts/data/prepare_kits23.py",
    "data/sources/kits23_v0.1.4_files.tsv",
]

INTRO = """# SPEC 002 — Prepare KiTS23 for nnU-Net (Kaggle, CPU only)

This notebook verifies the data, makes the locked split, and runs nnU-Net's
planning. The preprocessing itself runs in four shard notebooks afterwards
(`01b_preprocess_1..4`, D-017). **It uses no GPU quota.**

**Before running**
1. *Add Input*: attach the outputs of the three staging notebooks `kits23-stage-1..3`
   (`notebooks/00_stage_data_*.ipynb`, D-015).
2. *Settings*: **Accelerator = None** (CPU), **Internet = On** (to install nnU-Net).
3. Click **Save Version → Save & Run All (Commit)**. Don't run it interactively
   first: the commit run does the work once, in the background, for up to 12 hours.

**After it finishes**, run the four shard notebooks with this notebook's output
attached. The training notebook (SPEC 003) attaches this output and all four shards.

The code cells below are generated from the project repository
(`scripts/notebooks/build_prepare_notebook.py`). Edit the repository, not this notebook."""

ENV_CHECK = """# Step 0 - what machine did Kaggle give us?
import os, shutil, sys, platform, json, time
from pathlib import Path
print("python", sys.version.split()[0], "|", platform.platform())
print("CPUs:", os.cpu_count())
try:
    print("RAM GB:", round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9, 1))
except (ValueError, AttributeError):
    pass
for d in ("/kaggle/working", "/tmp"):
    u = shutil.disk_usage(d)
    print(f"{d}: {u.free / 1e9:.0f} GB free of {u.total / 1e9:.0f} GB")
WORK = "/kaggle/working/project23d"
for sub in ("src/project3d/data", "scripts/data", "data/sources"):
    os.makedirs(f"{WORK}/{sub}", exist_ok=True)
T0 = time.time()"""

INSTALL = f"""# Step 1 - install nnU-Net (pinned version, recorded in run_record.json)
import subprocess, importlib.metadata as md
def sh(cmd):
    print("$", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
try:
    print("torch before install:", md.version("torch"))
except md.PackageNotFoundError:
    print("torch not preinstalled")
sh([sys.executable, "-m", "pip", "install", "-q", "nnunetv2=={NNUNET_VERSION}", "nibabel"])
print("nnunetv2", md.version("nnunetv2"), "| torch", md.version("torch"))"""

PREPARE = """# Step 2 - verify every file, measure each case, make the locked split,
# and build the nnU-Net raw folder (symlinks: no extra disk).
os.environ["nnUNet_raw"] = "/tmp/nnUNet_raw"
os.environ["nnUNet_preprocessed"] = "/tmp/nnUNet_preprocessed"
os.environ["nnUNet_results"] = "/kaggle/working/nnUNet_results"
OUT = "/kaggle/working/spec002"
sh([sys.executable, f"{WORK}/scripts/data/prepare_kits23.py",
    "--input-root", "/kaggle/input",
    "--manifest", f"{WORK}/data/sources/kits23_v0.1.4_files.tsv",
    "--out-dir", OUT, "--raw-root", os.environ["nnUNet_raw"]])
split_record = json.load(open(f"{OUT}/split.json"))
print(json.dumps(split_record["summary"], indent=1))"""

PREPROCESS = """# Step 3 - nnU-Net fingerprint and plan (3d_fullres), no preprocessing here.
# The preprocessed data is about 50 GB, more than one notebook can save (about
# 20 GB), so four shard notebooks (01b_preprocess_1..4) preprocess a quarter each
# (D-017). This step writes the shard plan they follow. Expect about 1.5 hours.
import csv
sys.path.insert(0, f"{WORK}/src")
from project3d.data import preprocess_plan
t = time.time()
sh(["nnUNetv2_plan_and_preprocess", "-d", "220", "-c", "3d_fullres",
    "--verify_dataset_integrity", "--no_pp"])
PRE = f"{os.environ['nnUNet_preprocessed']}/Dataset220_KiTS2023"
plans = json.load(open(f"{PRE}/nnUNetPlans.json"))
fullres = plans["configurations"]["3d_fullres"]
print("3d_fullres patch size", fullres["patch_size"], "| spacing", fullres["spacing"],
      "| batch size", fullres["batch_size"])
mvox = preprocess_plan.case_mvox(list(csv.DictReader(open(f"{OUT}/case_features.csv"))),
                                 tuple(fullres["spacing"]))
shard_plan = preprocess_plan.write_plan(Path(f"{PRE}/shard_plan.json"), split_record["roles"], mvox,
                                        n_shards=N_SHARDS)
splits = preprocess_plan.filter_splits(json.load(open(f"{OUT}/splits_final.json")),
                                       list(shard_plan["excluded"]))
json.dump(splits, open(f"{PRE}/splits_final.json", "w"), indent=2)  # our locked fold 0
print("left out of training (too large for one Kaggle worker):", shard_plan["excluded"])
print("cases per shard:", [len(s) for s in shard_plan["shards"]], "| Mvox per shard:", shard_plan["shard_mvox"])
plan_hours = (time.time() - t) / 3600
print(f"planning took {plan_hours:.2f} h")"""

SAVE = """# Step 4 - save the plans, the shard plan, our splits and the reference labels
# (gt_segmentations, used by nnU-Net's final validation). Real copies, not symlinks.
DEST = Path("/kaggle/working/nnUNet_preprocessed/Dataset220_KiTS2023")
DEST.mkdir(parents=True, exist_ok=True)
for name in ("dataset.json", "nnUNetPlans.json", "dataset_fingerprint.json", "splits_final.json",
             "shard_plan.json"):
    shutil.copy(f"{PRE}/{name}", DEST / name)
labels = Path(os.environ["nnUNet_raw"]) / "Dataset220_KiTS2023" / "labelsTr"
(DEST / "gt_segmentations").mkdir(exist_ok=True)
for f in sorted(labels.iterdir()):
    shutil.copy(f, DEST / "gt_segmentations" / f.name)
fold0 = splits[0]
record = {
    "spec": "SPEC 002", "nnunetv2": md.version("nnunetv2"), "torch": md.version("torch"),
    "python": sys.version.split()[0], "cpus": os.cpu_count(),
    "split_fingerprint_sha256": split_record["fingerprint_sha256"],
    "split_totals": split_record["summary"]["total"],
    "fold0_train": len(fold0["train"]), "fold0_val": len(fold0["val"]),
    "excluded": shard_plan["excluded"], "n_shards": N_SHARDS, "shard_mvox": shard_plan["shard_mvox"],
    "plan_hours": round(plan_hours, 2), "total_hours": round((time.time() - T0) / 3600, 2),
    "fullres_patch_size": fullres["patch_size"], "fullres_spacing": fullres["spacing"],
    "fullres_batch_size": fullres["batch_size"],
}
json.dump(record, open(f"{OUT}/run_record.json", "w"), indent=2)
print(json.dumps(record, indent=1))
print("DONE. Next: the four shard notebooks (01b_preprocess_1..4) with this output attached.")"""


def build() -> dict:
    return notebook([md_cell(INTRO), code_cell(ENV_CHECK + f"\nN_SHARDS = {N_SHARDS}"), *writefile_cells(EMBEDDED),
                     code_cell(INSTALL), code_cell(PREPARE), code_cell(PREPROCESS), code_cell(SAVE)])


def render() -> str:
    return json.dumps(build(), indent=1, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    NOTEBOOK.parent.mkdir(parents=True, exist_ok=True)
    NOTEBOOK.write_text(render(), encoding="utf-8", newline="\n")
    print(f"wrote {NOTEBOOK}")
