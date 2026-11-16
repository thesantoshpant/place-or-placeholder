import json

import numpy as np
import pandas as pd
import yaml

from pop import runner
from pop.features import history as H
from test_history import synth_panel


def test_train_window_rule():
    p = synth_panel(n_weeks=574)
    g = H.make_grid(p)
    for Y in [2020, 2022, 2024]:
        tr, te = runner.select_split(g, {"name": "S1", "train_start_year": 2018}, Y)
        assert set(g.year[tr]) == set(range(2018, Y))
        assert set(g.year[te]) == {Y}
        # train rows (targets) never reach the test year; lags may reach back before 2018
        idx, X, y = runner.build(g, "L1", tr, 4, train=True, exclude_gap=True)
        assert g.year[idx.t].min() == 2018 and g.year[idx.t].max() == Y - 1
        assert X.notna().all().all()


def test_runner_end_to_end_and_resume(tmp_path):
    p = synth_panel(n_units=3, n_weeks=574)
    p.loc[p.index[100], "flag_gap"] = True
    p.to_parquet(tmp_path / "panel.parquet")
    cfg = dict(exp_name="t", country="X", panel=str(tmp_path / "panel.parquet"),
               split={"name": "S1", "train_start_year": 2018}, test_years=[2023, 2024],
               tune_year=2019, horizons=[1, 2], threads=2,
               runs=[{"model": "naive", "level": "L0"}, {"model": "nb", "level": "L1"},
                     {"model": "lgbm", "level": "L1", "params": {"num_boost_round": 20},
                      "tune": {"grid": {"min_data_in_leaf": [5, 20]}, "horizons": [1],
                               "quantiles": [0.1, 0.5, 0.9]}}],
               dm_pairs=[["lgbm-L1", "naive-L0"]])
    cf = tmp_path / "c.yaml"
    cf.write_text(yaml.safe_dump(cfg))
    out = runner.run_experiment(cf, root=tmp_path)
    for f in ["forecasts.parquet", "scores.parquet", "summary.csv", "config_resolved.yaml",
              "dm.csv", "run.log", "timing.csv"]:
        assert (out / f).exists(), f
    fc = pd.read_parquet(out / "forecasts.parquet")
    assert len(fc) % 9 == 0
    assert (fc.origin_week + pd.to_timedelta(7 * fc.horizon, "D") == fc.target_week).all()
    assert ((fc.target_week + pd.Timedelta(days=3)).dt.year == fc.test_year).all()
    sc = pd.read_parquet(out / "scores.parquet")
    assert sc["wis_log"].notna().all() and set(sc.run) == {"naive-L0", "nb-L1", "lgbm-L1"}
    # resume: chunks are skipped (done markers untouched)
    marks = {f: f.stat().st_mtime for f in (out / "chunks").glob("*.done.json")}
    runner.run_experiment(cf, root=tmp_path)
    assert all(f.stat().st_mtime == m for f, m in marks.items())
    assert "params_frozen" in yaml.safe_load((out / "config_resolved.yaml").read_text())["runs"][2]
