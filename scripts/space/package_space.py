"""SPEC 010: assemble the folder that becomes the Hugging Face Space.

A Space holds only its own folder, so the app and the few project modules it imports are copied
together. ``.github/workflows/sync-space.yml`` runs this on every release.

Example::

    python scripts/space/package_space.py --out-dir build/space
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP_FILES = ["app.py", "service.py", "requirements.txt", "README.md"]
SOURCE_FILES = [
    "project3d/__init__.py",
    "project3d/data/__init__.py",
    "project3d/data/features.py",
    "project3d/eval/__init__.py",
    "project3d/eval/postprocess.py",
    "project3d/inference/__init__.py",
    "project3d/inference/predictor.py",
]


def package(out_dir: Path) -> list[Path]:
    """Copy the Space app and the library files it needs into ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    copied = [Path(shutil.copy(ROOT / "apps" / "space" / name, out_dir)) for name in APP_FILES]
    for name in SOURCE_FILES:
        target = out_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        copied.append(Path(shutil.copy(ROOT / "src" / name, target)))
    return copied


def main(argv: list[str] | None = None) -> int:
    """Package the Hugging Face Space folder."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    print(f"wrote {len(package(args.out_dir))} files to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
