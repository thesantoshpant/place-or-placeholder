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
