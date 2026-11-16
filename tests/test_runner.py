import numpy as np
import pandas as pd
import pytest
import yaml

from pop import runner
from pop.splits import splits as SP
from test_levels import panel, split_dir, tables  # noqa: F401  (fixture)


def data(p=None, **opts):
    p = panel() if p is None else p
    d = runner.make_data(p, "BRAZIL", ".", opts)
    d.ctx.tables.update(tables())
    return {"BRAZIL": d}


def test_train_window_rule(split_dir):  # noqa: F811
    datas = data()
    g = datas["BRAZIL"].grid
    for Y in [2020, 2022, 2024]:
        sp = SP.get_split("S1", "BRAZIL", None, Y, split_dir=split_dir)
        m = runner.split_masks(datas["BRAZIL"], sp)
        assert set(g.year[m["train"].any(0)]) == set(range(2018, Y))
        assert set(g.year[m["test"].any(0)]) == {Y}
        idx, X, y = runner.build(datas["BRAZIL"], "L1", m["train"], 4, train=True, exclude_gap=True)
        assert g.year[idx.t].min() == 2018 and g.year[idx.t].max() == Y - 1
        assert X.notna().all().all()
        # same rows as the old internal S1 rule (all units x target weeks of 2018..Y-1)
        old = np.flatnonzero((g.year >= 2018) & (g.year <= Y - 1))
        assert len(idx) == len(g.units) * len(old)


def test_s4_test_units_never_in_training(split_dir, monkeypatch):  # noqa: F811
    datas = data()
    g = datas["BRAZIL"].grid
    seen = []
    orig = runner.build

    def spy(d, level, mask, h, *, train, exclude_gap):
        out = orig(d, level, mask, h, train=train, exclude_gap=exclude_gap)
        seen.append((train, set(d.grid.units[out[0]["u"]])))
        return out
    monkeypatch.setattr(runner, "build", spy)
    cfg = {"country": "BRAZIL", "split": {"name": "S4", "split_dir": split_dir}}
    for fold in SP.folds("S4", "BRAZIL", split_dir):
        sp = runner.get_split(cfg, fold, 2022)
        seen.clear()
        runner.build_train(datas, sp, "L2", 2, True)
        idx, Xte, _ = runner.build_test(datas, cfg, sp, "L2", 2)
        tr_units = set().union(*[u for t, u in seen if t])
        te_units = set(g.units[idx["u"]])
        assert te_units == set(sp.test_units) and not (tr_units & te_units)
        assert tr_units == set(sp.train_units)


def test_s0_rows_partition(split_dir):  # noqa: F811
    datas = data()
    sp = SP.get_split("S0", "BRAZIL", None, 2021, split_dir=split_dir)
    m = runner.split_masks(datas["BRAZIL"], sp)
    assert not (m["train"] & m["test"]).any()
    assert 0.1 < m["test"].sum() / (m["test"].sum() + (m["train"] & (datas["BRAZIL"].grid.year == 2021)).sum()) < 0.3


def test_runner_end_to_end_and_resume(tmp_path, split_dir):  # noqa: F811
    p = panel().iloc[: 3 * 574].copy()  # 3 units
    p.loc[p.index[100], "flag_gap"] = True
    p.to_parquet(tmp_path / "panel.parquet")
    tb = tables()
    (tmp_path / "data/interim/climate").mkdir(parents=True)
    tb["climate"].to_parquet(tmp_path / "data/interim/climate/climate_weekly_brazil_v1.parquet")
    cfg = dict(exp_name="t", country="Brazil", panel=str(tmp_path / "panel.parquet"),
               split={"name": "S1", "folds": "all", "split_dir": split_dir},
               test_years=[2023, 2024], tune_year=2019, horizons=[1, 2], threads=2,
               runs=[{"model": "naive", "level": "L0"}, {"model": "nb", "level": "L1"},
                     {"model": "lgbm", "level": "L2", "params": {"num_boost_round": 20},
                      "tune": {"grid": {"min_data_in_leaf": [5, 20]}, "horizons": [1],
                               "quantiles": [0.1, 0.5, 0.9]}}],
               dm_pairs=[["lgbm-L2", "naive-L0"]])
    cf = tmp_path / "c.yaml"
    cf.write_text(yaml.safe_dump(cfg))
    out = runner.run_experiment(cf, root=tmp_path)
    for f in ["forecasts.parquet", "scores.parquet", "summary.csv", "config_resolved.yaml",
              "dm.csv", "run.log", "timing.csv"]:
        assert (out / f).exists(), f
    fc = pd.read_parquet(out / "forecasts.parquet")
    assert len(fc) % 9 == 0 and set(fc.split) == {"S1"}
    assert (fc.origin_week + pd.to_timedelta(7 * fc.horizon, "D") == fc.target_week).all()
    assert ((fc.target_week + pd.Timedelta(days=3)).dt.year == fc.test_year).all()
    sc = pd.read_parquet(out / "scores.parquet")
    assert sc["wis_log"].notna().all() and set(sc.run) == {"naive-L0", "nb-L1", "lgbm-L2"}
    tm = pd.read_csv(out / "timing.csv")
    assert set(tm.loc[tm.run == "lgbm-L2", "n_features"]) == {74}
    marks = {f: f.stat().st_mtime for f in (out / "chunks").glob("*.done.json")}
    runner.run_experiment(cf, root=tmp_path)
    assert all(f.stat().st_mtime == m for f, m in marks.items())
    assert "params_frozen" in yaml.safe_load((out / "config_resolved.yaml").read_text())["runs"][2]


