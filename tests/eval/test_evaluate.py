import csv
import json

import evaluate
import numpy as np
import pytest
from helpers import write_nifti


def run(fx, *extra):
    out = fx["tmp"] / "eval"
    code = evaluate.main(["--pred-dir", str(fx["pred"]), "--segs-root", str(fx["segs"]),
                          "--split", str(fx["split"]), "--out-dir", str(out), *extra])
    return code, out


def test_official_path(fake_eval, fake_official):
    code, out = run(fake_eval)
    assert code == 0
    s = json.loads((out / "summary.json").read_text())
    rows = list(csv.DictReader((out / "per_case.csv").read_text().splitlines()))
    assert s["n_cases"] == 10 == len(rows)  # test role only
    assert {r["case_id"] for r in rows} == {c for c, r in fake_eval["roles"].items() if r == "test"}
    assert s["primary_valid"] and s["kits23_evaluator"] == "fake"
    assert s["dice_crosscheck_max_abs_diff"] == pytest.approx(0.0)
    md = [float(r["mean_dice"]) for r in rows]
    assert s["primary"]["mean_dice"]["mean"] == pytest.approx(np.mean(md))
    assert s["primary"]["mean_surface_dice"]["mean"] == pytest.approx(0.9 * np.mean(md))
    assert s["primary"]["mean_dice"]["ci95"] is not None
    # case_00000 has no tumor in the reference and a perfect prediction -> tumor Dice 1
    r0 = next(r for r in rows if r["case_id"] == "case_00000")
    assert float(r0["tumor_dice_official"]) == 1.0
    assert s["regions"]["tumor"]["n_ref_empty"] == 3


def test_no_official_marks_primary_invalid(fake_eval):
    code, out = run(fake_eval, "--no-official")
    assert code == 0
    s = json.loads((out / "summary.json").read_text())
    assert s["primary_valid"] is False
    assert s["primary"]["mean_surface_dice"]["n"] == 0


def test_config_mismatch_fails(fake_eval, fake_official):
    fake_official.HEC_SD_TOLERANCES_MM["tumor"] = 2.0
    with pytest.raises(AssertionError):
        run(fake_eval)


def test_stops_on_missing_prediction(fake_eval, capsys):
    (fake_eval["pred"] / "case_00003.nii.gz").unlink()
    code, out = run(fake_eval, "--no-official")
    assert code == 1 and "case_00003" in capsys.readouterr().out
    assert not (out / "summary.json").exists()


def test_rejects_misaligned_prediction(fake_eval):
    p = fake_eval["pred"] / "case_00001.nii.gz"
    import nibabel as nib
    write_nifti(p, np.asanyarray(nib.load(str(p)).dataobj), spacing=(2.0, 1.0, 2.0))
    with pytest.raises(ValueError, match="geometry mismatch"):
        run(fake_eval, "--no-official")
