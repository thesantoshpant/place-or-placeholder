"""Config-driven experiment runner (rolling-origin, one model per horizon).

Flow: load YAML -> panel -> dense grid -> (optional) tuning on ``tune_year`` ->
for each run (model x level) x seed x test year x horizon: fit on the train window,
forecast every target week of the test year, write + score one chunk (resumable)
-> assemble forecasts.parquet, scores.parquet, summary.csv, dm.csv, timing.csv.

To add a feature level, register ``name -> fn(grid, idx, h) -> DataFrame`` in
``LEVELS``. The function must only read grid values through
``pop.features.history._take`` (or an equivalent no-future check).
"""
from __future__ import annotations

import copy
import itertools
import json
import logging
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from pop.eval import scoring, stats
from pop.features import history
from pop.models import make_model

LEVELS = {"L0": history.l0_features, "L1": history.l1_features}
HISTORY_LEVELS = {"L0", "L1"}  # must never contain location columns
FC_KEYS = ["run", "model", "level", "seed", "test_year", "unit_id", "origin_week",
           "target_week", "horizon"]
log = logging.getLogger("pop.runner")


# ------------------------------------------------------------------ config
def load_config(path) -> dict:
    cfg = yaml.safe_load(Path(path).read_text())
    cfg.setdefault("horizons", [1, 2, 3, 4])
    cfg.setdefault("quantiles", list(scoring.PRIMARY_QUANTILES))
    cfg.setdefault("seeds", [0])
    cfg.setdefault("threads", 16)
    cfg.setdefault("coverage_levels", list(scoring.PRIMARY_COVERAGE))
    cfg.setdefault("exclude_flag_gap", True)
    cfg.setdefault("runs_dir", "runs")
    cfg.setdefault("dm_pairs", [])
    cfg.setdefault("split", {"name": "S1", "train_start_year": 2018})
    for r in cfg["runs"]:
        r.setdefault("params", {})
        r.setdefault("name", f"{r['model']}-{r['level']}")
        r.setdefault("seeded", r["model"] == "lgbm")
    return cfg


# ------------------------------------------------------------------ splits
def select_split(grid: history.Grid, split: dict, test_year: int):
    """(train target-week indices, test target-week indices).

    S1 (temporal): train targets in years [train_start_year, test_year-1],
    test targets in test_year. Replaceable by the pop.splits API later.
    """
    if split["name"] != "S1":
        raise NotImplementedError(f"split {split['name']} not implemented in runner")
    yr = grid.year
    tr = np.flatnonzero((yr >= split["train_start_year"]) & (yr <= test_year - 1))
    te = np.flatnonzero(yr == test_year)
    return tr, te


def build(grid, level, target_idx, h, *, train: bool, exclude_gap: bool):
    idx = history.design_index(grid, target_idx, h)
    X = LEVELS[level](grid, idx, h)
    if level in HISTORY_LEVELS:
        history.assert_no_location(X.columns)
    y = grid.y[idx["u"].to_numpy(), idx["t"].to_numpy()]
    if train:
        keep = np.isfinite(y)
        if exclude_gap:
            keep &= ~grid.flag_gap[idx["u"].to_numpy(), idx["t"].to_numpy()]
        idx, X, y = idx[keep], X[keep], y[keep]
    return idx.reset_index(drop=True), X.reset_index(drop=True), y


# ------------------------------------------------------------------ tuning
def pinball_log(y_log, qlog, quantiles):
    q = np.asarray(quantiles)[None, :]
    d = y_log[:, None] - qlog
    return float(np.mean(np.maximum(q * d, (q - 1) * d)))


def tune(cfg, grid, run, out: Path) -> dict:
    """Small grid on (train: tune_year-1 window, validate: tune_year); frozen after."""
    t = run.get("tune")
    if not t:
        return run["params"]
    f = out / f"tuning_{run['name']}.json"
    if f.exists():
        return json.loads(f.read_text())["best"]
    split = dict(cfg["split"])
    tr, va = select_split(grid, split, cfg["tune_year"])
    keys, vals = zip(*t["grid"].items())
    rows = []
    for combo in itertools.product(*vals):
        params = {**run["params"], **dict(zip(keys, combo))}
        losses = []
        for h in t.get("horizons", cfg["horizons"]):
            _, Xtr, ytr = build(grid, run["level"], tr, h, train=True,
                                exclude_gap=cfg["exclude_flag_gap"])
            _, Xva, yva = build(grid, run["level"], va, h, train=True,
                                exclude_gap=cfg["exclude_flag_gap"])
            m = make_model(run["model"], seed=cfg["seeds"][0], threads=cfg["threads"],
                           **params).fit(Xtr, ytr, quantiles=t["quantiles"])
            qlog = np.log1p(m.predict_quantiles(Xva, t["quantiles"]))
            losses.append(pinball_log(yva, qlog, t["quantiles"]))
        rows.append({**dict(zip(keys, combo)), "val_pinball_log": float(np.mean(losses))})
        log.info("tune %s %s -> %.5f", run["name"], rows[-1], rows[-1]["val_pinball_log"])
    res = pd.DataFrame(rows).sort_values("val_pinball_log")
    res.to_csv(out / f"tuning_{run['name']}.csv", index=False)
    best = {**run["params"], **{k: _py(res[k].iloc[0]) for k in keys}}
    f.write_text(json.dumps({"best": best}, indent=1))
    return best


