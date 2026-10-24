import json

import build_report
import case_analysis
import evaluate
from helpers import features_csv


def paths(tmp):
    return tmp / "prep.json", tmp / "train.json", tmp / "spec004", tmp / "reports" / "evaluation" / "results.md"


def test_everything_pending_without_records(tmp_path):
    prep, train, ev, out = paths(tmp_path)
    assert build_report.main(["--prep-record", str(prep), "--train-record", str(train),
                              "--eval-dir", str(ev), "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "| post-processed (primary) | *pending* | *pending* |" in text
    assert "| raw | *pending* | *pending* |" in text
    assert "n = *pending*" in text and "Split | *pending*" in text


def test_report_from_records(fake_eval, fake_official):
    prep, train, ev, out = paths(fake_eval["tmp"])
    for tag in ("pp", "raw"):
        assert evaluate.main(["--pred-dir", str(fake_eval["pred"]), "--segs-root", str(fake_eval["segs"]),
                              "--split", str(fake_eval["split"]), "--out-dir", str(ev / f"eval_{tag}")]) == 0
    assert case_analysis.main(["--per-case", str(ev / "eval_pp" / "per_case.csv"),
                               "--case-features", str(features_csv(fake_eval)),
                               "--out-dir", str(ev / "analysis")]) == 0
    prep.write_text(json.dumps({"nnunetv2": "2.8.1", "split_fingerprint_sha256": "f" * 64,
                                "split_totals": {"train": 343, "val": 73, "test": 73}}))
    (ev / "run_record.json").write_text(json.dumps({"disable_tta": False, "postprocessing_applied": True,
                                                    "kits23_evaluator": "fake", "gpu": "T4",
                                                    "predict_hours": 1.2}))
    build_report.main(["--prep-record", str(prep), "--train-record", str(train),
                       "--eval-dir", str(ev), "--out", str(out)])
    text = out.read_text(encoding="utf-8")
    summary = json.loads((ev / "eval_pp" / "summary.json").read_text())
    assert f"{summary['primary']['mean_dice']['mean']:.3f} (95% CI" in text
    assert "343/73/73" in text and "match" in text and "MISMATCH" not in text
    assert "](../../spec004/analysis/analysis.md)" in text
    assert "Training (SPEC 003) | *pending*" in text
    assert "Not valid" not in text


def test_fingerprint_mismatch_and_invalid_primary_are_flagged(fake_eval):
    prep, train, ev, out = paths(fake_eval["tmp"])
    evaluate.main(["--pred-dir", str(fake_eval["pred"]), "--segs-root", str(fake_eval["segs"]),
                   "--split", str(fake_eval["split"]), "--out-dir", str(ev / "eval_pp"), "--no-official"])
    prep.write_text(json.dumps({"split_fingerprint_sha256": "0" * 64}))
    build_report.main(["--prep-record", str(prep), "--train-record", str(train),
                       "--eval-dir", str(ev), "--out", str(out)])
    text = out.read_text(encoding="utf-8")
    assert "**MISMATCH**" in text and "Not valid" in text
