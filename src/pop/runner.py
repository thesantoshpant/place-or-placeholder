"""Config-driven experiment runner (rolling-origin, one model per horizon).

Flow: load YAML -> panel -> dense grid per country -> (optional) tuning on ``tune_year`` ->
for each run (model x level) x split fold x seed x test year x horizon: fit on the training rows
of the split instance, forecast its test rows, write + score one chunk (resumable)
-> assemble forecasts.parquet, scores.parquet, summary.csv, dm.csv, timing.csv.

Splits come from ``pop.splits.splits`` (S0-S5): ``get_split`` gives the unit sets / year window,
``row_masks`` the train / test / score / train_target_ok masks over target rows.

Feature levels live in ``pop.features.levels.LEVELS`` (``fn(grid, idx, h, ctx)``). Every read of
a grid / climate / remote-sensing / embedding value goes through an availability check.
"""
from __future__ import annotations

import contextlib
import copy
import fcntl
import itertools
import json
import logging
import multiprocessing as mp
import os
import resource
import socket
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from pop.eval import scoring, stats
from pop.features import history, levels
from pop.models import make_model
from pop.splits import splits as SP

LEVELS = levels.LEVELS
HISTORY_LEVELS = levels.NO_LOCATION_LEVELS  # must never contain location columns
FC_KEYS = ["run", "model", "level", "split", "fold", "seed", "test_year", "unit_id",
           "origin_week", "target_week", "horizon"]
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
    cfg.setdefault("features", {})
    sp = cfg.setdefault("split", {})
    sp.setdefault("name", "S1")
    sp.setdefault("folds", "all")
    if sp.get("train_start_year", SP.TRAIN_START) != SP.TRAIN_START:
        raise ValueError(f"train_start_year is fixed at {SP.TRAIN_START} by pop.splits")
    cfg["country"] = cfg["country"].upper()
    for r in cfg["runs"]:
        r.setdefault("params", {})
        r.setdefault("name", f"{r['model']}-{r['level']}")
        r.setdefault("seeded", r["model"] == "lgbm")
        if r.get("params_from") and r.get("tune"):
            raise ValueError(f"run {r['name']}: give params_from or tune, not both")
        if r["level"] not in LEVELS:
            raise ValueError(f"unknown level {r['level']}")
    return cfg


# ------------------------------------------------------------------ data per country
@dataclass
class CountryData:
    grid: history.Grid
    ctx: levels.Context
    frame: pd.DataFrame  # grid rows (u-major) with unit_id, week_start, year, flag_gap
    masks: dict = None   # cache: (split, fold, origin, seed) -> masks


def grid_frame(grid: history.Grid) -> pd.DataFrame:
    U, W = len(grid.units), len(grid.weeks)
    return pd.DataFrame({"unit_id": np.repeat(grid.units, W),
                         "week_start": np.tile(grid.weeks.values, U),
                         "year": np.tile(grid.year, U),
                         "flag_gap": grid.flag_gap.ravel()})


def make_data(panel: pd.DataFrame, country: str, root, options, all_panel=None) -> CountryData:
    g = history.make_grid(panel)
    ctx = levels.Context(country=country, root=Path(root), options=options,
                         panel=all_panel if all_panel is not None else panel)
    return CountryData(g, ctx, grid_frame(g))


# ------------------------------------------------------------------ splits
def split_folds(cfg) -> list:
    sp = cfg["split"]
    f = sp["folds"]
    if f == "all":
        return [cfg["country"]] if sp["name"] == "S5" else \
            SP.folds(sp["name"], cfg["country"], sp.get("split_dir"))
    return list(f)


def get_split(cfg, fold, origin) -> SP.Split:
    sp = cfg["split"]
    return SP.get_split(sp["name"], cfg["country"], fold, origin,
                        seed=sp.get("seed", SP.DEFAULT_SEED), split_dir=sp.get("split_dir"))


