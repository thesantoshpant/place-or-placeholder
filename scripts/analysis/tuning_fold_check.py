"""Fold-internal re-tuning check for the spatial splits S2-S4 (review item).

The S2-S4 runs reuse the country-wide S1 L1 tuning (origin 2019: train 2018 -> validate 2019,
all units). This script reruns exactly that grid search (same grid, horizons, quantiles,
metric, L1 level, seed) inside each fold, using ONLY the fold's training units: train on their
2018 targets, validate on their 2019 targets. Held-out (and S3 buffer) units contribute no rows.
No test-year forecasts are made.

A reference row (scope=S1_all_units) reruns the original S1 tuning to show reproduction.

Usage: python scripts/analysis/tuning_fold_check.py [--countries COLOMBIA BRAZIL]
       [--splits S2 S3 S4] [--threads 8] [--out docs/results/review/RF_tuning_fold_check.csv]
Resumable: (country, split, fold, combo) rows already in --out are skipped.
"""
from __future__ import annotations

import argparse
import itertools
import logging
import multiprocessing as mp
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from pop import runner as R
from pop.models import make_model
from pop.splits import splits as SP

log = logging.getLogger("tuning_fold_check")
CFG = {"BRAZIL": "configs/brazil_s1_baselines.yaml", "COLOMBIA": "configs/colombia_s1_baselines.yaml"}


def inner_split(name: str, country: str, fold, origin: int) -> SP.Split:
    """Split whose train AND validation units are the fold's training units."""
    if name == "S1":
        return SP.get_split("S1", country, None, origin)
    sp = SP.get_split(name, country, fold, origin)
    assert not (sp.train_units & sp.test_units)
    return replace(sp, test_units=sp.train_units)


def grid_rows(cfg, datas, run, sp, threads):
    t = run["tune"]
    keys, vals = zip(*t["grid"].items())
    for d in datas.values():
        d.ctx.seed = cfg["seeds"][0]
    designs = {}
    for h in t.get("horizons", cfg["horizons"]):
        Xtr, ytr = R.build_train(datas, sp, run["level"], h, cfg["exclude_flag_gap"])
        d = datas[sp.country]
        va = R.split_masks(d, sp)["test"]
        _, Xva, yva = R.build(d, run["level"], va, h, train=True, exclude_gap=cfg["exclude_flag_gap"])
        designs[h] = (Xtr, ytr, Xva, yva)
    n_tr = {h: len(v[1]) for h, v in designs.items()}
    n_va = {h: len(v[3]) for h, v in designs.items()}
    for combo in itertools.product(*vals):
        params = {**run["params"], **dict(zip(keys, combo))}
        losses = []
        t0 = time.time()
        for h, (Xtr, ytr, Xva, yva) in designs.items():
            m = make_model(run["model"], seed=cfg["seeds"][0], threads=threads,
                           **params).fit(Xtr, ytr, quantiles=t["quantiles"])
            qlog = np.log1p(m.predict_quantiles(Xva, t["quantiles"]))
            losses.append(R.pinball_log(yva, qlog, t["quantiles"]))
        yield {**dict(zip(keys, combo)), "val_pinball_log": float(np.mean(losses)),
               **{f"val_h{h}": l for h, l in zip(designs, losses)},
               "n_train_units": len(sp.train_units),
               "n_train_rows_h1": n_tr[min(n_tr)], "n_val_rows_h1": n_va[min(n_va)],
               "fit_s": round(time.time() - t0, 1)}


_G = {}


def _fold_job(name, fold):
    cfg, datas, run, threads, country = (_G[k] for k in ("cfg", "datas", "run", "threads", "country"))
    for d in datas.values():
        d.masks = None
    sp = inner_split(name, country, fold, cfg["tune_year"])
    rows = []
    for row in grid_rows(cfg, datas, run, sp, threads):
        rows.append({"country": country, "split": name, "fold": str(fold),
                     "scope": "S1_all_units" if name == "S1" else "fold_training_units_only", **row})
        log.info("%s %s %s %s", country, name, fold, rows[-1])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--countries", nargs="+", default=["COLOMBIA", "BRAZIL"])
    ap.add_argument("--splits", nargs="+", default=["S2", "S3", "S4"])
    ap.add_argument("--threads", type=int, default=1, help="LightGBM threads per fit")
    ap.add_argument("--jobs", type=int, default=8, help="folds tuned in parallel (forked)")
    ap.add_argument("--no-reference", action="store_true")
    ap.add_argument("--out", default="docs/results/review/RF_tuning_fold_check.csv")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    for country in a.countries:
        done = pd.read_csv(out, dtype={"fold": str}) if out.exists() else pd.DataFrame()
        cfg = R.load_config(CFG[country])
        run = next(r for r in cfg["runs"] if r.get("tune"))
        datas, _ = R.prepare_data(cfg, Path("."))
        log.info("%s data loaded", country)
        jobs = [] if a.no_reference else [("S1", None)]
        jobs += [(s, f) for s in a.splits for f in SP.folds(s, country)]
        if not done.empty:
            jobs = [(n, f) for n, f in jobs if ((done.country == country) & (done.split == n)
                                                & (done.fold == str(f))).sum() < 4]
        _G.update(cfg=cfg, datas=datas, run=run, threads=a.threads, country=country)
        with ProcessPoolExecutor(min(a.jobs, len(jobs)) or 1, mp_context=mp.get_context("fork")) as ex:
            futs = [ex.submit(_fold_job, n, f) for n, f in jobs]
            for fu in futs:
                rows = fu.result()
                pd.DataFrame(rows).to_csv(out, mode="a", header=not out.exists(), index=False)
        _G.clear()
        del datas


if __name__ == "__main__":
    main()
