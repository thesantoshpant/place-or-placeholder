import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pop.features import climate as C

OUT = Path("data/interim/climate/climate_weekly_brazil_v1.parquet")
PANEL = Path("data/processed/panel_weekly_v1.parquet")


def test_rh_magnus_known_values():
    assert C.rh_magnus(20.0, 20.0) == pytest.approx(100.0)
    # T=25, Td=15 -> ~53.8 % (Alduchov-Eskridge coefficients)
    es = lambda t: 6.1094 * math.exp(17.625 * t / (243.04 + t))
    assert C.rh_magnus(25.0, 15.0) == pytest.approx(100 * es(15) / es(25), rel=1e-9)
    assert C.rh_magnus(25.0, 15.0) == pytest.approx(53.8, abs=0.2)
    assert C.rh_magnus(10.0, 12.0) == 100.0  # supersaturation capped
    assert np.all(np.diff(C.rh_magnus(30.0, np.array([0.0, 10.0, 20.0, 30.0]))) > 0)


def test_nearest_epoch():
    assert [C.nearest_epoch(y) for y in (2013, 2017, 2018, 2022, 2023, 2024)] == [2015, 2015, 2020, 2020, 2025, 2025]


def test_snap_bbox_aligned_to_era5_grid():
    g = C.snap_bbox((-74.1, -33.8, -28.8, 5.3))
    for v in (g["x0"] - C.X0, C.Y0 - g["y0"]):
        assert abs(v / C.RES - round(v / C.RES)) < 1e-6
    assert g["x0"] <= -74.1 and g["y0"] >= 5.3


@pytest.mark.skipif(not OUT.exists() or not PANEL.exists(), reason="climate output not built")
def test_brazil_weeks_align_with_panel():
    clim = pd.read_parquet(OUT, columns=["unit_id", "week_start"])
    panel = pd.read_parquet(PANEL, columns=["unit_id", "country", "week_start"], filters=[("country", "==", "BRAZIL")])
    ws = pd.to_datetime(clim.week_start)
    assert (ws.dt.dayofweek == 6).all()  # Sunday starts
    p = set(zip(panel.unit_id.astype(str), pd.to_datetime(panel.week_start)))
    c = set(zip(clim.unit_id.astype(str), ws))
    assert p <= c
    assert not clim.duplicated().any()
