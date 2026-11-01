import subprocess
import sys

import package_space


def test_the_assembled_space_needs_nothing_from_the_repository(tmp_path):
    package_space.package(tmp_path)
    assert (tmp_path / "app.py").exists() and (tmp_path / "README.md").exists()
    # -I ignores the repository's paths, so only the assembled folder can supply project3d
    code = "import sys; sys.path.insert(0, '.'); import service; print(service.DISCLAIMER)"
    out = subprocess.run([sys.executable, "-I", "-c", code], cwd=tmp_path, capture_output=True, text=True, check=True)
    assert "not for clinical use" in out.stdout


def test_the_space_card_states_the_license_and_the_disclaimer(tmp_path):
    package_space.package(tmp_path)
    card = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "license: cc-by-nc-sa-4.0" in card
    assert "Research demo, not for clinical use" in card
