"""SPEC 005 / E-005: performance by case characteristics (no GPU).

Descriptive only: group sizes are small (73 test cases), so the tables give
n, mean, median and a bootstrap CI per group, and no significance claims are
made (docs/evaluation.md, statistical reporting).
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
from scipy import stats as sps

from .stats import bootstrap_ci, describe

SIZE_ORDER = ["none", "small", "medium", "large"]
METRICS = ["mean_dice", "mean_sd", "kidney_and_mass_dice", "mass_dice", "tumor_dice"]
FACTORS = ["size_bin", "has_cyst", "cohort", "fg_volume_quartile"]


def _num(value: object) -> float:
    """The value as a float, or NaN when it is blank or not a number."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _truthy(value: object) -> bool:
    """True for the CSV spellings ``True`` and ``1``."""
    return str(value).strip().lower() in ("true", "1")


def join_rows(per_case: list[dict], case_features: list[dict]) -> list[dict]:
    """Merge metrics with SPEC 002 features and add the foreground-volume quartile.

    ``tumor_dice`` etc. prefer the official columns when present.
    """
    features_by_case = {r["case_id"]: r for r in case_features}
    rows = []
    for metrics in per_case:
        feat = features_by_case[metrics["case_id"]]
        row = {"case_id": metrics["case_id"], "cohort": feat["cohort"], "size_bin": feat["size_bin"],
               "has_cyst": _truthy(feat["has_cyst"]), "has_tumor": _truthy(feat["has_tumor"]),
               "tumor_ml": _num(feat["tumor_ml"]),
               "fg_ml": _num(feat["kidney_ml"]) + _num(feat["tumor_ml"]) + _num(feat["cyst_ml"]),
               "mean_dice": _num(metrics["mean_dice"]), "mean_sd": _num(metrics["mean_sd"]),
               "tumor_pred_ml": _num(metrics["tumor_pred_ml"])}
        for region in ("kidney_and_mass", "mass", "tumor"):
            row[f"{region}_dice"] = _num(metrics.get(f"{region}_dice_official", metrics[f"{region}_dice"]))
        rows.append(row)
    fg = np.array([r["fg_ml"] for r in rows])
    cuts = np.quantile(fg, [0.25, 0.5, 0.75]) if len(rows) else []
    for r in rows:
        r["fg_volume_quartile"] = f"Q{int(np.searchsorted(cuts, r['fg_ml'], side='left')) + 1}"
    return rows


def group_table(rows: list[dict], factor: str, metric: str) -> list[dict]:
    """n, mean, median and bootstrap CI of ``metric`` for each value of ``factor``."""
    groups = sorted({r[factor] for r in rows},
                    key=lambda g: SIZE_ORDER.index(g) if g in SIZE_ORDER else str(g))
    out = []
    for group in groups:
        values = [r[metric] for r in rows if r[factor] == group]
        summary = describe(values)
        out.append({"group": str(group), "n": summary["n"], "mean": summary.get("mean"),
                    "median": summary.get("median"), "ci95": bootstrap_ci(values)})
    return out


def spearman_with_ci(x: npt.ArrayLike, y: npt.ArrayLike, n_boot: int = 2000, seed: int = 42) -> dict:
    """Spearman correlation and a case-bootstrap 95% CI (None if under 10 pairs)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    if x.size < 10:
        return {"n": int(x.size), "rho": None, "ci95": None}
    rho = float(sps.spearmanr(x, y).statistic)
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        sample = rng.integers(0, x.size, x.size)
        resampled_rho = sps.spearmanr(x[sample], y[sample]).statistic
        if not np.isnan(resampled_rho):
            boots.append(resampled_rho)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"n": int(x.size), "rho": rho, "ci95": [float(lo), float(hi)]}


def analyse(rows: list[dict], n_worst: int = 10) -> dict:
    """Group tables, the tumor-volume correlation, no-tumor false positives and the worst cases."""
    tables = {f: {m: group_table(rows, f, m) for m in METRICS} for f in FACTORS}
    tumor = [r for r in rows if r["has_tumor"]]
    no_tumor = [r for r in rows if not r["has_tumor"]]
    worst = sorted(rows, key=lambda r: r["mean_dice"])[:n_worst]
    return {
        "n_cases": len(rows),
        "tables": tables,
        "tumor_volume_vs_tumor_dice": spearman_with_ci(
            [r["tumor_ml"] for r in tumor], [r["tumor_dice"] for r in tumor]),
        "no_tumor_cases": {"n": len(no_tumor),
                           "n_with_predicted_tumor": sum(r["tumor_pred_ml"] > 0 for r in no_tumor)},
        "worst_cases": [{k: r[k] for k in ("case_id", "mean_dice", "tumor_dice", "size_bin",
                                           "has_cyst", "cohort", "tumor_ml")} for r in worst],
    }


def pick_examples(rows: list[dict], metric: str = "mean_dice") -> dict:
    """Best, median and worst case by ``metric`` (ties broken by case ID)."""
    ranked = sorted(rows, key=lambda r: (r[metric], r["case_id"]))
    return {"worst": ranked[0]["case_id"], "median": ranked[len(ranked) // 2]["case_id"],
            "best": ranked[-1]["case_id"]}


def to_markdown(result: dict) -> str:
    """The ``analyse`` result as a Markdown report."""

    def fmt(value: float | None) -> str:
        return "–" if value is None else f"{value:.3f}"

    def ci(interval: list[float] | None) -> str:
        return "–" if interval is None else f"{interval[0]:.3f} to {interval[1]:.3f}"

    lines = [f"# E-005 — Performance by case characteristics (n = {result['n_cases']})", "",
             "Descriptive only; groups are small and no significance test is made.", ""]
    for factor, by_metric in result["tables"].items():
        lines += [f"## {factor}", "",
                  "| group | n | mean Dice | 95% CI | tumor Dice | 95% CI | mean surface Dice |",
                  "|---|---|---|---|---|---|---|"]
        for md, td, sd in zip(by_metric["mean_dice"], by_metric["tumor_dice"], by_metric["mean_sd"], strict=True):
            lines.append(f"| {md['group']} | {md['n']} | {fmt(md['mean'])} | {ci(md['ci95'])} | "
                         f"{fmt(td['mean'])} | {ci(td['ci95'])} | {fmt(sd['mean'])} |")
        lines.append("")
    sp = result["tumor_volume_vs_tumor_dice"]
    lines += ["## Tumor volume vs tumor Dice (tumor cases)", "",
              f"Spearman rho = {fmt(sp['rho'])}, 95% CI {ci(sp['ci95'])}, n = {sp['n']}.", ""]
    nt = result["no_tumor_cases"]
    lines += ["## Cases without tumor", "",
              f"{nt['n_with_predicted_tumor']} of {nt['n']} predicted some tumor (false positive).", "",
              "## Worst cases by mean Dice", "", "| case | mean Dice | tumor Dice | size bin | cyst | cohort |",
              "|---|---|---|---|---|---|"]
    for w in result["worst_cases"]:
        lines.append(f"| {w['case_id']} | {w['mean_dice']:.3f} | {w['tumor_dice']:.3f} | "
                     f"{w['size_bin']} | {w['has_cyst']} | {w['cohort']} |")
    return "\n".join(lines) + "\n"
