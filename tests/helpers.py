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