def split_masks(data: CountryData, split: SP.Split) -> dict[str, np.ndarray]:
    """pop.splits.row_masks reshaped to the (U, W) grid of one country."""
    key = (split.name, str(split.fold), split.origin, split.seed)
    if data.masks is None:
        data.masks = {}
    if key not in data.masks:
        m = SP.row_masks(data.frame, split)
        data.masks[key] = {k: v.reshape(data.grid.y.shape) for k, v in m.items()}
    return data.masks[key]


def design_index(grid, mask: np.ndarray, h: int) -> pd.DataFrame:
    """Rows (u, t, o=t-h) for target cells in ``mask`` (u-major, same order as history.design_index)."""
    u, t = np.nonzero(mask)
    keep = t - h >= 0
    u, t = u[keep], t[keep]
    return pd.DataFrame({"u": u, "t": t, "o": t - h})


def build(data: CountryData, level, mask, h, *, train: bool, exclude_gap: bool):
    """Features + log1p targets for target cells in ``mask``. For training, ``mask`` should be
    the split's train (or train_target_ok) mask; NaN targets (and flag_gap if asked) are dropped."""
    grid = data.grid
    if train:
        mask = mask & np.isfinite(grid.y)
        if exclude_gap:
            mask = mask & ~grid.flag_gap
    idx = design_index(grid, mask, h)
    X = LEVELS[level](grid, idx, h, data.ctx)
    if level in HISTORY_LEVELS:
        history.assert_no_location(X.columns)
    y = grid.y[idx["u"].to_numpy(), idx["t"].to_numpy()]
    return idx, X.reset_index(drop=True), y


def build_train(datas, split, level, h, exclude_gap):
    """Training design over every loaded country (S5 trains on the other countries)."""
    Xs, ys = [], []
    for d in datas.values():
        d.ctx.split = split
        m = split_masks(d, split)
        if not m["train"].any():
            continue
        _, X, y = build(d, level, m["train"], h, train=True, exclude_gap=exclude_gap)
        Xs.append(X)
        ys.append(y)
    if not Xs:
        raise ValueError(f"split {split.name}/{split.fold}/{split.origin}: no training rows")
    return pd.concat(Xs, ignore_index=True), np.concatenate(ys)


def build_test(datas, cfg, split, level, h):
    d = datas[split.country]
    d.ctx.split = split
    m = split_masks(d, split)
    return build(d, level, m["test"], h, train=False, exclude_gap=False)


# ------------------------------------------------------------------ tuning
def pinball_log(y_log, qlog, quantiles):
    q = np.asarray(quantiles)[None, :]
    d = y_log[:, None] - qlog
    return float(np.mean(np.maximum(q * d, (q - 1) * d)))


def tune(cfg, datas, run, out: Path) -> dict:
    """Small grid on origin ``tune_year`` (train 2018 -> validate 2019) of the split's first fold;
    frozen afterwards for every fold and test year."""
    pf = run.get("params_from")
    if pf:  # reuse another run's frozen params (e.g. L3+Ck takes L3's); config params override
        best = {**json.loads(Path(pf).read_text())["best"], **run["params"]}
        log.info("params for %s from %s: %s", run["name"], pf, best)
        return best
    t = run.get("tune")
    if not t:
        return run["params"]
    f = out / f"tuning_{run['name']}.json"
    if f.exists():
        return json.loads(f.read_text())["best"]
    sp = get_split(cfg, split_folds(cfg)[0], cfg["tune_year"])
    keys, vals = zip(*t["grid"].items())
    for d in datas.values():
        d.ctx.seed = cfg["seeds"][0]
    designs = {}
    for h in t.get("horizons", cfg["horizons"]):
        Xtr, ytr = build_train(datas, sp, run["level"], h, cfg["exclude_flag_gap"])
        d = datas[sp.country]
        va = split_masks(d, sp)["test"]
        _, Xva, yva = build(d, run["level"], va, h, train=True, exclude_gap=cfg["exclude_flag_gap"])
        designs[h] = (Xtr, ytr, Xva, yva)
    rows = []
    for combo in itertools.product(*vals):
        params = {**run["params"], **dict(zip(keys, combo))}
        losses = []
        for h, (Xtr, ytr, Xva, yva) in designs.items():
            m = make_model(run["model"], seed=cfg["seeds"][0], threads=cfg["threads"],
                           **params).fit(Xtr, ytr, quantiles=t["quantiles"])
            qlog = np.log1p(m.predict_quantiles(Xva, t["quantiles"]))
            losses.append(pinball_log(yva, qlog, t["quantiles"]))
        rows.append({**dict(zip(keys, combo)), "val_pinball_log": float(np.mean(losses))})
        log.info("tune %s %s -> %.5f", run["name"], rows[-1], rows[-1]["val_pinball_log"])
    res = pd.DataFrame(rows).sort_values("val_pinball_log")
    res.to_csv(out / f"tuning_{run['name']}.csv", index=False)
    best = {**run["params"], **{k: _py(res[k].iloc[0]) for k in keys}}
    f.write_text(json.dumps({"best": best, "split": sp.name, "fold": str(sp.fold),
                             "origin": sp.origin}, indent=1))
    return best


