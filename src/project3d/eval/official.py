"""Thin wrapper around the official KiTS23 evaluator (co-primary metrics, D-012).

Requires ``pip install git+https://github.com/neheller/kits23`` (done in the
Kaggle notebook). The official ``compute_metrics_for_case`` returns a 3x2
array: HECs (kidney_and_mass, mass, tumor) x (Dice, surface Dice). Its own
shape/spacing checks are ineffective, so evaluate.py checks geometry first.
"""

from __future__ import annotations

from .metrics import HECS, SD_TOLERANCES_MM


def check_config() -> None:
    """Fail if the installed evaluator's classes or tolerances differ from ours."""
    from kits23.configuration import labels

    assert list(labels.HEC_NAME_LIST) == list(HECS), labels.HEC_NAME_LIST
    for name, lab in HECS.items():
        assert tuple(labels.KITS_HEC_LABEL_MAPPING[name]) == lab, name
        assert abs(labels.HEC_SD_TOLERANCES_MM[name] - SD_TOLERANCES_MM[name]) < 1e-12, name


def official_case(pred_path: str, ref_path: str) -> dict:
    """Official Dice and surface Dice for one case, as ``<region>_dice_official`` and ``_sd_official``."""
    from kits23.evaluation.metrics import compute_metrics_for_case

    scores = compute_metrics_for_case(str(pred_path), str(ref_path))
    out = {}
    for i, name in enumerate(HECS):
        out[f"{name}_dice_official"] = float(scores[i, 0])
        out[f"{name}_sd_official"] = float(scores[i, 1])
    return out


def official_version() -> str:
    """Installed kits23 version plus the git commit pip recorded, if any."""
    import importlib.metadata as md
    import json

    dist = md.distribution("kits23")
    commit = ""
    direct = dist.read_text("direct_url.json")
    if direct:
        commit = json.loads(direct).get("vcs_info", {}).get("commit_id", "")
    return f"{dist.version} {commit}".strip()
