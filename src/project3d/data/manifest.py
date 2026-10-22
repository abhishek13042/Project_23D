"""Locate KiTS23 files and verify them against the pinned checksum manifest.

The manifest is ``data/sources/kits23_v0.1.4_files.tsv`` (D-011): one row per
file with ``case_id, kind, size_bytes, sha256, url``. ``kind`` is ``image`` or
``segmentation``.
"""

from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

KINDS = ("image", "segmentation")
CASE_FILE_RE = re.compile(r"^(case_\d{5})\.nii(\.gz)?$")

# Verification statuses. Only OK is a pass; DECOMPRESSED is a warning (the file
# exists but the platform un-gzipped it, so the published hash cannot apply).
OK = "OK"
MISSING = "MISSING"
SIZE_MISMATCH = "SIZE_MISMATCH"
HASH_MISMATCH = "HASH_MISMATCH"
DECOMPRESSED = "DECOMPRESSED_UNVERIFIED"
DUPLICATE = "DUPLICATE"
FAILING = {MISSING, SIZE_MISMATCH, HASH_MISMATCH, DUPLICATE}


@dataclass(frozen=True)
class Expected:
    case_id: str
    kind: str
    size_bytes: int
    sha256: str


def load_manifest(tsv_path: str | Path) -> dict[tuple[str, str], Expected]:
    """Read the checksum manifest, keyed by ``(case_id, kind)``."""
    out: dict[tuple[str, str], Expected] = {}
    with open(tsv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row["kind"] not in KINDS:
                raise ValueError(f"unknown kind {row['kind']!r} for {row['case_id']}")
            key = (row["case_id"], row["kind"])
            if key in out:
                raise ValueError(f"duplicate manifest row {key}")
            out[key] = Expected(row["case_id"], row["kind"], int(row["size_bytes"]), row["sha256"].lower())
    return out


def find_case_files(root: str | Path) -> dict[str, list[Path]]:
    """Recursively find ``case_XXXXX.nii.gz`` (or ``.nii``) files under ``root``.

    Returns every path per case so duplicates can be reported, not silently picked.
    """
    found: dict[str, list[Path]] = {}
    for path in sorted(Path(root).rglob("case_*")):
        m = CASE_FILE_RE.match(path.name)
        if m and path.is_file():
            found.setdefault(m.group(1), []).append(path)
    return found


def sha256_file(path: str | Path, chunk: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while block := fh.read(chunk):
            h.update(block)
    return h.hexdigest()


def verify_kind(
    manifest: dict[tuple[str, str], Expected],
    kind: str,
    root: str | Path,
    check_hash: bool = True,
) -> list[dict]:
    """Check every manifest entry of one kind against the files under ``root``.

    Returns one report row per manifest entry, plus one row per file found
    under ``root`` that the manifest does not list (status ``UNEXPECTED``).
    """
    found = find_case_files(root)
    rows = []
    for (case_id, k), exp in sorted(manifest.items()):
        if k != kind:
            continue
        paths = found.pop(case_id, [])
        row = {"case_id": case_id, "kind": kind, "path": "", "status": OK,
               "size_bytes": "", "sha256": ""}
        if not paths:
            row["status"] = MISSING
        elif len(paths) > 1:
            row.update(status=DUPLICATE, path=";".join(str(p) for p in paths))
        else:
            path = paths[0]
            row["path"] = str(path)
            row["size_bytes"] = path.stat().st_size
            if path.suffix != ".gz":
                row["status"] = DECOMPRESSED
            elif row["size_bytes"] != exp.size_bytes:
                row["status"] = SIZE_MISMATCH
            elif check_hash:
                row["sha256"] = sha256_file(path)
                if row["sha256"] != exp.sha256:
                    row["status"] = HASH_MISMATCH
        rows.append(row)
    for case_id, paths in sorted(found.items()):
        for p in paths:
            rows.append({"case_id": case_id, "kind": kind, "path": str(p),
                         "status": "UNEXPECTED", "size_bytes": p.stat().st_size, "sha256": ""})
    return rows


def summarize(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return counts


def resolved_paths(rows: list[dict]) -> dict[str, Path]:
    """Map case_id to its single verified path (OK or DECOMPRESSED rows only)."""
    return {r["case_id"]: Path(r["path"]) for r in rows if r["status"] in (OK, DECOMPRESSED)}
