"""Build split fold assignments (S2/S3/S4) and S3 buffers; estimate buffer distance D from correlograms.

Usage: python scripts/splits/build_splits.py [--seed N]
Re-runnable: everything is recomputed from the panel and the current boundaries file (units without
geometry fall back to the adm1 mean centroid and are flagged in `centroid_source`).

Outputs
  data/processed/splits_v1/unit_folds.parquet          unit_id, country, adm1, s2_fold, s3_block, s4_fold, centroid_source, lon, lat
  data/processed/splits_v1/s3_buffer_exclusions.parquet country, test_block, excluded_unit_id, dist_km
  data/processed/splits_v1/buffer_distance.json         D per country + method details
  data/processed/splits_v1/fold_sizes.csv
  outputs/splits/correlogram_<country>.png/.csv
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from pop.splits import spatial as sp  # noqa: E402
from pop.splits import splits as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/processed/splits_v1"
FIG = ROOT / "outputs/splits"
SPATIAL = ("BRAZIL", "COLOMBIA")
CG_YEARS = (2014, 2019)        # correlogram estimated on pre-test years only (<= tuning origin)
THRESH = 0.1
N_BLOCKS = {"BRAZIL": 10, "COLOMBIA": 6}
N_S4 = 5
BIN_KM = {"BRAZIL": 25.0, "COLOMBIA": 10.0}
MAX_KM = {"BRAZIL": 2000.0, "COLOMBIA": 800.0}


def s4_folds(units: pd.DataFrame, k: int, seed: int) -> np.ndarray:
    """Stratified by adm1: shuffle within adm1, deal round-robin with a running offset across adm1s."""
    rng = np.random.default_rng(seed)
    fold = pd.Series(-1, index=units.index)
    offset = 0
    for _, g in units.sort_values(["adm1", "unit_id"]).groupby("adm1", sort=True):
        idx = rng.permutation(g.index.to_numpy())
        fold.loc[idx] = (np.arange(len(idx)) + offset) % k
        offset = (offset + len(idx)) % k
    return fold.to_numpy()


def buffer_distance(res: dict) -> float:
    """D = max of the first 0.1-crossings of the 'additive' (protocol) and 'week_fe' correlograms.

    The additive curve can plateau above 0.1 (country-wide epidemic years: a non-spatial floor that no
    buffer can remove), in which case only the week_fe crossing is defined; otherwise take the larger.
    """
    xs = [res[m]["first_crossing_km"] for m in ("additive", "week_fe")]
    xs = [x for x in xs if np.isfinite(x)]
    return float(max(xs))


def correlogram_country(panel, cent, c):
    q = panel[(panel.country == c) & panel.year.between(*CG_YEARS)]
    res, curves = {}, {}
    for mode in ("additive", "week_fe", "unit_woy"):
        r = sp.deseasonalised_residuals(q, mode)
        cg = sp.correlogram(r, cent, BIN_KM[c], MAX_KM[c])
        curves[mode] = cg
        fit = sp.fit_exponential(cg)
        res[mode] = {"n_units": int(r.shape[1]), "n_weeks": int(r.shape[0]),
                     "first_crossing_km": sp.first_crossing(cg, THRESH), **fit}
    out = pd.concat([cg.assign(mode=m) for m, cg in curves.items()], ignore_index=True)
    out.to_csv(FIG / f"correlogram_{c.lower()}.csv", index=False)
    fig, ax = plt.subplots(figsize=(6.4, 4))
    for m, cg in curves.items():
        f = res[m]
        h = np.linspace(0, MAX_KM[c], 400)
        ax.plot(cg.dist_mid, cg["mean"], "o", ms=3, label=f"{m} (n={f['n_units']})")
        ax.plot(h, f["c0"] * np.exp(-h / f["a_km"]) + f["c_inf"], lw=1, color=ax.lines[-1].get_color())
    ax.axhline(THRESH, color="grey", ls="--", lw=0.8)
    D = buffer_distance(res)
    ax.axvline(D, color="k", lw=0.8)
    ax.text(D, ax.get_ylim()[1] * 0.9, f" D = {D:.0f} km", fontsize=9)
    ax.set(xlabel="centroid distance (km)", ylabel="mean pairwise correlation",
           title=f"{c}: de-seasonalised log1p(cases), {CG_YEARS[0]}-{CG_YEARS[1]}")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / f"correlogram_{c.lower()}.png", dpi=150)
    plt.close(fig)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=S.DEFAULT_SEED)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)

    panel = pd.read_parquet(ROOT / "data/processed/panel_weekly_v1.parquet",
                            columns=["unit_id", "country", "adm1", "week_start", "year", "cases", "flag_gap"])
    bnd = pd.read_parquet(ROOT / "data/interim/boundaries/opendengue_units_v1.parquet",
                          columns=["unit_id", "centroid_lon", "centroid_lat"])
    uf = sp.unit_centroids(panel, bnd).sort_values(["country", "adm1", "unit_id"]).reset_index(drop=True)
    for col in ("s2_fold", "s3_block", "s4_fold"):
        uf[col] = pd.array([pd.NA] * len(uf), dtype="Int16")

    dist_info, excl = {}, []
    for c in SPATIAL:
        m = (uf.country == c).to_numpy()
        cu = uf[m]
        adm1 = sorted(cu.adm1.unique())
        uf.loc[m, "s2_fold"] = cu.adm1.map({x: i for i, x in enumerate(adm1)}).astype("Int16").to_numpy()
        uf.loc[m, "s4_fold"] = s4_folds(cu, N_S4, a.seed)
        blocks = sp.kmeans_blocks(cu, N_BLOCKS[c], seed=a.seed % (2**31))
        uf.loc[m, "s3_block"] = blocks
        info = correlogram_country(panel, uf, c)
        D = buffer_distance(info)
        dist_info[c] = {"D_km": D, "threshold": THRESH, "years": CG_YEARS, "bin_km": BIN_KM[c],
                        "n_blocks": N_BLOCKS[c], **{k: {kk: (float(vv) if isinstance(vv, (float, np.floating)) else vv)
                                                         for kk, vv in v.items()} for k, v in info.items()}}
        ex = sp.buffer_exclusions(cu.reset_index(drop=True), blocks, D)
        excl.append(ex.assign(country=c))
        print(c, json.dumps(dist_info[c], indent=1))

    uf.to_parquet(OUT / "unit_folds.parquet", index=False)
    excl = pd.concat(excl, ignore_index=True)[["country", "test_block", "excluded_unit_id", "dist_km"]]
    excl["test_block"] = excl.test_block.astype("int16")
    excl.to_parquet(OUT / "s3_buffer_exclusions.parquet", index=False)
    (OUT / "buffer_distance.json").write_text(json.dumps(dist_info, indent=1))

    S.load_unit_folds.cache_clear()
    S.load_buffer_exclusions.cache_clear()
    rows = []
    for name in S.SPLITS:
        for sp_ in S.iter_folds(name):
            if sp_.origin != S.FIRST_TEST_ORIGIN:
                continue
            rows.append({"split": name, "country": sp_.country, "fold": sp_.fold,
                         "n_train_units": len(sp_.train_units), "n_test_units": len(sp_.test_units),
                         "n_buffer_excluded": len(set(uf.unit_id[uf.country == sp_.country]) - sp_.train_units
                                                  - sp_.test_units) if name in ("S2", "S3", "S4") else 0})
    fs = pd.DataFrame(rows)
    fs.to_csv(OUT / "fold_sizes.csv", index=False)
    print(fs.groupby(["split", "country"]).agg(n_folds=("fold", "size"), test_min=("n_test_units", "min"),
                                               test_max=("n_test_units", "max"), train_min=("n_train_units", "min"),
                                               train_max=("n_train_units", "max"),
                                               buf_mean=("n_buffer_excluded", "mean")).to_string())
    print(uf[uf.centroid_source != "polygon"][["unit_id", "country", "adm1", "centroid_source"]].to_string())


if __name__ == "__main__":
    main()