def _py(v):
    return v.item() if hasattr(v, "item") else v


# ------------------------------------------------------------------ chunks
def chunk_name(run, seed, year, h, fold=None):
    f = "" if fold is None else f"__f{fold}"
    return f"{run['model']}__{run['level']}{f}__s{seed}__{year}__h{h}"


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
    if cfg["exclude_flag_gap"]:  # == the split API's score mask (test & ~flag_gap)
        lg = lg[~lg["flag_gap"].astype(bool)]
    return lg[keys + ["cases", "zero_filled", "wis_log", "ae_log", "wis_case", "ae_case"]
              + [c for c in lg.columns if c.startswith("cov_")]]


def _atomic(path: Path, write):
    """Write via ``<path>.tmp.<pid>`` + rename, so a killed process never leaves a half file."""
    tmp = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    write(tmp)
    os.replace(tmp, path)


def run_chunk(cfg, datas, truth, run, params, seed, year, h, cdir: Path, fold=None):
    name = chunk_name(run, seed, year, h, fold)
    done = cdir / f"{name}.done.json"
    if done.exists():
        return json.loads(done.read_text())
    t0 = time.time()
    sp = get_split(cfg, fold, year)
    for d in datas.values():
        d.ctx.seed = seed
    Xtr, ytr = build_train(datas, sp, run["level"], h, cfg["exclude_flag_gap"])
    idx, Xte, _ = build_test(datas, cfg, sp, run["level"], h)
    assert list(Xtr.columns) == list(Xte.columns)
    m = make_model(run["model"], seed=seed, threads=cfg["threads"], **params)
    m.fit(Xtr, ytr, quantiles=cfg["quantiles"])
    Q = m.predict_quantiles(Xte, cfg["quantiles"])
    assert np.all(np.diff(Q, axis=1) >= 0), "non-monotone quantiles"
    meta = dict(run=run["name"], model=run["model"], level=run["level"], split=sp.name,
                fold="" if fold is None else str(fold), seed=seed, test_year=year, horizon=h)
    fc = to_long(datas[sp.country].grid, idx, Q, cfg["quantiles"], meta)
    sc = score_chunk(fc, truth, cfg)
    # forecasts/scores first, .done.json last: a chunk without .done.json is never treated as done
    _atomic(cdir / f"{name}.forecasts.parquet", lambda p: fc.to_parquet(p, index=False))
    _atomic(cdir / f"{name}.scores.parquet", lambda p: sc.to_parquet(p, index=False))
    info = dict(chunk=name, run=run["name"], split=sp.name, fold=meta["fold"], test_year=year,
                horizon=h, seed=seed, n_train=int(len(ytr)), n_test=int(len(Xte)),
                n_features=int(Xtr.shape[1]), seconds=round(time.time() - t0, 1),
                threads=int(cfg["threads"]), pid=os.getpid(),
                maxrss_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2))
    if hasattr(m, "alpha_"):
        info.update(nb_alpha=m.alpha_, nb_converged=m.converged_)
    _atomic(done, lambda p: p.write_text(json.dumps(info)))
    log.info("chunk %s done in %.1fs (n_train=%d, p=%d)", name, info["seconds"], info["n_train"],
             info["n_features"])
    return info