def _py(v):
    return v.item() if hasattr(v, "item") else v


# ------------------------------------------------------------------ chunks
def chunk_name(run, seed, year, h):
    return f"{run['model']}__{run['level']}__s{seed}__{year}__h{h}"


def to_long(grid, idx, Q, quantiles, meta) -> pd.DataFrame:
    n, k = Q.shape
    u, t, o = (idx[c].to_numpy() for c in ("u", "t", "o"))
    df = pd.DataFrame({
        "unit_id": np.repeat(grid.units[u], k),
        "origin_week": np.repeat(grid.weeks[o].values, k),
        "target_week": np.repeat(grid.weeks[t].values, k),
        "quantile": np.tile(np.asarray(quantiles, float), n),
        "value": Q.reshape(-1).astype(np.float64),
    })
    for c, v in meta.items():
        df[c] = v
    return df[FC_KEYS + ["quantile", "value"]]


def score_chunk(fc, truth, cfg) -> pd.DataFrame:
    kw = dict(quantiles=cfg["quantiles"], coverage_levels=cfg["coverage_levels"])
    lg = scoring.score_forecasts(fc, truth, scale="log", **kw)
    cs = scoring.score_forecasts(fc, truth, scale="case", **kw)
    keys = [c for c in fc.columns if c not in ("quantile", "value")]
    lg = lg.rename(columns={"wis": "wis_log", "ae_median": "ae_log"})
    lg["wis_case"] = cs["wis"].to_numpy()
    lg["ae_case"] = cs["ae_median"].to_numpy()
    lg = lg.merge(truth[["unit_id", "target_week", "flag_gap", "zero_filled"]],
                  on=["unit_id", "target_week"], how="left")
    if cfg["exclude_flag_gap"]:
        lg = lg[~lg["flag_gap"].astype(bool)]
    return lg[keys + ["cases", "zero_filled", "wis_log", "ae_log", "wis_case", "ae_case"]
              + [c for c in lg.columns if c.startswith("cov_")]]


def run_chunk(cfg, grid, truth, run, params, seed, year, h, cdir: Path):
    name = chunk_name(run, seed, year, h)
    done = cdir / f"{name}.done.json"
    if done.exists():
        return json.loads(done.read_text())
    t0 = time.time()
    tr, te = select_split(grid, cfg["split"], year)
    _, Xtr, ytr = build(grid, run["level"], tr, h, train=True, exclude_gap=cfg["exclude_flag_gap"])
    idx, Xte, _ = build(grid, run["level"], te, h, train=False, exclude_gap=False)
    m = make_model(run["model"], seed=seed, threads=cfg["threads"], **params)
    m.fit(Xtr, ytr, quantiles=cfg["quantiles"])
    Q = m.predict_quantiles(Xte, cfg["quantiles"])
    assert np.all(np.diff(Q, axis=1) >= 0), "non-monotone quantiles"
    meta = dict(run=run["name"], model=run["model"], level=run["level"], seed=seed,
                test_year=year, horizon=h)
    fc = to_long(grid, idx, Q, cfg["quantiles"], meta)
    fc.to_parquet(cdir / f"{name}.forecasts.parquet", index=False)
    score_chunk(fc, truth, cfg).to_parquet(cdir / f"{name}.scores.parquet", index=False)
    info = dict(chunk=name, run=run["name"], test_year=year, horizon=h, seed=seed,
                n_train=int(len(ytr)), n_test=int(len(Xte)), seconds=round(time.time() - t0, 1))
    if hasattr(m, "alpha_"):
        info.update(nb_alpha=m.alpha_, nb_converged=m.converged_)
    done.write_text(json.dumps(info))
    log.info("chunk %s done in %.1fs (n_train=%d)", name, info["seconds"], info["n_train"])
    return info


