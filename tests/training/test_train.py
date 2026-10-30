import gzip
import json
import sys
import time

import pytest

import train


def make_fold(root, trainer, files=()):
    fold = root / train.DATASET / train.trainer_dir_name(trainer) / "fold_0"
    fold.mkdir(parents=True)
    for f in files:
        (fold / f).parent.mkdir(parents=True, exist_ok=True)
        (fold / f).write_text("{}")
    return fold


def make_preprocessed(root, shards):
    """Prepare output under root/prep plus one output per shard; returns the case IDs."""
    plans = root / "prep" / train.DATASET
    (plans / "gt_segmentations").mkdir(parents=True)
    (plans / "gt_segmentations" / "case_00000.nii.gz").write_text("")
    (plans / "nnUNetPlans.json").write_text("{}")
    cases = [c for s in shards for c in s]
    (plans / "splits_final.json").write_text(json.dumps([{"train": cases[1:], "val": cases[:1]}]))
    for k, shard in enumerate(shards):
        data = root / f"shard{k}" / train.DATASET / "nnUNetPlans_3d_fullres"
        data.mkdir(parents=True)
        for c in shard:
            for s in (".b2nd", "_seg.b2nd", ".pkl"):
                (data / f"{c}{s}").write_text("")
    return cases


def test_assemble_preprocessed(tmp_path):
    make_preprocessed(tmp_path / "in", [["case_00000", "case_00001"], ["case_00002"]])
    dest = tmp_path / "pre" / train.DATASET
    assert train.assemble_preprocessed(tmp_path / "in", dest, link=False) == 3
    assert (dest / "nnUNetPlans.json").exists() and (dest / "gt_segmentations" / "case_00000.nii.gz").exists()
    assert (dest / "nnUNetPlans_3d_fullres" / "case_00002_seg.b2nd").exists()


def test_assemble_preprocessed_needs_every_shard(tmp_path):
    make_preprocessed(tmp_path / "in", [["case_00000"], ["case_00001"]])
    for f in (tmp_path / "in" / "shard1").rglob("*.pkl"):
        f.unlink()
    with pytest.raises(SystemExit, match="not preprocessed"):
        train.assemble_preprocessed(tmp_path / "in", tmp_path / "pre", link=False)


def test_assemble_preprocessed_rejects_overlapping_shards(tmp_path):
    make_preprocessed(tmp_path / "in", [["case_00000"], ["case_00000"]])
    with pytest.raises(SystemExit, match="more than one shard"):
        train.assemble_preprocessed(tmp_path / "in", tmp_path / "pre", link=False)


def test_find_previous(tmp_path):
    t = "nnUNetTrainer_100epochs_kaggle"
    assert train.find_previous(tmp_path, t) is None
    make_fold(tmp_path / "pilot", "nnUNetTrainer_5epochs", ["checkpoint_final.pth"])
    assert train.find_previous(tmp_path, t) is None  # other trainers are ignored
    fold = make_fold(tmp_path / "s1", t, ["checkpoint_latest.pth"])
    assert train.find_previous(tmp_path, t) == fold
    make_fold(tmp_path / "s2", t, ["checkpoint_latest.pth"])
    with pytest.raises(SystemExit):
        train.find_previous(tmp_path, t)


def test_state(tmp_path):
    fold = tmp_path / "fold_0"
    assert train.state(fold) == "new"
    fold.mkdir()
    (fold / "checkpoint_best.pth").write_text("")
    assert train.state(fold) == "new"
    (fold / "checkpoint_latest.pth").write_text("")
    assert train.state(fold) == "resume"
    (fold / "checkpoint_final.pth").write_text("")
    assert train.state(fold) == "validate"
    (fold / "validation").mkdir()
    (fold / "validation" / "summary.json").write_text("{}")
    assert train.state(fold) == "done"


def test_checkpoint_epoch(tmp_path):
    torch = pytest.importorskip("torch")
    assert train.checkpoint_epoch(tmp_path) == 0
    torch.save({"current_epoch": 35, "network_weights": {}}, tmp_path / "checkpoint_latest.pth")
    assert train.checkpoint_epoch(tmp_path) == 35
    torch.save({"current_epoch": 100}, tmp_path / "checkpoint_final.pth")
    assert train.checkpoint_epoch(tmp_path) == 100


LOG = """
2026-10-25 10:00:00.000000: Epoch 0
2026-10-25 10:00:00.000001: Current learning rate: 0.01
2026-10-25 10:05:00.000000: train_loss -0.1
2026-10-25 10:05:00.000001: val_loss -0.2
2026-10-25 10:05:00.000002: Pseudo dice [np.float32(0.9), np.float32(0.5), np.float32(0.4)]
2026-10-25 10:05:00.000003: Epoch time: 300.5 s
2026-10-25 10:05:00.000004: Yayy! New best EMA pseudo Dice: 0.6
2026-10-25 10:05:01.000000: Epoch 1
2026-10-25 10:10:00.000000: Pseudo dice [0.92, 0.6, 0.5]
2026-10-25 10:10:00.000001: Epoch time: 299.5 s
2026-10-25 10:10:01.000000: Epoch 2
"""


