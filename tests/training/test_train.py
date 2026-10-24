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


def test_find_preprocessed(tmp_path):
    pre = tmp_path / "in" / "prep" / "nnUNet_preprocessed" / train.DATASET
    (pre / "nnUNetPlans_3d_fullres").mkdir(parents=True)
    (pre / "nnUNetPlans.json").write_text("{}")
    other = tmp_path / "in" / "x" / train.DATASET  # plans only, no data folder
    other.mkdir(parents=True)
    (other / "nnUNetPlans.json").write_text("{}")
    assert train.find_preprocessed(tmp_path / "in") == pre
    (other / "nnUNetPlans_3d_fullres").mkdir()
    with pytest.raises(SystemExit):
        train.find_preprocessed(tmp_path / "in")


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
    pre = tmp_path / "in" / "prep" / train.DATASET
    (pre / "nnUNetPlans_3d_fullres").mkdir(parents=True)
    (pre / "nnUNetPlans.json").write_text("{}")
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