def test_runner_2019_origin_with_params_from(tmp_path, split_dir):  # noqa: F811
    """C* selection setting: score the 2019 origin (train targets 2018 only) with params frozen
    from another run's tuning file."""
    import json
    p = panel().iloc[: 3 * 574].copy()
    p.to_parquet(tmp_path / "panel.parquet")
    (tmp_path / "data/interim/climate").mkdir(parents=True)
    tables()["climate"].to_parquet(tmp_path / "data/interim/climate/climate_weekly_brazil_v1.parquet")
    (tmp_path / "frozen.json").write_text(json.dumps({"best": {"num_boost_round": 15,
                                                               "min_data_in_leaf": 7}}))
    cfg = dict(exp_name="t19", country="BRAZIL", panel=str(tmp_path / "panel.parquet"),
               split={"name": "S1", "folds": "all", "split_dir": split_dir},
               test_years=[2019], tune_year=2019, horizons=[1, 3], threads=2, seeds=[0, 1],
               runs=[{"model": "lgbm", "level": "L2", "params_from": "frozen.json",
                      "params": {"num_boost_round": 10}, "seeded": False}])
    cf = tmp_path / "c.yaml"
    cf.write_text(yaml.safe_dump(cfg))
    out = runner.run_experiment(cf, root=tmp_path)
    fc = pd.read_parquet(out / "forecasts.parquet")
    assert set(fc.test_year) == {2019} and set(fc.seed) == {0}
    assert ((fc.target_week + pd.Timedelta(days=3)).dt.year == 2019).all()
    frozen = yaml.safe_load((out / "config_resolved.yaml").read_text())["runs"][0]["params_frozen"]
    assert frozen == {"num_boost_round": 10, "min_data_in_leaf": 7}
    sp = SP.get_split("S1", "BRAZIL", None, 2019, split_dir=split_dir)
    assert set(sp.train_years) == {2018}
    cfg["runs"][0]["tune"] = {"grid": {"min_data_in_leaf": [5]}}
    cf.write_text(yaml.safe_dump(cfg))
    with pytest.raises(ValueError):
        runner.load_config(cf)


def test_unknown_level_rejected(tmp_path):
    cf = tmp_path / "c.yaml"
    cf.write_text(yaml.safe_dump({"country": "BRAZIL", "runs": [{"model": "lgbm", "level": "L9"}]}))
    with pytest.raises(ValueError):
        runner.load_config(cf)


# ------------------------------------------------------------------ parallel executor
import json  # noqa: E402
import os  # noqa: E402
import signal  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run/run_experiment.py"


def _small_setup(tmp_path, split_dir, name="p"):  # noqa: F811
    p = panel().iloc[: 3 * 574].copy()
    p.to_parquet(tmp_path / "panel.parquet")
    for r in (tmp_path, tmp_path / "serial", tmp_path / "par"):  # roots used by the tests
        (r / "data/interim/climate").mkdir(parents=True, exist_ok=True)
        tables()["climate"].to_parquet(r / "data/interim/climate/climate_weekly_brazil_v1.parquet")
    cfg = dict(exp_name=name, country="BRAZIL", panel=str(tmp_path / "panel.parquet"),
               split={"name": "S1", "folds": "all", "split_dir": split_dir},
               test_years=[2022, 2023, 2024], tune_year=2019, horizons=[1, 2], threads=2,
               runs=[{"model": "lgbm", "level": "L2", "params": {"num_boost_round": 15},
                      "tune": {"grid": {"min_data_in_leaf": [5, 20]}, "horizons": [1],
                               "quantiles": [0.1, 0.5, 0.9]}}])
    cf = tmp_path / f"{name}.yaml"
    cf.write_text(yaml.safe_dump(cfg))
    return cf


def _cli(cf, root, *extra, wait=True):
    env = {**os.environ, "PYTHONHASHSEED": "0"}
    cmd = [sys.executable, str(SCRIPT), str(cf), "--root", str(root), *extra]
    if not wait:
        return subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stdout + r.stderr
    return r


def _fc(out):
    return pd.read_parquet(out / "forecasts.parquet").sort_values(
        ["run", "test_year", "horizon", "unit_id", "target_week", "quantile"]).reset_index(drop=True)


def _done_lines(out):
    import collections
    c = collections.Counter(l.split("chunk ")[1].split(" done")[0]
                            for l in (out / "run.log").read_text().splitlines() if " done in " in l)
    return c


