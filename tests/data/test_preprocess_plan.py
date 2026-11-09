import json

import pytest

from project3d.data import preprocess_plan as pp


def test_resampled_mvox_scales_with_the_target_spacing():
    assert pp.resampled_mvox((100, 512, 512), (2.0, 0.78125, 0.78125), (1.0, 0.78125, 0.78125)) == pytest.approx(
        200 * 512 * 512 / 1e6)


def test_case_mvox_reads_feature_rows():
    rows = [{"case_id": "case_00000", "shape": "100x200x300", "spacing_mm": "1.0000x0.5000x0.5000"}]
    assert pp.case_mvox(rows, (1.0, 1.0, 1.0)) == {"case_00000": pytest.approx(100 * 100 * 150 / 1e6)}


def test_select_cases_excludes_only_large_train_cases():
    roles = {"a": "train", "b": "train", "c": "val", "d": "test"}
    mvox = {"a": 500, "b": 100, "c": 500, "d": 900}
    assert pp.select_cases(roles, mvox, max_mvox=350) == (["b", "c"], ["a"])


def test_filter_splits_drops_the_given_cases():
    splits = [{"train": ["a", "b"], "val": ["c"]}]
    assert pp.filter_splits(splits, ["a"]) == [{"train": ["b"], "val": ["c"]}]


def test_plan_shards_covers_every_case_once_and_balances():
    cases = [f"case_{i:05d}" for i in range(100)]
    mvox = {c: 50 + (i % 7) * 30 for i, c in enumerate(cases)}
    shards = pp.plan_shards(cases, mvox, 4)
    assert [c for s in shards for c in s] == cases
    totals = [sum(mvox[c] for c in s) for s in shards]
    assert max(totals) - min(totals) <= 2 * max(mvox.values())


def test_write_plan_excludes_oversized_cases_and_saves_the_plan(tmp_path):
    roles = {f"case_{i:05d}": "train" for i in range(10)} | {"case_00010": "val", "case_00011": "test"}
    mvox = {c: 100 for c in roles} | {"case_00003": 600}
    plan = pp.write_plan(tmp_path / "plan.json", roles, mvox, n_shards=2)
    assert plan["excluded"] == {"case_00003": 600}
    assert sum(len(s) for s in plan["shards"]) == 10 and plan["shard_mvox"] == [500, 500]
    assert json.loads((tmp_path / "plan.json").read_text()) == plan
