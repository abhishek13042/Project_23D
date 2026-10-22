"""Generate notebooks/01_prepare_data.ipynb from the tested source files.

The notebook embeds the SPEC 002 code with %%writefile cells, so Kaggle runs
exactly the code the local tests cover. Re-run this script after any change to
the embedded files; tests/data/test_notebook.py fails if the notebook is stale.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "notebooks" / "01_prepare_data.ipynb"
EMBEDDED = [
    "src/project3d/__init__.py",
    "src/project3d/data/__init__.py",
    "src/project3d/data/manifest.py",
    "src/project3d/data/features.py",
    "src/project3d/data/split.py",
    "src/project3d/data/nnunet_export.py",
    "scripts/data/prepare_kits23.py",
    "data/sources/kits23_v0.1.4_files.tsv",
]
NNUNET_VERSION = "2.8.1"

INTRO = """# SPEC 002 — Prepare KiTS23 for nnU-Net (Kaggle, CPU only)

This notebook verifies the data, makes the locked split, and runs nnU-Net's
planning and preprocessing. **It uses no GPU quota.**

**Before running**
1. *Add Input*: attach your two private datasets (KiTS23 images and segmentations).
2. *Settings*: **Accelerator = None** (CPU), **Internet = On** (to install nnU-Net).
3. Click **Save Version → Save & Run All (Commit)**. Don't run it interactively
   first: the commit run does the work once, in the background, for up to 12 hours.

**After it finishes**, open the version's *Output* tab and click **New Dataset**.
Name it `kits23-nnunet-preprocessed` and keep it **Private**. The training
notebook (SPEC 003) uses that dataset.

The code cells below are generated from the project repository
(`scripts/data/build_kaggle_notebook.py`). Edit the repository, not this notebook."""

ENV_CHECK = """# Step 0 - what machine did Kaggle give us?
import os, shutil, sys, platform, json, time
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

PREPROCESS = """# Step 3 - nnU-Net fingerprint, plan and preprocess (3d_fullres only).
# CPU-heavy: expect roughly 1-4 hours. If the kernel dies from memory, set
# NUM_PROCESSES = 2 and run again.
NUM_PROCESSES = 3
t = time.time()
sh(["nnUNetv2_plan_and_preprocess", "-d", "220", "-c", "3d_fullres",
    "-np", str(NUM_PROCESSES), "--verify_dataset_integrity"])
PRE = f"{os.environ['nnUNet_preprocessed']}/Dataset220_KiTS2023"
shutil.copy(f"{OUT}/splits_final.json", f"{PRE}/splits_final.json")  # our locked fold 0
preprocess_hours = (time.time() - t) / 3600
print(f"preprocessing took {preprocess_hours:.2f} h")"""

SAVE = """# Step 4 - move the preprocessed data into the saved output (limit about 20 GB).
from pathlib import Path
def folder_gb(path):
    return sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file()) / 1e9
size_gb = folder_gb(PRE)
print(f"preprocessed size: {size_gb:.1f} GB")
plans = json.load(open(f"{PRE}/nnUNetPlans.json"))
fullres = plans["configurations"]["3d_fullres"]
print("3d_fullres patch size", fullres["patch_size"], "| spacing", fullres["spacing"],
      "| batch size", fullres["batch_size"])
saved = size_gb <= 19.0
if saved:
    shutil.move(PRE, "/kaggle/working/nnUNet_preprocessed/Dataset220_KiTS2023")
else:
    print("TOO BIG for /kaggle/working. Only the reports are saved. Tell Claude the size above;"
          " the fallback is 3d_lowres or preprocessing inside the training notebook.")
    os.makedirs("/kaggle/working/nnUNet_preprocessed/Dataset220_KiTS2023", exist_ok=True)
    for name in ("dataset.json", "nnUNetPlans.json", "dataset_fingerprint.json", "splits_final.json"):
        shutil.copy(f"{PRE}/{name}", f"/kaggle/working/nnUNet_preprocessed/Dataset220_KiTS2023/{name}")
record = {
    "spec": "SPEC 002", "nnunetv2": md.version("nnunetv2"), "torch": md.version("torch"),
    "python": sys.version.split()[0], "cpus": os.cpu_count(),
    "split_fingerprint_sha256": split_record["fingerprint_sha256"],
    "split_totals": split_record["summary"]["total"],
    "preprocess_hours": round(preprocess_hours, 2), "preprocessed_gb": round(size_gb, 2),
    "preprocessed_saved": saved, "total_hours": round((time.time() - T0) / 3600, 2),
    "fullres_patch_size": fullres["patch_size"], "fullres_spacing": fullres["spacing"],
}
json.dump(record, open(f"{OUT}/run_record.json", "w"), indent=2)
print(json.dumps(record, indent=1))
print("DONE. Copy the printed run_record above back to Claude.")"""


def md_cell(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code_cell(text: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.splitlines(keepends=True)}


def build() -> dict:
    cells = [md_cell(INTRO), code_cell(ENV_CHECK)]
    cells.append(md_cell("Write the project code (generated from the repository)."))
    for rel in EMBEDDED:
        body = (ROOT / rel).read_text(encoding="utf-8").replace("\r\n", "\n")
        cells.append(code_cell(f"%%writefile /kaggle/working/project23d/{rel}\n{body}"))
    cells += [code_cell(INSTALL), code_cell(PREPARE), code_cell(PREPROCESS), code_cell(SAVE)]
    return {"cells": cells, "nbformat": 4, "nbformat_minor": 5,
            "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3",
                                        "language": "python"},
                         "language_info": {"name": "python"}}}


def render() -> str:
    return json.dumps(build(), indent=1, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    NOTEBOOK.parent.mkdir(parents=True, exist_ok=True)
    NOTEBOOK.write_text(render(), encoding="utf-8", newline="\n")
    print(f"wrote {NOTEBOOK}")
