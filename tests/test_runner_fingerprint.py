"""Chunk fingerprints (audit 3 M-3, 2026-11-16b)."""
import json

import yaml

from pop import runner
from test_levels import panel, split_dir, tables  # noqa: F401  (fixture)


def _cfg(tmp_path, split_dir, min_leaf=5):  # noqa: F811
    p = panel().iloc[: 3 * 574].copy()
    p.to_parquet(tmp_path / "panel.parquet")
    (tmp_path / "data/interim/climate").mkdir(parents=True, exist_ok=True)
    tables()["climate"].to_parquet(tmp_path / "data/interim/climate/climate_weekly_brazil_v1.parquet")
    cfg = dict(exp_name="t", country="Brazil", panel=str(tmp_path / "panel.parquet"),
               split={"name": "S1", "folds": "all", "split_dir": split_dir},
               test_years=[2024], tune_year=2019, horizons=[1], threads=2,
               runs=[{"model": "lgbm", "level": "L2",
                      "params": {"num_boost_round": 10, "min_data_in_leaf": min_leaf}}])
    cf = tmp_path / "c.yaml"
    cf.write_text(yaml.safe_dump(cfg))
    return cf


def test_fingerprint_stored_reused_and_mismatch_recomputed(tmp_path, split_dir, monkeypatch):  # noqa: F811
    monkeypatch.setattr(runner, "FP_LOG", tmp_path / "fp.log")
    cf = _cfg(tmp_path, split_dir)
    out = runner.run_experiment(cf, root=tmp_path)
    done = next((out / "chunks").glob("*.done.json"))
    fp1 = json.loads(done.read_text())["fingerprint"]
    assert len(fp1) == 40
    m = done.stat().st_mtime
    runner.run_experiment(cf, root=tmp_path)  # same config: reused
    assert done.stat().st_mtime == m
    # legacy chunk without a fingerprint: accepted
    info = json.loads(done.read_text())
    info.pop("fingerprint")
    done.write_text(json.dumps(info))
    m = done.stat().st_mtime
    runner.run_experiment(cf, root=tmp_path)
    assert done.stat().st_mtime == m and "fingerprint" not in json.loads(done.read_text())
    # changed params under the same chunk name: moved aside and recomputed
    info["fingerprint"] = fp1
    done.write_text(json.dumps(info))
    cf = _cfg(tmp_path, split_dir, min_leaf=7)
    runner.run_experiment(cf, root=tmp_path)
    fp2 = json.loads(done.read_text())["fingerprint"]
    assert fp2 != fp1
    moved = list((out / "chunks_fpmismatch").glob("*.done.json.*"))
    assert len(moved) == 1 and json.loads(moved[0].read_text())["fingerprint"] == fp1
    assert "recomputed" in (tmp_path / "fp.log").read_text()


def test_fingerprint_ignores_threads_and_other_controls():
    cfg = {"quantiles": [0.1, 0.5, 0.9], "split": {"name": "S1"}, "threads": 4,
           "features": {"yearly_ref": "target", "control_kw": {"C1": {"c1_period": "auto"},
                                                              "C4": {"range_km": 100.0}}}}
    run = {"model": "lgbm", "level": "L3+C1"}
    a = runner.chunk_fingerprint(cfg, run, {"num_leaves": 31})
    b = runner.chunk_fingerprint({**cfg, "threads": 16, "features": {
        **cfg["features"], "control_kw": {"C1": {"c1_period": "auto"}, "C4": {"range_km": 5.0}}}},
        run, {"num_leaves": 31})
    assert a == b
    c4 = {"model": "lgbm", "level": "L3+C4"}
    assert runner.chunk_fingerprint(cfg, c4, {}) != runner.chunk_fingerprint(
        {**cfg, "features": {**cfg["features"], "control_kw": {"C4": {"range_km": 5.0}}}}, c4, {})
    assert a != runner.chunk_fingerprint({**cfg, "features": {**cfg["features"], "report_delay": 2}},
                                         run, {"num_leaves": 31})
