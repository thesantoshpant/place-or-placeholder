from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import scipy.sparse as sp

from pop.features import population as P
from pop.features import remote_sensing as R

MON = Path("data/interim/remote_sensing/rs_monthly_brazil_v1.parquet")


def test_epochs_for_years():
    assert P.epochs_for_years(2013, 2024) == [2010, 2015, 2020, 2025]
    assert P.epochs_for_years(2015, 2020) == [2015, 2020]
    assert P.epochs_for_years(1997, 2024) == [1995, 2000, 2005, 2010, 2015, 2020, 2025]


def test_interp_linear_loglinear_and_clamp():
    v = np.array([[100.0, 200.0, 200.0], [0.0, 10.0, 20.0]])
    ep = [2010, 2015, 2020]
    lin = P.interp_years(v, ep, [2010, 2012, 2015, 2018, 2020, 2008, 2022], "linear")
    assert lin[0].tolist() == pytest.approx([100, 140, 200, 200, 200, 100, 200])
    lg = P.interp_years(v, ep, [2010, 2012, 2015, 2017], "loglinear")
    assert lg[0, 1] == pytest.approx(100 * 2 ** 0.4)  # constant growth rate
    assert lg[0, [0, 2]].tolist() == pytest.approx([100, 200])  # epochs reproduced exactly
    assert lg[1, 1] == pytest.approx(4.0)  # zero endpoint -> linear fallback
    assert lg[1, 3] == pytest.approx(10 * 2 ** 0.4)


def test_composite_month_uses_last_day():
    s = pd.to_datetime(["2023-01-01", "2023-01-17", "2023-12-19", "2023-03-22", "2023-12-27", "2024-02-26"])
    m13 = R.composite_month(s[:4], R.MOD13).astype(str).tolist()
    assert m13 == ["2023-01", "2023-02", "2024-01", "2023-04"]  # 16-day: start + 15 d
    m11 = R.composite_month(s[3:], R.MOD11).astype(str).tolist()
    assert m11 == ["2023-03", "2023-12", "2024-03"]  # 8-day: start + 7 d, year-end composite stays in Dec
    # leakage guard: a composite's last day (8-day ones capped at 31 Dec) never falls after its month
    st = pd.Series(pd.date_range("2020-01-01", "2021-12-31", freq="D"))
    for prod, days in R.COMPOSITE_DAYS.items():
        last = st + pd.Timedelta(days=days - 1)
        if prod == R.MOD11:
            last = last.where(last.dt.year == st.dt.year, pd.to_datetime(st.dt.year.astype(str) + "-12-31"))
        assert (last <= R.composite_month(st, prod).dt.end_time).all()
        assert (st.dt.to_period("M") <= R.composite_month(st, prod)).all()


def test_zonal_mean_renormalises_over_valid_cells():
    W = sp.csr_matrix(np.array([[1.0, 3.0, 0.0], [0.0, 0.0, 2.0]]))
    X = np.array([[1.0, 5.0, np.nan], [np.nan, 5.0, 7.0]])
    out = R.zonal_mean(W, X)
    assert out[0].tolist() == pytest.approx([4.0, np.nan], nan_ok=True)
    assert out[1].tolist() == pytest.approx([5.0, 7.0])


def test_fill_prev_year_only_backward():
    df = pd.DataFrame({"unit_id": ["a"] * 3, "year": [2020, 2021, 2022], "month": 7, "x": [1.0, np.nan, np.nan]})
    out, n = R.fill_prev_year(df, ["x"])
    assert out.x.tolist()[:2] == [1.0, 1.0] and np.isnan(out.x.iloc[2]) and n["x"] == 1


@pytest.mark.skipif(not MON.exists(), reason="brazil output not built")
def test_monthly_output_grid_complete():
    df = pd.read_parquet(MON, columns=["unit_id", "year", "month"])
    assert df.month.between(1, 12).all()
    n = df.groupby(["unit_id", "year"]).month.nunique()
    assert (n == 12).all() and not df.duplicated().any()


def test_monthly_band_names_order():
    n = R.monthly_band_names()
    assert len(n) == 36 and n[:4] == ["ndvi_01", "lst_day_01", "lst_night_01", "ndvi_02"] and n[-1] == "lst_night_12"


def test_monthly_frame_maps_bands_and_rejects_short_stacks():
    # regression (Taiwan 2000 crash): MODIS starts Feb 2000, so Jan/Feb had no composites and the
    # image had 32 bands; positional band indexing then overflowed (or would silently shift months)
    ids = np.array(["a", "b"])
    vp = np.arange(72, dtype=float).reshape(36, 2)
    df = R.monthly_frame(ids, 2000, vp, -vp)
    assert len(df) == 24 and set(df.month) == set(range(1, 13))
    r = df[(df.unit_id == "b") & (df.month == 3)].iloc[0]
    b = R.monthly_band_names().index("lst_day_03")
    assert r.lst_day_pw == vp[b, 1] and r.lst_day_aw == -vp[b, 1]
    with pytest.raises(ValueError):
        R.monthly_frame(ids, 2000, vp[:32], vp[:32])