# ------------------------------------------------------------------ claiming (crash-safe)
@contextlib.contextmanager
def chunk_lock(cdir: Path, name: str):
    """Non-blocking exclusive ``flock`` on ``chunks/<name>.lock``; yields True if claimed.

    The kernel drops the lock when the holder exits or is killed, so a crashed worker never
    leaves a stale claim (checked on the MooseFS /net/home mount). Lock files hold the owner's
    host/pid for information only."""
    path = cdir / f"{name}.lock"
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        try:
            os.ftruncate(fd, 0)
            os.write(fd, json.dumps({"host": socket.gethostname(), "pid": os.getpid(),
                                     "time": time.time()}).encode())
            yield True
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def claim_and_run(cfg, datas, truth, run, params, seed, year, h, cdir: Path, fold=None):
    """``run_chunk`` under the chunk's lock. Returns the chunk info, or None if another process
    holds the chunk right now. ``.done.json`` is re-checked after the lock is taken, so a chunk
    finished by the previous holder is not recomputed."""
    name = chunk_name(run, seed, year, h, fold)
    done = cdir / f"{name}.done.json"
    if done.exists():
        return json.loads(done.read_text())
    with chunk_lock(cdir, name) as got:
        if not got:
            return None
        if done.exists():
            return json.loads(done.read_text())
        info = run_chunk(cfg, datas, truth, run, params, seed, year, h, cdir, fold)
        (cdir / f"{name}.lock").unlink(missing_ok=True)  # safe: done exists before unlock
        return info


WAIT_SECONDS = 30


def wait_for_chunks(cfg, datas, truth, tasks, tuned, cdir, infos: dict):
    """Chunks held by another process: poll until they are done (or run them if the holder died)."""
    left = [t for t in tasks if infos.get(t[0]) is None]
    if left:
        log.info("%d chunks are held by another process; waiting", len(left))
    while left:
        for key, run, seed, year, h, fold in list(left):
            info = claim_and_run(cfg, datas, truth, run, tuned[run["name"]], seed, year, h, cdir,
                                 fold)
            if info is not None:
                infos[key] = info
                left.remove((key, run, seed, year, h, fold))
        if left:
            time.sleep(WAIT_SECONDS)


# ------------------------------------------------------------------ parallel executor
# Workers are forked after the data are loaded (copy-on-write sharing of grids and feature
# tables). GNU libgomp (used by LightGBM) hangs in a forked child if the parent has already run an
# OpenMP region, so the parent never fits a model on this path: tuning runs in a forked helper
# process, and if this process has fitted a model before (e.g. an earlier serial run in the same
# interpreter) the pool falls back to ``spawn``, where each worker reloads the data.
_G: dict = {}
_FITTED_IN_PROCESS = False


def _init_worker(spawn_args):
    if spawn_args is not None:  # spawn: rebuild the data in this worker
        cfg, root, out = spawn_args
        log.setLevel(logging.INFO)
        if not any(isinstance(hd, logging.FileHandler) for hd in log.handlers):
            fh = logging.FileHandler(Path(out) / "run.log")
            fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
            log.addHandler(fh)
        datas, truth = prepare_data(cfg, Path(root))
        _G.update(cfg=cfg, datas=datas, truth=truth)
    t = str(_G["cfg"]["threads"])
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[v] = t


def _worker_chunk(key, run, params, seed, year, h, cdir, fold):
    return key, claim_and_run(_G["cfg"], _G["datas"], _G["truth"], run, params, seed, year, h,
                              Path(cdir), fold)


def _tune_all(cfg, datas, out):
    return {run["name"]: tune(cfg, datas, run, out) for run in cfg["runs"]}


def _tune_from_globals():
    return _tune_all(_G["cfg"], _G["datas"], _G["out"])


