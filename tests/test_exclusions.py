import pandas as pd
import pytest

from pop.eval import exclusions as X


def _rows():
    return pd.DataFrame({
        "test_year": [2020, 2020, 2021, 2021, 2022],
        "unit_id": ["1", "2", "1", "3", "2"],
        "state": ["SP", "RJ", "SP", "sp", "RJ"],
        "origin_week": pd.to_datetime(["2019-12-29", "2020-01-05", "2021-01-03", "2021-01-03",
                                       "2022-01-02"]),
        "target_week": pd.to_datetime(["2020-01-05", "2020-01-12", "2021-01-10", "2021-01-10",
                                       "2022-01-09"]),
    })


def test_exclude_units(tmp_path):
    f = tmp_path / "u.csv"
    pd.DataFrame({"unit_id": ["2", " 9"]}).to_csv(f, index=False)
    out, n = X.exclude_units(_rows(), f)
    assert n == 2 and set(out.unit_id) == {"1", "3"}


def test_exclude_weeks_country_and_adm1(tmp_path):
    f = tmp_path / "w.csv"
    pd.DataFrame({"country": ["BRAZIL", "brazil", "PERU"],
                  "week_start": ["2020-01-12", "2021-01-10", "2020-01-05"],
                  "scope": ["country", "adm1", "country"],
                  "adm1": ["", "SP", ""]}).to_csv(f, index=False)
    out, n = X.exclude_weeks(_rows(), f, country="BRAZIL")
    assert n == 3  # 2020-01-12 everywhere; 2021-01-10 in SP (case-insensitive) twice
    assert out.target_week.dt.strftime("%Y-%m-%d").tolist() == ["2020-01-05", "2022-01-09"]
    out, n = X.exclude_weeks(_rows(), f, country="COLOMBIA")
    assert n == 0 and len(out) == 5
    bad = tmp_path / "b.csv"
    pd.DataFrame({"country": ["BRAZIL"], "week_start": ["2020-01-12"], "scope": ["state"]}).to_csv(bad, index=False)
    with pytest.raises(ValueError):
        X.exclude_weeks(_rows(), bad, country="BRAZIL")


def test_exclude_late_entry(tmp_path):
    f = tmp_path / "l.csv"
    pd.DataFrame({"unit_id": ["2", "3"], "first_case_year": [2021, 2021]}).to_csv(f, index=False)
    out, n = X.exclude_late_entry(_rows(), f)
    # unit 2 first case 2021: dropped in 2020, kept in 2022; unit 3 kept in 2021
    assert n == 1 and not ((out.unit_id == "2") & (out.test_year == 2020)).any()


def test_exclude_weeks_action_filter(tmp_path):
    f = tmp_path / "w.csv"
    pd.DataFrame({"country": ["BRAZIL", "BRAZIL"], "week_start": ["2020-01-12", "2020-01-05"],
                  "scope": ["country", "country"], "adm1": ["", ""],
                  "action": ["exclude", "sensitivity"]}).to_csv(f, index=False)
    out, n = X.exclude_weeks(_rows(), f, country="BRAZIL", actions=["exclude"])
    assert n == 1 and "2020-01-12" not in out.target_week.dt.strftime("%Y-%m-%d").tolist()
    assert X.exclude_weeks(_rows(), f, country="BRAZIL")[1] == 2
