"""SPEC 002 pipeline: verify -> features -> split -> nnU-Net raw dataset.

Runs on a Kaggle CPU session (or locally on a small subset). Example::

    python scripts/data/prepare_kits23.py --input-root /kaggle/input \
        --manifest data/sources/kits23_v0.1.4_files.tsv \
        --out-dir /kaggle/working/spec002 --raw-root /tmp/nnUNet_raw

Outputs in ``--out-dir``: verify_report.csv, case_features.csv, split.json,
splits_final.json. The nnU-Net raw dataset is written under ``--raw-root``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from project3d.data import features, manifest, nnunet_export, split  # noqa: E402

IMAGE_MIN_BYTES = 10 * 1024 * 1024  # CT volumes are tens of MB; label files are ~1 MB


def detect_roots(input_root: Path, min_files: int = 1) -> tuple[Path, Path]:
    """Find the images folder and the segmentations folder by typical file size.

    Folders with fewer than ``min_files`` case files are ignored (e.g. nnU-Net's
    validation predictions sitting next to the full dataset).
    """
    by_dir: dict[Path, list[int]] = {}
    for paths in manifest.find_case_files(input_root).values():
        for p in paths:
            by_dir.setdefault(p.parent, []).append(p.stat().st_size)
    by_dir = {d: s for d, s in by_dir.items() if len(s) >= min_files}
    if not by_dir:
        raise SystemExit(f"no case_XXXXX.nii(.gz) files found under {input_root}")
    big = [d for d, s in by_dir.items() if statistics.median(s) >= IMAGE_MIN_BYTES]
    small = [d for d, s in by_dir.items() if statistics.median(s) < IMAGE_MIN_BYTES]
    if len(big) != 1 or len(small) != 1:
        raise SystemExit(f"could not tell images from segmentations; folders found: "
                         f"{ {str(d): len(s) for d, s in by_dir.items()} }. "
                         f"Pass --images-root and --segs-root explicitly.")
    return big[0], small[0]


def write_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--input-root", type=Path, help="auto-detect images/segmentation folders here")
    ap.add_argument("--images-root", type=Path)
    ap.add_argument("--segs-root", type=Path)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--raw-root", type=Path, required=True)
    ap.add_argument("--link-mode", choices=("symlink", "copy"), default="symlink")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--subset", action="store_true",
                    help="allow missing cases (local smoke test); never use for the real run")
    ap.add_argument("--skip-hash", action="store_true", help="size check only (faster, weaker)")
    args = ap.parse_args(argv)

    t0 = time.time()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.images_root and args.segs_root:
        images_root, segs_root = args.images_root, args.segs_root
    elif args.input_root:
        images_root, segs_root = detect_roots(args.input_root)
    else:
        ap.error("give --input-root, or both --images-root and --segs-root")
    print(f"images: {images_root}\nsegmentations: {segs_root}")

    # 1. Verify every file against the pinned manifest.
    exp = manifest.load_manifest(args.manifest)
    report = (manifest.verify_kind(exp, "image", images_root, not args.skip_hash)
              + manifest.verify_kind(exp, "segmentation", segs_root, not args.skip_hash))
    write_csv(args.out_dir / "verify_report.csv", report)
    counts = manifest.summarize(report)
    print(f"[1/4] verify: {counts}  ({time.time() - t0:.0f}s)")
    failing = {s: n for s, n in counts.items() if s in manifest.FAILING or s == "UNEXPECTED"}
    if args.subset:
        failing.pop(manifest.MISSING, None)
    if failing:
        print("STOP: verification failed; see verify_report.csv")
        return 1
    if counts.get(manifest.DECOMPRESSED):
        print("WARNING: some files were un-gzipped by the platform; their hashes cannot be checked")

    images = manifest.resolved_paths([r for r in report if r["kind"] == "image"])
    segs = manifest.resolved_paths([r for r in report if r["kind"] == "segmentation"])
    cases = sorted(set(images) & set(segs))
    if not args.subset and len(cases) != len({c for c, _ in exp}):
        print(f"STOP: only {len(cases)} cases have both image and label")
        return 1

    # 2. Image/mask geometry must agree (SPEC 001 5.4), then label features per case.
    bad = {c: why for c in cases if (why := features.geometry_mismatch(images[c], segs[c]))}
    if bad:
        print(f"STOP: image/mask geometry mismatch: {bad}")
        return 1
    rows = [features.case_features(c, segs[c]) for c in cases]
    cuts = features.add_size_bins(rows)
    write_csv(args.out_dir / "case_features.csv", rows)
    print(f"[2/4] features: {len(rows)} cases, tumor-size tertile cuts (ml) = "
          f"{cuts[0]:.2f}, {cuts[1]:.2f}  ({time.time() - t0:.0f}s)")

    # 3. Split once, fingerprint, save.
    roles = split.make_split(rows, seed=args.seed)
    record = {
        "spec": "SPEC 002",
        "dataset": "KiTS23 v0.1.4",
        # Line endings normalized so Windows and Kaggle copies hash the same.
        "manifest_sha256": hashlib.sha256(
            args.manifest.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "seed": args.seed,
        "fractions": {"train": 0.70, "val": 0.15, "test": 0.15},
        "strata": "cohort | size_bin | cyst",
        "size_bin_cuts_ml": list(cuts),
        "fingerprint_sha256": split.fingerprint(roles),
        "summary": split.summary(rows, roles),
        "roles": roles,
    }
    (args.out_dir / "split.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    (args.out_dir / "splits_final.json").write_text(
        json.dumps(split.nnunet_splits(roles), indent=2), encoding="utf-8")
    print(f"[3/4] split: {record['summary']['total']}  fingerprint {record['fingerprint_sha256'][:16]}...")

    # 4. nnU-Net raw dataset (train+val only in imagesTr).
    ds = nnunet_export.build_raw_dataset(roles, images, segs, args.raw_root, mode=args.link_mode)
    nnunet_export.check_no_test_leak(ds, roles)
    print(f"[4/4] nnU-Net raw dataset: {ds}  ({time.time() - t0:.0f}s total)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
