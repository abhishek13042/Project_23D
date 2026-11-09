"""SPEC 008: segment one NIfTI scan with the packaged model.

Example::

    python scripts/inference/predict.py --model-dir model_package --input scan.nii.gz \
        --output scan_seg.nii.gz --summary scan_seg.json

The defaults match the evaluation. ``--no-tta`` is about 8x faster.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from project3d.inference.predictor import InvalidInput, Model, NnUNetModel, Options, Predictor


def main(argv: list[str] | None = None, model_factory: Callable[..., Model] = NnUNetModel) -> int:
    """Segment one CT scan and save the label map and a JSON summary."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, help="JSON summary (default: printed only)")
    parser.add_argument("--no-tta", action="store_true", help="turn test-time augmentation off")
    parser.add_argument("--tile-step", type=float, default=Options.tile_step)
    parser.add_argument("--device", default=Options.device, choices=("cuda", "cpu"))
    args = parser.parse_args(argv)

    options = Options(tta=not args.no_tta, tile_step=args.tile_step, device=args.device)
    predictor = Predictor(model_factory(args.model_dir, options), options)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        summary = predictor.predict_file(args.input, args.output)
    except InvalidInput as exc:
        print(f"STOP: {exc}")
        return 1
    text = json.dumps(summary, indent=2)
    if args.summary:
        args.summary.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
