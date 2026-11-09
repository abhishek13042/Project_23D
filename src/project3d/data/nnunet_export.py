"""Build the nnU-Net v2 raw dataset folder for KiTS23 (SPEC 002).

Mirrors nnU-Net's own ``dataset_conversion/Dataset220_KiTS2023.py``: region-based
labels (kidney+masses, masses, tumor), ``regions_class_order`` (1, 3, 2) and the
``NibabelIOWithReorient`` reader. Two differences, both deliberate:

- only train and validation cases go into ``imagesTr``/``labelsTr``, so the
  locked test cases cannot influence nnU-Net's planning or normalization;
- files are symlinked by default instead of copied, so no extra disk is used.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

DATASET_ID = 220
DATASET_NAME = "KiTS2023"
DATASET_JSON = {
    "channel_names": {"0": "CT"},
    "labels": {"background": 0, "kidney": [1, 2, 3], "masses": [2, 3], "tumor": 2},
    "regions_class_order": [1, 3, 2],
    "overwrite_image_reader_writer": "NibabelIOWithReorient",
    "name": DATASET_NAME,
    "release": "0.1.4",
    "reference": "https://github.com/neheller/kits23",
    "licence": "CC BY-NC-SA 4.0 (KiTS23 data terms)",
    "description": "KiTS23 train+val cases only; locked test cases excluded (D-012)",
}


def dataset_folder_name(dataset_id: int = DATASET_ID, name: str = DATASET_NAME) -> str:
    """nnU-Net's folder name for a dataset, e.g. ``Dataset220_KiTS2023``."""
    return f"Dataset{dataset_id:03d}_{name}"


def _file_ending(paths: list[Path]) -> str:
    endings = {".nii.gz" if p.name.endswith(".nii.gz") else p.suffix for p in paths}
    if len(endings) != 1:
        raise ValueError(f"mixed file endings {sorted(endings)}; nnU-Net needs one")
    return endings.pop()


def _place(src: Path, dst: Path, mode: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    if mode == "symlink":
        os.symlink(src.resolve(), dst)
    elif mode == "copy":
        shutil.copy2(src, dst)
    else:
        raise ValueError(f"unknown mode {mode!r}")


def build_raw_dataset(roles: dict[str, str], images: dict[str, Path], segs: dict[str, Path],
                      raw_root: str | Path, mode: str = "symlink",
                      dataset_id: int = DATASET_ID) -> Path:
    """Create ``<raw_root>/DatasetXXX_KiTS2023`` and return its path.

    ``imagesTr``/``labelsTr`` hold train+val cases; ``imagesTs`` holds test images.
    Test labels are never placed in the nnU-Net folder.
    """
    trainval = sorted(c for c, r in roles.items() if r in ("train", "val"))
    test = sorted(c for c, r in roles.items() if r == "test")
    missing = [c for c in roles if c not in images or (c in trainval and c not in segs)]
    if missing:
        raise ValueError(f"no verified file for {len(missing)} cases, e.g. {missing[:3]}")

    ending = _file_ending([images[c] for c in roles] + [segs[c] for c in trainval])
    out = Path(raw_root) / dataset_folder_name(dataset_id)
    if out.exists():
        shutil.rmtree(out)
    for c in trainval:
        _place(images[c], out / "imagesTr" / f"{c}_0000{ending}", mode)
        _place(segs[c], out / "labelsTr" / f"{c}{ending}", mode)
    for c in test:
        _place(images[c], out / "imagesTs" / f"{c}_0000{ending}", mode)

    meta = dict(DATASET_JSON, numTraining=len(trainval), file_ending=ending)
    (out / "dataset.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return out


def check_no_test_leak(dataset_dir: str | Path, roles: dict[str, str]) -> None:
    """Fail if any test case appears in imagesTr or labelsTr."""
    test = {c for c, r in roles.items() if r == "test"}
    for sub in ("imagesTr", "labelsTr"):
        for p in (Path(dataset_dir) / sub).iterdir():
            if p.name[:10] in test:
                raise AssertionError(f"test case {p.name[:10]} found in {sub}")
