"""Feature-level registry: L0..L4 and the L3+C1..C5 control variants.

A level is ``fn(grid, idx, h, ctx) -> DataFrame`` (rows aligned with ``idx``: columns u, t, o =
unit index, target-week index, origin-week index = t - h). ``ctx`` is a :class:`Context` that
holds the country, the non-case inputs (loaded lazily from ``data/interim`` or injected for tests)
and, for the controls, the current split instance.

    L0   history.l0_features                                     (1 col)
    L1   history.l1_features                                     (23 cols)
    L2   L1 + climate                                            (23 + 51 = 74 cols)
         lags 0..11 of tmean, precip, rh (36) + 4/8/12-week rolling means of
         tmean, tmin, tmax, precip, rh (15); all pop-weighted, relative to the origin week.
    L3   L2 + standard remote sensing                            (74 + 12 = 86 cols)
         ndvi, lst_day, lst_night (pop-weighted) for the 3 latest complete months before the
         origin (9); night lights + built share, year y-1 (2); log1p(population), year y-1 (1).
    L4   L3 + AlphaEarth                                         (86 + 64 = 150 cols)
         pop-weighted mean embedding (w_A00..w_A63) of year y-1, renormalised to unit length.
    L3+Ck  L3 + control Ck (replaces the AlphaEarth block); refit per split instance and origin.
    L4+Ck  L4 + the same control block as L3+Ck (identical construction, seed and kwargs);
           used for G_excess = WIS(L3+C*) - WIS(L4+C*).

Availability rules (asserted at read time):
    weekly  source week <= origin week                       (history._take)
    monthly source month ended before the origin week starts (month index < month of origin)
    yearly  source year < target epi-year (y-1)               ("yearly_ref: origin" -> < origin year)
"""
from __future__ import annotations

import glob
import logging
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from pop.features import history as H

log = logging.getLogger("pop.levels")
ROOT = Path(__file__).resolve().parents[3]

CLIMATE_VARS = ("tmean", "tmin", "tmax", "precip", "rh")
CLIMATE_LAG_VARS = ("tmean", "precip", "rh")
CLIMATE_LAGS = tuple(range(12))
CLIMATE_ROLL = (4, 8, 12)
MONTHLY_VARS = ("ndvi_pw", "lst_day_pw", "lst_night_pw")
MONTHS_BACK = (1, 2, 3)
YEARLY_VARS = ("ntl_pw", "built_share")
AE_DIM = 64
AE_BANDS = [f"A{i:02d}" for i in range(AE_DIM)]
CONTROLS = ("C1", "C2", "C3", "C4", "C5")

PATHS = {
    "climate": ["data/interim/climate/climate_weekly_{c}_v1.parquet"],
    "rs_monthly": ["data/interim/remote_sensing/rs_monthly_{c}_v1.parquet"],
    "rs_yearly": ["data/interim/remote_sensing/rs_yearly_{c}_v1.parquet"],
    "population": ["data/interim/population/unit_population_yearly_{c}_v1.parquet",
                   "data/interim/population/unit_population_yearly_v1.parquet"],
    "alphaearth": ["data/interim/alphaearth/{c}/alphaearth_{c}_*.parquet"],
}
LST_VARS = ("lst_day_pw", "lst_night_pw")
LST_SCREEN_DROP_C = 10.0     # flag LST more than 10 degC below the unit's calendar-month median
LST_SCREEN_LAST_YEAR = 2017  # median from years <= 2017 (before the first training target year 2018)
RS_VERSIONS = ("v1", "v2")  # rs_monthly: v1 = unmasked LST, v2 = QC-masked LST (same keys/columns)


class MissingInput(FileNotFoundError):
    """A level needs an input table that has not been built yet."""


