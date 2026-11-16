#!/usr/bin/env python
"""Pick the ID control C* from a 2019-origin selection run (configs/brazil_s1_controls_2019.yaml).

Usage: python scripts/run/select_control.py RUN_DIR [RUN_DIR ...] [--ref lgbm-L3] [--replace RUN ...]
                                            [--out DIR]

Several run dirs are pooled. A run name present in more than one dir is an error unless it is
listed in --replace; then the LAST dir that has it wins and earlier copies stay in the table as
'<run> (superseded)' (shown, never eligible for C*). Outputs go to --out (default: last run dir).

Mean log1p WIS per run x seed (rows pooled over h1-h4, or per horizon), then mean / sd / min / max
over seeds. C* = control with the lowest seed-averaged pooled log-WIS. Only test_year 2019 is
accepted (no 2020+ rows may enter the choice). Writes selection.csv, selection.json, selection.md.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dirs", nargs="+")
    ap.add_argument("--ref", default="lgbm-L3")
    ap.add_argument("--replace", nargs="*", default=[], help="run names later dirs may override")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    d = Path(a.out or a.run_dirs[-1])
    d.mkdir(parents=True, exist_ok=True)
    cols = ["run", "level", "seed", "horizon", "test_year", "wis_log", "cov_40", "cov_80"]
    parts = []
    for rd in a.run_dirs:
        x = pd.read_parquet(Path(rd) / "scores.parquet", columns=cols)
        x["run"] = x["run"].astype(str)
        for prev in parts:
            dup = set(prev.run) & set(x.run)
            if dup - set(a.replace):
                raise SystemExit(f"run(s) {sorted(dup - set(a.replace))} in several dirs; use --replace")
            prev.loc[prev.run.isin(dup), "run"] = prev.run + " (superseded)"
        parts.append(x)
    sc = pd.concat(parts, ignore_index=True)
    if set(sc.test_year.astype(int)) != {2019}:
        raise SystemExit(f"selection must use the 2019 origin only, got {sorted(sc.test_year.unique())}")
    per_seed = sc.groupby(["run", "seed"])[["wis_log", "cov_40", "cov_80"]].mean()
    per_seed_h = sc.groupby(["run", "seed", "horizon"]).wis_log.mean().unstack("horizon")
    per_seed_h.columns = [f"wis_log_h{h}" for h in per_seed_h.columns]
    ps = per_seed.join(per_seed_h)
    g = ps.groupby("run")
    tab = g.mean().add_suffix("")
    tab["n_seeds"] = g.size()
    tab["wis_log_sd_seeds"] = g.wis_log.std()
    tab["wis_log_min_seed"] = g.wis_log.min()
    tab["wis_log_max_seed"] = g.wis_log.max()
    tab = tab.sort_values("wis_log")
    ctrl = tab[tab.index.str.contains(r"\+C\d") & ~tab.index.str.endswith("(superseded)")]
    if ctrl.empty:
        raise SystemExit("no L3+Ck runs found")
    best = ctrl.index[0]
    ref = float(tab.loc[a.ref, "wis_log"]) if a.ref in tab.index else None
    tab["delta_vs_ref"] = tab.wis_log - ref if ref is not None else float("nan")
    tab.to_csv(d / "selection.csv")
    res = {"c_star": best.split("+")[-1], "run": best, "run_dirs": [str(x) for x in a.run_dirs],
           "replaced": a.replace, "wis_log": float(ctrl.wis_log.iloc[0]),
           "ref": a.ref, "ref_wis_log": ref, "origin": 2019,
           "ranking": {k: float(v) for k, v in ctrl.wis_log.items()}}
    (d / "selection.json").write_text(json.dumps(res, indent=1))
    (d / "selection.md").write_text(f"# C* selection, 2019 origin\n\nC* = {res['c_star']}\n\n"
                                    f"Sources: {', '.join(res['run_dirs'])}\n\n```\n"
                                    f"{tab.round(5).to_string()}\n```\n")
    print(tab.round(5).to_string())
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
