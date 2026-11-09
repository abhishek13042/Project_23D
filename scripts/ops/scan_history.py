"""SPEC 012: scan every object in the git history for secrets, data and weights.

Reads blobs, not diffs, so a file that was committed and later removed still counts. Run it
before the repository goes public; CI repeats it on every push.

Example::

    python scripts/ops/scan_history.py
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_BLOB_BYTES = 10_000_000
FORBIDDEN_SUFFIXES = (
    ".nii", ".nii.gz", ".mha", ".mhd", ".nrrd", ".npz", ".pt", ".pth", ".ckpt", ".onnx", ".safetensors",
)
SECRET_PATTERNS = {
    "Hugging Face token": re.compile(rb"\bhf_[A-Za-z0-9]{30,}"),
    "GitHub token": re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,})"),
    "Kaggle token": re.compile(rb"\bKGAT_[a-f0-9]{20,}|\"key\"\s*:\s*\"[a-f0-9]{32}\""),
    "Vercel token": re.compile(rb"\bvc[pkr]_[A-Za-z0-9]{30,}"),
    "AWS key": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "database password": re.compile(rb"postgres(?:ql)?://[^:\s/'\"]+:(?!password|PASSWORD)[^@\s'\"]+@"),
    "private key": re.compile(rb"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----"),
}


def path_problem(path: str, size: int) -> str | None:
    """Why this file path must not be in git, or None if it is fine."""
    if path.lower().endswith(FORBIDDEN_SUFFIXES):
        return "data or weights file"
    if re.search(r"(^|/)\.env(\.(?!example$)[^/]+)?$", path):
        return "environment file"
    if re.search(r"(^|/)overlay_[^/]*\.png$", path):
        return "CT overlay"
    if size > MAX_BLOB_BYTES:
        return f"{size} bytes, over the size limit"
    return None


def secret_problems(content: bytes) -> list[str]:
    """Names of the secret patterns found in this file content."""
    return [name for name, pattern in SECRET_PATTERNS.items() if pattern.search(content)]


def git(*args: str, stdin: bytes | None = None) -> bytes:
    """Run a git command in the repo and return its output."""
    return subprocess.run(["git", *args], cwd=ROOT, input=stdin, capture_output=True, check=True).stdout


def history_blobs() -> dict[str, list[str]]:
    """Map each blob hash in any commit to the paths it has appeared at."""
    blobs: dict[str, list[str]] = {}
    for line in git("rev-list", "--objects", "--all").decode("utf-8", "replace").splitlines():
        sha, _, path = line.partition(" ")
        if path:
            blobs.setdefault(sha, []).append(path)
    return blobs


def scan() -> list[str]:
    """Check every file ever committed and list the problems found."""
    blobs = history_blobs()
    query = "".join(f"{sha}\n" for sha in blobs).encode()
    out = git("cat-file", "--batch", stdin=query)
    problems, position = [], 0
    while position < len(out):
        end = out.index(b"\n", position)
        sha, kind, size = out[position:end].decode().split()
        start = end + 1
        position = start + int(size) + 1
        if kind != "blob":
            continue
        secrets = secret_problems(out[start : start + int(size)])
        for path in blobs[sha]:
            issue = path_problem(path, int(size))
            problems += [f"{path}: {reason}" for reason in ([issue] if issue else []) + secrets]
    return sorted(set(problems))


def main(argv: list[str] | None = None) -> int:
    """Scan the git history and exit with 1 if anything was found."""
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    problems = scan()
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"{len(problems)} problems in the git history")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
