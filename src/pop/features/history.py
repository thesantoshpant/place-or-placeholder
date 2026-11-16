"""History features on a dense (unit x week) grid of log1p(cases).

A design row is (unit u, origin week index o, horizon h); the target is week o+h.
Every feature value is read through ``_take`` which asserts the source week index
is <= the origin index, so no feature can see data after the origin week.

L0: ``sy1_0`` only (same week last year, T-52), used by the seasonal-naive model.
L1: lags 0..11 relative to the origin; target-week value 1,2,3 years back (T-52j)
    and +-1 week around it; week-of-year sin/cos of the target week.
No unit identifiers, coordinates or admin names are ever produced here.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

LAGS: tuple[int, ...] = tuple(range(12))
SEASONAL_YEARS: tuple[int, ...] = (1, 2, 3)
SEASONAL_OFFSETS: tuple[int, ...] = (-1, 0, 1)
WEEKS_PER_YEAR = 52
WOY_PERIOD = 52.18

# Any column whose name contains one of these tokens is location-specific and
# must not appear in L0/L1 (the controls C1-C4 add them deliberately).
LOCATION_TOKENS = ("unit", "adm", "country", "lat", "lon", "coord", "geo", "name",
                   "code", "state", "region", "district", "muni", "embed", "id")


@dataclass
class Grid:
    units: np.ndarray            # (U,) unit_id strings
    weeks: pd.DatetimeIndex      # (W,) Sunday week_start, regular 7-day spacing
    y: np.ndarray                # (U, W) log1p(cases), float64
    cases: np.ndarray            # (U, W)
    flag_gap: np.ndarray         # (U, W) bool
    zero_filled: np.ndarray      # (U, W) bool
    year: np.ndarray             # (W,) epidemiological year of each week
    woy: np.ndarray              # (W,) epi week number (1..53)


def epi_week_number(weeks: pd.DatetimeIndex) -> np.ndarray:
    """Week number within the epi year (year = calendar year of the Wednesday)."""
    wed = weeks + pd.Timedelta(days=3)
    return (np.asarray(wed.day_of_year) - 1) // 7 + 1


def make_grid(panel: pd.DataFrame) -> Grid:
    """Pivot a zero-filled single-country panel into a dense grid (checks regularity)."""
    p = panel.assign(week_start=pd.to_datetime(panel["week_start"]))
    weeks = pd.DatetimeIndex(np.sort(p["week_start"].unique()))
    if len(weeks) > 1 and not (np.diff(weeks.values) == np.timedelta64(7, "D")).all():
        raise ValueError("weeks are not a regular 7-day sequence")
    units = np.sort(p["unit_id"].astype(str).unique())
    if len(p) != len(units) * len(weeks):
        raise ValueError("panel is not a complete unit x week grid")
    p = p.assign(unit_id=p["unit_id"].astype(str)).sort_values(["unit_id", "week_start"])
    shape = (len(units), len(weeks))
    cases = p["cases"].to_numpy(float).reshape(shape)
    wed = weeks + pd.Timedelta(days=3)
    return Grid(
        units=units, weeks=weeks, y=np.log1p(cases), cases=cases,
        flag_gap=p["flag_gap"].to_numpy(bool).reshape(shape),
        zero_filled=p["zero_filled"].to_numpy(bool).reshape(shape),
        year=wed.year.to_numpy(), woy=epi_week_number(weeks),
    )


def _take(y: np.ndarray, u: np.ndarray, src: np.ndarray, origin: np.ndarray) -> np.ndarray:
    """y[u, src] with a hard no-future check; NaN where src < 0."""
    if np.any(src > origin):
        raise AssertionError("feature would read a week after the origin")
    out = np.full(src.shape, np.nan)
    ok = src >= 0
    out[ok] = y[u[ok], src[ok]]
    return out


def design_index(grid: Grid, target_idx: np.ndarray, h: int) -> pd.DataFrame:
    """All units x the given target-week indices, for horizon h."""
    U = len(grid.units)
    t = np.asarray(target_idx, int)
    t = t[t - h >= 0]
    u = np.repeat(np.arange(U), len(t))
    tt = np.tile(t, U)
    return pd.DataFrame({"u": u, "t": tt, "o": tt - h})


def l0_features(grid: Grid, idx: pd.DataFrame, h: int) -> pd.DataFrame:
    u, o, t = idx["u"].to_numpy(), idx["o"].to_numpy(), idx["t"].to_numpy()
    return pd.DataFrame({"sy1_0": _take(grid.y, u, t - WEEKS_PER_YEAR, o)}, index=idx.index)


def l1_features(grid: Grid, idx: pd.DataFrame, h: int) -> pd.DataFrame:
    u, o, t = idx["u"].to_numpy(), idx["o"].to_numpy(), idx["t"].to_numpy()
    cols: dict[str, np.ndarray] = {}
    for k in LAGS:
        cols[f"lag_{k}"] = _take(grid.y, u, o - k, o)
    for j in SEASONAL_YEARS:
        for d in SEASONAL_OFFSETS:
            name = f"sy{j}_" + ({-1: "m1", 0: "0", 1: "p1"}[d])
            cols[name] = _take(grid.y, u, t - WEEKS_PER_YEAR * j + d, o)
    ang = 2 * np.pi * grid.woy[t] / WOY_PERIOD
    cols["woy_sin"] = np.sin(ang)
    cols["woy_cos"] = np.cos(ang)
    X = pd.DataFrame(cols, index=idx.index)
    assert_no_location(X.columns)
    return X


def assert_no_location(columns) -> None:
    bad = [c for c in columns if any(tok in c.lower() for tok in LOCATION_TOKENS)]
    if bad:
        raise AssertionError(f"location-specific columns in a history level: {bad}")
