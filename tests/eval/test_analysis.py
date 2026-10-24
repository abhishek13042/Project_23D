import json

import numpy as np
import pytest

import case_analysis
import evaluate
from project3d.eval import analysis


def features_csv(fx):
    """case_features.csv in the SPEC 002 format for the fake cases."""
    path = fx["tmp"] / "case_features.csv"
    lines = ["case_id,cohort,shape,spacing_mm,kidney_ml,tumor_ml,cyst_ml,has_tumor,has_cyst,size_bin"]
    for i, cid in enumerate(fx["ids"]):
        tumor = 4 * (i % 4) * 0.002
        size = ["none", "small", "medium", "large"][i % 4]
        lines.append(f"{cid},{'kits21' if i < 6 else 'kits23_new'},12x10x8,1x1x2,0.06,{tumor},"
                     f"{2 * (i % 2) * 0.002},{tumor > 0},{i % 2 == 1},{size}")
    path.write_text("\n".join(lines) + "\n")
    return path


def test_case_analysis_end_to_end(fake_eval):
    out_eval = fake_eval["tmp"] / "eval"
    assert evaluate.main(["--pred-dir", str(fake_eval["pred"]), "--segs-root", str(fake_eval["segs"]),
                          "--split", str(fake_eval["split"]), "--out-dir", str(out_eval),
                          "--no-official"]) == 0
    out = fake_eval["tmp"] / "analysis"
    code = case_analysis.main(["--per-case", str(out_eval / "per_case.csv"),
                               "--case-features", str(features_csv(fake_eval)),
                               "--images-root", str(fake_eval["images"]),
                               "--segs-root", str(fake_eval["segs"]),
                               "--pred-dir", str(fake_eval["pred"]), "--out-dir", str(out)])
    assert code == 0
    res = json.loads((out / "analysis.json").read_text())
    assert res["n_cases"] == 10
    sizes = [g["group"] for g in res["tables"]["size_bin"]["tumor_dice"]]
    assert sizes == ["none", "small", "medium", "large"]
    assert sum(g["n"] for g in res["tables"]["cohort"]["mean_dice"]) == 10
    assert len(res["figures"]) == 5  # 2 box plots + best/median/worst overlays
    for name in res["figures"]:
        assert (out / "figures" / name).stat().st_size > 1000
    assert "Performance by case characteristics" in (out / "analysis.md").read_text(encoding="utf-8")


def test_quartiles_and_examples():
    feats = [{"case_id": f"c{i}", "cohort": "kits21", "size_bin": "small", "has_cyst": "False",
              "has_tumor": "True", "kidney_ml": str(i), "tumor_ml": "1", "cyst_ml": "0"} for i in range(8)]
    per = [{"case_id": f"c{i}", "mean_dice": str(i / 10), "mean_sd": "nan", "tumor_pred_ml": "1",
            "kidney_and_mass_dice": "1", "mass_dice": "1", "tumor_dice": str(i / 10)} for i in range(8)]
    rows = analysis.join_rows(per, feats)
    assert [r["fg_volume_quartile"] for r in rows] == ["Q1", "Q1", "Q2", "Q2", "Q3", "Q3", "Q4", "Q4"]
    assert analysis.pick_examples(rows) == {"worst": "c0", "median": "c4", "best": "c7"}


def test_spearman_ci():
    x = np.arange(30.0)
    s = analysis.spearman_with_ci(x, x ** 2)
    assert s["rho"] == pytest.approx(1.0)
    assert s["ci95"][0] > 0.9
    assert analysis.spearman_with_ci(x[:5], x[:5])["rho"] is None
