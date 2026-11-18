"""Results kit: per-cell computation with an on-disk cache.

Reuses the existing inference stack only:
  scripts/run/estimands_report.load_cell / read_scores  (rows, exclusions, strata flags)
  pop.eval.estimands.compute_estimands_v2               (DM/EWC + HLN, TOST, MDE, seeds)
Nothing here re-implements a test; it only slices rows and collects the outputs.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

import rk_cells as C
from estimands_report import KEYS, load_cell, read_scores  # scripts/run (on sys.path)
from pop.eval.estimands import ESTIMANDS, compute_estimands_v2

KIT_VERSION = "3"  # 2: primary pooled = manifest primary_horizons; 3: row filter, 3 strata, extras
FIELDS = ["estimate", "se", "df", "T", "p", "lo95", "hi95", "lo90", "hi90", "wis_ref", "margin",
          "pct_of_ref", "tost_p", "cls", "mde", "mde_pct", "n_seeds", "seed_sd", "boot_lo",
          "boot_hi", "n_rows", "n_weeks"]


# ------------------------------------------------------------------ cache
def _file_stat(p):
    p = Path(p) if p else None
    return [str(p), p.stat().st_size, p.stat().st_mtime_ns] if p and p.exists() else [str(p), None]


def cache_key(cell: dict, excl: dict, opts: dict, ladder_dirs: list[str]) -> str:
    parts = {"v": KIT_VERSION, "opts": opts,
             "roles": {r: [C.run_fingerprint(d) for d in cell["roles"][r]["dirs"]] for r in C.ROLES},
             "ladder": [C.run_fingerprint(d) for d in ladder_dirs],
             "excl": {k: (_file_stat(v) if isinstance(v, (str, Path)) else v) for k, v in excl.items()},
             "cell": {k: cell.get(k) for k in ("estimands", "role_labels", "ref", "panel", "cstar", "flags",
                                                "primary_horizons", "secondary_horizons", "row_filter")}}
    return hashlib.sha1(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _atomic_parquet(df: pd.DataFrame, path: Path) -> None:
    tmp = path.with_suffix(".tmp.parquet")
    df.to_parquet(tmp, index=False)
    os.replace(tmp, path)


# ------------------------------------------------------------------ estimands
def _est_rows(g, label, *, margin_rel, bootstrap, n_boot, block_len):
    r = compute_estimands_v2(g, bootstrap=bootstrap, n_boot=n_boot, block_len=block_len,
                             margin_rel=margin_rel, cluster_col="state", time_col="target_week")
    rows = [{**label, "estimand": e, **{f: r[e].get(f, np.nan) for f in FIELDS}} for e in ESTIMANDS]
    rows.append({**label, "estimand": "ID_share", "estimate": r["ID_share"]["estimate"],
                 "boot_lo": r["ID_share"].get("boot_lo", np.nan),
                 "boot_hi": r["ID_share"].get("boot_hi", np.nan), "reason": r["ID_share"]["reason"]})
    return rows


def hlabel(hs) -> str:
    """Text label of a horizon set, e.g. [1, 4] -> 'h{1,4}'."""
    return "h{" + ",".join(str(int(h)) for h in sorted(hs)) + "}"


def resolve_horizons(present, primary_horizons=None, secondary_horizons=None):
    """(primary set used, secondary set used or None) among the horizons present.

    primary: the manifest's primary_horizons (None = every horizon present, legacy).
    secondary: emitted only when it covers strictly more horizons than the primary set
    (e.g. S1 h1-h4 vs h{1,4}); otherwise None."""
    primary, secondary = primary_horizons, secondary_horizons
    present = sorted(int(h) for h in present)
    hp = [h for h in present if primary is None or h in set(int(x) for x in primary)]
    hs = None
    if secondary:
        hs = [h for h in present if h in set(int(x) for x in secondary)]
        if not set(hp) < set(hs):
            hs = None
    return hp, hs


def sec_label(hs) -> str:
    """Horizon label of the secondary pooled row, e.g. 'pooled_h1-4'."""
    hs = sorted(int(h) for h in hs)
    contiguous = hs == list(range(hs[0], hs[-1] + 1))
    return f"pooled_h{hs[0]}-{hs[-1]}" if contiguous else "pooled_h" + "_".join(map(str, hs))


def estimand_table(g: pd.DataFrame, *, margin_rel=0.01, n_boot=0, block_len=52,
                   primary_horizons=None, secondary_horizons=None) -> pd.DataFrame:
    """Per-horizon rows (every horizon present) + rows labelled horizon == "pooled", which pool
    over the PRIMARY horizons only (overall, per test year, per stratum, per stratum x year),
    + one secondary row horizon == sec_label(...) (pooled over secondary_horizons; overall
    only) when that set is larger than the primary one. Column `pooled_over` lists the
    horizons behind every row."""
    rows = []
    hp, hs = resolve_horizons(g.horizon.unique(), primary_horizons, secondary_horizons)

    def sub(mask, base=g):
        s = base[mask] if mask is not None else base
        s.attrs = dict(g.attrs)
        return s

    def add(s, label, boot=False):
        if len(s) == 0 or s.target_week.nunique() < 10:
            return
        try:
            rows.extend(_est_rows(s, label, margin_rel=margin_rel, bootstrap=boot and n_boot > 0,
                                  n_boot=n_boot, block_len=block_len))
        except Exception as e:  # noqa: BLE001 - a thin stratum must not kill the cell
            rows.append({**label, "estimand": "error", "reason": repr(e)[:200]})

    for h in sorted(g.horizon.unique()):
        add(sub(g.horizon == h), {"horizon": str(int(h)), "test_year": "pooled", "stratum": "all",
                                  "pooled_over": str(int(h))})
    gp = sub(g.horizon.isin(hp)) if hp else g.iloc[:0]
    po = ",".join(map(str, hp))
    add(gp, {"horizon": "pooled", "test_year": "pooled", "stratum": "all", "pooled_over": po},
        boot=True)
    if hs:
        # only test years scored at every secondary horizon (TW 2021 runs have h1/h4 only)
        yh = g[g.horizon.isin(hs)].groupby("test_year").horizon.nunique()
        yok = yh.index[yh == len(hs)]
        add(sub(g.horizon.isin(hs) & g.test_year.isin(yok)),
            {"horizon": sec_label(hs), "test_year": "pooled", "stratum": "all",
             "pooled_over": ",".join(map(str, hs))})
    for y in sorted(gp.test_year.unique()):
        add(sub(gp.test_year == y, gp), {"horizon": "pooled", "test_year": str(int(y)),
                                         "stratum": "all", "pooled_over": po})
    s3 = strata3_labels(gp) if len(gp) else np.array([], dtype=object)
    strata = {"positive": s3 == "positive", "recorded_zero": s3 == "recorded_zero",
              "zero_filled": s3 == "zero_filled",
              "outbreak": gp.outbreak.to_numpy(bool), "non_outbreak": ~gp.outbreak.to_numpy(bool)}
    for name, m in strata.items():
        add(sub(m, gp), {"horizon": "pooled", "test_year": "pooled", "stratum": name,
                         "pooled_over": po})
        for y in sorted(gp.test_year.unique()):
            add(sub(m & (gp.test_year == y), gp),
                {"horizon": "pooled", "test_year": str(int(y)), "stratum": name, "pooled_over": po})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ ladder
def _int_keys(df: pd.DataFrame, units: pd.Index) -> np.ndarray:
    """int64 key over (unit, origin_week, test_year, horizon); -1 for unknown units."""
    code = units.get_indexer(df.unit_id.astype(str))
    od = (pd.to_datetime(df.origin_week).to_numpy().astype("datetime64[D]").astype(np.int64)
          - np.datetime64("1990-01-01", "D").astype(np.int64))
    k = ((code.astype(np.int64) * 20000 + od) * 64 + (df.test_year.astype(int).to_numpy() - 2000)) * 8 \
        + df.horizon.astype(int).to_numpy()
    return np.where(code < 0, -1, k)


def ladder_table(g: pd.DataFrame, rungs: list[tuple[str, list, str | None]],
                 primary_horizons=None, secondary_horizons=None) -> pd.DataFrame:
    """rungs: (label, [run dirs], run-name filter or None). Rows of all dirs of a label (e.g.
    extra-seed runs) are averaged per key (seed-averaged loss). Only keys of g
    scored by every rung; mean log1p WIS and 40/80% coverage, per horizon, "pooled" (row mean
    over the PRIMARY horizons) and, when larger, the secondary pooled set (e.g. pooled_h1-4)."""
    units = pd.Index(sorted(g.unit_id.astype(str).unique()))
    gk = _int_keys(g, units)
    order = np.argsort(gk)
    gks = gk[order]
    n = len(g)
    vals = {}
    for label, dirs, run in rungs:
        s = read_scores(dirs, cols=("wis_log", "cov_40", "cov_80"))
        if run is not None:
            s = s[s.label == run]
        s = s[s.wis_log.notna()]
        k = _int_keys(s, units)
        pos = np.searchsorted(gks, k)
        pos = np.clip(pos, 0, n - 1)
        ok = (k >= 0) & (gks[pos] == k)
        idx = order[pos[ok]]
        cnt = np.bincount(idx, minlength=n).astype(float)
        out = {}
        for c in ("wis_log", "cov_40", "cov_80"):
            v = s[c].to_numpy(dtype=float)[ok] if c in s else np.full(ok.sum(), np.nan)
            with np.errstate(invalid="ignore", divide="ignore"):
                out[c] = np.bincount(idx, weights=v, minlength=n) / cnt
        vals[label] = out
        del s
    common = np.all([np.isfinite(v["wis_log"]) for v in vals.values()], axis=0)
    h = g.horizon.to_numpy()
    nz = g.cases.to_numpy() > 0
    hp, hs = resolve_horizons(np.unique(h), primary_horizons, secondary_horizons)
    sets = [(str(int(x)), [int(x)]) for x in sorted(np.unique(h))] + [("pooled", hp)]
    if hs:
        sets.append((sec_label(hs), hs))
    rows = []
    for label, v in vals.items():
        for hh, hset in sets:
            m = common & np.isin(h, hset)
            rows.append({"label": label, "horizon": hh, "pooled_over": ",".join(map(str, hset)),
                         "n_rows": int(m.sum()),
                         "wis_log": float(np.nanmean(v["wis_log"][m])) if m.any() else np.nan,
                         "cov_40": float(np.nanmean(v["cov_40"][m])) if m.any() else np.nan,
                         "cov_80": float(np.nanmean(v["cov_80"][m])) if m.any() else np.nan,
                         "cov_80_nonzero": float(np.nanmean(v["cov_80"][m & nz])) if (m & nz).any() else np.nan})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ one cell
def ladder_rungs(cell: dict) -> tuple[list, list]:
    """(rungs to use, notes on rungs skipped because incomplete)."""
    lab = cell.get("role_labels") or {"L3": "L3", "L4": "L4", "L3C": "L3+C*", "L4C": "L4+C*"}
    rungs, notes = [], []
    for e in cell.get("ladder", []):
        st = C.run_state(e["dir"], e.get("marker"))
        if st == "complete":
            rungs.append((e["label"], [e["dir"]], e.get("run")))
        elif not e.get("optional"):
            notes.append(f"{e['label']} ({Path(e['dir']).name}): {st}")
    for r in C.ROLES:
        if cell.get("estimands") and r in ("L3C", "L4C"):
            continue
        rungs.append((lab[r], list(cell["roles"][r]["dirs"]), None))
    return rungs, notes


# ------------------------------------------------------------------ v3: row filter
def epi_year(d) -> np.ndarray:
    """Epi-year of a week start = calendar year of its Wednesday (pop.data.panel rule)."""
    return (pd.to_datetime(pd.Series(np.asarray(d))) + pd.Timedelta(days=3)).dt.year.to_numpy()


def origin_year_mask(g: pd.DataFrame) -> np.ndarray:
    """True where the forecast origin lies in the target's epi-year (test_year). Removes every
    row whose yearly features (target-year aligned) or annual model's training labels reach past
    the origin (review R1; deviation row 24): the first h epi-weeks of each test year."""
    return epi_year(g.origin_week) == g.test_year.astype(int).to_numpy()


ROW_FILTERS = {"origin_year": origin_year_mask}


def apply_row_filter(g: pd.DataFrame, rule: str | None) -> tuple[pd.DataFrame, dict]:
    """(filtered copy with attrs kept, info). rule None -> g unchanged."""
    if not rule:
        return g, {"row_filter": None}
    if rule not in ROW_FILTERS:
        raise ValueError(f"unknown row_filter {rule!r}; known: {sorted(ROW_FILTERS)}")
    m = ROW_FILTERS[rule](g)
    h = g.horizon.to_numpy()
    info = {"row_filter": rule, "rows_before_filter": int(len(g)), "rows_dropped_by_filter": int((~m).sum()),
            "pct_dropped_by_h": {str(int(x)): float(100 * (1 - m[h == x].mean())) for x in np.unique(h)}}
    out = g[m].reset_index(drop=True)
    out.attrs = dict(g.attrs)
    return out, info



# ------------------------------------------------------------------ v3: unit-week exclusions (v2 set)
def load_unit_weeks(path) -> pd.DataFrame | None:
    if not path or not Path(path).exists():
        return None
    t = pd.read_csv(path, dtype={"unit_id": str}, keep_default_na=False)
    t = t[t.get("action", "exclude") == "exclude"] if "action" in t else t
    return t


def unit_week_mask(g: pd.DataFrame, table: pd.DataFrame | None) -> np.ndarray:
    """True for rows to DROP: unit listed and from_week <= target_week (<= to_week if set)."""
    drop = np.zeros(len(g), bool)
    if table is None or table.empty or not len(g):
        return drop
    u = g.unit_id.astype(str)
    tw = pd.to_datetime(g.target_week)
    for (w0, w1), grp in table.groupby(["from_week", "to_week"]):
        m = u.isin(set(grp.unit_id)).to_numpy() & (tw >= pd.Timestamp(w0)).to_numpy()
        if w1:
            m &= (tw <= pd.Timestamp(w1)).to_numpy()
        drop |= m
    return drop


def apply_unit_weeks(g: pd.DataFrame, path) -> tuple[pd.DataFrame, dict]:
    t = load_unit_weeks(path)
    if t is None:
        return g, {"unit_week_exclusions": None}
    d = unit_week_mask(g, t)
    out = g[~d].reset_index(drop=True)
    out.attrs = dict(g.attrs)
    return out, {"unit_week_exclusions": str(path), "unit_week_rows_dropped": int(d.sum()),
                 "unit_week_share_dropped": float(d.mean()) if len(d) else 0.0}


# ------------------------------------------------------------------ v3: strata
STRATA3 = ("positive", "recorded_zero", "zero_filled")


def strata3_labels(g: pd.DataFrame) -> np.ndarray:
    """'positive' (cases > 0) / 'recorded_zero' (0, listed by the source) / 'zero_filled'."""
    zf = g.zero_filled.astype(bool).to_numpy()
    pos = g.cases.to_numpy(float) > 0
    if np.any(zf & pos):
        raise ValueError("zero-filled rows with positive cases")
    return np.where(pos, "positive", np.where(zf, "zero_filled", "recorded_zero")).astype(object)


def _sub(g, m):
    s = g[np.asarray(m, bool)]
    s.attrs = dict(g.attrs)
    return s


def strata3_table(gp: pd.DataFrame, *, margin_rel=0.01) -> pd.DataFrame:
    """Per estimand and stratum: the stratum estimate (primary estimator on the stratum's rows,
    % of the stratum's own WIS(L3)) and its exact additive contribution to the cell total
    (review_explore.week_contributions identity; % of the total WIS(L3)); residual
    total - sum(contributions) per estimand (0 up to rounding)."""
    from review_explore import week_contributions
    from pop.eval.estimands import infer_estimand
    from pop.eval.stats import ewc_inference
    hmax = int(gp.horizon.max())
    gg = gp.assign(stratum3=strata3_labels(gp))
    gg.attrs = dict(gp.attrs)
    wis_tot = float(weekly_pooled(gg, "wis_L3").mean())
    rows = []
    for e in ESTIMANDS:
        c_t, tot_t = week_contributions(gg, e, "stratum3")
        tot = float(tot_t.mean())
        resid = tot - float(c_t.sum(axis=1).mean())
        for st in STRATA3:
            m = (gg.stratum3 == st).to_numpy()
            r = {"estimand": e, "stratum": st, "row_share": float(m.mean()), "n_rows": int(m.sum()),
                 "n_weeks": int(gg.target_week[m].nunique()), "total": tot,
                 "total_pct": 100 * tot / wis_tot, "wis_ref_total": wis_tot,
                 "identity_residual": resid}
            if st in c_t.columns:
                ci = ewc_inference(c_t[st].to_numpy(), h=hmax)
                r.update(contribution=float(c_t[st].mean()), contrib_lo95=ci.lo95,
                         contrib_hi95=ci.hi95, contrib_p=ci.p)
            else:
                r.update(contribution=0.0, contrib_lo95=np.nan, contrib_hi95=np.nan, contrib_p=np.nan)
            r["contrib_pct"] = 100 * r["contribution"] / wis_tot
            r["contrib_lo95_pct"] = 100 * r["contrib_lo95"] / wis_tot
            r["contrib_hi95_pct"] = 100 * r["contrib_hi95"] / wis_tot
            if r["n_weeks"] >= 10:
                q = infer_estimand(_sub(gg, m), e, margin_rel=margin_rel)
                r.update({k: q[k] for k in ("estimate", "p", "lo95", "hi95", "wis_ref", "pct_of_ref",
                                            "cls")})
                r["lo95_pct"] = 100 * q["lo95"] / q["wis_ref"]
                r["hi95_pct"] = 100 * q["hi95"] / q["wis_ref"]
                for k in ("L3", "L4", "L3C", "L4C"):
                    r[f"WIS_{k}"] = float(weekly_pooled(_sub(gg, m), f"wis_{k}").mean())
            rows.append(r)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ v3: robustness
def weekly_pooled(g, col):
    from pop.eval.estimands import weekly_pooled as wp
    return wp(g, col)


def ewc_fixed_B(d, h: int, B: int = 4) -> dict:
    """EWC + HLN with a fixed number of cosine terms B (t_B reference): robust to a non-flat
    spectrum near frequency 0 (review RC: size <= 9% in 12/13 cells). Same construction as
    inference_size_sim.run_methods['ewc_hln_B4']."""
    from scipy import stats as st
    from pop.eval.stats import ewc_var, hln_factor
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    T = d.size
    v, _ = ewc_var(d, B=B)
    se = float(np.sqrt(max(v, 0.0) / T) / hln_factor(T, h))
    dbar = float(d.mean())
    t975 = st.t.ppf(0.975, B)
    p = float(2 * st.t.sf(abs(dbar / se), B)) if se > 0 else (1.0 if dbar == 0 else 0.0)
    return {"estimate": dbar, "se": se, "df": B, "p": p, "lo95": dbar - t975 * se,
            "hi95": dbar + t975 * se}


def iaaft_pvalue(d, h: int, reps: int, seed) -> float:
    """Surrogate-calibrated p of the primary DM/EWC+HLN statistic: share of windowed-IAAFT null
    surrogates (inference_size_sim.IAAFT: real marginal and smoothed spectrum, mean 0) with
    |stat| >= |observed|; (1 + k) / (1 + reps)."""
    from inference_size_sim import IAAFT
    from pop.eval.stats import dm_test
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    tobs = abs(dm_test(d, h=h, lag="ewc").stat)
    gen = IAAFT(d)
    rng = np.random.default_rng(seed)
    k = sum(abs(dm_test(gen.draw(rng), h=h, lag="ewc").stat) >= tobs for _ in range(reps))
    return float((1 + k) / (1 + reps))


def robust_table(gp: pd.DataFrame, cell_id: str, *, iaaft_reps=0, iaaft_ests=("G_excess",),
                 seed=20261118) -> pd.DataFrame:
    """Per estimand (primary pooled rows): EWC B=4 p/CI, delta-method CI of the percent gain
    (WIS(L3) estimated; review_sens.delta_ratio_ci), IAAFT-calibrated p (selected estimands)."""
    import zlib
    from review_sens import delta_ratio_ci
    hmax = int(gp.horizon.max())
    w = weekly_pooled(gp, "wis_L3")
    wref = float(w.mean())
    rows = []
    for j, e in enumerate(ESTIMANDS):
        d = weekly_pooled(gp, e)
        b4 = ewc_fixed_B(d.to_numpy(), hmax, 4)
        dr = delta_ratio_ci(d.to_numpy(), w.reindex(d.index).to_numpy(), hmax)
        r = {"estimand": e, "wis_ref": wref, "B4_p": b4["p"], "B4_lo95_pct": 100 * b4["lo95"] / wref,
             "B4_hi95_pct": 100 * b4["hi95"] / wref, "delta_pct": 100 * dr["ratio"],
             "delta_lo95_pct": 100 * dr["lo95"], "delta_hi95_pct": 100 * dr["hi95"],
             "delta_lo90_pct": 100 * dr["lo90"], "delta_hi90_pct": 100 * dr["hi90"],
             "p_iaaft": np.nan, "iaaft_reps": 0}
        if iaaft_reps and e in iaaft_ests:
            r["p_iaaft"] = iaaft_pvalue(d.to_numpy(), hmax, iaaft_reps,
                                        [seed, zlib.crc32(cell_id.encode()), j])
            r["iaaft_reps"] = int(iaaft_reps)
        rows.append(r)
    return pd.DataFrame(rows)


def pooled_est_rows(gp: pd.DataFrame, *, margin_rel=0.01) -> pd.DataFrame:
    """The three estimands on the rows of gp (primary estimator; % of WIS(L3))."""
    from pop.eval.estimands import infer_estimand
    rows = []
    for e in ESTIMANDS:
        q = infer_estimand(gp, e, margin_rel=margin_rel)
        rows.append({"estimand": e, **{k: q.get(k, np.nan) for k in FIELDS if k in q},
                     "lo95_pct": 100 * q["lo95"] / q["wis_ref"], "hi95_pct": 100 * q["hi95"] / q["wis_ref"]})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ v3: one cell
EXTRAS_LEVELS = ("none", "cheap", "all")


def cell_opts(cell, *, margin_rel, n_boot, block_len, extras, iaaft_reps) -> dict:
    return {"margin_rel": margin_rel, "n_boot": n_boot, "block_len": block_len,
            "row_filter": cell.get("row_filter"), "extras": extras,
            "iaaft_reps": iaaft_reps if (cell.get("group") == "primary" and extras != "none") else 0,
            "group": cell.get("group")}


def cell_key(cell, excl, opts) -> str:
    rungs, _ = ladder_rungs(cell)
    return cache_key(cell, excl, opts, sorted({d for _, ds, _ in rungs for d in ds}))


def load_cached(cdir: Path) -> dict:
    ex = {}
    if (cdir / "extras").is_dir():
        ex = {f.stem: pd.read_parquet(f) for f in sorted((cdir / "extras").glob("*.parquet"))}
    return {"est": pd.read_parquet(cdir / "est.parquet"),
            "ladder": pd.read_parquet(cdir / "ladder.parquet"),
            "info": json.loads((cdir / "info.json").read_text()), "extras": ex}


def cache_valid(cdir: Path, key: str) -> bool:
    return (cdir / "key.txt").exists() and (cdir / "key.txt").read_text().strip() == key


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].map(lambda v: v if v is None or isinstance(v, str) else
                              (str(v) if not isinstance(v, float) else v))
            if df[c].map(lambda v: isinstance(v, float)).any():
                df[c] = df[c].astype(str)
    return df


def _load_metric(cell, excl, metric, horizons):
    """load_cell with another score column (e.g. wis_case) served as wis_log."""
    import estimands_report as ER
    from review_sens import patched_reader
    with patched_reader(metric, horizons):
        g, info = ER.load_cell({r: cell["roles"][r]["dirs"] for r in C.ROLES}, panel=cell.get("panel"),
                               **{k: v for k, v in excl.items() if k != "unit_weeks"})
    if excl.get("unit_weeks"):
        g, _ = apply_unit_weeks(g, excl["unit_weeks"])
    return g, info


def compute_extras(cell, gp, gp_unf, excl, opts, log) -> tuple[dict, dict]:
    """Supporting analyses on the primary (filtered, primary-horizon) rows. Each one is
    independent; a failure is recorded and does not stop the cell."""
    out, errs = {}, {}
    lvl = opts["extras"]
    prim = cell.get("group") == "primary" and not cell.get("estimands")
    hp = sorted(int(h) for h in gp.horizon.unique())

    def run(name, fn):
        try:
            r = fn()
            if r is not None:
                out[name] = r
        except Exception as e:  # noqa: BLE001
            errs[name] = repr(e)[:300]
            log(f"  {cell['id']}: extra {name} failed: {e!r}")

    if not cell.get("estimands"):
        run("unfiltered", lambda: pooled_est_rows(gp_unf, margin_rel=opts["margin_rel"])
            if gp_unf is not None else None)
        run("robust", lambda: robust_table(gp, cell["id"], iaaft_reps=opts["iaaft_reps"]))
        run("strata3", lambda: strata3_table(gp, margin_rel=opts["margin_rel"]))
    if not prim or lvl == "none":
        return out, errs
    import review_more as RM

    def casescale():
        g2, _ = _load_metric(cell, excl, "wis_case", hp)
        g2 = g2[g2.horizon.isin(hp)]
        g2, _ = apply_row_filter(g2, opts["row_filter"])
        r = pooled_est_rows(g2, margin_rel=opts["margin_rel"])
        r["n_rows"] = len(g2)
        return r
    run("casescale", casescale)
    run("weighted", lambda: RM.run_weighted(cell, gp))
    run("outbreak", lambda: RM.run_outbreak(cell, gp))
    run("peryear", lambda: RM.run_peryear(cell, gp))
    if cell["split"] == "S1":
        run("baselines", lambda: RM.run_baselines(cell, gp))
    if lvl == "all":
        def fc():
            o = RM.run_forecast_analyses(cell, gp, {"recal", "mech"})
            out["recal_check"] = o["check"]
            out["mech"] = o["mech"]
            return o["recal"]
        run("recal", fc)
        if cell["split"] in ("S2", "S3", "S4", "S5"):
            def dist():
                import review_explore as RX
                r = RX.run_distance(cell, gp)
                return r["units"]
            run("distance_unit_years", dist)
    return out, errs


def compute_cell(cell: dict, *, cache_root: Path, excl: dict, margin_rel=0.01, n_boot=0,
                 block_len=52, force=False, log=print, extras="none", iaaft_reps=0) -> dict:
    """Returns {'est', 'ladder', 'info', 'extras'} (cached under cache_root/<cell>/)."""
    if extras not in EXTRAS_LEVELS:
        raise ValueError(extras)
    opts = cell_opts(cell, margin_rel=margin_rel, n_boot=n_boot, block_len=block_len,
                     extras=extras, iaaft_reps=iaaft_reps)
    key = cell_key(cell, excl, opts)
    cdir = Path(cache_root) / cell["id"]
    if not force and cache_valid(cdir, key):
        log(f"  {cell['id']}: cache hit ({key})")
        return load_cached(cdir)
    log(f"  {cell['id']}: computing (row_filter={opts['row_filter']}, extras={extras}) ...")
    rungs, notes = ladder_rungs(cell)
    roles = {r: cell["roles"][r]["dirs"] for r in C.ROLES}
    lexcl = {k: v for k, v in excl.items() if k != "unit_weeks"}
    g0, info = load_cell(roles, panel=cell.get("panel"), **lexcl)
    g_v1 = None
    if excl.get("unit_weeks"):
        g_v1 = g0
        g0, uinfo = apply_unit_weeks(g0, excl["unit_weeks"])
        info = {**info, **uinfo}
        if uinfo.get("unit_week_rows_dropped", 0) == 0:
            g_v1 = None
    g, finfo = apply_row_filter(g0, opts["row_filter"])
    hkw = {"primary_horizons": cell.get("primary_horizons"),
           "secondary_horizons": cell.get("secondary_horizons")}
    hp, hs = resolve_horizons(g.horizon.unique(), **hkw)
    gp_unf = None
    if opts["row_filter"]:
        gp_unf = _sub(g0, g0.horizon.isin(hp).to_numpy())
    del g0
    gp_v1 = None
    if g_v1 is not None:     # sensitivity: v1 exclusions (no unit-week exclusion), same row filter
        gf1, _ = apply_row_filter(g_v1, opts["row_filter"])
        gp_v1 = _sub(gf1, gf1.horizon.isin(hp).to_numpy())
        del gf1
    del g_v1
    est = estimand_table(g, margin_rel=margin_rel, n_boot=n_boot, block_len=block_len, **hkw)
    if cell.get("estimands"):
        est = est[est.estimand.isin(cell["estimands"] + ["error"])]
    lad = ladder_table(g, rungs, **hkw)
    sb = {r: {int(k): tuple(v) for k, v in info["roles"][r].get("seeds_by_h", {}).items()}
          for r in C.ROLES} if "roles" in info else {}
    mis = [f"{e} h{h}" for e, (a, b) in ESTIMANDS.items() for h in hp
           if sb and sb[a].get(h) != sb[b].get(h)]
    gp = _sub(g, g.horizon.isin(hp).to_numpy())
    yh = g[g.horizon.isin(hs or [])].groupby("test_year").horizon.nunique() if hs else None
    info = {**info, **finfo, "cache_key": key, "ladder_skipped": notes,
            "states": int(g.state.nunique()),
            "outbreak_share": float(g.outbreak.mean()), "zero_filled_share": float(g.zero_filled.mean()),
            "horizons": sorted(int(x) for x in g.horizon.unique()),
            "primary_horizons": hp, "secondary_horizons": hs,
            "secondary_years": sorted(int(y) for y in yh.index[yh == len(hs)]) if hs else None,
            "seed_set_mismatch_primary": mis, "seed_policy": g.attrs.get("seed_policy"),
            "test_years": sorted(int(x) for x in g.test_year.unique()),
            "rows_scored_primary": int(len(gp)), "units_scored": int(gp.unit_id.nunique()),
            "ladder_rows_pooled": int(lad[lad.horizon == "pooled"].n_rows.max()) if len(lad) else 0,
            "flags": cell.get("flags", []), "opts": opts}
    del g
    ex, errs = compute_extras(cell, gp, gp_unf, excl, opts, log)
    if gp_v1 is not None and not cell.get("estimands"):
        try:
            ex["excl_v1"] = pooled_est_rows(gp_v1, margin_rel=margin_rel).assign(n_rows=len(gp_v1))
            ex["strata3_excl_v1"] = strata3_table(gp_v1, margin_rel=margin_rel)
            info["unit_week_rows_dropped_primary"] = int(len(gp_v1) - len(gp))
            info["unit_week_share_dropped_primary"] = float(1 - len(gp) / len(gp_v1))
        except Exception as e:  # noqa: BLE001
            errs["excl_v1"] = repr(e)[:300]
        del gp_v1
    info["extras_errors"] = errs
    info["extras_done"] = sorted(ex)
    for df in (est, lad):
        df.insert(0, "cell", cell["id"])
    if "pooled_over" not in est:
        est["pooled_over"] = ""
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "key.txt").unlink(missing_ok=True)
    _atomic_parquet(est.astype({c: str for c in ("horizon", "test_year", "stratum", "estimand", "cls",
                                                   "reason", "pooled_over") if c in est}), cdir / "est.parquet")
    _atomic_parquet(lad, cdir / "ladder.parquet")
    xd = cdir / "extras"
    if xd.exists():
        for f in xd.glob("*.parquet"):
            f.unlink()
    xd.mkdir(exist_ok=True)
    for k, df in ex.items():
        df = df.copy()
        df.insert(0, "cell", cell["id"]) if "cell" not in df else None
        _atomic_parquet(_clean(df), xd / f"{k}.parquet")
    (cdir / "info.json").write_text(json.dumps(info, indent=1, default=str))
    (cdir / "key.txt").write_text(key)
    del gp, gp_unf
    return load_cached(cdir)
