"""Download one shard of KiTS23 v0.1.4 from the pinned URLs and verify it (D-015).

Kaggle saves at most about 20 GB of notebook output, and the images are 42 GB, so
the 489 images are split into ``--n-shards`` contiguous shards of similar size.
Shard 1 also holds all 489 segmentations (0.14 GB). Each file's size and SHA-256
are checked against the manifest while it streams; a bad file is retried, then
reported. Example::

    python scripts/data/stage_kits23.py --manifest data/sources/kits23_v0.1.4_files.tsv \
        --shard 1 --out-dir /kaggle/working/kits23

Writes ``images/``, ``segmentations/`` (shard 1 only) and ``stage_record.json``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

FOLDER = {"image": "images", "segmentation": "segmentations"}


def load_rows(tsv_path: Path) -> list[dict]:
    """Read the pinned file list, sorted by kind and case."""
    with open(tsv_path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    for r in rows:
        r["size_bytes"] = int(r["size_bytes"])
    return sorted(rows, key=lambda r: (r["kind"], r["case_id"]))


def plan_shard(rows: list[dict], shard: int, n_shards: int) -> list[dict]:
    """Rows for ``shard`` (1-based): a contiguous run of images by cumulative size."""
    if not 1 <= shard <= n_shards:
        raise ValueError(f"shard must be in 1..{n_shards}, got {shard}")
    images = [r for r in rows if r["kind"] == "image"]
    total = sum(r["size_bytes"] for r in images)
    picked, done = [], 0
    for r in images:
        # a file belongs to the shard in which its midpoint falls
        if int((done + r["size_bytes"] / 2) * n_shards // total) + 1 == shard:
            picked.append(r)
        done += r["size_bytes"]
    if shard == 1:
        picked += [r for r in rows if r["kind"] == "segmentation"]
    return picked


def fetch(row: dict, out_dir: Path, retries: int = 3) -> dict:
    """Download one file until its size and SHA-256 match the manifest; return its status row."""
    dst = out_dir / FOLDER[row["kind"]] / f"{row['case_id']}.nii.gz"
    status = "MISSING"
    for attempt in range(1, retries + 1):
        if dst.exists() and dst.stat().st_size == row["size_bytes"]:
            digest = hashlib.sha256()
            with open(dst, "rb") as fh:
                while chunk := fh.read(8 * 1024 * 1024):
                    digest.update(chunk)
            if digest.hexdigest() == row["sha256"]:
                return {"case_id": row["case_id"], "kind": row["kind"], "status": "OK", "attempts": attempt - 1}
        part = dst.with_suffix(".part")
        try:
            h, size = hashlib.sha256(), 0
            with urllib.request.urlopen(row["url"], timeout=120) as resp, open(part, "wb") as fh:
                while chunk := resp.read(8 * 1024 * 1024):
                    h.update(chunk)
                    size += len(chunk)
                    fh.write(chunk)
            if size != row["size_bytes"]:
                status = "SIZE_MISMATCH"
            elif h.hexdigest() != row["sha256"]:
                status = "HASH_MISMATCH"
            else:
                part.replace(dst)
                return {"case_id": row["case_id"], "kind": row["kind"], "status": "OK", "attempts": attempt}
        except OSError as e:
            status = f"ERROR {type(e).__name__}: {e}"
        part.unlink(missing_ok=True)
        time.sleep(2 * attempt)
    return {"case_id": row["case_id"], "kind": row["kind"], "status": status, "attempts": retries}


def main(argv: list[str] | None = None) -> int:
    """Download and check one shard of the KiTS23 files."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--n-shards", type=int, default=3)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args(argv)

    t0 = time.time()
    rows = plan_shard(load_rows(args.manifest), args.shard, args.n_shards)
    for kind in {r["kind"] for r in rows}:
        (args.out_dir / FOLDER[kind]).mkdir(parents=True, exist_ok=True)
    gb = sum(r["size_bytes"] for r in rows) / 1e9
    print(f"shard {args.shard}/{args.n_shards}: {len(rows)} files, {gb:.1f} GB", flush=True)
    results = []
    with ThreadPoolExecutor(args.workers) as pool:
        for i, res in enumerate(pool.map(lambda r: fetch(r, args.out_dir), rows), 1):
            results.append(res)
            if res["status"] != "OK" or i % 25 == 0 or i == len(rows):
                print(f"[{i}/{len(rows)}] {res['case_id']} {res['kind']}: {res['status']}"
                      f"  ({time.time() - t0:.0f}s)", flush=True)
    failed = [r for r in results if r["status"] != "OK"]
    record = {"shard": args.shard, "n_shards": args.n_shards, "files": len(rows),
              "images": sum(r["kind"] == "image" for r in rows),
              "segmentations": sum(r["kind"] == "segmentation" for r in rows),
              "gb": round(gb, 2), "ok": len(results) - len(failed), "failed": failed,
              "minutes": round((time.time() - t0) / 60, 1)}
    (args.out_dir / "stage_record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if k != "failed"}, indent=1))
    if failed:
        print(f"STOP: {len(failed)} files failed; rerun this notebook")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