def tune_in_fork(cfg, datas, out):
    """Tuning in a forked one-shot process (inherits the data; keeps OpenMP out of the parent)."""
    _G.update(cfg=cfg, datas=datas, out=out)
    try:
        with ProcessPoolExecutor(1, mp_context=mp.get_context("fork")) as ex:
            return ex.submit(_tune_from_globals).result()
    finally:
        _G.clear()


def warm_caches(cfg, datas):
    """Build each level's grid-aligned arrays once in the parent so forked workers share them."""
    for base in {r["level"].split("+")[0] for r in cfg["runs"]}:
        for c, d in datas.items():
            ys = np.flatnonzero(d.grid.year == SP.FIRST_TEST_ORIGIN)
            if len(ys) == 0 or ys[0] < 1:
                continue
            idx = pd.DataFrame({"u": [0], "t": [ys[0]], "o": [ys[0] - 1]})
            try:
                LEVELS[base](d.grid, idx, 1, d.ctx)
            except levels.MissingInput as e:
                log.info("warm %s %s: %s", c, base, e)


def submit_order(tasks) -> list:
    """Chunk tasks sorted by test year, latest first (stable otherwise)."""
    return sorted(tasks, key=lambda t: -int(t[3]))


def run_parallel(cfg, datas, truth, tasks, tuned, cdir, out, root, workers, start_method):
    if start_method == "fork" and _FITTED_IN_PROCESS:
        log.warning("a model was fitted in this process before; using spawn instead of fork")
        start_method = "spawn"
    if start_method == "fork":
        warm_caches(cfg, datas)
        _G.update(cfg=cfg, datas=datas, truth=truth)
        spawn_args = None
    else:
        spawn_args = (cfg, str(root), str(out))
    infos, failed = {}, []
    log.info("parallel: %d chunks, %d workers x %d threads (%s)", len(tasks), workers,
             cfg["threads"], start_method)
    try:
        with ProcessPoolExecutor(workers, mp_context=mp.get_context(start_method),
                                 initializer=_init_worker, initargs=(spawn_args,)) as ex:
            # latest test years first (largest training sets): shorter tail when workers drain.
            # Scheduling only; each chunk's output does not depend on the order.
            futs = {ex.submit(_worker_chunk, key, run, tuned[run["name"]], seed, year, h,
                              str(cdir), fold): key
                    for key, run, seed, year, h, fold in submit_order(tasks)}
            for f in as_completed(futs):
                try:
                    key, info = f.result()
                    infos[key] = info
                except Exception as e:  # noqa: BLE001  (BrokenProcessPool included)
                    failed.append(futs[f])
                    log.error("chunk %s failed: %r", futs[f], e)
    finally:
        _G.clear()
    if failed:
        raise RuntimeError(f"{len(failed)} chunks failed (rerun to resume): {sorted(failed)[:10]}")
    return infos


# ------------------------------------------------------------------ assemble
def concat_parquet(files, dest: Path):
    import pyarrow as pa  # noqa: F401
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
def load_panel(cfg, countries=None) -> pd.DataFrame:
    p = pd.read_parquet(cfg["panel"])
    cs = {c.upper() for c in (countries or [cfg["country"]])}
    p = p[p["country"].astype(str).str.upper().isin(cs)].copy()
    if p.empty:
        raise ValueError(f"no rows for countries {sorted(cs)}")
    p["week_start"] = pd.to_datetime(p["week_start"])
    p["unit_id"] = p["unit_id"].astype(str)
    return p


def prepare_data(cfg, root: Path):
    """Panel -> per-country CountryData (+ truth table of the scored country)."""
    countries = list(SP.S5_ORDER) if cfg["split"]["name"] == "S5" else [cfg["country"]]
    panel = load_panel(cfg, countries)
    datas = {c: make_data(g, c, root, cfg["features"], all_panel=panel)
             for c, g in panel.groupby(panel["country"].astype(str).str.upper())}
    truth = panel[panel["country"].astype(str).str.upper() == cfg["country"]].rename(
        columns={"week_start": "target_week"})[
        ["unit_id", "target_week", "cases", "flag_gap", "zero_filled"]]
    return datas, truth