def _ee_ok():
    try:
        from pop.features import ee_utils as U
        U.init()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _ee_ok(), reason="Earth Engine not available")
def test_monthly_image_2000_keeps_all_bands():
    """Months without MODIS composites become fully masked bands, so band order is fixed."""
    assert R.monthly_image(2000).bandNames().getInfo() == R.monthly_band_names()


@pytest.mark.parametrize("country", ["brazil", "colombia", "peru", "taiwan"])
def test_monthly_output_grid_complete_all(country):
    f = Path(f"data/interim/remote_sensing/rs_monthly_{country}_v1.parquet")
    if not f.exists():
        pytest.skip(f"{country} output not built")
    df = pd.read_parquet(f, columns=["unit_id", "year", "month"])
    n = df.groupby(["unit_id", "year"]).month.nunique()
    assert (n == 12).all() and not df.duplicated().any()
    assert df.groupby("unit_id").year.nunique().nunique() == 1  # same years for every unit


def test_lst_qc_rule_v2():
    q = np.arange(256)
    ok = R.lst_qc_ok_np(q)
    mand, err = q & 3, (q >> 6) & 3
    assert ok[mand == 0].all()  # good quality always kept
    assert not ok[mand >= 2].any()  # not produced (cloud / other) never kept
    assert R.LST_MAX_ERR_FLAG == 0
    assert (ok[mand == 1] == (err[mand == 1] == 0)).all()  # other quality only if LST error <= 1 K
    assert ok.sum() == 64 + 16
    assert R.lst_qc_ok_np([0b00000000, 0b00000001, 0b01000001, 0b01000000, 0b00000010]).tolist() == \
        [True, True, False, True, False]  # 0b01000001 = other quality, error <= 2 K (Colombia cold pixels)
    loose = R.lst_qc_ok_np(q, max_err_flag=1)
    assert (loose[mand == 1] == (err[mand == 1] <= 1)).all() and loose.sum() == 64 + 32


def test_monthly_frame_lst_only_vars():
    ids = np.array(["a", "b"])
    vp = np.arange(48, dtype=float).reshape(24, 2)
    df = R.monthly_frame(ids, 2020, vp, -vp, R.LST_VARS)
    names = R.monthly_band_names(vars_=R.LST_VARS)
    r = df[(df.unit_id == "a") & (df.month == 5)].iloc[0]
    assert r.lst_night_pw == vp[names.index("lst_night_05"), 0] and "ndvi_pw" not in df
    with pytest.raises(ValueError):
        R.monthly_frame(ids, 2020, vp, vp)  # 24 bands are not 12 x 3 vars


@pytest.mark.skipif(not _ee_ok(), reason="Earth Engine not available")
def test_lst_qc_rule_ee_matches_numpy():
    import ee
    q = list(range(256))
    img = R.lst_qc_ok(ee.Image.constant(q))
    names = img.bandNames().getInfo()
    got = img.reduceRegion(ee.Reducer.first(), ee.Geometry.Point([0, 0]), 1000).getInfo()
    assert [bool(got[n]) for n in names] == R.lst_qc_ok_np(q).tolist()
    assert R.lst_image(2000).bandNames().getInfo() == R.monthly_band_names(vars_=R.LST_VARS)


@pytest.mark.parametrize("country", ["brazil", "colombia", "peru", "taiwan"])
def test_v2_matches_v1_except_lst(country):
    f1 = Path(f"data/interim/remote_sensing/rs_monthly_{country}_v1.parquet")
    f2 = f1.with_name(f"rs_monthly_{country}_v2.parquet")
    if not f2.exists():
        pytest.skip(f"{country} v2 not built")
    a, b = pd.read_parquet(f1), pd.read_parquet(f2)
    assert list(a.columns) == list(b.columns) and (a.dtypes == b.dtypes).all() and len(a) == len(b)
    for c in a.columns:
        if c.startswith("lst_"):
            continue
        if pd.api.types.is_numeric_dtype(a[c]):
            assert a[c].to_numpy().tobytes() == b[c].to_numpy().tobytes(), c  # bit-identical (NaN too)
        else:
            assert a[c].equals(b[c]), c
    for c in [c for c in a.columns if c.startswith("lst_")]:
        assert b[c].dropna().between(-60, 80).all()
