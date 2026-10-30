"""Qualitative figures for SPEC 005: orthogonal overlays and a box plot.

Reference contours are drawn solid, predictions dashed. CT is shown with a
soft-tissue window (level 40, width 400 HU) for display only.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

WINDOW = (-160.0, 240.0)
COLORS = {"kidney_and_mass": "#2ca02c", "mass": "#ff7f0e", "tumor": "#d62728"}
LABELS = {"kidney_and_mass": (1, 2, 3), "mass": (2, 3), "tumor": (2,)}


def focus_index(ref: np.ndarray) -> tuple[int, int, int]:
    """Voxel to centre the views on: largest mass slice, else kidney, else the middle."""
    for labels in ((2, 3), (1, 2, 3)):
        m = np.isin(ref, labels)
        if m.any():
            k = int(np.argmax(m.sum(axis=(1, 2))))
            j = int(np.argmax(m.sum(axis=(0, 2))))
            i = int(np.argmax(m.sum(axis=(0, 1))))
            return k, j, i
    return tuple(s // 2 for s in ref.shape)


def overlay_figure(image: np.ndarray, ref: np.ndarray, pred: np.ndarray,
                   spacing_mm: tuple[float, float, float], title: str, out_path: Path) -> Path:
    """Axial, coronal and sagittal views through the focus voxel.

    Arrays are in file order (axis 0 = slices, as in KiTS23 NIfTI files).
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    k, j, i = focus_index(ref)
    s0, s1, s2 = spacing_mm
    # (name, slice, pixel aspect, image origin): "upper" puts the spine at the bottom
    # of the axial view, as radiologists read it.
    views = [("axial", np.s_[k, :, :], s1 / s2, "upper"), ("coronal", np.s_[:, j, :], s0 / s2, "lower"),
             ("sagittal", np.s_[:, :, i], s0 / s1, "lower")]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.4))
    for ax, (name, sl, aspect, origin) in zip(axes, views, strict=True):
        ax.imshow(np.clip(image[sl], *WINDOW), cmap="gray", aspect=aspect, origin=origin)
        for region, labels in LABELS.items():
            for arr, style in ((ref, "solid"), (pred, "dashed")):
                m = np.isin(arr[sl], labels).astype(float)
                if m.any():
                    ax.contour(m, levels=[0.5], colors=COLORS[region], linestyles=style,
                               linewidths=1, origin=origin)
        ax.set_title(name)
        ax.axis("off")
    fig.suptitle(f"{title}   (solid = reference, dashed = prediction; "
                 f"green kidney+mass, orange mass, red tumor)", fontsize=9)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
    return out_path


def boxplot_by_group(rows: list[dict], factor: str, metric: str, order: list[str],
                     out_path: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    groups = [g for g in order if any(str(r[factor]) == g for r in rows)]
    data = [[r[metric] for r in rows if str(r[factor]) == g] for g in groups]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.boxplot(data, showmeans=True)
    ax.set_xticks(range(1, len(groups) + 1), [f"{g}\n(n={len(d)})" for g, d in zip(groups, data, strict=True)])
    ax.set_ylabel(metric)
    ax.set_xlabel(factor)
    ax.set_ylim(-0.02, 1.02)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
    return out_path
