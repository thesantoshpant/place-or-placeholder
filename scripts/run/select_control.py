#!/usr/bin/env python
"""Pick the ID control C* from a 2019-origin selection run. Selection rule v2 (2026-11-16b,
pre-declared before any spatial-split result was read; applies to every cell, S1 included).

Usage: python scripts/run/select_control.py RUN_DIR [RUN_DIR ...] [--ref lgbm-L3] [--replace RUN ...]
                                            [--candidates C1 C2 ...] [--out DIR]
       python scripts/run/select_control.py --report OUT.md RUN_DIR ...   # collate selection.json files

Several run dirs are pooled. A run name present in more than one dir is an error unless it is
listed in --replace; then the LAST dir that has it wins and earlier copies stay in the table as
'<run> (superseded)' (shown, never eligible). Outputs go to --out (default: last run dir).

Rule v2
1. Candidates = the split's protocol list (explicit, no regex):
     history arm, S0-S4: C1 C2 C3 C4 C4s C5        history arm, S5: C2 C3 C4 C4s C5
     no-history arm (ref lgbm-N3): C2 C3 C4 C4s (+ C6 in S1)
   minus C4s where the range rule min(D, fitted) gives the fitted range (C4s identical to C4; in S5
   judged for the held-out = scored country), minus DEGENERATE candidates:
     (a) control features (geography controls C2/C4/C4s, recomputed from the config) all-NaN or
         constant for any country present in the split;
     (b) seed-0 2019 forecasts bitwise identical to the reference (plain L3 / N3) in every chunk.
2. Score_k = pooled log-WIS at 2019 (rows pooled over horizons, folds), mean over k's seeds.
   sigma_seed = pooled within-candidate seed SD over the multi-seed candidates of the cell;
   SE_k = sigma_seed / sqrt(n_seeds_k).
3. Tie set T = {k : Score_k - Score_best <= 2 sqrt(SE_best^2 + SE_k^2)}.
   C* = first member of T in the fixed priority order C1 > C3 > C2 > C4s > C4 > C5
   (no-history: C3 > C2 > C6 > C4s > C4).
4. sigma_seed 0 or undefined -> the cell is 'uninformative': C* = first non-degenerate candidate
   in priority order.
Writes selection.csv, selection.json (rule_version 2), selection.md.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

RULE_VERSION = 2
HIST_ALL = ["C1", "C2", "C3", "C4", "C4s", "C5"]
HIST_S5 = ["C2", "C3", "C4", "C4s", "C5"]
NOHIST = ["C2", "C3", "C4", "C4s"]
PRIORITY_HIST = ["C1", "C3", "C2", "C4s", "C4", "C5"]
PRIORITY_NOHIST = ["C3", "C2", "C6", "C4s", "C4"]
GEO = ("C2", "C4", "C4s")
S5_COUNTRIES = ("BRAZIL", "COLOMBIA", "PERU", "TAIWAN")


def protocol(split: str, nohist: bool):
    if nohist:
        return NOHIST + (["C6"] if split == "S1" else []), PRIORITY_NOHIST
    return (HIST_S5 if split == "S5" else HIST_ALL), PRIORITY_HIST


def c4s_is_c4(ckw: dict, country: str) -> bool:
    """min(D, fitted) == fitted -> C4s identical to C4 (judged for the scored country)."""
    def get(k):
        r = (ckw.get(k) or {}).get("range_km")
        return r.get(country) if isinstance(r, dict) else r
    r4, r4s = get("C4"), get("C4s")
    if r4 is None or r4s is None:
        return False
    return float(r4s) >= float(r4)  # C4s run at a range >= fitted: under the rule it equals C4


def feature_degenerate(k: str, cfg: dict, pts) -> str | None:
    """Geography controls: all-NaN or constant features for a country of the split."""
    from pop.features import controls as C
    ckw = (cfg.get("features") or {}).get("control_kw", {}) or {}
    countries = S5_COUNTRIES if cfg["split"]["name"] == "S5" else (cfg["country"].upper(),)
    for c in countries:
        p = pts[pts.country == c]
        kw = dict(ckw.get(k, {}) or {})
        if k in ("C4", "C4s"):
            r = kw.get("range_km")
            kw = {"range_km": r[c] if isinstance(r, dict) else r}
        else:
            kw = {kk: v for kk, v in kw.items() if kk == "L"}
        F = C.make_controls(k, pts, set(p.unit_id), set(), 2019, seed=0, **kw)
        X = F.drop(columns="unit_id").to_numpy(float)
        fin = np.isfinite(X).all(1)
        if not fin.any():
            return f"features all-NaN for {c}"
        if np.all(np.std(X[fin], axis=0) == 0):
            return f"features constant for {c}"
    return None


def _chunk_files(dirs, pattern):
    out = {}
    for d in dirs:  # later dirs win
        for f in (Path(d) / "chunks").glob(pattern):
            out[f.name] = f
    return out


def forecasts_identical(k: str, ref_level: str, dirs) -> str | None:
    lvl = f"{ref_level}+{k}"
    cand = _chunk_files(dirs, f"lgbm__{lvl}__*s0__2019__h*.forecasts.parquet")
    cand = {n: f for n, f in cand.items() if n.split("__")[1] == lvl}
    if not cand:
        return None
    refs = _chunk_files(dirs, f"lgbm__{ref_level}__*s0__2019__h*.forecasts.parquet")
    keys = ["unit_id", "origin_week", "target_week", "horizon", "fold", "quantile"]
    for n, f in cand.items():
        rn = n.replace(f"__{lvl}__", f"__{ref_level}__", 1)
        if rn not in refs:
            return None
        a = pd.read_parquet(f, columns=keys + ["value"]).sort_values(keys, kind="stable")
        b = pd.read_parquet(refs[rn], columns=keys + ["value"]).sort_values(keys, kind="stable")
        if len(a) != len(b) or not np.array_equal(a.value.to_numpy(), b.value.to_numpy()):
            return None
    return f"seed-0 forecasts bitwise identical to {ref_level} in all {len(cand)} chunks"


def select(tab: pd.DataFrame, cands: list, priority: list, excluded: dict):
    """tab: index = control name; columns wis_log (seed mean), n_seeds, wis_log_sd_seeds."""
    elig = [k for k in cands if k not in excluded]
    if not elig:
        raise SystemExit("no eligible C* candidate")
    rows = {k: tab.loc[k] for k in elig}
    multi = [(int(r.n_seeds), float(r.wis_log_sd_seeds)) for r in rows.values()
             if r.n_seeds > 1 and np.isfinite(r.wis_log_sd_seeds)]
    dof = sum(n - 1 for n, _ in multi)
    sigma = math.sqrt(sum((n - 1) * s ** 2 for n, s in multi) / dof) if dof > 0 else float("nan")
    order = sorted(elig, key=lambda k: (float(rows[k].wis_log), priority.index(k)))
    best = order[0]
    info = {k: {"wis_log": float(rows[k].wis_log), "n_seeds": int(rows[k].n_seeds),
                "seed_sd": (float(rows[k].wis_log_sd_seeds) if np.isfinite(rows[k].wis_log_sd_seeds)
                            else None),
                "delta_vs_best": float(rows[k].wis_log - rows[best].wis_log)} for k in order}
    if not (np.isfinite(sigma) and sigma > 0):
        cstar = sorted(elig, key=priority.index)[0]
        return cstar, {"uninformative": True, "sigma_seed": None if not np.isfinite(sigma) else 0.0,
                       "best_by_score": best, "tie_set": sorted(elig, key=priority.index),
                       "candidates": info}
    se = {k: sigma / math.sqrt(rows[k].n_seeds) for k in elig}
    tie = []
    for k in order:
        thr = 2 * math.sqrt(se[best] ** 2 + se[k] ** 2)
        info[k].update(se=se[k], tie_threshold=thr)
        if rows[k].wis_log - rows[best].wis_log <= thr:
            tie.append(k)
    tie = sorted(tie, key=priority.index)
    return tie[0], {"uninformative": False, "sigma_seed": sigma, "best_by_score": best,
                    "tie_set": tie, "candidates": info}


def report(out: Path, dirs):
    lines = ["# C* selection, rule v2 (all cells)", "",
             "Generated by `python scripts/run/select_control.py --report "
             "docs/results/control_selection_v2.md runs/*_controls_2019`. The rule is in the docstring "
             "of `scripts/run/select_control.py`: protocol candidate list per split; C4s dropped where "
             "min(D, fitted) = fitted; degenerate candidates excluded (features all-NaN/constant, or "
             "seed-0 forecasts bitwise equal to plain L3/N3); tie set = within 2 SE of the best "
             "(SE from the pooled within-candidate seed SD); C* = first of the tie set in the fixed "
             "priority C1 > C3 > C2 > C4s > C4 > C5 (no-history C3 > C2 > C6 > C4s > C4); "
             "seed SD 0/undefined -> 'uninformative', priority order. Pre-declared 2026-11-16 "
             "before any spatial-split result was read.", ""]
    for d in dirs:
        f = Path(d) / "selection.json"
        if not f.exists():
            continue
        s = json.loads(f.read_text())
        if s.get("rule_version") != RULE_VERSION:
            lines += [f"## {Path(d).name}", "",
                      f"Rule v1 only (C* = {s.get('c_star')}); not re-selected (superseded/sensitivity dir).", ""]
            continue
        sig = s["sigma_seed"]
        lines += [f"## {Path(d).name}", "",
                  f"**C\\* = {s['c_star']}**" + (" (uninformative cell: priority order)" if s["uninformative"] else "")
                  + f"; v1 C\\* = {s.get('c_star_v1')}; ref {s['ref']} = {s['ref_wis_log']:.6f}; "
                  f"sigma_seed = {('%.2e' % sig) if sig else sig}; tie set = {', '.join(s['tie_set'])}", "",
                  "| candidate | log-WIS (seed mean) | seeds | seed SD | SE | delta vs best | in tie set |",
                  "|---|---|---|---|---|---|---|"]
        for k, v in s["candidates"].items():
            sd = v.get("seed_sd")
            lines.append(f"| {k} | {v['wis_log']:.6f} | {v['n_seeds']} | {('%.2e' % sd) if sd else '-'} | "
                         f"{('%.2e' % v['se']) if 'se' in v else '-'} | {v['delta_vs_best']:+.2e} | "
                         f"{'yes' if k in s['tie_set'] else ''} |")
        for k, why in s["excluded"].items():
            lines.append(f"| {k} | excluded: {why} | | | | | |")
        lines.append("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print("wrote", out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dirs", nargs="+")
    ap.add_argument("--ref", default="lgbm-L3")
    ap.add_argument("--replace", nargs="*", default=[], help="run names later dirs may override")
    ap.add_argument("--candidates", nargs="*", default=None, help="override the protocol list")
    ap.add_argument("--out", default=None)
    ap.add_argument("--report", default=None, help="collate selection.json of RUN_DIRs into this .md")
    ap.add_argument("--no-feature-check", action="store_true")
    a = ap.parse_args()
    if a.report:
        report(Path(a.report), a.run_dirs)
        return
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    d = Path(a.out or a.run_dirs[-1])
    d.mkdir(parents=True, exist_ok=True)
    cfg = yaml.safe_load((Path(a.run_dirs[-1]) / "config_resolved.yaml").read_text())
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
    tab = g.mean()
    tab["n_seeds"] = g.size()
    tab["wis_log_sd_seeds"] = g.wis_log.std()
    tab["wis_log_min_seed"] = g.wis_log.min()
    tab["wis_log_max_seed"] = g.wis_log.max()
    tab = tab.sort_values("wis_log", kind="stable")
    ref = float(tab.loc[a.ref, "wis_log"]) if a.ref in tab.index else None
    tab["delta_vs_ref"] = tab.wis_log - ref if ref is not None else float("nan")

    ref_level = a.ref.split("-", 1)[1]
    nohist = ref_level.startswith("N")
    split = cfg["split"]["name"]
    proto, priority = protocol(split, nohist)
    cands = list(a.candidates) if a.candidates is not None else proto
    excluded = {}
    run_of = {k: f"lgbm-{ref_level}+{k}" for k in cands}
    for k in cands:
        if run_of[k] not in tab.index:
            excluded[k] = "not run in this cell"
    ckw = (cfg.get("features") or {}).get("control_kw", {}) or {}
    if "C4s" in cands and "C4s" not in excluded and c4s_is_c4(ckw, cfg["country"].upper()):
        excluded["C4s"] = "range rule min(D, fitted) = fitted: C4s identical to C4"
    pts = None
    for k in cands:
        if k in excluded:
            continue
        why = None
        if k in GEO and not a.no_feature_check:
            if pts is None:
                from pop.features.controls import load_unit_points
                pts = load_unit_points()
            why = feature_degenerate(k, cfg, pts)
        why = why or forecasts_identical(k, ref_level, a.run_dirs)
        if why:
            excluded[k] = "degenerate: " + why
    ktab = tab.rename(index={v: k for k, v in run_of.items()})
    cstar, sel = select(ktab, cands, priority, excluded)
    old = d / "selection.json"
    prev = json.loads(old.read_text()) if old.exists() else {}
    v1 = prev.get("c_star_v1") if prev.get("rule_version") == RULE_VERSION else prev.get("c_star")
    tab.to_csv(d / "selection.csv")
    res = {"rule_version": RULE_VERSION, "c_star": cstar, "run": run_of[cstar], "c_star_v1": v1,
           "run_dirs": [str(x) for x in a.run_dirs], "replaced": a.replace, "split": split,
           "country": cfg["country"], "arm": "no-history" if nohist else "history",
           "wis_log": float(ktab.loc[cstar, "wis_log"]), "ref": a.ref, "ref_wis_log": ref,
           "origin": 2019, "candidate_list": cands, "priority": priority,
           "excluded": excluded, **sel,
           "ranking": {k: float(ktab.loc[k, "wis_log"]) for k in cands if k not in excluded}}
    (d / "selection.json").write_text(json.dumps(res, indent=1))
    (d / "selection.md").write_text(
        f"# C* selection, 2019 origin (rule v{RULE_VERSION})\n\nC* = {cstar}"
        f"{' (uninformative cell)' if sel['uninformative'] else ''}; tie set {sel['tie_set']}; "
        f"sigma_seed {sel['sigma_seed']}\n\nExcluded: {json.dumps(excluded)}\n\n"
        f"Sources: {', '.join(res['run_dirs'])}\n\n```\n{tab.round(6).to_string()}\n```\n")
    print(tab.round(6).to_string())
    print(json.dumps({k: res[k] for k in ("c_star", "c_star_v1", "tie_set", "sigma_seed",
                                          "uninformative", "excluded")}, indent=1))


if __name__ == "__main__":
    main()
