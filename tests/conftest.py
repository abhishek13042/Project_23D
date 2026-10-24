import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "data"))
sys.path.insert(0, str(ROOT / "scripts" / "eval"))
sys.path.insert(0, str(ROOT / "scripts" / "report"))
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
