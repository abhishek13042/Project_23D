"""SPEC 012: the health check and the history scan."""

import pytest
from health_check import failures, targets
from scan_history import path_problem, scan, secret_problems


def test_targets_cover_pages_cases_and_gallery_files():
    urls = targets("https://site.test/", "https://files.test/g/", ["case_00001"])
    assert "https://site.test/" in urls
    assert "https://site.test/case/case_00001" in urls
    assert "https://files.test/g/case_00001/gt.nii.gz" in urls


def test_targets_skip_gallery_files_until_they_are_published():
    assert not [url for url in targets("https://site.test", "", ["case_00001"]) if url.endswith(".gz")]


def test_failures_keep_only_what_is_down():
    status = {"https://a.test": 200, "https://b.test": 503, "https://c.test": 0}
    assert failures(list(status), status.__getitem__) == [("https://b.test", 503), ("https://c.test", 0)]


@pytest.mark.parametrize(
    "path",
    [
        "a/case.nii.gz",
        "scan.nii",
        "checkpoint_best.pth",
        "model.safetensors",
        ".env",
        "apps/web/.env.local",
        "reports/figures/overlay_case_1.png",
    ],
)
def test_forbidden_paths_are_reported(path):
    assert path_problem(path, 10)


@pytest.mark.parametrize("path", ["apps/web/.env.example", "src/a.py", "reports/release/gallery_index.json"])
def test_ordinary_paths_pass(path):
    assert path_problem(path, 10) is None


def test_large_files_are_reported():
    assert path_problem("notebooks/a.ipynb", 20_000_000)


@pytest.mark.parametrize(
    "secret",
    [
        b"hf_" + b"a1" * 16,
        b"ghp_" + b"a" * 36,
        b"postgresql://neondb_owner:" + b"s3cret" + b"@host/db",
        b"-----BEGIN " + b"PRIVATE KEY-----",
    ],
)
def test_secrets_are_found(secret):
    assert secret_problems(b"value = " + secret)


def test_placeholders_are_not_secrets():
    assert not secret_problems(b"DATABASE_URL=\npostgres://user:password@host/db\nhf_token = os.environ['HF_TOKEN']")


def test_the_real_history_is_clean():
    assert scan() == []