def test_parse_log():
    epochs = train.parse_log(LOG)
    assert [e["epoch"] for e in epochs] == [0, 1]  # epoch 2 never finished
    assert epochs[0] == {"epoch": 0, "pseudo_dice": 0.6, "seconds": 300.5}
    assert epochs[1]["pseudo_dice"] == pytest.approx(0.6733, abs=1e-4)


def test_run_with_budget_stops_a_long_process():
    t = time.time()
    code, stopped = train.run_with_budget([sys.executable, "-c", "import time; time.sleep(60)"], 1)
    assert stopped and code is None and time.time() - t < 30
    code, stopped = train.run_with_budget([sys.executable, "-c", "pass"], 30)
    assert (code, stopped) == (0, False)


def test_main_done_session_writes_record(tmp_path, monkeypatch):
    """An attached output that already finished is restored and only recorded."""
    t = "nnUNetTrainer_100epochs_kaggle"
    make_preprocessed(tmp_path / "in", [["case_00000", "case_00001"]])
    fold = make_fold(tmp_path / "in" / "s1", t, ["checkpoint_final.pth"])
    (fold / "validation").mkdir()
    (fold / "validation" / "summary.json").write_text(json.dumps({"foreground_mean": {"Dice": 0.81234}}))
    (fold / "training_log_2026_10_25_10_00_00.txt").write_text(LOG)
    monkeypatch.setattr(train, "checkpoint_epoch", lambda f: 100)  # no torch needed here
    out = tmp_path / "out" / "run_record.json"
    code = train.main(["--input-root", str(tmp_path / "in"), "--preprocessed-root", str(tmp_path / "pre"),
                       "--results-root", str(tmp_path / "res"), "--trainer", t, "--budget-hours", "1",
                       "--out", str(out), "--gpu", "Tesla T4"])
    assert code == 0
    rec = json.loads(out.read_text())
    assert rec["state"] == "done" and rec["epochs_done"] == 100 and rec["sessions"] == 1
    assert rec["fold0_validation_dice"] == 0.8123 and rec["mean_epoch_seconds"] == 300.0
    assert (tmp_path / "pre" / train.DATASET / "nnUNetPlans.json").exists()
    sessions = tmp_path / "res" / train.DATASET / train.trainer_dir_name(t) / train.SESSIONS_FILE
    assert json.loads(sessions.read_text())[0]["state_before"] == "done"


def test_trainer_settings(monkeypatch):
    pytest.importorskip("nnunetv2")
    import torch
    from nnunetv2.training.nnUNetTrainer.nnUNetTrainer import nnUNetTrainer

    from project3d.training.nnunet_trainer import nnUNetTrainer_100epochs_kaggle

    monkeypatch.setattr(nnUNetTrainer, "__init__", lambda self, *a, **k: None)
    tr = nnUNetTrainer_100epochs_kaggle({}, "3d_fullres", 0, {}, torch.device("cpu"))
    assert (tr.num_epochs, tr.save_every) == (100, 5)


def test_trainer_final_validation_skips_predicted_cases(tmp_path, monkeypatch):
    pytest.importorskip("nnunetv2")
    import torch
    from nnunetv2.training.nnUNetTrainer.nnUNetTrainer import nnUNetTrainer

    from project3d.training.nnunet_trainer import nnUNetTrainer_100epochs_kaggle

    monkeypatch.setattr(nnUNetTrainer, "__init__", lambda self, *a, **k: None)
    monkeypatch.setattr(nnUNetTrainer, "do_split", lambda self: (["a"], ["b", "c"]))
    seen = []
    monkeypatch.setattr(nnUNetTrainer, "perform_actual_validation", lambda self, p=False: seen.append(self.do_split()))
    tr = nnUNetTrainer_100epochs_kaggle({}, "3d_fullres", 0, {}, torch.device("cpu"))
    tr.output_folder = str(tmp_path)
    (tmp_path / "validation").mkdir()
    (tmp_path / "validation" / "b.nii.gz").write_bytes(b"x")
    assert tr.do_split() == (["a"], ["b", "c"])  # training sees every case
    tr.perform_actual_validation()
    assert seen == [(["a"], ["c"])]


def test_drop_unreadable_removes_only_truncated_files(tmp_path):
    good = gzip.compress(b"x" * 5000 + bytes(range(256)) * 100)
    (tmp_path / "good.nii.gz").write_bytes(good)
    (tmp_path / "cut.nii.gz").write_bytes(good[: len(good) // 2])
    (tmp_path / "junk.nii.gz").write_bytes(b"not gzip at all")
    (tmp_path / "summary.json").write_text("{}")
    assert train.drop_unreadable(tmp_path) == ["cut.nii.gz", "junk.nii.gz"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["good.nii.gz", "summary.json"]
