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


def _run(root: Path, name: str, label: str, shift: float, panel: Path, horizons=(1, 2)) -> str:
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
            "roles": {r: {"dirs": [d], "markers": [None]} for r, d in dirs.items()}}


def test_kit_end_to_end(tmp_path, capsys):
    panel = tmp_path / "panel.parquet"
    _panel(panel)
    dirs = {r: _run(tmp_path, f"x_{r}", f"lgbm-{r}", s, panel)
            for r, s in {"L3": 0.0, "L4": -0.001, "L3C": 0.0, "L4C": 0.0005}.items()}
    pending = {r: f"runs/missing_{r}" for r in rk_cells.ROLES}
    reg = tmp_path / "reg.json"
    reg.write_text(json.dumps([_cell("BR_S1", dirs), _cell("CO_S1", pending)]))
    args = ["--root", str(tmp_path), "--registry", str(reg), "--no-scheduler", "--no-exclusions"]
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
