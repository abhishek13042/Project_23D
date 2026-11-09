"""SPEC 008: the predictor used by the command line, the benchmark and the live service.

``Predictor`` holds everything that must stay true for every caller: input checks, the
post-processing rule from evaluation (D-021), the geometry check and the region volumes.
``NnUNetModel`` is the only part that needs nnU-Net and a GPU, so the rest is tested locally
with a fake model.
"""

from __future__ import annotations

import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

import numpy as np

from project3d.data import features
from project3d.eval.postprocess import keep_largest_regions

if TYPE_CHECKING:
    from nibabel.spatialimages import SpatialImage

CHECKPOINT = "checkpoint_final.pth"
TRAINER_FILE = "project23d_trainer.py"  # the name it gets inside nnU-Net's package
LABELS = {"kidney": 1, "tumor": 2, "cyst": 3}
MAX_VOXELS = 300_000_000  # about 512 x 512 x 1150, larger than any scan used in training
SPACING_RANGE_MM = (0.1, 20.0)


class InvalidInput(ValueError):
    """The scan can't be used. The message is written for the person who supplied it."""


@dataclass(frozen=True)
class Options:
    """Inference settings. The defaults are the setting used in the evaluation (SPEC 004)."""

    tta: bool = True
    tile_step: float = 0.5
    device: str = "cuda"

    def __post_init__(self) -> None:
        if not 0 < self.tile_step <= 1:
            raise ValueError(f"tile_step must be in (0, 1], got {self.tile_step}")


class Model(Protocol):
    """What ``Predictor`` needs from a model. Tests use a fake one."""

    def read(self, path: Path) -> tuple[np.ndarray, dict]:
        """Load a scan as the model expects it, with its geometry properties."""
        ...

    def predict(self, data: np.ndarray, properties: dict) -> np.ndarray:
        """Return the label map for a loaded scan."""
        ...

    def write(self, seg: np.ndarray, path: Path, properties: dict) -> None:
        """Save a label map with the geometry of the original scan."""
        ...


def check_header(shape: tuple, spacing: tuple, max_voxels: int = MAX_VOXELS) -> None:
    """Raise InvalidInput for a scan that isn't 3D, has bad spacing or is too large."""
    if len(shape) != 3:
        raise InvalidInput(f"Expected a 3D scan, but this file has {len(shape)} dimensions {tuple(shape)}.")
    low, high = SPACING_RANGE_MM
    if not all(np.isfinite(s) and low <= s <= high for s in spacing[:3]):
        raise InvalidInput(f"Voxel spacing {tuple(float(s) for s in spacing[:3])} mm is invalid: "
                           f"each axis must be between {low} and {high} mm.")
    voxels = int(np.prod([int(n) for n in shape]))
    if voxels > max_voxels:
        raise InvalidInput(f"This scan has {voxels:,} voxels; the limit is {max_voxels:,}.")


def load_checked(path: str | Path, max_voxels: int = MAX_VOXELS) -> SpatialImage:
    """Open a NIfTI file and check its header. Voxel data is not read."""
    import nibabel as nib

    try:
        img = nib.load(str(path))
    except Exception as exc:
        raise InvalidInput("The file could not be read as a NIfTI scan.") from exc
    check_header(img.shape, img.header.get_zooms(), max_voxels)
    return img


def region_volumes(seg: np.ndarray, spacing: tuple) -> dict[str, float]:
    """Volume in mL of each region. One mL is 1000 cubic millimetres."""
    voxel_ml = float(np.prod([float(s) for s in spacing[:3]])) / 1000
    return {f"{name}_ml": round(float((seg == label).sum()) * voxel_ml, 3) for name, label in LABELS.items()}


class Predictor:
    """Runs a model on one scan with the same checks and post-processing for every caller."""

    def __init__(self, model: Model, options: Options | None = None):
        self.model = model
        self.options = options or Options()

    def predict_file(self, src: str | Path, dst: str | Path) -> dict[str, Any]:
        """Segment one scan, write the labels to ``dst`` and return a summary.

        The summary has no file names, so a caller can log or store it.
        """
        src, dst = Path(src), Path(dst)
        img = load_checked(src)
        data, properties = self.model.read(src)
        seg = keep_largest_regions(np.asarray(self.model.predict(data, properties)).astype(np.uint8))
        self.model.write(seg, dst, properties)
        why = features.geometry_mismatch(dst, src)
        if why:
            raise RuntimeError(f"output does not match the input geometry ({why})")
        spacing = tuple(float(z) for z in img.header.get_zooms()[:3])
        return {"shape": [int(n) for n in img.shape], "spacing_mm": list(spacing),
                "voxel_count": int(np.prod([int(n) for n in img.shape])),
                "volumes_ml": region_volumes(seg, spacing), "options": asdict(self.options),
                "postprocessing": "keep the two largest foreground regions"}


def install_trainer(trainer_file: Path, variants_dir: Path | None = None) -> Path:
    """Copy our trainer into nnU-Net, which only looks for trainer classes in its own package.

    The checkpoint names that class, so loading fails without this step.
    """
    if variants_dir is None:
        import nnunetv2

        variants_dir = Path(nnunetv2.__file__).parent / "training" / "nnUNetTrainer" / "variants"
    return Path(shutil.copy(trainer_file, variants_dir / TRAINER_FILE))


class NnUNetModel:
    """The packaged nnU-Net model, reading files the same way training did."""

    def __init__(self, model_dir: str | Path, options: Options | None = None):
        options = options or Options()
        model_dir = Path(model_dir)
        install_trainer(model_dir / TRAINER_FILE)
        import torch
        from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor

        self.predictor = nnUNetPredictor(tile_step_size=options.tile_step, use_mirroring=options.tta,
                                         device=torch.device(options.device), allow_tqdm=False)
        self.predictor.initialize_from_trained_model_folder(str(model_dir), use_folds=(0,),
                                                            checkpoint_name=CHECKPOINT)
        self.io = self.predictor.plans_manager.image_reader_writer_class()

    def read(self, path: Path) -> tuple[np.ndarray, dict]:
        """Load a scan with the reader nnU-Net used in training."""
        return self.io.read_images([str(path)])

    def predict(self, data: np.ndarray, properties: dict) -> np.ndarray:
        """Run the network on one loaded scan."""
        # runs in this process: nnU-Net's worker processes can't be used inside a ZeroGPU call
        return self.predictor.predict_single_npy_array(data, properties)

    def write(self, seg: np.ndarray, path: Path, properties: dict) -> None:
        """Save the labels in the scan's original geometry."""
        self.io.write_seg(seg, str(path), properties)
