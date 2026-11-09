"""SPEC 002, part 2: run nnU-Net preprocessing for one shard of cases (D-017).

Needs the SPEC 002 prepare output (``nnUNetPlans.json``, ``dataset.json`` and
``shard_plan.json``) and the KiTS23 staging outputs under ``--input-root``. Each
case runs in its own process, ``--workers`` at a time, so memory is returned after
every case. A case whose process dies is retried once with nothing else running.
Cases already written are skipped, so a rerun picks up where it stopped. Example::

    python scripts/data/preprocess_shard.py --input-root /kaggle/input --shard 1 \
        --out-dir /kaggle/working/nnUNet_preprocessed/Dataset220_KiTS2023/nnUNetPlans_3d_fullres \
        --record /kaggle/working/spec002/shard_1.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from prepare_kits23 import detect_roots, manifest  # also puts src/ on sys.path

DATASET = "Dataset220_KiTS2023"
CONFIG = "3d_fullres"
N_CASES = 489
SUFFIXES = (".b2nd", "_seg.b2nd", ".pkl")


def find_plans_dir(root: Path) -> Path:
    """Find the one dataset folder that holds the nnU-Net plans and the shard plan."""
    hits = sorted(p.parent for p in root.rglob("shard_plan.json")
                  if p.parent.name == DATASET and (p.parent / "nnUNetPlans.json").exists())
    if len(hits) != 1:
        raise SystemExit(f"need exactly one {DATASET} folder with nnUNetPlans.json and shard_plan.json, found {hits}")
    return hits[0]


def is_done(out_dir: Path, case: str) -> bool:
    """True when all preprocessed files for this case are already written."""
    return all((out_dir / f"{case}{s}").exists() for s in SUFFIXES)


def preprocess_one(case: str, image: str, seg: str, plans_dir: Path, out_dir: Path) -> None:
    """Preprocess one case with nnU-Net (runs inside its own child process)."""
    from batchgenerators.utilities.file_and_folder_operations import load_json
    from nnunetv2.utilities.plans_handling.plans_handler import PlansManager

    plans = PlansManager(load_json(str(plans_dir / "nnUNetPlans.json")))
    config = plans.get_configuration(CONFIG)
    preprocessor = config.preprocessor_class(verbose=False)
    preprocessor.run_case_save(str(out_dir / case), [image], seg, plans, config,
                               load_json(str(plans_dir / "dataset.json")))


def run_case(case: str, image: Path, seg: Path, plans_dir: Path, out_dir: Path) -> tuple[str, int, float]:
    """Preprocess one case in a child process; return (case, exit code, seconds)."""
    start = time.time()
    code = subprocess.run([sys.executable, __file__, "--one", case, str(image), str(seg),
                           str(plans_dir), str(out_dir)]).returncode
    if code == 0 and not is_done(out_dir, case):
        code = -1
    print(f"{case}: {'ok' if code == 0 else f'FAILED ({code})'} in {time.time() - start:.0f} s", flush=True)
    return case, code, time.time() - start


def main(argv: list[str] | None = None) -> int:
    """Preprocess every case of one shard, retrying failures one at a time."""
    if argv is None and len(sys.argv) > 1 and sys.argv[1] == "--one":
        case, image, seg, plans_dir, out_dir = sys.argv[2:7]
        preprocess_one(case, image, seg, Path(plans_dir), Path(out_dir))
        return 0
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--shard", type=int, required=True, help="1-based")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--link-dir", type=Path, default=Path("/tmp/kits23_merged"))
    args = parser.parse_args(argv)
    t0 = time.time()

    plans_dir = find_plans_dir(args.input_root)
    plan = json.loads((plans_dir / "shard_plan.json").read_text())
    cases = plan["shards"][args.shard - 1]
    images_root, segs_root = detect_roots(args.input_root, min_files=N_CASES, link_dir=args.link_dir)
    images, segs = manifest.find_case_files(images_root), manifest.find_case_files(segs_root)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    todo = [c for c in cases if not is_done(args.out_dir, c)]
    print(f"shard {args.shard}/{plan['n_shards']}: {len(cases)} cases, {len(todo)} to do, "
          f"{args.workers} workers", flush=True)

    def job(case: str) -> tuple[str, int, float]:
        return run_case(case, images[case][0], segs[case][0], plans_dir, args.out_dir)

    with ThreadPoolExecutor(args.workers) as ex:
        results = list(ex.map(job, todo))
    retry = [c for c, code, _ in results if code != 0]
    if retry:
        print(f"retrying {len(retry)} failed case(s) one at a time: {retry}", flush=True)
        results += [job(case) for case in retry]
    failed = [c for c in cases if not is_done(args.out_dir, c)]
    secs = [s for _, code, s in results if code == 0]
    size_gb = sum(f.stat().st_size for f in args.out_dir.iterdir()) / 1e9
    record = {
        "shard": args.shard, "n_shards": plan["n_shards"], "cases": len(cases),
        "done": len(cases) - len(failed), "failed": failed, "workers": args.workers,
        "mean_case_seconds": round(sum(secs) / len(secs), 1) if secs else None,
        "size_gb": round(size_gb, 2), "hours": round((time.time() - t0) / 3600, 2),
    }
    args.record.parent.mkdir(parents=True, exist_ok=True)
    args.record.write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=1))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
