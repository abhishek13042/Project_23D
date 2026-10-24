"""SPEC 005 / E-005: performance by case characteristics (no GPU).

Descriptive only: group sizes are small (73 test cases), so the tables give
n, mean, median and a bootstrap CI per group, and no significance claims are
made (docs/evaluation.md, statistical reporting).
"""

from __future__ import annotations

import numpy as np
from scipy import stats as sps

from .stats import bootstrap_ci, describe

SIZE_ORDER = ["none", "small", "medium", "large"]
METRICS = ["mean_dice", "mean_sd", "kidney_and_mass_dice", "mass_dice", "tumor_dice"]
FACTORS = ["size_bin", "has_cyst", "cohort", "fg_volume_quartile"]


def _num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def _truthy(v) -> bool:
    return str(v).strip().lower() in ("true", "1")


def join_rows(per_case: list[dict], case_features: list[dict]) -> list[dict]:
    """Merge metrics with SPEC 002 features and add the foreground-volume quartile.

    ``tumor_dice`` etc. prefer the official columns when present.
    """
    feats = {r["case_id"]: r for r in case_features}
    rows = []
    for pc in per_case:
        f = feats[pc["case_id"]]
        row = {"case_id": pc["case_id"], "cohort": f["cohort"], "size_bin": f["size_bin"],
               "has_cyst": _truthy(f["has_cyst"]), "has_tumor": _truthy(f["has_tumor"]),
               "tumor_ml": _num(f["tumor_ml"]),
               "fg_ml": _num(f["kidney_ml"]) + _num(f["tumor_ml"]) + _num(f["cyst_ml"]),
               "mean_dice": _num(pc["mean_dice"]), "mean_sd": _num(pc["mean_sd"]),
               "tumor_pred_ml": _num(pc["tumor_pred_ml"])}
        for h in ("kidney_and_mass", "mass", "tumor"):
            row[f"{h}_dice"] = _num(pc.get(f"{h}_dice_official", pc[f"{h}_dice"]))
        rows.append(row)
    fg = np.array([r["fg_ml"] for r in rows])
    cuts = np.quantile(fg, [0.25, 0.5, 0.75]) if len(rows) else []
    for r in rows:
        r["fg_volume_quartile"] = f"Q{int(np.searchsorted(cuts, r['fg_ml'], side='left')) + 1}"
    return rows


def group_table(rows: list[dict], factor: str, metric: str) -> list[dict]:
    groups = sorted({r[factor] for r in rows},
                    key=lambda g: SIZE_ORDER.index(g) if g in SIZE_ORDER else str(g))
    out = []
    for g in groups:
        vals = [r[metric] for r in rows if r[factor] == g]
        d = describe(vals)
        out.append({"group": str(g), "n": d["n"], "mean": d.get("mean"),
                    "median": d.get("median"), "ci95": bootstrap_ci(vals)})
    return out


def spearman_with_ci(x, y, n_boot: int = 2000, seed: int = 42) -> dict:
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
        i = rng.integers(0, x.size, x.size)
        r = sps.spearmanr(x[i], y[i]).statistic
        if not np.isnan(r):
            boots.append(r)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"n": int(x.size), "rho": rho, "ci95": [float(lo), float(hi)]}


def analyse(rows: list[dict], n_worst: int = 10) -> dict:
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
    s = sorted(rows, key=lambda r: (r[metric], r["case_id"]))
    return {"worst": s[0]["case_id"], "median": s[len(s) // 2]["case_id"], "best": s[-1]["case_id"]}


def to_markdown(result: dict) -> str:
    def fmt(v):
        return "–" if v is None else f"{v:.3f}"

    def ci(c):
        return "–" if c is None else f"{c[0]:.3f} to {c[1]:.3f}"

    lines = [f"# E-005 — Performance by case characteristics (n = {result['n_cases']})", "",
             "Descriptive only; groups are small and no significance test is made.", ""]
    for factor, by_metric in result["tables"].items():
        lines += [f"## {factor}", "",
                  "| group | n | mean Dice | 95% CI | tumor Dice | 95% CI | mean surface Dice |",
                  "|---|---|---|---|---|---|---|"]
        for md, td, sd in zip(by_metric["mean_dice"], by_metric["tumor_dice"], by_metric["mean_sd"]):
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
