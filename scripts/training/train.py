"""SPEC 003: train nnU-Net v2 fold 0 on Kaggle within one session's time budget.

Finds the SPEC 002 preprocessed dataset under ``--input-root`` and copies it to
local disk. If an earlier session's output is attached, it restores that results
folder and resumes. Then it runs ``nnUNetv2_train`` until the training (and
nnU-Net's own fold-0 validation) finishes or the budget runs out. A stopped run
loses at most ``save_every`` epochs; attach this output to the next session.
Example::

    python scripts/training/train.py --input-root /kaggle/input \
        --preprocessed-root /tmp/nnUNet_preprocessed \
        --results-root /kaggle/working/nnUNet_results \
        --trainer nnUNetTrainer_100epochs_kaggle --budget-hours 11 \
        --out /kaggle/working/spec003/run_record.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

DATASET = "Dataset220_KiTS2023"
CONFIG = "3d_fullres"
FOLD = 0
SESSIONS_FILE = "project23d_sessions.json"


def trainer_dir_name(trainer: str) -> str:
    return f"{trainer}__nnUNetPlans__{CONFIG}"


def find_preprocessed(root: Path) -> Path:
    hits = sorted(p.parent for p in root.rglob("nnUNetPlans.json")
                  if p.parent.name == DATASET and (p.parent / f"nnUNetPlans_{CONFIG}").is_dir())
    if len(hits) != 1:
        raise SystemExit(f"need exactly one preprocessed {DATASET} with nnUNetPlans_{CONFIG}/, found {hits}")
    return hits[0]


def find_previous(root: Path, trainer: str) -> Path | None:
    """The fold folder of an attached earlier session, if any."""
    hits = sorted(p for p in root.rglob(f"fold_{FOLD}")
                  if p.parent.name == trainer_dir_name(trainer) and any(p.glob("checkpoint_*.pth")))
    if len(hits) > 1:
        raise SystemExit(f"several earlier training outputs attached, keep only the latest: {hits}")
    return hits[0] if hits else None


def state(fold_dir: Path) -> str:
    if (fold_dir / "checkpoint_final.pth").exists():
        return "done" if (fold_dir / "validation" / "summary.json").exists() else "validate"
    if (fold_dir / "checkpoint_latest.pth").exists():
        return "resume"
    return "new"


def checkpoint_epoch(fold_dir: Path) -> int:
    for name in ("checkpoint_final.pth", "checkpoint_latest.pth"):
        if (fold_dir / name).exists():
            import torch

            ckpt = torch.load(fold_dir / name, map_location="cpu", weights_only=False)
            return int(ckpt["current_epoch"])
    return 0


def parse_log(text: str) -> list[dict]:
    """Per-epoch time and mean pseudo Dice from nnU-Net training_log_*.txt text."""
    epochs, cur = [], None
    for line in text.splitlines():
        msg = line.split(": ", 1)[1] if ": " in line else line
        if m := re.fullmatch(r"Epoch (\d+)", msg.strip()):
            cur = {"epoch": int(m.group(1))}
            epochs.append(cur)
        elif cur is not None and (m := re.match(r"Pseudo dice \[(.*)\]", msg)):
            vals = [float(v) for v in re.findall(r"-?\d+\.\d+(?:e-?\d+)?|nan", m.group(1))]
            cur["pseudo_dice"] = round(sum(vals) / len(vals), 4) if vals else None
        elif cur is not None and (m := re.match(r"Epoch time: ([\d.]+) s", msg)):
            cur["seconds"] = float(m.group(1))
    return [e for e in epochs if "seconds" in e]


def stop(proc: subprocess.Popen, grace: float = 60) -> None:
    """Stop the trainer and its data-augmentation workers."""
    def signal_all(sig):
        if os.name == "posix":
            os.killpg(proc.pid, sig)
        else:
            proc.kill()
    signal_all(signal.SIGTERM)
    try:
        proc.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        signal_all(getattr(signal, "SIGKILL", signal.SIGTERM))
        proc.wait()


def run_with_budget(cmd: list[str], seconds: float) -> tuple[int | None, bool]:
    """Return (exit code, stopped by budget)."""
    print("$", " ".join(cmd), f"  (budget {seconds / 3600:.2f} h)", flush=True)
    proc = subprocess.Popen(cmd, start_new_session=os.name == "posix")
    try:
        return proc.wait(timeout=max(seconds, 1)), False
    except subprocess.TimeoutExpired:
        print("time budget reached: stopping training (latest checkpoint is kept)", flush=True)
        stop(proc)
        return None, True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input-root", type=Path, required=True)
    ap.add_argument("--preprocessed-root", type=Path, required=True)
    ap.add_argument("--results-root", type=Path, required=True)
    ap.add_argument("--trainer", required=True)
    ap.add_argument("--budget-hours", type=float, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--gpu", default="unknown")
    args = ap.parse_args(argv)
    t0 = time.time()

    pre = args.preprocessed_root / DATASET
    if not pre.exists():
        src = find_preprocessed(args.input_root)
        print(f"copying preprocessed data from {src}", flush=True)
        shutil.copytree(src, pre)
    trainer_dir = args.results_root / DATASET / trainer_dir_name(args.trainer)
    prev = find_previous(args.input_root, args.trainer)
    if prev is not None and not trainer_dir.exists():
        print(f"resuming from {prev}", flush=True)
        shutil.copytree(prev.parent, trainer_dir)
    fold = trainer_dir / f"fold_{FOLD}"
    before, start_epoch = state(fold), checkpoint_epoch(fold)
    print(f"state: {before}, epochs done: {start_epoch}", flush=True)

    code, stopped = 0, False
    if before != "done":
        cmd = ["nnUNetv2_train", DATASET.split("_")[0].removeprefix("Dataset"), CONFIG, str(FOLD),
               "-tr", args.trainer]
        cmd += {"new": [], "resume": ["--c"], "validate": ["--val"]}[before]
        budget = args.budget_hours * 3600 - (time.time() - t0)
        code, stopped = run_with_budget(cmd, budget)

    after, end_epoch = state(fold), checkpoint_epoch(fold)
    hours = (time.time() - t0) / 3600
    sessions_path = trainer_dir / SESSIONS_FILE
    sessions = json.loads(sessions_path.read_text()) if sessions_path.exists() else []
    sessions.append({"session": len(sessions) + 1, "gpu": args.gpu, "hours": round(hours, 2),
                     "state_before": before, "state_after": after, "start_epoch": start_epoch,
                     "end_epoch": end_epoch, "stopped_by_budget": stopped, "exit_code": code})
    trainer_dir.mkdir(parents=True, exist_ok=True)
    sessions_path.write_text(json.dumps(sessions, indent=2))

    epochs = []
    for log in sorted(fold.glob("training_log_*.txt")):
        epochs += parse_log(log.read_text(encoding="utf-8", errors="replace"))
    secs = [e["seconds"] for e in epochs]
    summary = fold / "validation" / "summary.json"
    val_dice = json.loads(summary.read_text())["foreground_mean"]["Dice"] if summary.exists() else None
    record = {
        "spec": "SPEC 003", "trainer": args.trainer, "configuration": CONFIG, "fold": FOLD,
        "gpu": args.gpu, "sessions": len(sessions),
        "train_hours_total": round(sum(s["hours"] for s in sessions), 2),
        "epochs_done": end_epoch, "state": after,
        "mean_epoch_seconds": round(sum(secs) / len(secs), 1) if secs else None,
        "last_pseudo_dice": next((e.get("pseudo_dice") for e in reversed(epochs)), None),
        "fold0_validation_dice": None if val_dice is None else round(val_dice, 4),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=1))
    if after == "done":
        print("DONE: checkpoint_final.pth and fold_0/validation/ are in the output.")
    elif code not in (0, None):
        print(f"STOP: nnUNetv2_train failed with exit code {code}; see the log above")
        return 1
    else:
        print("NOT FINISHED: attach this notebook's output to the next training session.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