@dataclass
class Context:
    """Per-country inputs for the feature levels.

    options: climate_lag_vars, yearly_ref ('target' | 'origin'),
             remote_sensing {version: 'v1' (default) | 'v2'} (v2 = QC-masked MODIS LST; monthly table only),
                            {lst_screen: bool} (default false; LST outlier screen, see screen_lst),
             alphaearth {weights: 'w' | 'u', normalize: bool}, control_kw {C4: {range_km: ...}}.
    tables:  name -> DataFrame; anything missing is loaded from PATHS under ``root``.
    split / seed / panel / units are used by the controls only.
    """
    country: str
    root: Path = ROOT
    options: dict = field(default_factory=dict)
    tables: dict = field(default_factory=dict)
    split: object = None
    seed: int = 0
    panel: pd.DataFrame | None = None
    _cache: dict = field(default_factory=dict, repr=False)
    _grid: object = field(default=None, repr=False)

    # -------------------------------------------------------------- tables
    def table(self, name: str) -> pd.DataFrame:
        if name not in self.tables:
            self.tables[name] = self._load(name)
        return self.tables[name]

    def _load(self, name: str) -> pd.DataFrame:
        if name == "units":
            from pop.features.controls import load_unit_points
            return load_unit_points()
        c = self.country.lower()
        tpls = PATHS[name]
        if name == "rs_monthly":
            ver = self.options.get("remote_sensing", {}).get("version", "v1")
            if ver not in RS_VERSIONS:
                raise ValueError(f"remote_sensing version {ver!r} not in {RS_VERSIONS}")
            tpls = [t.replace("_v1.parquet", f"_{ver}.parquet") for t in tpls]
        for tpl in tpls:
            pat = str(Path(self.root) / tpl.format(c=c))
            files = sorted(glob.glob(pat))
            if not files:
                continue
            if name == "alphaearth":
                parts = []
                for f in files:
                    m = re.search(r"_(\d{4})\.parquet$", f)
                    if m:
                        parts.append(pd.read_parquet(f).assign(year=int(m.group(1))))
                if parts:
                    return pd.concat(parts, ignore_index=True)
                continue
            df = pd.read_parquet(files[0])
            if "country" in df.columns:  # pooled multi-country file
                df = df[df["country"].astype(str).str.upper() == self.country.upper()]
            return df
        raise MissingInput(f"{name} for {self.country}: none of {tpls} under {self.root}")

    # -------------------------------------------------------------- grid-aligned arrays
    def _cached(self, grid, key, fn):
        if self._grid is not grid:
            self._cache = {k: v for k, v in self._cache.items() if k[0] == "split"}
            self._grid = grid
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    def weekly(self, grid, vars_=CLIMATE_VARS) -> np.ndarray:
        """(V, U, W) climate aligned to the grid (NaN where missing)."""
        def make():
            df = self.table("climate")
            ui = pd.Index(grid.units).get_indexer(df["unit_id"].astype(str))
            wi = pd.DatetimeIndex(grid.weeks).as_unit("ns").get_indexer(
                pd.DatetimeIndex(pd.to_datetime(df["week_start"])).as_unit("ns"))
            ok = (ui >= 0) & (wi >= 0)
            A = np.full((len(vars_), len(grid.units), len(grid.weeks)), np.nan)
            for k, v in enumerate(vars_):
                A[k, ui[ok], wi[ok]] = df[v].to_numpy(float)[ok]
            return A
        return self._cached(grid, ("weekly", vars_), make)

    def periodic(self, grid, name, vars_, period_col) -> tuple[np.ndarray, int]:
        """(V, U, P) array of a monthly (period = year*12 + month-1) or yearly table + offset."""
        def make():
            df = self.table(name)
            per = (df["year"].astype(int) * 12 + df["month"].astype(int) - 1
                   if period_col == "month" else df["year"].astype(int)).to_numpy()
            p0 = int(per.min())
            ui = pd.Index(grid.units).get_indexer(df["unit_id"].astype(str))
            ok = ui >= 0
            A = np.full((len(vars_), len(grid.units), int(per.max()) - p0 + 1), np.nan)
            for k, v in enumerate(vars_):
                A[k, ui[ok], per[ok] - p0] = df[v].to_numpy(float)[ok]
            return A, p0
        return self._cached(grid, (name, tuple(vars_)), make)

    def embeddings(self) -> pd.DataFrame:
        """unit_id, year, A00..A63 from the AlphaEarth table (weights/normalisation per options)."""
        if ("emb",) not in self._cache:
            o = {"weights": "w", "normalize": True, **self.options.get("alphaearth", {})}
            df = self.table("alphaearth")
            cols = [f"{o['weights']}_{b}" for b in AE_BANDS]
            V = df[cols].to_numpy(float)
            if o["normalize"]:
                V = renormalize(V)
            e = pd.DataFrame(V, columns=AE_BANDS)
            e.insert(0, "year", df["year"].astype(int).to_numpy())
            e.insert(0, "unit_id", df["unit_id"].astype(str).to_numpy())
            if e.duplicated(["unit_id", "year"]).any():
                raise ValueError("duplicate (unit_id, year) in AlphaEarth table")
            self._cache[("emb",)] = e
        return self._cache[("emb",)]