# ------------------------------------------------------------------ assemble
def concat_parquet(files, dest: Path):
    import pyarrow as pa
    import pyarrow.parquet as pq
    writer = None
    try:
        for f in files:
            t = pq.read_table(f)
            if writer is None:
                writer = pq.ParquetWriter(dest, t.schema, compression="zstd")
            writer.write_table(t.cast(writer.schema))
    finally:
        if writer is not None:
            writer.close()


def summarize(scores: pd.DataFrame) -> pd.DataFrame:
    met = ["wis_log", "wis_case", "ae_log"] + [c for c in scores.columns if c.startswith("cov_")]
    by = ["run", "model", "level", "horizon"]
    a = scores.groupby(by + ["test_year"])[met].mean()
    a["n"] = scores.groupby(by + ["test_year"]).size()
    b = scores.groupby(by)[met].mean()
    b["n"] = scores.groupby(by).size()
    b = b.reset_index().assign(test_year="all")
    return pd.concat([a.reset_index().assign(test_year=lambda d: d.test_year.astype(str)), b],
                     ignore_index=True)


def dm_table(scores, pairs, horizons) -> pd.DataFrame:
    rows = []
    for (a, b), h in itertools.product(pairs, horizons):
        s = scores[scores["horizon"] == h]
        d = stats.loss_diff_series(s, a, b, metric="wis_log", model_col="run")
        r = stats.dm_test(d.to_numpy(), h=h)
        rows.append({"A": a, "B": b, "horizon": h, **r.to_dict()})
    out = pd.DataFrame(rows)
    if len(out):
        out["p_holm"] = stats.holm(out["p_value"].to_numpy())
    return out


# ------------------------------------------------------------------ main
def load_panel(cfg) -> pd.DataFrame:
    p = pd.read_parquet(cfg["panel"])
    p = p[p["country"].astype(str).str.upper() == cfg["country"].upper()].copy()
    if p.empty:
        raise ValueError(f"no rows for country {cfg['country']}")
    p["week_start"] = pd.to_datetime(p["week_start"])
    return p


def run_experiment(config_path, root: str | Path = ".") -> Path:
    cfg = load_config(config_path)
    root = Path(root)
    out = root / cfg["runs_dir"] / cfg["exp_name"]
    cdir = out / "chunks"
    cdir.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(out / "run.log")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(fh)
    log.setLevel(logging.INFO)
    try:
        t0 = time.time()
        panel_path = Path(cfg["panel"])
        if not panel_path.is_absolute():
            cfg["panel"] = str(root / panel_path)
        panel = load_panel(cfg)
        grid = history.make_grid(panel)
        truth = panel.rename(columns={"week_start": "target_week"})[
            ["unit_id", "target_week", "cases", "flag_gap", "zero_filled"]].assign(
            unit_id=lambda d: d["unit_id"].astype(str))
        log.info("grid: %d units x %d weeks (%s..%s)", len(grid.units), len(grid.weeks),
                 grid.weeks[0].date(), grid.weeks[-1].date())
        resolved = copy.deepcopy(cfg)
        tuned = {}
        for run in cfg["runs"]:
            tuned[run["name"]] = tune(cfg, grid, run, out)
            next(r for r in resolved["runs"] if r["name"] == run["name"])["params_frozen"] = \
                tuned[run["name"]]
        import lightgbm, statsmodels
        resolved["versions"] = {"lightgbm": lightgbm.__version__,
                                "statsmodels": statsmodels.__version__,
                                "pandas": pd.__version__, "numpy": np.__version__}
        (out / "config_resolved.yaml").write_text(yaml.safe_dump(resolved, sort_keys=False))
        infos = []
        for run in cfg["runs"]:
            seeds = cfg["seeds"] if run["seeded"] else cfg["seeds"][:1]
            for seed, year, h in itertools.product(seeds, cfg["test_years"], cfg["horizons"]):
                infos.append(run_chunk(cfg, grid, truth, run, tuned[run["name"]],
                                       seed, year, h, cdir))
        pd.DataFrame(infos).to_csv(out / "timing.csv", index=False)
        names = [i["chunk"] for i in infos]
        concat_parquet([cdir / f"{n}.forecasts.parquet" for n in names], out / "forecasts.parquet")
        scores = pd.concat([pd.read_parquet(cdir / f"{n}.scores.parquet") for n in names],
                           ignore_index=True)
        scores.to_parquet(out / "scores.parquet", index=False)
        summarize(scores).to_csv(out / "summary.csv", index=False)
        if cfg["dm_pairs"]:
            dm_table(scores, cfg["dm_pairs"], cfg["horizons"]).to_csv(out / "dm.csv", index=False)
        log.info("experiment %s finished in %.1fs", cfg["exp_name"], time.time() - t0)
    finally:
        log.removeHandler(fh)
        fh.close()
    return out
