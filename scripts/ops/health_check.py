"""SPEC 012: check that the public site and every gallery file respond.

Only the standard library is used, so CI needs no install step. Exits 1 if anything is down.

Example::

    python scripts/ops/health_check.py --site https://example.vercel.app --gallery https://host/gallery
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GALLERY_INDEX = ROOT / "reports" / "release" / "gallery_index.json"
PAGES = ["", "gallery", "results", "about", "try"]
CASE_FILES = ["ct.nii.gz", "pred.nii.gz", "gt.nii.gz"]
TIMEOUT_SECONDS = 30


def targets(site: str, gallery: str, case_ids: list[str]) -> list[str]:
    site, gallery = site.rstrip("/"), gallery.rstrip("/")
    urls = [f"{site}/{page}" for page in PAGES]
    urls += [f"{site}/case/{case_id}" for case_id in case_ids]
    if gallery:
        urls += [f"{gallery}/{case_id}/{name}" for case_id in case_ids for name in CASE_FILES]
    return urls


def status_of(url: str) -> int:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "project-23d-health-check"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code
    except OSError:
        return 0


def failures(urls: list[str], check: Callable[[str], int] = status_of) -> list[tuple[str, int]]:
    results = [(url, check(url)) for url in urls]
    return [(url, status) for url, status in results if status != 200]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--site", required=True)
    ap.add_argument("--gallery", default="")
    args = ap.parse_args(argv)
    case_ids = [case["case_id"] for case in json.loads(GALLERY_INDEX.read_text(encoding="utf-8"))]
    urls = targets(args.site, args.gallery, case_ids)
    bad = failures(urls)
    for url, status in bad:
        print(f"FAILED {status} {url}", file=sys.stderr)
    print(f"{len(urls) - len(bad)} of {len(urls)} responded")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