def renormalize(V: np.ndarray) -> np.ndarray:
    """Rows scaled to unit L2 norm (rows with zero / non-finite norm -> NaN)."""
    n = np.linalg.norm(V, axis=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = V / n
    out[~np.isfinite(n[:, 0]) | (n[:, 0] == 0)] = np.nan
    return out


def lst_screen_flags(A: np.ndarray, p0: int, last_year: int = LST_SCREEN_LAST_YEAR,
                     drop: float = LST_SCREEN_DROP_C) -> np.ndarray:
    """Cloud-contamination screen for one monthly LST array A (U, P), period p0 = year*12+month-1.

    True where the value is more than ``drop`` degC below the unit's median for that calendar
    month, the median taken over years <= ``last_year`` only (causal: before the first training
    target year, hence identical at every origin). Unit-months without reference data: no flag.
    """
    per = np.arange(A.shape[1]) + p0
    cal, yr = per % 12, per // 12
    flag = np.zeros(A.shape, bool)
    for c in range(12):
        cols = cal == c
        ref = cols & (yr <= last_year)
        if not ref.any():
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            med = np.nanmedian(A[:, ref], axis=1)
        with np.errstate(invalid="ignore"):
            flag[:, cols] = A[:, cols] < (med[:, None] - drop)
    return flag


def screen_lst(M: np.ndarray, p0: int, vars_=MONTHLY_VARS, **kw) -> np.ndarray:
    """Copy of the (V, U, P) monthly array with screened LST values (lst_screen_flags) set to NaN."""
    out = M.copy()
    for k, v in enumerate(vars_):
        if v in LST_VARS:
            out[k][lst_screen_flags(M[k], p0, **kw)] = np.nan
    return out


# ------------------------------------------------------------------ availability-checked reads
def _take_before(A: np.ndarray, u: np.ndarray, src: np.ndarray, limit: np.ndarray, p0: int):
    """A[u, src - p0] with a hard check src < limit (strictly earlier period); NaN out of range."""
    if np.any(src >= limit):
        raise AssertionError("feature would read a period that is not complete at the origin")
    j = src - p0
    out = np.full(src.shape, np.nan)
    ok = (j >= 0) & (j < A.shape[1])
    out[ok] = A[u[ok], j[ok]]
    return out


def month_index(dates: pd.DatetimeIndex) -> np.ndarray:
    return (dates.year * 12 + dates.month - 1).to_numpy()


def _yearly_src(grid, idx, ctx):
    """(source year, limit year): y-1 of the target epi-year (default) or of the origin week."""
    ref = ctx.options.get("yearly_ref", "target")
    col = {"target": "t", "origin": "o"}[ref]
    lim = grid.year[idx[col].to_numpy()].astype(int)
    return lim - 1, lim


# ------------------------------------------------------------------ blocks
def climate_block(grid, idx, ctx) -> pd.DataFrame:
    lag_vars = tuple(ctx.options.get("climate_lag_vars", CLIMATE_LAG_VARS))
    A = ctx.weekly(grid)
    u, o = idx["u"].to_numpy(), idx["o"].to_numpy()
    cols = {}
    for k, v in enumerate(CLIMATE_VARS):
        lags = np.stack([H._take(A[k], u, o - L, o) for L in range(max(CLIMATE_ROLL))])
        if v in lag_vars:
            for L in CLIMATE_LAGS:
                cols[f"{v}_l{L}"] = lags[L].astype(np.float32)
        for r in CLIMATE_ROLL:
            cols[f"{v}_r{r}"] = lags[:r].mean(axis=0).astype(np.float32)
    return pd.DataFrame(cols, index=idx.index)


def rs_block(grid, idx, ctx) -> pd.DataFrame:
    u, o = idx["u"].to_numpy(), idx["o"].to_numpy()
    cols = {}
    M, m0 = ctx.periodic(grid, "rs_monthly", MONTHLY_VARS, "month")
    if ctx.options.get("remote_sensing", {}).get("lst_screen", False):
        M = ctx._cached(grid, ("rs_monthly_lst_screened",), lambda: screen_lst(M, m0))
    om = month_index(pd.DatetimeIndex(grid.weeks[o]))
    for k, v in enumerate(MONTHLY_VARS):
        for b in MONTHS_BACK:
            cols[f"{v}_m{b}"] = _take_before(M[k], u, om - b, om, m0).astype(np.float32)
    src, lim = _yearly_src(grid, idx, ctx)
    Y, y0 = ctx.periodic(grid, "rs_yearly", YEARLY_VARS, "year")
    for k, v in enumerate(YEARLY_VARS):
        cols[f"{v}_y1"] = _take_before(Y[k], u, src, lim, y0).astype(np.float32)
    P, p0 = ctx.periodic(grid, "population", ("pop",), "year")
    cols["log_pop_y1"] = np.log1p(_take_before(P[0], u, src, lim, p0)).astype(np.float32)
    return pd.DataFrame(cols, index=idx.index)


def alphaearth_block(grid, idx, ctx) -> pd.DataFrame:
    """Embedding of year y-1 (y = target epi-year), unit-normalised w_ vector by default."""
    def make():
        e = ctx.embeddings()
        yrs = e["year"].to_numpy()
        y0 = int(yrs.min())
        ui = pd.Index(grid.units).get_indexer(e["unit_id"])
        ok = ui >= 0
        A = np.full((AE_DIM, len(grid.units), int(yrs.max()) - y0 + 1), np.nan)
        A[:, ui[ok], yrs[ok] - y0] = e[AE_BANDS].to_numpy(float)[ok].T
        return A, y0
    A, y0 = ctx._cached(grid, ("ae",), make)
    u = idx["u"].to_numpy()
    src, lim = _yearly_src(grid, idx, ctx)
    X = np.stack([_take_before(A[k], u, src, lim, y0) for k in range(AE_DIM)], axis=1)
    miss = np.isnan(X).all(axis=1).mean()
    if miss > 0:
        log.warning("AlphaEarth: %.1f%% of rows have no y-1 embedding", 100 * miss)
    return pd.DataFrame(X.astype(np.float32), columns=[f"ae_{i:02d}" for i in range(AE_DIM)],
                        index=idx.index)


def control_block(control, grid, idx, ctx) -> pd.DataFrame:
    """Control Ck for the current split instance (ctx.split), refit per (split, fold, origin, seed)."""
    from pop.features.controls import make_controls_for_split
    sp = ctx.split
    if sp is None:
        raise ValueError("control levels need ctx.split")
    key = ("split", control, sp.name, str(sp.fold), sp.origin, ctx.seed)
    if key not in ctx._cache:
        kw = dict(ctx.options.get("control_kw", {}).get(control, {}))
        emb = ctx.embeddings() if control in ("C3", "C5") else None
        df = make_controls_for_split(control, sp, ctx.table("units"), panel=ctx.panel,
                                     emb_df=emb, seed=ctx.seed, **kw)
        ctx._cache[key] = df.drop(columns=[c for c in df.columns if c.endswith("_src_unit")])
    df = ctx._cache[key]
    feat = [c for c in df.columns if c not in ("unit_id", "year")]
    left = pd.DataFrame({"unit_id": grid.units[idx["u"].to_numpy()]})
    on = ["unit_id"]
    if "year" in df.columns:  # C3: embedding year y-1
        src, lim = _yearly_src(grid, idx, ctx)
        assert np.all(src < lim)
        left["year"] = src
        on.append("year")
    X = left.merge(df.astype({"unit_id": str}), on=on, how="left")[feat]
    X.index = idx.index
    return X.astype(np.float32)


# ------------------------------------------------------------------ registry
def _l0(grid, idx, h, ctx=None):
    return H.l0_features(grid, idx, h)


def _l1(grid, idx, h, ctx=None):
    return H.l1_features(grid, idx, h)


def _l2(grid, idx, h, ctx):
    return pd.concat([H.l1_features(grid, idx, h), climate_block(grid, idx, ctx)], axis=1)


def _l3(grid, idx, h, ctx):
    return pd.concat([_l2(grid, idx, h, ctx), rs_block(grid, idx, ctx)], axis=1)


def _l4(grid, idx, h, ctx):
    return pd.concat([_l3(grid, idx, h, ctx), alphaearth_block(grid, idx, ctx)], axis=1)


def _l3c(control):
    def fn(grid, idx, h, ctx):
        return pd.concat([_l3(grid, idx, h, ctx), control_block(control, grid, idx, ctx)], axis=1)
    fn.__name__ = f"l3_{control.lower()}"
    return fn


def _l4c(control):
    def fn(grid, idx, h, ctx):
        return pd.concat([_l4(grid, idx, h, ctx), control_block(control, grid, idx, ctx)], axis=1)
    fn.__name__ = f"l4_{control.lower()}"
    return fn


LEVELS = {"L0": _l0, "L1": _l1, "L2": _l2, "L3": _l3, "L4": _l4,
          **{f"L3+{c}": _l3c(c) for c in CONTROLS},
          **{f"L4+{c}": _l4c(c) for c in CONTROLS}}
NO_LOCATION_LEVELS = {"L0", "L1", "L2"}  # history + climate: no location columns allowed
