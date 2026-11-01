"""SPEC 010: everything the Space does except the Gradio page and the GPU call.

Nothing here needs a GPU, so the checks run before any GPU time is requested and the tests run
anywhere. This module logs nothing: a scan's file name and content stay out of the Space logs.
"""

from __future__ import annotations

import math
from pathlib import Path

from project3d.inference.predictor import InvalidInput, Options, Predictor, load_checked

DISCLAIMER = "Research demo, not for clinical use"
RESULT_NAME = "segmentation.nii.gz"
SUFFIXES = (".nii", ".nii.gz")
MAX_FILE_MB = 500
MAX_VOXELS = 200_000_000  # above this, one scan could not finish inside MAX_GPU_SECONDS
OPTIONS = Options(tta=False, tile_step=0.5)  # measured on validation cases in SPEC 008

# the model resamples every scan to this spacing, so the work depends on it, not on the raw voxels
TARGET_SPACING_MM = (1.0, 0.78125, 0.78125)
BASE_GPU_SECONDS = 20
GPU_SECONDS_PER_MILLION_VOXELS = 0.5
MIN_GPU_SECONDS = 30
MAX_GPU_SECONDS = 120  # the daily quota without an account is 2 minutes (docs/deployment.md)

# The website reads the part before the colon, so these codes are part of the API.
INVALID = "INVALID_INPUT"
QUOTA = "QUOTA_EXCEEDED"
BUSY = "BUSY"
FAILED = "FAILED"
MESSAGES = {
    QUOTA: "The free GPU quota for today is used up. Try again tomorrow, sign in to Hugging Face for "
           "more quota, or use the gallery.",
    BUSY: "The GPU queue is full right now. Please try again in a few minutes.",
    FAILED: "The scan could not be processed. Check that it is a valid CT scan in NIfTI format.",
}


def check_upload(path: str | Path, max_mb: float = MAX_FILE_MB, max_voxels: int = MAX_VOXELS) -> None:
    """Refuse a bad upload from its name, size and header alone. Raises InvalidInput."""
    path = Path(path)
    if not path.name.lower().endswith(SUFFIXES):
        raise InvalidInput("Please upload a NIfTI file (.nii or .nii.gz).")
    size_mb = path.stat().st_size / 1e6
    if size_mb > max_mb:
        raise InvalidInput(f"This file is {size_mb:.0f} MB; the limit is {max_mb:g} MB.")
    load_checked(path, max_voxels)


def resampled_voxels(shape: tuple, spacing: tuple) -> float:
    """Voxel count after the model's resampling: the scan's physical size over the target voxel."""
    return math.prod(n * s / t for n, s, t in zip(shape[:3], spacing[:3], TARGET_SPACING_MM, strict=True))


def gpu_seconds(path: str | Path) -> int:
    """GPU time to request for this scan. It grows with the number of voxels the model will see."""
    img = load_checked(path, MAX_VOXELS)
    spacing = tuple(float(z) for z in img.header.get_zooms()[:3])
    wanted = BASE_GPU_SECONDS + GPU_SECONDS_PER_MILLION_VOXELS * resampled_voxels(img.shape, spacing) / 1e6
    return int(min(max(wanted, MIN_GPU_SECONDS), MAX_GPU_SECONDS))


def segment_file(model, path: str | Path, out_dir: str | Path, options: Options = OPTIONS) -> tuple[Path, dict]:
    """Segment one scan. The JSON summary holds no file name, so the website may store it."""
    dst = Path(out_dir) / RESULT_NAME
    summary = Predictor(model, options).predict_file(path, dst)
    return dst, summary | {"notice": DISCLAIMER}


def error_text(exc: Exception) -> str:
    """Turn any failure into ``CODE: message``. Other text is dropped, as it can hold file paths."""
    text = str(exc).lower()
    if isinstance(exc, InvalidInput):
        return f"{INVALID}: {exc}"
    if "quota" in text:
        return f"{QUOTA}: {MESSAGES[QUOTA]}"
    if "queue" in text or "no gpu" in text or "too many" in text:
        return f"{BUSY}: {MESSAGES[BUSY]}"
    return f"{FAILED}: {MESSAGES[FAILED]}"
