"""Post-processing chosen on the fold-0 validation cases (D-021)."""

from __future__ import annotations

import numpy as np
from scipy import ndimage

N_KIDNEYS = 2
CONNECTIVITY = np.ones((3, 3, 3), dtype=bool)  # 26-connected


def keep_largest_regions(seg: np.ndarray, n: int = N_KIDNEYS) -> np.ndarray:
    """Clear everything except the ``n`` largest connected foreground regions.

    Labels inside the kept regions do not change. A label map with ``n`` regions or
    fewer is returned as is.
    """
    regions, count = ndimage.label(seg > 0, structure=CONNECTIVITY)
    if count <= n:
        return seg
    sizes = np.bincount(regions.ravel())
    sizes[0] = 0  # background
    keep = np.argsort(sizes)[-n:]
    return np.where(np.isin(regions, keep), seg, 0).astype(seg.dtype)
