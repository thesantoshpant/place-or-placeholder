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

KIT_VERSION = "2"  # 2: primary pooled = manifest primary_horizons
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
             "cell": {k: cell.get(k) for k in ("estimands", "role_labels", "ref", "panel",
                                                "primary_horizons", "secondary_horizons")}}
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
        add(sub(g.horizon.isin(hs)), {"horizon": sec_label(hs), "test_year": "pooled",
                                      "stratum": "all", "pooled_over": ",".join(map(str, hs))})
    for y in sorted(gp.test_year.unique()):
        add(sub(gp.test_year == y, gp), {"horizon": "pooled", "test_year": str(int(y)),
                                         "stratum": "all", "pooled_over": po})
    strata = {"observed": ~gp.zero_filled, "zero_filled": gp.zero_filled,
              "outbreak": gp.outbreak, "non_outbreak": ~gp.outbreak}
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


def compute_cell(cell: dict, *, cache_root: Path, excl: dict, margin_rel=0.01, n_boot=0,
                 block_len=52, force=False, log=print) -> dict:
    """Returns {'est': DataFrame, 'ladder': DataFrame, 'info': dict} (cached)."""
    rungs, notes = ladder_rungs(cell)
    opts = {"margin_rel": margin_rel, "n_boot": n_boot, "block_len": block_len}
    key = cache_key(cell, excl, opts, sorted({d for _, ds, _ in rungs for d in ds}))
    cdir = Path(cache_root) / cell["id"]
    if not force and (cdir / "key.txt").exists() and (cdir / "key.txt").read_text().strip() == key:
        log(f"  {cell['id']}: cache hit ({key})")
        return {"est": pd.read_parquet(cdir / "est.parquet"),
                "ladder": pd.read_parquet(cdir / "ladder.parquet"),
                "info": json.loads((cdir / "info.json").read_text())}
    log(f"  {cell['id']}: computing ...")
    roles = {r: cell["roles"][r]["dirs"] for r in C.ROLES}
    g, info = load_cell(roles, panel=cell.get("panel"), **excl)
    hkw = {"primary_horizons": cell.get("primary_horizons"),
           "secondary_horizons": cell.get("secondary_horizons")}
    est = estimand_table(g, margin_rel=margin_rel, n_boot=n_boot, block_len=block_len, **hkw)
    if cell.get("estimands"):
        est = est[est.estimand.isin(cell["estimands"] + ["error"])]
    lad = ladder_table(g, rungs, **hkw)
    hp, hs = resolve_horizons(g.horizon.unique(), **hkw)
    # seed sets of the two roles of each estimand at the primary horizons (deviations row 22);
    # the common-seed policy of load_cell handles a mismatch, it is only recorded here
    sb = {r: {int(k): tuple(v) for k, v in info["roles"][r].get("seeds_by_h", {}).items()}
          for r in C.ROLES} if "roles" in info else {}
    mis = [f"{e} h{h}" for e, (a, b) in ESTIMANDS.items() for h in hp
           if sb and sb[a].get(h) != sb[b].get(h)]
    info = {**info, "cache_key": key, "ladder_skipped": notes, "states": int(g.state.nunique()),
            "outbreak_share": float(g.outbreak.mean()), "zero_filled_share": float(g.zero_filled.mean()),
            "horizons": sorted(int(x) for x in g.horizon.unique()),
            "primary_horizons": hp, "secondary_horizons": hs, "seed_set_mismatch_primary": mis,
            "seed_policy": g.attrs.get("seed_policy"),
            "test_years": sorted(int(x) for x in g.test_year.unique())}
    for df in (est, lad):
        df.insert(0, "cell", cell["id"])
    if "pooled_over" not in est:
        est["pooled_over"] = ""
    cdir.mkdir(parents=True, exist_ok=True)
    _atomic_parquet(est.astype({c: str for c in ("horizon", "test_year", "stratum", "estimand", "cls",
                                                   "reason", "pooled_over") if c in est}), cdir / "est.parquet")
    _atomic_parquet(lad, cdir / "ladder.parquet")
    (cdir / "info.json").write_text(json.dumps(info, indent=1, default=str))
    (cdir / "key.txt").write_text(key)
    del g
    return {"est": pd.read_parquet(cdir / "est.parquet"), "ladder": lad, "info": info}
