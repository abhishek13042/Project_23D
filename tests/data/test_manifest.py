import gzip
import shutil

from project3d.data import manifest as m


def test_matching_files_all_verify_ok(fake_kits):
    exp = m.load_manifest(fake_kits["manifest"])
    rows = m.verify_kind(exp, "image", fake_kits["images"])
    assert m.summarize(rows) == {m.OK: 6}
    assert set(m.resolved_paths(rows)) == set(fake_kits["ids"])


def test_missing_hash_mismatch_unexpected(fake_kits):
    segs = fake_kits["segs"]
    (segs / "case_00001.nii.gz").unlink()
    # Same size, different bytes -> hash mismatch.
    p = segs / "case_00002.nii.gz"
    data = bytearray(p.read_bytes())
    data[-1] ^= 0xFF
    p.write_bytes(bytes(data))
    shutil.copy(segs / "case_00400.nii.gz", segs / "case_00999.nii.gz")
    exp = m.load_manifest(fake_kits["manifest"])
    status = {r["case_id"]: r["status"] for r in m.verify_kind(exp, "segmentation", segs)}
    assert status["case_00001"] == m.MISSING
    assert status["case_00002"] == m.HASH_MISMATCH
    assert status["case_00999"] == "UNEXPECTED"
    assert status["case_00400"] == m.OK


def test_size_mismatch_duplicate_and_decompressed(fake_kits):
    imgs = fake_kits["images"]
    with open(imgs / "case_00001.nii.gz", "ab") as fh:
        fh.write(b"x")
    (imgs / "copy").mkdir()
    shutil.copy(imgs / "case_00002.nii.gz", imgs / "copy" / "case_00002.nii.gz")
    raw = gzip.decompress((imgs / "case_00400.nii.gz").read_bytes())
    (imgs / "case_00400.nii.gz").unlink()
    (imgs / "case_00400.nii").write_bytes(raw)
    exp = m.load_manifest(fake_kits["manifest"])
    status = {r["case_id"]: r["status"] for r in m.verify_kind(exp, "image", imgs)}
    assert status["case_00001"] == m.SIZE_MISMATCH
    assert status["case_00002"] == m.DUPLICATE
    assert status["case_00400"] == m.DECOMPRESSED


def test_real_manifest_lists_every_case_twice():
    from pathlib import Path

    tsv = Path(__file__).resolve().parents[2] / "data" / "sources" / "kits23_v0.1.4_files.tsv"
    exp = m.load_manifest(tsv)
    assert len(exp) == 978
    ids = {c for c, _ in exp}
    assert len(ids) == 489
    assert all(len(e.sha256) == 64 for e in exp.values())
