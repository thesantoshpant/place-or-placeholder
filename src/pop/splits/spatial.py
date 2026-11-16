"""Spatial helpers for split S3: centroids, correlogram-based buffer distance, k-means blocks, buffers.

Distances are great-circle (haversine) km between unit centroids.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

R_EARTH_KM = 6371.0088


# ----------------------------------------------------------------------------------------- centroids
def unit_centroids(units: pd.DataFrame, boundaries: pd.DataFrame) -> pd.DataFrame:
    """One row per unit in `units` (unit_id, country, adm1) with lon/lat and `centroid_source`.

    Units without a matched polygon fall back to the mean centroid of matched units in the same
    (country, adm1); `centroid_source` is 'polygon' or 'adm1_mean' (or 'missing' if even that fails).
    """
    b = boundaries[["unit_id", "centroid_lon", "centroid_lat"]].rename(
        columns={"centroid_lon": "lon", "centroid_lat": "lat"})
    d = units[["unit_id", "country", "adm1"]].drop_duplicates("unit_id").merge(b, on="unit_id", how="left")
    ok = d.lon.notna() & d.lat.notna()
    d["centroid_source"] = np.where(ok, "polygon", "adm1_mean")
    m = d[ok].groupby(["country", "adm1"])[["lon", "lat"]].mean()
    fb = d.loc[~ok, ["country", "adm1"]].merge(m, left_on=["country", "adm1"], right_index=True, how="left")
    d.loc[~ok, "lon"] = fb["lon"].to_numpy()
    d.loc[~ok, "lat"] = fb["lat"].to_numpy()
    d.loc[d.lon.isna(), "centroid_source"] = "missing"
    return d.reset_index(drop=True)


def haversine_matrix(lon1, lat1, lon2=None, lat2=None) -> np.ndarray:
    """Pairwise great-circle distances (km); (n1, n2)."""
    if lon2 is None:
        lon2, lat2 = lon1, lat1
    l1, p1, l2, p2 = (np.radians(np.asarray(x, float)) for x in (lon1, lat1, lon2, lat2))
    dlat = p2[None, :] - p1[:, None]
    dlon = l2[None, :] - l1[:, None]
    a = np.sin(dlat / 2) ** 2 + np.cos(p1)[:, None] * np.cos(p2)[None, :] * np.sin(dlon / 2) ** 2
    return 2 * R_EARTH_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


# --------------------------------------------------------------------------------------- correlogram
def deseasonalised_residuals(panel: pd.DataFrame, mode: str = "additive",
                              min_nonzero_weeks: int = 10) -> pd.DataFrame:
    """Wide (week x unit) residuals of log1p(cases).

    mode='additive': y - unit mean - country week-of-year effect (of unit-demeaned y)   [primary]
    mode='unit_woy': y - unit x week-of-year mean (unit-specific seasonality removed)    [sensitivity]
    mode='week_fe' : y - unit mean - calendar-week mean (removes the country-wide signal of each week,
                     incl. national epidemic years; isolates spatially structured co-variation)
    flag_gap rows are set to NaN. Units with < `min_nonzero_weeks` non-zero case weeks are dropped
    (near-all-zero series carry no signal and have unstable correlations).
    """
    d = panel[["unit_id", "week_start", "cases", "flag_gap"]].copy()
    nz = (d.cases > 0).groupby(d.unit_id).sum()
    d = d[d.unit_id.isin(nz.index[nz >= min_nonzero_weeks])]
    d["y"] = np.log1p(d.cases.astype(float))
    d.loc[d.flag_gap.astype(bool), "y"] = np.nan
    d["woy"] = np.minimum(pd.to_datetime(d.week_start).dt.isocalendar().week.astype(int), 52)
    if mode == "additive":
        d["y"] = d.y - d.groupby("unit_id").y.transform("mean")
        d["y"] = d.y - d.groupby("woy").y.transform("mean")
    elif mode == "week_fe":
        d["y"] = d.y - d.groupby("unit_id").y.transform("mean")
        d["y"] = d.y - d.groupby("week_start").y.transform("mean")
    elif mode == "unit_woy":
        d["y"] = d.y - d.groupby(["unit_id", "woy"]).y.transform("mean")
    else:
        raise ValueError(mode)
    return d.pivot(index="week_start", columns="unit_id", values="y")


def correlogram(resid: pd.DataFrame, cent: pd.DataFrame, bin_km: float = 25.0,
                max_km: float = 1500.0) -> pd.DataFrame:
    """Mean pairwise Pearson correlation of residual series by centroid-distance bin.

    NaNs (flag_gap) are filled with 0 (= unit/seasonal expectation).
    """
    c = cent.set_index("unit_id").loc[resid.columns]
    keep = c.lon.notna().to_numpy()
    X = resid.loc[:, keep].fillna(0.0).to_numpy()
    c = c[keep]
    X = X - X.mean(0)
    sd = X.std(0)
    ok = sd > 0
    X, c = X[:, ok] / sd[ok], c[ok]
    C = (X.T @ X) / X.shape[0]
    D = haversine_matrix(c.lon.to_numpy(), c.lat.to_numpy())
    iu = np.triu_indices(len(c), 1)
    dist, corr = D[iu], C[iu]
    sel = dist < max_km
    edges = np.arange(0, max_km + bin_km, bin_km)
    b = np.digitize(dist[sel], edges) - 1
    out = pd.DataFrame({"bin": b, "corr": corr[sel]}).groupby("bin")["corr"].agg(["mean", "median", "count"])
    out["dist_lo"] = edges[out.index]
    out["dist_mid"] = out.dist_lo + bin_km / 2
    out.attrs["n_units"] = int(len(c))
    return out.reset_index(drop=True)[["dist_lo", "dist_mid", "mean", "median", "count"]]


def first_crossing(cg: pd.DataFrame, thr: float = 0.1, col: str = "mean", min_pairs: int = 30) -> float:
    """Upper edge (km) of the first distance bin whose mean correlation is < thr."""
    g = cg[cg["count"] >= min_pairs]
    below = g[g[col] < thr]
    if below.empty:
        return float("nan")
    width = float(g.dist_mid.iloc[0] - g.dist_lo.iloc[0]) * 2
    return float(below.dist_lo.iloc[0] + width)


def fit_exponential(cg: pd.DataFrame, min_pairs: int = 30) -> dict:
    """Fit corr(h) = c0 * exp(-h / a) + c_inf by weighted least squares. Practical range = 3a."""
    from scipy.optimize import curve_fit
    g = cg[cg["count"] >= min_pairs]
    f = lambda h, c0, a, cinf: c0 * np.exp(-h / a) + cinf  # noqa: E731
    p, _ = curve_fit(f, g.dist_mid, g["mean"], p0=[g["mean"].iloc[0], 200.0, 0.0],
                     sigma=1 / np.sqrt(g["count"]), bounds=([0, 1, -1], [2, 1e4, 1]), maxfev=20000)
    return {"c0": p[0], "a_km": p[1], "c_inf": p[2], "practical_range_km": 3 * p[1]}


# --------------------------------------------------------------------------------------------- blocks
def kmeans_blocks(cent: pd.DataFrame, k: int, seed: int = 0) -> np.ndarray:
    """k-means on locally-projected (equirectangular, km) centroids; labels ordered west->east."""
    from sklearn.cluster import KMeans
    lat0 = np.radians(cent.lat.mean())
    xy = np.c_[np.radians(cent.lon) * np.cos(lat0), np.radians(cent.lat)] * R_EARTH_KM
    km = KMeans(n_clusters=k, n_init=20, random_state=seed).fit(xy)
    order = np.argsort(np.argsort(km.cluster_centers_[:, 0] + 1e-6 * km.cluster_centers_[:, 1]))
    return order[km.labels_]


def buffer_exclusions(cent: pd.DataFrame, blocks: np.ndarray, d_km: float) -> pd.DataFrame:
    """(test_block, excluded_unit_id, dist_km): non-test-block units within d_km of any unit of the block."""
    lon, lat = cent.lon.to_numpy(), cent.lat.to_numpy()
    rows = []
    for blk in np.unique(blocks):
        inb = blocks == blk
        dmin = haversine_matrix(lon[inb], lat[inb], lon[~inb], lat[~inb]).min(0)
        ids = cent.unit_id.to_numpy()[~inb]
        hit = dmin <= d_km
        rows.append(pd.DataFrame({"test_block": int(blk), "excluded_unit_id": ids[hit], "dist_km": dmin[hit]}))
    return pd.concat(rows, ignore_index=True)
