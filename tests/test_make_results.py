"""Fast end-to-end test of the results kit on a tiny synthetic run tree."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
sys.path.insert(0, str(ROOT / "scripts" / "run"))
pytest.importorskip("matplotlib")

import make_results  # noqa: E402
import rk_cells  # noqa: E402

UNITS = [f"u{i}" for i in range(6)]
WEEKS = pd.date_range("2018-01-07", periods=60, freq="7D")


def _panel(path: Path) -> None:
    rng = np.random.default_rng(0)
    rows = [{"unit_id": u, "country": "BRAZIL", "adm1": f"S{i % 3}", "week_start": w,
             "year": w.year, "cases": float(rng.poisson(3)), "zero_filled": False, "flag_gap": False}
            for i, u in enumerate(UNITS)
            for w in pd.date_range("2013-01-06", "2019-12-29", freq="7D")]
    pd.DataFrame(rows).to_parquet(path)


def _run(root: Path, name: str, label: str, shift: float, panel: Path, horizons=(1, 2, 3, 4)) -> str:
    d = root / "runs" / name
    d.mkdir(parents=True)
    (d / "config_resolved.yaml").write_text(yaml.safe_dump({"country": "BRAZIL", "panel": str(panel)}))
    pnl = pd.read_parquet(panel).set_index(["unit_id", "week_start"]).cases
    rng = np.random.default_rng(abs(hash(name)) % 2**32)
    rows = []
    for u in UNITS:
        for o in WEEKS:
            for h in horizons:
                t = o + pd.Timedelta(weeks=h)
                rows.append({"run": label, "seed": 0, "test_year": 2019 if o.year >= 2019 else 2018,
                             "unit_id": u, "origin_week": o, "target_week": t, "horizon": h,
                             "cases": float(pnl.get((u, t), 0.0)),
                             "wis_log": 0.2 + shift + 0.05 * rng.random(),
                             "cov_40": float(rng.random() < 0.4), "cov_80": float(rng.random() < 0.8)})
    pd.DataFrame(rows).to_parquet(d / "scores.parquet")
    return f"runs/{name}"


def _cell(cid, dirs, group="primary"):
    return {"id": cid, "group": group, "arm": "history", "country": "brazil", "split": "S1",
            "desc": f"synthetic {cid}", "ref": "L3", "ladder": [], "selection": None,
            "cstar": "C1", "estimands": None, "role_labels": None,
            "primary_horizons": [1, 4], "secondary_horizons": [1, 2, 3, 4],
            "roles": {r: {"dirs": [d], "markers": [None]} for r, d in dirs.items()}}


def test_kit_end_to_end(tmp_path, capsys):
    panel = tmp_path / "panel.parquet"
    _panel(panel)
    dirs = {r: _run(tmp_path, f"x_{r}", f"lgbm-{r}", s, panel)
            for r, s in {"L3": 0.0, "L4": -0.001, "L3C": 0.0, "L4C": 0.0005}.items()}
    pending = {r: f"runs/missing_{r}" for r in rk_cells.ROLES}
    reg = tmp_path / "reg.json"
    reg.write_text(json.dumps([_cell("BR_S1", dirs), _cell("CO_S1", pending)]))
    args = ["--root", str(tmp_path), "--registry", str(reg), "--no-scheduler", "--no-exclusions",
            "--extras", "none", "--in-process"]
    assert make_results.main(args) == 0
    t1 = pd.read_csv(tmp_path / "docs/results/tables/T1_primary_family.csv")
    assert list(t1.status) == ["available", "pending"]
    r = t1.iloc[0]
    assert r.TOST_class in {"equivalent", "superior", "inferior", "inconclusive"}
    assert r.lo95 <= r.G_excess <= r.hi95
    for f in ("T2_ladder.csv", "T3_estimands.csv", "T5_strata.csv", "T6a_sensitivities.csv",
              "T1_primary_family.tex"):
        assert (tmp_path / "docs/results/tables" / f).exists(), f
    assert (tmp_path / "docs/results/figures/F1_forest_G_excess.pdf").exists()
    brief = (tmp_path / "docs/results/RESULTS_BRIEF.md").read_text()
    assert "CO_S1" in brief and "pending" in brief and "G_excess" in brief
    assert "h{1,4}" in brief and "pooled_h1-4" in brief
    # primary pooled = h{1,4} only; S1 secondary row pooled over h1-h4; per-horizon rows kept
    t3 = pd.read_csv(tmp_path / "docs/results/tables/T3_estimands.csv", dtype={"horizon": str})
    t3 = t3[(t3.cell == "BR_S1") & (t3.test_year == "pooled")]
    assert set(t3.horizon) == {"1", "2", "3", "4", "pooled", "pooled_h1-4"}
    assert set(t3[t3.horizon == "pooled"].pooled_over) == {"1,4"}
    assert set(t3[t3.horizon == "pooled_h1-4"].pooled_over) == {"1,2,3,4"}
    from estimands_report import load_cell
    from pop.eval.estimands import infer_estimand
    import os
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        g, _ = load_cell({r: [d] for r, d in dirs.items()}, exclude_units=None, exclude_weeks=None)
    finally:
        os.chdir(cwd)
    for hs, lab in (([1, 4], "pooled"), ([1, 2, 3, 4], "pooled_h1-4")):
        gp = g[g.horizon.isin(hs)].reset_index(drop=True)
        gp.attrs = dict(g.attrs)
        ref = infer_estimand(gp, "G_excess")
        row = t3[(t3.horizon == lab) & (t3.estimand == "G_excess")].iloc[0]
        assert abs(row.estimate - ref["estimate"]) < 1e-12 and abs(row.p - ref["p"]) < 1e-9
        assert abs(row.lo95 - ref["lo95"]) < 1e-12
    assert abs(r.G_excess - t3[(t3.horizon == "pooled") & (t3.estimand == "G_excess")].estimate.iloc[0]) < 1e-12
    assert r.sec_horizons == "pooled_h1-4" and np.isfinite(r.sec_DM_p)
    lad = pd.read_csv(tmp_path / "docs/results/tables/T2_ladder_long.csv", dtype={"horizon": str})
    assert {"pooled", "pooled_h1-4"} <= set(lad.horizon)
    # second run: cache hit, no recomputation
    capsys.readouterr()
    assert make_results.main(args) == 0
    assert "cache hit" in capsys.readouterr().out


def test_run_state(tmp_path):
    d = tmp_path / "r"
    assert rk_cells.run_state(d) == "not started"
    (d / "chunks").mkdir(parents=True)
    (d / "chunks" / "a.done.json").write_text("{}")
    assert rk_cells.run_state(d).startswith("partial")
    (d / "scores.parquet").write_text("x")
    assert rk_cells.run_state(d) == "complete"
    (tmp_path / "pipe").mkdir()
    assert rk_cells.run_state(d, tmp_path / "pipe" / "stage_L3.done") == "stage not done"


def test_cstar_rule_version(tmp_path):
    sel = tmp_path / "x_controls_2019"
    sel.mkdir()
    assert rk_cells._cstar(sel, {"c_star": "C2"}) is None          # plan.json is never used
    (sel / "selection.json").write_text(json.dumps({"c_star": "C4"}))   # pre-fix (no rule_version)
    assert rk_cells._cstar(sel) is None
    assert rk_cells.cstar_label({"cstar": rk_cells._cstar(sel)}) == "selection pending (stale)"
    (sel / "selection.json").write_text(json.dumps({"c_star": "C1", "rule_version": 2}))
    assert rk_cells._cstar(sel) == "C1"


def test_resolve_horizons():
    import rk_compute
    assert rk_compute.resolve_horizons([1, 2, 3, 4], [1, 4], [1, 2, 3, 4]) == ([1, 4], [1, 2, 3, 4])
    assert rk_compute.resolve_horizons([1, 4], [1, 4], [1, 2, 3, 4]) == ([1, 4], None)
    assert rk_compute.resolve_horizons([1, 2], None, None) == ([1, 2], None)
    assert rk_compute.sec_label([1, 2, 3, 4]) == "pooled_h1-4"


# ---------------------------------------------------------------- results kit v3
def _two_year_cell(tmp_path):
    panel = tmp_path / "panel.parquet"
    _panel(panel)
    dirs = {r: _run(tmp_path, f"y_{r}", f"lgbm-{r}", s, panel)
            for r, s in {"L3": 0.0, "L4": -0.001, "L3C": 0.0, "L4C": 0.0005}.items()}
    return panel, dirs


def test_origin_year_filter():
    import rk_compute as K
    g = pd.DataFrame({"origin_week": pd.to_datetime(["2019-12-29", "2020-01-05", "2019-12-22",
                                                     "2020-01-26"]),
                      "target_week": pd.to_datetime(["2020-01-05", "2020-01-12", "2020-01-19",
                                                     "2020-02-02"]),
                      "test_year": [2020, 2020, 2020, 2020], "horizon": [1, 1, 4, 1]})
    # 2019-12-29 (Sunday): its Wednesday is 2020-01-01 -> epi-year 2020 (kept)
    assert list(K.origin_year_mask(g)) == [True, True, False, True]
    f, info = K.apply_row_filter(g.assign(x=1), "origin_year")
    assert len(f) == 3 and info["rows_dropped_by_filter"] == 1
    assert K.apply_row_filter(g, None)[0] is g
    with pytest.raises(ValueError):
        K.apply_row_filter(g, "nope")


def test_kit_v3_filter_t1_and_strata(tmp_path):
    import rk_compute as K
    from estimands_report import load_cell
    from pop.eval.estimands import infer_estimand
    import os
    panel, dirs = _two_year_cell(tmp_path)
    cell = _cell("BR_S1", dirs)
    cell["row_filter"] = "origin_year"
    reg = tmp_path / "reg.json"
    reg.write_text(json.dumps([cell]))
    args = ["--root", str(tmp_path), "--registry", str(reg), "--no-scheduler", "--no-exclusions",
            "--extras", "none"]
    assert make_results.main(args) == 0          # default: forked child per cell
    t1 = pd.read_csv(tmp_path / "docs/results/tables/T1_primary_family.csv")
    r = t1.iloc[0]
    assert isinstance(r.T_weeks, (int, np.integer)) and r.T_weeks > 10   # was a Series repr
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        g, _ = load_cell({k: [d] for k, d in dirs.items()}, exclude_units=None, exclude_weeks=None)
    finally:
        os.chdir(cwd)
    gf, _ = K.apply_row_filter(g, "origin_year")
    gp = gf[gf.horizon.isin([1, 4])].reset_index(drop=True)
    gp.attrs = dict(g.attrs)
    ref = infer_estimand(gp, "G_excess")
    assert abs(r.G_excess - ref["estimate"]) < 1e-12 and r.n_rows == len(gp) < len(g[g.horizon.isin([1, 4])])
    # absolute WIS columns are consistent with the gains
    assert abs((r.WIS_L3C - r.WIS_L4C) - r.G_excess) < 1e-12
    assert abs((r.WIS_L3 - r.WIS_L4) - r.G_emb) < 1e-12
    # unfiltered sensitivity column = estimator on all primary-horizon rows
    gu = g[g.horizon.isin([1, 4])].reset_index(drop=True)
    gu.attrs = dict(g.attrs)
    assert abs(r.unfiltered_pct - infer_estimand(gu, "G_excess")["pct_of_ref"]) < 1e-9
    for c in ("Holm_p", "TOST_class_Holm", "plain_label", "B4_p", "delta_lo95_pct", "loss_or_gain"):
        assert c in t1.columns, c
    t5 = pd.read_csv(tmp_path / "docs/results/tables/T5_strata.csv")
    assert set(t5.stratum) == {"positive", "recorded_zero", "zero_filled"}
    assert t5.identity_residual.abs().max() < 1e-12
    for e, x in t5.groupby("estimand"):
        assert abs(x.contribution.sum() - x.total.iloc[0]) < 1e-12
    assert (tmp_path / "docs/results/tables/T1b_margin_sensitivity.csv").exists()
    assert (tmp_path / "docs/results/figures/F1_forest_G_excess.png").exists()
    assert (tmp_path / "docs/results/figures/F2_strata_contributions.png").exists()


def test_strata3_identity_with_zero_filled():
    import rk_compute as K
    rng = np.random.default_rng(1)
    n = 4000
    g = pd.DataFrame({"horizon": rng.choice([1, 4], n),
                      "target_week": pd.Timestamp("2020-01-05") + pd.to_timedelta(7 * rng.integers(0, 40, n), "D"),
                      "cases": rng.choice([0, 0, 3], n).astype(float), "unit_id": rng.integers(0, 50, n).astype(str)})
    g["zero_filled"] = (g.cases == 0) & (rng.random(n) < 0.6)
    for k in ("L3", "L4", "L3C", "L4C"):
        g[f"wis_{k}"] = 0.2 + 0.05 * rng.random(n)
    g["G_emb"], g["G_id"] = g.wis_L3 - g.wis_L4, g.wis_L3 - g.wis_L3C
    g["G_excess"] = g.wis_L3C - g.wis_L4C
    t = K.strata3_table(g)
    for e, x in t.groupby("estimand"):
        assert abs(x.contribution.sum() - x.total.iloc[0]) < 1e-14
        assert abs(x.identity_residual).max() < 1e-14
    with pytest.raises(ValueError):
        K.strata3_labels(g.assign(zero_filled=True))


def test_ewc_B4_and_iaaft():
    import rk_compute as K
    from inference_size_sim import run_methods
    rng = np.random.default_rng(3)
    d = rng.standard_normal(150) * 0.01 + 0.002
    b4 = K.ewc_fixed_B(d, 4, 4)
    ref = run_methods(d, np.random.default_rng(0), n_boot=20)["ewc_hln_B4"]
    assert np.isclose(b4["lo95"], ref["lo"]) and np.isclose(b4["hi95"], ref["hi"])
    p1 = K.iaaft_pvalue(d, 4, 60, [1, 2])
    assert p1 == K.iaaft_pvalue(d, 4, 60, [1, 2]) and 1 / 61 <= p1 <= 1


def test_labels_and_holm_class():
    assert make_results.holm_class(-1e-3, -2e-3, -5e-4, 0.01, 0.2) == "inferior"
    assert make_results.holm_class(-1e-3, -2e-3, -5e-4, 0.01, 0.01) == "equivalent"
    assert make_results.holm_class(1e-3, -2e-3, 3e-3, 0.30, 0.2) == "inconclusive"
    lab = make_results.plain_label(-0.4, -0.6, -0.2, 0.001, 0.01, 0.02, 1.0)
    assert lab == "small negative difference, significant after Holm correction; within ±1% (TOST, Holm-adjusted)"
    assert make_results.plain_label(0.3, -0.2, 0.8, 0.4, 0.9, 0.2, 1.0).startswith("no significant difference")
    assert make_results.cell_label("TW_S5") == "Taiwan, S5 held-out country"


def test_registry_add_test_years(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runs = {r: f"runs/tw_{r}" for r in rk_cells.ROLES}
    add = {r: f"runs/tw21_{r}" for r in rk_cells.ROLES}
    man = {"row_filter": "origin_year", "family_size": 1, "primary_horizons": [1, 4],
           "cells": [{"country": "taiwan", "split": "S5", "family": "primary", "runs": runs,
                      "add_test_years": {"years": [2021], "runs": add}}]}
    (tmp_path / "m.yaml").write_text(yaml.safe_dump(man))
    for d in list(runs.values()) + list(add.values())[:3]:
        (tmp_path / d).mkdir(parents=True)
        (tmp_path / d / "scores.parquet").write_text("x")
    cells = {c["id"]: c for c in rk_cells.build_registry("m.yaml")}
    tw, old = cells["TW_S5"], cells["TW_S5_no2021"]
    assert tw["group"] == "primary" and old["group"] == "secondary"
    assert tw["flags"] == ["2021 pending (base test years only)"]
    assert tw["roles"]["L3"]["dirs"] == ["runs/tw_L3"] and tw["row_filter"] == "origin_year"
    (tmp_path / add["L4C"]).mkdir(parents=True)
    (tmp_path / add["L4C"] / "scores.parquet").write_text("x")
    cells = {c["id"]: c for c in rk_cells.build_registry("m.yaml")}
    tw = cells["TW_S5"]
    assert tw["flags"] == [] and tw["roles"]["L3"]["dirs"] == ["runs/tw_L3", "runs/tw21_L3"]
    assert cells["TW_S5_no2021"]["roles"]["L3"]["dirs"] == ["runs/tw_L3"]
    assert rk_cells.FAMILY_SIZE == 1


def test_unit_week_exclusion(tmp_path):
    import rk_compute as K
    t = pd.DataFrame({"unit_id": ["3200102", "3200201"], "from_week": ["2020-12-20"] * 2,
                      "to_week": ["", ""], "action": ["exclude"] * 2})
    f = tmp_path / "uw.csv"
    t.to_csv(f, index=False)
    g = pd.DataFrame({"unit_id": ["3200102", "3200102", "3300100", "3200201"],
                      "target_week": pd.to_datetime(["2020-12-13", "2020-12-20", "2021-05-02", "2024-01-07"])})
    assert list(K.unit_week_mask(g, K.load_unit_weeks(f))) == [False, True, False, True]
    out, info = K.apply_unit_weeks(g, f)
    assert len(out) == 2 and info["unit_week_rows_dropped"] == 2
    assert K.apply_unit_weeks(g, tmp_path / "missing.csv")[0] is g


def test_kit_v2_exclusions_sensitivity(tmp_path, monkeypatch):
    import rk_compute as K
    panel, dirs = _two_year_cell(tmp_path)
    monkeypatch.chdir(tmp_path)
    uw = tmp_path / "uw.csv"
    pd.DataFrame({"unit_id": ["u0", "u1"], "from_week": ["2018-06-03"] * 2, "to_week": ["", ""],
                  "action": ["exclude"] * 2}).to_csv(uw, index=False)
    excl = {"exclude_units": None, "exclude_weeks": None, "late_entry": None,
            "week_actions": ("exclude",), "unit_weeks": str(uw)}
    cell = _cell("BR_S1", dirs)
    cell["row_filter"] = "origin_year"
    res = K.compute_cell(cell, cache_root=tmp_path / "cache", excl=excl, extras="none", log=lambda m: None)
    info, ex = res["info"], res["extras"]
    assert info["unit_week_rows_dropped"] > 0 and 0 < info["unit_week_share_dropped_primary"] < 1
    assert "excl_v1" in ex and "strata3_excl_v1" in ex
    # v1 column = the same pipeline without the unit-week exclusion
    excl1 = {k: v for k, v in excl.items() if k != "unit_weeks"}
    r1 = K.compute_cell({**cell, "id": "BR_S1_v1"}, cache_root=tmp_path / "cache", excl=excl1,
                        extras="none", log=lambda m: None)
    a = ex["excl_v1"].set_index("estimand").loc["G_excess", "estimate"]
    b = r1["est"].query("estimand == 'G_excess' and horizon == 'pooled' and test_year == 'pooled' "
                        "and stratum == 'all'").estimate.iloc[0]
    assert abs(a - b) < 1e-12
    assert info["rows_scored_primary"] < r1["info"]["rows_scored_primary"]
