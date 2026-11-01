"""SPEC 008: package the trained model for release, with a checksum for every file.

Example (Kaggle)::

    python scripts/release/export_model.py \
        --trainer-dir .../nnUNetTrainer_100epochs_kaggle__nnUNetPlans__3d_fullres \
        --out-dir /kaggle/working/model_package

The folder holds everything nnU-Net needs to load the model, plus the trainer class, the
post-processing rule and the model card. It is uploaded to Hugging Face as it is.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from project3d.eval.postprocess import N_KIDNEYS
from project3d.inference.predictor import CHECKPOINT, TRAINER_FILE

CHECKSUMS = "checksums.json"
MODEL_CARD = ROOT / "reports/release/model_card.md"
TRAINER_SOURCE = ROOT / "src/project3d/training/nnunet_trainer.py"
FRONT_MATTER = """---
license: cc-by-nc-sa-4.0
library_name: nnunet
pipeline_tag: image-segmentation
tags:
  - medical-imaging
  - ct
  - kidney
  - segmentation
  - kits23
---

"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def model_card_text(card: Path = MODEL_CARD) -> str:
    """The model card for Hugging Face. Links into this repository would be dead there."""
    body = card.read_text(encoding="utf-8").replace("\r\n", "\n")
    return FRONT_MATTER + re.sub(r"\[([^\]]+)\]\((?:\.\./|docs/|reports/)[^)]*\)", r"\1", body)


def export(trainer_dir: Path, out_dir: Path) -> dict:
    sources = {"plans.json": trainer_dir / "plans.json", "dataset.json": trainer_dir / "dataset.json",
               f"fold_0/{CHECKPOINT}": trainer_dir / "fold_0" / CHECKPOINT, TRAINER_FILE: TRAINER_SOURCE}
    missing = [str(p) for p in sources.values() if not p.exists()]
    if missing:
        raise FileNotFoundError(f"missing {missing}")
    (out_dir / "fold_0").mkdir(parents=True, exist_ok=True)
    for name, src in sources.items():
        shutil.copy(src, out_dir / name)
    rule = {"rule": "keep the largest connected foreground regions", "n_regions": N_KIDNEYS,
            "connectivity": 26, "decision": "D-021"}
    (out_dir / "postprocessing.json").write_text(json.dumps(rule, indent=2), encoding="utf-8")
    (out_dir / "README.md").write_text(model_card_text(), encoding="utf-8", newline="\n")
    files = sorted(p for p in out_dir.rglob("*") if p.is_file() and p.name != CHECKSUMS)
    record = {p.relative_to(out_dir).as_posix(): {"sha256": sha256(p), "bytes": p.stat().st_size} for p in files}
    (out_dir / CHECKSUMS).write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def verify(out_dir: Path) -> list[str]:
    """Names of the files that are missing or don't match their recorded checksum."""
    record = json.loads((out_dir / CHECKSUMS).read_text(encoding="utf-8"))
    return [name for name, entry in record.items()
            if not (out_dir / name).exists() or sha256(out_dir / name) != entry["sha256"]]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--trainer-dir", type=Path, required=True, help="folder holding plans.json and fold_0/")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args(argv)
    try:
        record = export(args.trainer_dir, args.out_dir)
    except FileNotFoundError as exc:
        print(f"STOP: {exc}")
        return 1
    print(f"packaged {len(record)} files into {args.out_dir}")
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
