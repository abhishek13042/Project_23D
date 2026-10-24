"""Small NIfTI helpers shared by the tests."""

from pathlib import Path

import numpy as np


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


def features_csv(fx):
    """case_features.csv in the SPEC 002 format for the fake cases."""
    path = fx["tmp"] / "case_features.csv"
    lines = ["case_id,cohort,shape,spacing_mm,kidney_ml,tumor_ml,cyst_ml,has_tumor,has_cyst,size_bin"]
    for i, cid in enumerate(fx["ids"]):
        tumor = 4 * (i % 4) * 0.002
        size = ["none", "small", "medium", "large"][i % 4]
        lines.append(f"{cid},{'kits21' if i < 6 else 'kits23_new'},12x10x8,1x1x2,0.06,{tumor},"
                     f"{2 * (i % 2) * 0.002},{tumor > 0},{i % 2 == 1},{size}")
    path.write_text("\n".join(lines) + "\n")
    return path
