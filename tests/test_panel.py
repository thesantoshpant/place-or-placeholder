import pandas as pd
import pytest

from pop.data.opendengue import ibge7, ibge_check_digit, normalise_case_definition
from pop.data.panel import build_panel, epi_year


def _row(c, a1, a2, ws, n, s="Admin2", ibge=None, cd="Total"):
    return dict(adm_0_name=c, adm_1_name=a1, adm_2_name=a2, IBGE_code=ibge,
                calendar_start_date=pd.Timestamp(ws), dengue_total=float(n),
                case_definition_standardised=cd, S_res=s, T_res="Week")


@pytest.fixture
def toy():
    rows = [
        _row("PERU", "LIMA", "A", "2020-01-05", 3),
        _row("PERU", "LIMA", "B", "2020-01-19", 1),
        _row("PERU", "LIMA", "A", "2020-01-26", 2),
        _row("PERU", None, None, "2020-01-05", 3, s="Admin0"),
        _row("PERU", None, None, "2020-01-12", 50, s="Admin0"),  # gap week
        _row("BRAZIL", "RJ", "RIO", "2013-12-22", 9, ibge="3304557"),  # before start
        _row("BRAZIL", "RJ", "RIO", "2013-12-29", 4, ibge="3304557"),
        _row("BRAZIL", "SP", "SAO PAULO", "2014-01-12", 5, ibge="355030"),
    ]
    return pd.DataFrame(rows)


def test_zero_fill_and_bounds(toy):
    panel, uni, w, yr = build_panel(toy)
    pe = panel[panel.country == "PERU"]
    assert pe.week_start.min() == pd.Timestamp("2020-01-05")
    assert pe.week_start.max() == pd.Timestamp("2020-01-26")
    assert len(pe) == 2 * 4
    assert pe.observed.sum() == 3 and pe.zero_filled.sum() == 5
    assert pe.loc[pe.zero_filled, "cases"].eq(0).all()
    assert pe.cases.sum() == 6
    assert set(pe.unit_id) == {"PERU|LIMA|A", "PERU|LIMA|B"}
    br = panel[panel.country == "BRAZIL"]
    assert br.week_start.min() == pd.Timestamp("2013-12-29")  # epi week 2014-01
    assert br.cases.sum() == 9 and len(br) == 2 * 3
    assert set(br.unit_id) == {"3304557", "3550308"}
    assert (br.year == 2014).all()


def test_flag_gap(toy):
    panel, *_ = build_panel(toy)
    flagged = panel[panel.flag_gap].week_start.unique()
    assert list(flagged) == [pd.Timestamp("2020-01-12")]


def test_universe(toy):
    _, uni, *_ = build_panel(toy)
    a = uni.set_index("unit_id").loc["PERU|LIMA|A"]
    assert a.n_observed_weeks == 2 and a.total_cases == 5


@pytest.mark.parametrize("code7", ["3304557", "3550308", "5300108", "1100015", "4314902"])
def test_ibge_check_digit(code7):
    assert ibge_check_digit(code7[:6]) == int(code7[6])
    assert ibge7(code7[:6]) == code7 and ibge7(code7) == code7


def test_misc():
    assert list(normalise_case_definition(pd.Series(["confirmed", "Confirmed"]))) == \
        ["Confirmed", "Confirmed"]
    assert epi_year(pd.Series(pd.to_datetime(["2013-12-29", "2014-12-28", "2016-01-03"]))).tolist() == \
        [2014, 2014, 2016]
