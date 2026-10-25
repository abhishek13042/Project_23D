import pytest

import preprocess_shard as ps


def test_find_plans_dir(tmp_path):
    with pytest.raises(SystemExit):
        ps.find_plans_dir(tmp_path)
    d = tmp_path / "prep" / ps.DATASET
    d.mkdir(parents=True)
    (d / "shard_plan.json").write_text("{}")
    (d / "nnUNetPlans.json").write_text("{}")
    assert ps.find_plans_dir(tmp_path) == d


def test_is_done_needs_all_three_files(tmp_path):
    for s in (".b2nd", "_seg.b2nd"):
        (tmp_path / f"case_00000{s}").write_text("")
    assert not ps.is_done(tmp_path, "case_00000")
    (tmp_path / "case_00000.pkl").write_text("")
    assert ps.is_done(tmp_path, "case_00000")
