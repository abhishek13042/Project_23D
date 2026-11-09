"""SPEC 004: apply the fixed post-processing rule to a folder of predictions (D-021).

Example (Kaggle)::

    python scripts/eval/postprocess.py --pred-dir /kaggle/working/spec004/pred_raw \
        --out-dir /kaggle/working/spec004/pred_pp --np 3
"""

from __future__ import annotations

import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from project3d.eval.postprocess import keep_largest_regions


def process_case(args: tuple[Path, Path]) -> str:
    """Keep the largest connected regions in one prediction and save it."""
    src, dst = args
    import nibabel as nib

    img = nib.load(str(src))
    seg = np.asanyarray(img.dataobj).astype(np.uint8)
    out = nib.Nifti1Image(keep_largest_regions(seg), img.affine, img.header)
    out.set_data_dtype(np.uint8)
    nib.save(out, str(dst))
    return src.name


def main(argv: list[str] | None = None) -> int:
    """Post-process every prediction in a folder."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pred-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--np", type=int, default=1, help="worker processes")
    args = parser.parse_args(argv)

    files = sorted(args.pred_dir.glob("case_*.nii.gz"))
    if not files:
        print(f"STOP: no predictions in {args.pred_dir}")
        return 1
    args.out_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(f, args.out_dir / f.name) for f in files]
    if args.np > 1:
        with Pool(args.np) as pool:
            done = pool.map(process_case, jobs)
    else:
        done = [process_case(j) for j in jobs]
    print(f"post-processed {len(done)} cases into {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