def test_chunk_lock_exclusive_and_released_on_kill(tmp_path):
    code = ("import sys,time; from pathlib import Path; from pop import runner\n"
            "with runner.chunk_lock(Path(sys.argv[1]), 'c') as g:\n"
            "    print(g, flush=True); time.sleep(120 if g else 0)\n")
    holder = subprocess.Popen([sys.executable, "-c", code, str(tmp_path)], stdout=subprocess.PIPE,
                              text=True)
    assert holder.stdout.readline().strip() == "True"
    with runner.chunk_lock(tmp_path, "c") as got:
        assert got is False  # held by the other process
    other = subprocess.run([sys.executable, "-c", code, str(tmp_path)], capture_output=True,
                           text=True)
    assert other.stdout.strip() == "False"
    holder.send_signal(signal.SIGKILL)
    holder.wait()
    with runner.chunk_lock(tmp_path, "c") as got:  # the kernel dropped the dead holder's lock
        assert got is True


def test_parallel_cli_matches_serial_no_duplicates_and_resumes(tmp_path, split_dir):  # noqa: F811
    cf = _small_setup(tmp_path, split_dir)
    ser = runner.run_experiment(cf, root=tmp_path / "serial")
    # two concurrent parallel invocations on the same run dir: every chunk computed exactly once
    procs = [_cli(cf, tmp_path / "par", "--workers", "3", wait=False) for _ in range(2)]
    for pr in procs:
        o = pr.communicate(timeout=600)[0]
        assert pr.returncode == 0, o
    par = tmp_path / "par/runs/p"
    counts = _done_lines(par)
    assert len(counts) == 6 and set(counts.values()) == {1}, counts
    pd.testing.assert_frame_equal(_fc(ser), _fc(par))  # bit-identical at equal threads
    assert set(pd.read_csv(par / "timing.csv")["threads"]) == {2}

    # resume after a killed worker: chunk with a partial output, no .done.json, lock left behind
    name = "lgbm__L2__s0__2023__h2"
    ref = pd.read_parquet(par / f"chunks/{name}.forecasts.parquet")
    (par / f"chunks/{name}.done.json").unlink()
    (par / f"chunks/{name}.forecasts.parquet").write_bytes(b"partial")
    code = ("import sys,time; from pathlib import Path; from pop import runner\n"
            "with runner.chunk_lock(Path(sys.argv[1]), sys.argv[2]) as g:\n"
            "    print(g, flush=True); time.sleep(120)\n")
    holder = subprocess.Popen([sys.executable, "-c", code, str(par / "chunks"), name],
                              stdout=subprocess.PIPE, text=True)
    assert holder.stdout.readline().strip() == "True"
    holder.send_signal(signal.SIGKILL)
    holder.wait()
    _cli(cf, tmp_path / "par", "--workers", "2")
    info = json.loads((par / f"chunks/{name}.done.json").read_text())
    assert info["chunk"] == name
    pd.testing.assert_frame_equal(pd.read_parquet(par / f"chunks/{name}.forecasts.parquet"), ref)
    assert _done_lines(par)[name] == 2 and sum(_done_lines(par).values()) == 7
    pd.testing.assert_frame_equal(_fc(ser), _fc(par))


def test_parallel_in_process_falls_back_to_spawn(tmp_path, split_dir):  # noqa: F811
    cf = _small_setup(tmp_path, split_dir, name="q")
    ser = runner.run_experiment(cf, root=tmp_path / "serial")  # fits in this process
    assert runner._FITTED_IN_PROCESS
    par = runner.run_experiment(cf, root=tmp_path / "par", workers=2)  # must not hang (spawn)
    pd.testing.assert_frame_equal(_fc(ser), _fc(par))
    assert "using spawn instead of fork" in (par / "run.log").read_text()


def test_serial_skips_chunk_held_by_another_process(tmp_path, split_dir, monkeypatch):  # noqa: F811
    cf = _small_setup(tmp_path, split_dir, name="r")
    out = tmp_path / "runs/r"
    (out / "chunks").mkdir(parents=True)
    name = "lgbm__L2__s0__2022__h1"
    code = ("import sys,time; from pathlib import Path; from pop import runner\n"
            "with runner.chunk_lock(Path(sys.argv[1]), sys.argv[2]) as g:\n"
            "    print(g, flush=True); time.sleep(float(sys.argv[3]))\n")
    holder = subprocess.Popen([sys.executable, "-c", code, str(out / "chunks"), name, "4"],
                              stdout=subprocess.PIPE, text=True)
    assert holder.stdout.readline().strip() == "True"
    monkeypatch.setattr(runner, "WAIT_SECONDS", 1)
    t0 = time.time()
    runner.run_experiment(cf, root=tmp_path)  # waits for the holder, then computes the chunk itself
    holder.wait()
    assert (out / f"chunks/{name}.done.json").exists() and time.time() - t0 >= 1
    assert "held by another process" in (out / "run.log").read_text()


def test_submit_order_latest_year_first():
    tasks = [(f"k{y}{h}", None, 0, y, h, None) for y in (2020, 2021, 2022) for h in (1, 2)]
    out = runner.submit_order(tasks)
    assert [t[3] for t in out] == [2022, 2022, 2021, 2021, 2020, 2020]
    assert sorted(out) == sorted(tasks) and [t[4] for t in out[:2]] == [1, 2]
