import random

import pytest

from project3d.data import split as s


def synthetic_rows(n=489, seed=1):
    """Rows shaped like KiTS23 features: two cohorts, size bins, ~30% cysts."""
    rng = random.Random(seed)
    ids = [f"case_{i:05d}" for i in range(300)] + [f"case_{i:05d}" for i in range(400, 400 + n - 300)]
    return [{
        "case_id": cid,
        "cohort": "kits21" if int(cid[5:]) <= 299 else "kits23_new",
        "size_bin": rng.choice(["none", "small", "medium", "large", "small", "medium", "large"]),
        "has_cyst": rng.random() < 0.3,
    } for cid in ids]


def test_exact_global_counts_and_disjoint():
    rows = synthetic_rows()
    roles = s.make_split(rows)
    counts = {r: list(roles.values()).count(r) for r in s.ROLES}
    assert counts == {"train": 489 - 73 - 73, "val": 73, "test": 73}
    assert set(roles) == {r["case_id"] for r in rows}


def test_deterministic_and_seed_sensitive():
    rows = synthetic_rows()
    a, b = s.make_split(rows, seed=42), s.make_split(list(reversed(rows)), seed=42)
    assert a == b  # input order does not matter
    assert s.fingerprint(a) == s.fingerprint(b)
    assert s.fingerprint(s.make_split(rows, seed=7)) != s.fingerprint(a)


def test_every_stratum_is_proportional():
    rows = synthetic_rows()
    roles = s.make_split(rows)
    strata = {}
    for r in rows:
        strata.setdefault(s.stratum_key(r), []).append(roles[r["case_id"]])
    for key, members in strata.items():
        n = len(members)
        assert abs(members.count("test") - 0.15 * n) <= 1, key
        assert abs(members.count("val") - 0.15 * n) <= 1, key


def test_nnunet_splits_exclude_test():
    roles = s.make_split(synthetic_rows())
    (fold0,) = s.nnunet_splits(roles)
    test = {c for c, r in roles.items() if r == "test"}
    assert not test & (set(fold0["train"]) | set(fold0["val"]))
    assert len(fold0["train"]) + len(fold0["val"]) + len(test) == 489


def test_rejects_duplicates_and_bad_fractions():
    rows = synthetic_rows(n=310)
    with pytest.raises(ValueError):
        s.make_split(rows + rows[:1])
    with pytest.raises(ValueError):
        s.make_split(rows, fractions=(0.8, 0.15, 0.15))


def test_summary_totals():
    rows = synthetic_rows()
    roles = s.make_split(rows)
    summ = s.summary(rows, roles)
    assert sum(summ["total"].values()) == 489
    assert sum(sum(v.values()) for v in summ["cohort"].values()) == 489
