import json

import benchmark
import export_model
import numpy as np
import predict
from helpers import write_nifti
from test_predictor import FakeModel

from project3d.inference import predictor as pr


def trainer_dir(tmp_path):
    d = tmp_path / "trainer"
    (d / "fold_0").mkdir(parents=True)
    (d / "plans.json").write_text("{}")
    (d / "dataset.json").write_text("{}")
    (d / "fold_0" / pr.CHECKPOINT).write_bytes(b"weights")
    return d


def test_export_packages_and_checksums_every_file(tmp_path):
    out = tmp_path / "pkg"
    assert export_model.main(["--trainer-dir", str(trainer_dir(tmp_path)), "--out-dir", str(out)]) == 0
    record = json.loads((out / export_model.CHECKSUMS).read_text())
    assert set(record) == {"plans.json", "dataset.json", f"fold_0/{pr.CHECKPOINT}", pr.TRAINER_FILE,
                           "postprocessing.json", "README.md"}
    assert export_model.verify(out) == []
    assert json.loads((out / "postprocessing.json").read_text())["n_regions"] == 2
    (out / "fold_0" / pr.CHECKPOINT).write_bytes(b"changed")
    assert export_model.verify(out) == [f"fold_0/{pr.CHECKPOINT}"]


def test_export_stops_when_the_checkpoint_is_missing(tmp_path):
    d = trainer_dir(tmp_path)
    (d / "fold_0" / pr.CHECKPOINT).unlink()
    assert export_model.main(["--trainer-dir", str(d), "--out-dir", str(tmp_path / "p")]) == 1


def test_model_card_states_the_release_terms():
    text = export_model.model_card_text()
    assert text.startswith("---\nlicense: cc-by-nc-sa-4.0")
    for phrase in ("CC BY-NC-SA 4.0", "KiTS23", "nnU-Net", "not for clinical use"):
        assert phrase in text
    assert "](../" not in text


def test_cli_writes_the_segmentation_and_summary(tmp_path):
    src = write_nifti(tmp_path / "scan.nii.gz", np.zeros((16, 16, 16), np.int16))
    out, summary = tmp_path / "o" / "seg.nii.gz", tmp_path / "s.json"
    seen = {}

    def factory(model_dir, options):
        seen["options"] = options
        return FakeModel()

    code = predict.main(["--model-dir", "m", "--input", str(src), "--output", str(out), "--summary", str(summary),
                         "--no-tta", "--tile-step", "0.75"], model_factory=factory)
    assert code == 0 and out.exists()
    assert seen["options"] == pr.Options(tta=False, tile_step=0.75)
    assert json.loads(summary.read_text())["options"]["tta"] is False


def test_cli_reports_an_invalid_scan(tmp_path, capsys):
    bad = tmp_path / "bad.nii.gz"
    bad.write_bytes(b"x")
    code = predict.main(["--model-dir", "m", "--input", str(bad), "--output", str(tmp_path / "o.nii.gz")],
                        model_factory=lambda *_: FakeModel())
    assert code == 1 and "STOP" in capsys.readouterr().out


def test_benchmark_covers_the_three_required_settings():
    s = benchmark.SETTINGS
    assert s["full"] == pr.Options()
    assert (s["no_tta"].tta, s["no_tta"].tile_step) == (False, 0.5)
    assert (s["no_tta_step_0.75"].tta, s["no_tta_step_0.75"].tile_step) == (False, 0.75)


def test_benchmark_never_picks_a_test_case():
    roles = {f"case_{i:05d}": ("val" if i % 3 == 0 else "test") for i in range(90)}
    cases = benchmark.choose_cases(roles, 6)
    assert len(set(cases)) == 6 and all(roles[c] == "val" for c in cases)


def test_label_dice():
    a = np.array([0, 1, 1, 2])
    assert benchmark.label_dice(a, a) == 1.0
    assert benchmark.label_dice(a, np.array([0, 1, 0, 2])) == (2 / 3 + 1) / 2
    assert benchmark.label_dice(np.zeros(3), np.zeros(3)) == 1.0
