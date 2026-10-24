import json

import pytest

import prepare_kits23
from project3d.data import nnunet_export


def run(fake, *extra):
    out, raw = fake["tmp"] / "out", fake["tmp"] / "raw"
    code = prepare_kits23.main([
        "--manifest", str(fake["manifest"]),
        "--images-root", str(fake["images"]), "--segs-root", str(fake["segs"]),
        "--out-dir", str(out), "--raw-root", str(raw), "--link-mode", "copy", *extra])
    return code, out, raw


def test_end_to_end(fake_kits):
    code, out, raw = run(fake_kits)
    assert code == 0
    for name in ("verify_report.csv", "case_features.csv", "split.json", "splits_final.json"):
        assert (out / name).exists()
    rec = json.loads((out / "split.json").read_text())
    roles = rec["roles"]
    assert set(roles) == set(fake_kits["ids"])
    assert len(rec["fingerprint_sha256"]) == 64

    ds = raw / "Dataset220_KiTS2023"
    meta = json.loads((ds / "dataset.json").read_text())
    trainval = sorted(c for c, r in roles.items() if r != "test")
    assert meta["numTraining"] == len(trainval)
    assert meta["regions_class_order"] == [1, 3, 2]
    assert meta["file_ending"] == ".nii.gz"
    assert sorted(p.name for p in (ds / "labelsTr").iterdir()) == [f"{c}.nii.gz" for c in trainval]
    assert sorted(p.name for p in (ds / "imagesTr").iterdir()) == [f"{c}_0000.nii.gz" for c in trainval]
    test = sorted(c for c, r in roles.items() if r == "test")
    imgs_ts = sorted(p.name for p in (ds / "imagesTs").iterdir()) if test else []
    assert imgs_ts == [f"{c}_0000.nii.gz" for c in test]
    assert not (ds / "labelsTs").exists()


def test_stops_on_corrupt_file(fake_kits, capsys):
    p = fake_kits["segs"] / "case_00400.nii.gz"
    data = bytearray(p.read_bytes())
    data[-1] ^= 0xFF
    p.write_bytes(bytes(data))
    code, out, raw = run(fake_kits)
    assert code == 1
    assert "STOP" in capsys.readouterr().out
    assert not (out / "split.json").exists()


def test_stops_on_missing_case_unless_subset(fake_kits):
    (fake_kits["images"] / "case_00588.nii.gz").unlink()
    assert run(fake_kits)[0] == 1
    code, out, _ = run(fake_kits, "--subset")
    assert code == 0
    assert "case_00588" not in json.loads((out / "split.json").read_text())["roles"]


def test_detect_roots(fake_kits, monkeypatch):
    monkeypatch.setattr(prepare_kits23, "IMAGE_MIN_BYTES", 1500)
    sizes = [p.stat().st_size for p in fake_kits["images"].iterdir()]
    seg_sizes = [p.stat().st_size for p in fake_kits["segs"].iterdir()]
    if not min(sizes) >= 1500 > max(seg_sizes):
        pytest.skip("fake file sizes do not separate at the test threshold")
    images, segs = prepare_kits23.detect_roots(fake_kits["tmp"] / "in")
    assert images == fake_kits["images"] and segs == fake_kits["segs"]
    # a small extra folder of label files (e.g. validation predictions) is ignored
    extra = fake_kits["tmp"] / "in" / "results" / "validation"
    extra.mkdir(parents=True)
    first = sorted(fake_kits["segs"].iterdir())[0]
    (extra / first.name).write_bytes(first.read_bytes())
    with pytest.raises(SystemExit):
        prepare_kits23.detect_roots(fake_kits["tmp"] / "in")
    n = len(list(fake_kits["segs"].iterdir()))
    assert prepare_kits23.detect_roots(fake_kits["tmp"] / "in", min_files=n) == (images, segs)
    # images split over two staging shards are merged into one linked folder
    shard = fake_kits["tmp"] / "in" / "shard2" / "images"
    shard.mkdir(parents=True)
    for p in sorted(images.iterdir())[:3]:
        p.rename(shard / p.name)
    with pytest.raises(SystemExit):
        prepare_kits23.detect_roots(fake_kits["tmp"] / "in", min_files=n)
    link = fake_kits["tmp"] / "merged"
    merged, segs2 = prepare_kits23.detect_roots(fake_kits["tmp"] / "in", min_files=n,
                                                link_dir=link, link_mode="copy")
    assert segs2 == segs and merged == link / "images"
    assert sorted(p.name for p in merged.iterdir()) == [f"{c}.nii.gz" for c in fake_kits["ids"]]


def test_leak_check_catches_test_case(fake_kits):
    _, out, raw = run(fake_kits)
    roles = json.loads((out / "split.json").read_text())["roles"]
    ds = raw / "Dataset220_KiTS2023"
    nnunet_export.check_no_test_leak(ds, roles)  # the real split is clean
    victim = next(c for c, r in roles.items() if r != "test")
    with pytest.raises(AssertionError):
        nnunet_export.check_no_test_leak(ds, {**roles, victim: "test"})


def test_stops_on_geometry_mismatch(fake_kits, capsys):
    import hashlib

    from helpers import make_seg, write_nifti
    p = write_nifti(fake_kits["segs"] / "case_00002.nii.gz", make_seg(tumor=5), spacing=(1.0, 1.0, 3.0))
    lines = fake_kits["manifest"].read_text().splitlines()
    for i, line in enumerate(lines):  # re-pin the changed file so only geometry fails
        if line.startswith("case_00002\tsegmentation"):
            cid, kind, _, _, url = line.split("\t")
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            lines[i] = "\t".join([cid, kind, str(p.stat().st_size), digest, url])
    fake_kits["manifest"].write_text("\n".join(lines) + "\n")
    code, out, _ = run(fake_kits)
    assert code == 1
    assert "geometry mismatch" in capsys.readouterr().out
    assert not (out / "split.json").exists()
