import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "data"))


def write_nifti(path: Path, arr: np.ndarray, spacing=(1.0, 1.0, 2.0)) -> Path:
    import nibabel as nib

    path.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(arr, np.diag([*spacing, 1.0])), str(path))
    return path


def make_seg(tumor: int = 0, cyst: int = 0, kidney: int = 20, shape=(10, 10, 6)) -> np.ndarray:
    """Tiny label volume with the given voxel counts per class."""
    flat = np.zeros(int(np.prod(shape)), dtype=np.uint8)
    flat[:kidney] = 1
    flat[kidney:kidney + tumor] = 2
    flat[kidney + tumor:kidney + tumor + cyst] = 3
    return flat.reshape(shape)


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