def chunk_tasks(cfg) -> list:
    """(chunk name, run, seed, year, h, fold) in the serial order."""
    tasks = []
    for run in cfg["runs"]:
        seeds = cfg["seeds"] if run["seeded"] else cfg["seeds"][:1]
        for fold, seed, year, h in itertools.product(split_folds(cfg), seeds,
                                                     cfg["test_years"], cfg["horizons"]):
            tasks.append((chunk_name(run, seed, year, h, fold), run, seed, year, h, fold))
    return tasks


def run_experiment(config_path, root: str | Path = ".", workers: int = 1,
                   threads: int | None = None, start_method: str = "fork") -> Path:
    """Serial by default (``workers=1``). ``workers>1`` runs chunks in a process pool; ``threads``
    overrides the config's per-model thread count (LightGBM results depend on it, see
    docs/methods/compute_plan.md)."""
    global _FITTED_IN_PROCESS
    cfg = load_config(config_path)
    if threads is not None:
        cfg["threads"] = int(threads)
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
        datas, truth = prepare_data(cfg, root)
        for c, d in datas.items():
            log.info("grid %s: %d units x %d weeks (%s..%s)", c, len(d.grid.units),
                     len(d.grid.weeks), d.grid.weeks[0].date(), d.grid.weeks[-1].date())
        for run in cfg["runs"]:
            if run.get("params_from") and not Path(run["params_from"]).is_absolute():
                run["params_from"] = str(root / run["params_from"])
        parallel = workers > 1
        if parallel and start_method == "fork" and not _FITTED_IN_PROCESS:
            tuned = tune_in_fork(cfg, datas, out)
        else:
            tuned = _tune_all(cfg, datas, out)
            _FITTED_IN_PROCESS = _FITTED_IN_PROCESS or any(r.get("tune") for r in cfg["runs"])
        resolved = copy.deepcopy(cfg)
        for run in cfg["runs"]:
            next(r for r in resolved["runs"] if r["name"] == run["name"])["params_frozen"] = \
                tuned[run["name"]]
        import lightgbm
        import statsmodels
        resolved["versions"] = {"lightgbm": lightgbm.__version__,
                                "statsmodels": statsmodels.__version__,
                                "pandas": pd.__version__, "numpy": np.__version__}
        (out / "config_resolved.yaml").write_text(yaml.safe_dump(resolved, sort_keys=False))
        tasks = chunk_tasks(cfg)
        if parallel:
            infos = run_parallel(cfg, datas, truth, tasks, tuned, cdir, out, root, workers,
                                 start_method)
        else:
            infos = {}
            for key, run, seed, year, h, fold in tasks:
                infos[key] = claim_and_run(cfg, datas, truth, run, tuned[run["name"]], seed,
                                           year, h, cdir, fold)
                _FITTED_IN_PROCESS = _FITTED_IN_PROCESS or infos[key] is not None
        wait_for_chunks(cfg, datas, truth, tasks, tuned, cdir, infos)
        infos = [infos[t[0]] for t in tasks]
        pd.DataFrame(infos).to_csv(out / "timing.csv", index=False)
        names = [i["chunk"] for i in infos]
        concat_parquet([cdir / f"{n}.forecasts.parquet" for n in names], out / "forecasts.parquet")
        scores = pd.concat([pd.read_parquet(cdir / f"{n}.scores.parquet") for n in names],
                           ignore_index=True)
        scores.to_parquet(out / "scores.parquet", index=False)
        summarize(scores).to_csv(out / "summary.csv", index=False)
        if cfg["dm_pairs"]:
            dm_table(scores, cfg["dm_pairs"], cfg["horizons"]).to_csv(out / "dm.csv", index=False)
        log.info("experiment %s finished in %.1fs (peak child RSS %.2f GB)", cfg["exp_name"],
                 time.time() - t0,
                 resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1e6)
    finally:
        log.removeHandler(fh)
        fh.close()
    return out
