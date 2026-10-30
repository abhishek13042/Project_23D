import hashlib
import json

import pytest
import stage_kits23

ROOT = stage_kits23.Path(__file__).resolve().parents[2]


def test_real_manifest_shards_cover_every_file_once_under_20gb():
    rows = stage_kits23.load_rows(ROOT / "data/sources/kits23_v0.1.4_files.tsv")
    shards = [stage_kits23.plan_shard(rows, k, 3) for k in (1, 2, 3)]
    keys = [(r["case_id"], r["kind"]) for s in shards for r in s]
    assert len(keys) == len(set(keys)) == len(rows) == 978
    for s in shards:
        assert sum(r["size_bytes"] for r in s) < 19e9
    assert all(r["kind"] == "image" for s in shards[1:] for r in s)
    with pytest.raises(ValueError):
        stage_kits23.plan_shard(rows, 4, 3)


def make_source(tmp_path, n=4):
    src, lines = tmp_path / "src", ["case_id\tkind\tsize_bytes\tsha256\turl"]
    src.mkdir()
    for i in range(n):
        for kind, size in (("image", 3000 + i), ("segmentation", 100 + i)):
            p = src / f"case_{i:05d}_{kind}.nii.gz"
            p.write_bytes(bytes([i]) * size)
            lines.append(f"case_{i:05d}\t{kind}\t{size}\t{hashlib.sha256(p.read_bytes()).hexdigest()}"
                         f"\t{p.as_uri()}")
    tsv = tmp_path / "files.tsv"
    tsv.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return src, tsv


def test_download_verifies_and_reports(tmp_path, monkeypatch):
    monkeypatch.setattr(stage_kits23.time, "sleep", lambda s: None)
    src, tsv = make_source(tmp_path)
    out = tmp_path / "out"
    assert stage_kits23.main(["--manifest", str(tsv), "--shard", "1", "--n-shards", "2",
                              "--out-dir", str(out)]) == 0
    rec = json.loads((out / "stage_record.json").read_text())
    assert rec["ok"] == rec["files"] == 2 + 4 and rec["segmentations"] == 4 and not rec["failed"]
    assert sorted(p.name for p in (out / "images").iterdir()) == ["case_00000.nii.gz", "case_00001.nii.gz"]
    # a source file that no longer matches the manifest is retried, then reported
    (src / "case_00003_image.nii.gz").write_bytes(b"x" * 3003)
    out2 = tmp_path / "out2"
    assert stage_kits23.main(["--manifest", str(tsv), "--shard", "2", "--n-shards", "2",
                              "--out-dir", str(out2)]) == 1
    rec = json.loads((out2 / "stage_record.json").read_text())
    assert [(f["case_id"], f["status"]) for f in rec["failed"]] == [("case_00003", "HASH_MISMATCH")]
    assert not list((out2 / "images").glob("*.part"))
