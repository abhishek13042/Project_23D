import hashlib
import json
import sys
import types
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "data"))
sys.path.insert(0, str(ROOT / "scripts" / "eval"))
sys.path.insert(0, str(ROOT / "scripts" / "report"))
sys.path.insert(0, str(ROOT / "scripts" / "training"))
sys.path.insert(0, str(ROOT / "tests"))

from helpers import make_seg, write_nifti  # noqa: E402


@pytest.fixture
def fake_kits(tmp_path):
    """Six fake cases (images + labels) and a matching checksum manifest."""
    ids = ["case_00001", "case_00002", "case_00299",
           "case_00400", "case_00401", "case_00588"]
    img_dir, seg_dir = tmp_path / "in" / "images", tmp_path / "in" / "segs"
    rows = ["case_id\tkind\tsize_bytes\tsha256\turl"]
    rng = np.random.default_rng(0)
    for i, cid in enumerate(ids):
        img = write_nifti(img_dir / f"{cid}.nii.gz", rng.normal(size=(10, 10, 6)).astype(np.float32))
        seg = write_nifti(seg_dir / f"{cid}.nii.gz", make_seg(tumor=5 * (i + 1), cyst=3 * (i % 2)))
        for kind, p in (("image", img), ("segmentation", seg)):
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            rows.append(f"{cid}\t{kind}\t{p.stat().st_size}\t{digest}\thttps://example.invalid/{p.name}")
    tsv = tmp_path / "manifest.tsv"
    tsv.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return {"ids": ids, "images": img_dir, "segs": seg_dir, "manifest": tsv, "tmp": tmp_path}


@pytest.fixture
def fake_eval(tmp_path):
    """Twelve cases: references, predictions (some imperfect) and a split.json."""
    rng = np.random.default_rng(3)
    ids = [f"case_{i:05d}" for i in range(12)]
    segs, preds, images = tmp_path / "segs", tmp_path / "pred", tmp_path / "images"
    roles = {}
    for i, cid in enumerate(ids):
        ref = make_seg(tumor=4 * (i % 4), cyst=2 * (i % 2), kidney=30, shape=(12, 10, 8))
        pred = ref.copy()
        flip = rng.random(ref.shape) < 0.02 * (i % 3)
        pred[flip & (ref == 0)] = 1
        write_nifti(segs / f"{cid}.nii.gz", ref)
        write_nifti(preds / f"{cid}.nii.gz", pred)
        write_nifti(images / f"{cid}.nii.gz", rng.normal(size=ref.shape).astype(np.float32))
        roles[cid] = "test" if i < 10 else "train"
    split = tmp_path / "split.json"
    split.write_text(json.dumps({"roles": roles, "fingerprint_sha256": "f" * 64}))
    return {"ids": ids, "segs": segs, "pred": preds, "images": images, "split": split,
            "roles": roles, "tmp": tmp_path}


@pytest.fixture
def fake_official(monkeypatch):
    """Stand-in for the kits23 package: Dice from our metrics, surface Dice = 0.9 x Dice."""
    import nibabel as nib

    from project3d.eval import metrics as m

    labels = types.ModuleType("kits23.configuration.labels")
    labels.HEC_NAME_LIST = list(m.HECS)
    labels.KITS_HEC_LABEL_MAPPING = dict(m.HECS)
    labels.HEC_SD_TOLERANCES_MM = dict(m.SD_TOLERANCES_MM)

    def compute_metrics_for_case(pred_path, ref_path):
        p = np.asanyarray(nib.load(pred_path).dataobj)
        r = np.asanyarray(nib.load(ref_path).dataobj)
        out = np.zeros((3, 2))
        for i, lab in enumerate(m.HECS.values()):
            d = m.overlap(m.region_mask(p, lab), m.region_mask(r, lab))["dice"]
            out[i] = d, 0.9 * d
        return out

    ev = types.ModuleType("kits23.evaluation.metrics")
    ev.compute_metrics_for_case = compute_metrics_for_case
    names = {"kits23": types.ModuleType("kits23"),
             "kits23.configuration": types.ModuleType("kits23.configuration"),
             "kits23.configuration.labels": labels,
             "kits23.evaluation": types.ModuleType("kits23.evaluation"),
             "kits23.evaluation.metrics": ev}
    names["kits23"].configuration = names["kits23.configuration"]
    names["kits23"].evaluation = names["kits23.evaluation"]
    names["kits23.configuration"].labels = labels
    names["kits23.evaluation"].metrics = ev
    for k, v in names.items():
        monkeypatch.setitem(sys.modules, k, v)
    from project3d.eval import official
    monkeypatch.setattr(official, "official_version", lambda: "fake")
    return labels
