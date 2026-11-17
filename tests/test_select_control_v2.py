"""C* selection rule v2 (scripts/run/select_control.py)."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("select_control", ROOT / "scripts/run/select_control.py")
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


def tab(rows):
    return pd.DataFrame(rows, columns=["k", "wis_log", "n_seeds", "wis_log_sd_seeds"]).set_index("k")


def test_tie_set_and_priority():
    t = tab([("C1", 0.1003, 1, np.nan), ("C2", 0.1010, 1, np.nan), ("C3", 0.1000, 3, 0.0002),
             ("C4", 0.1001, 3, 0.0002), ("C5", 0.1100, 1, np.nan)])
    cands = ["C1", "C2", "C3", "C4", "C5"]
    k, info = S.select(t, cands, S.PRIORITY_HIST, {})
    # sigma = 2e-4; SE(best C3) = 1.15e-4; SE(C1) = 2e-4 -> thr(C1) = 2*sqrt(1.33e-8+4e-8) = 4.6e-4
    assert info["best_by_score"] == "C3"
    assert info["tie_set"] == ["C1", "C3", "C4"]  # C2 (+1e-3) and C5 out
    assert k == "C1" and not info["uninformative"]
    assert abs(info["sigma_seed"] - 2e-4) < 1e-12


def test_clear_winner_and_exclusion():
    t = tab([("C1", 0.12, 1, np.nan), ("C3", 0.10, 3, 0.0001), ("C4", 0.10, 3, 0.0001)])
    k, info = S.select(t, ["C1", "C3", "C4"], S.PRIORITY_HIST, {"C3": "degenerate"})
    assert k == "C4" and info["tie_set"] == ["C4"]


def test_uninformative_cell_uses_priority():
    t = tab([("C1", 0.0034, 1, np.nan), ("C2", 0.0034, 1, np.nan), ("C3", 0.0034, 3, 0.0),
             ("C4", 0.0034, 3, 0.0), ("C5", 0.0030, 1, np.nan)])
    k, info = S.select(t, ["C1", "C2", "C3", "C4", "C5"], S.PRIORITY_HIST, {"C1": "x"})
    assert info["uninformative"] and k == "C3"


def test_protocol_lists_and_c4s_rule():
    assert S.protocol("S5", False)[0] == ["C2", "C3", "C4", "C4s", "C5"]
    assert S.protocol("S2", False)[0] == ["C1", "C2", "C3", "C4", "C4s", "C5"]
    assert S.protocol("S1", True)[0] == ["C2", "C3", "C4", "C4s", "C6"]
    assert "C6" not in S.protocol("S2", True)[0]
    assert S.c4s_is_c4({"C4": {"range_km": 27.1}, "C4s": {"range_km": 170.0}}, "TAIWAN")
    assert S.c4s_is_c4({"C4": {"range_km": 27.1}, "C4s": {"range_km": 27.1}}, "TAIWAN")
    assert not S.c4s_is_c4({"C4": {"range_km": 705.0}, "C4s": {"range_km": 130.0}}, "COLOMBIA")
    s5 = {"C4": {"range_km": {"PERU": 148.0, "BRAZIL": 8483.0}},
          "C4s": {"range_km": {"PERU": 148.0, "BRAZIL": 225.0}}}
    assert S.c4s_is_c4(s5, "PERU") and not S.c4s_is_c4(s5, "BRAZIL")


def test_forecasts_identical(tmp_path):
    c = tmp_path / "chunks"
    c.mkdir()
    base = pd.DataFrame({"unit_id": ["a", "b"], "origin_week": [1, 1], "target_week": [2, 2],
                         "horizon": [1, 1], "fold": ["", ""], "quantile": [0.5, 0.5], "value": [1.0, 2.0]})
    base.to_parquet(c / "lgbm__L3__s0__2019__h1.forecasts.parquet")
    base.iloc[::-1].to_parquet(c / "lgbm__L3+C4__s0__2019__h1.forecasts.parquet")
    base.assign(value=[1.0, 2.5]).to_parquet(c / "lgbm__L3+C4s__s0__2019__h1.forecasts.parquet")
    assert S.forecasts_identical("C4", "L3", [tmp_path])
    assert S.forecasts_identical("C4s", "L3", [tmp_path]) is None
