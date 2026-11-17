"""C4 / C4s on the real unit points (fix 2026-11-16b): units without geometry (NaN lat/lon) must
not turn every field of their country into NaN."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pop.features import controls as C

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(not C.BOUNDARIES.exists(), reason="boundaries not built")


@pytest.fixture(scope="module")
def pts():
    return C.load_unit_points()


def _fitted(c):
    if c == "BRAZIL":
        import yaml
        y = yaml.safe_load((ROOT / "configs/brazil_s1_controls_2019.yaml").read_text())
        return float(y["features"]["control_kw"]["C4"]["range_km"])
    return float(json.loads((ROOT / f"runs/{c.lower()}_s1/c4_range_km.json").read_text())["range_km"])


@pytest.mark.parametrize("country", ["COLOMBIA", "TAIWAN"])
def test_c4_finite_for_units_with_geometry(pts, country):
    p = pts[pts.country == country]
    assert (~np.isfinite(p.lat)).sum() >= 1  # the case that broke C4
    ok = set(p.unit_id[np.isfinite(p.lat) & np.isfinite(p.lon)])
    D = C.c4s_range(country)
    for ctrl, r in (("C4", _fitted(country)), ("C4s", min(D, _fitted(country)))):
        F = C.make_controls(ctrl, pts, set(p.unit_id), set(), 2019, seed=0, range_km=r).set_index("unit_id")
        X = F.to_numpy()
        fin = F.index.isin(ok)
        assert np.isfinite(X[fin]).all(), (ctrl, country)
        assert np.isnan(X[~fin]).all()
        assert np.allclose(X[fin].std(0), 1) and np.allclose(X[fin].mean(0), 0, atol=1e-9)


def test_c4_differs_from_c4s_colombia(pts):
    p = pts[pts.country == "COLOMBIA"]
    a = C.make_controls("C4", pts, set(p.unit_id), set(), 2019, seed=1, range_km=_fitted("COLOMBIA"))
    r, is_c4 = C.c4s_range_rule(C.c4s_range("COLOMBIA"), _fitted("COLOMBIA"))
    assert not is_c4 and r == 130.0
    b = C.make_controls("C4s", pts, set(p.unit_id), set(), 2019, seed=1, range_km=r)
    A, B = a.drop(columns="unit_id").to_numpy(), b.drop(columns="unit_id").to_numpy()
    fin = np.isfinite(A).all(1)
    assert fin.sum() == len(p) - 1
    assert not np.allclose(A[fin], B[fin])


@pytest.mark.parametrize("country", ["PERU", "TAIWAN"])
def test_c4s_rule_drops_c4s_where_fitted_is_shorter(country):
    r, is_c4 = C.c4s_range_rule(C.c4s_range(country), _fitted(country))
    assert is_c4 and r == _fitted(country)


def test_c4_brazil_peru_unchanged_by_fix(pts):
    """All coordinates finite -> same draw as the pre-fix code path (gaussian_random_fields on all)."""
    p = pts[pts.country == "PERU"]
    F = C.make_controls("C4", pts, set(p.unit_id), set(), 2019, seed=2, range_km=148.0)
    g = C._subset(pts, set(p.unit_id))
    G = C.gaussian_random_fields(*C._latlon(g), 148.0, 64, C._rng(2, "C4", "PERU"))
    G = (G - G.mean(0)) / G.std(0)
    assert np.array_equal(F.drop(columns="unit_id").to_numpy(), G)


def test_c4_s5_pooled(pts):
    """S5 pools the four countries; fields are per country and finite for every unit with
    geometry, also for the Colombia / Taiwan blocks."""
    rng = {c: _fitted(c) for c in ("BRAZIL", "COLOMBIA", "PERU", "TAIWAN")}
    allu = set(pts.unit_id)
    F = C.make_controls("C4", pts, allu - set(pts.unit_id[pts.country == "PERU"]),
                        set(pts.unit_id[pts.country == "PERU"]), 2019, seed=0, range_km=rng)
    F = F.merge(pts[["unit_id", "country", "lat"]], on="unit_id")
    X = F.filter(like="c4_f").to_numpy()
    fin = np.isfinite(F.lat.to_numpy())
    assert np.isfinite(X[fin]).all() and np.isnan(X[~fin]).all()
    for c, g in F.groupby("country"):
        assert np.isfinite(g.filter(like="c4_f").to_numpy()).mean() > 0.99, c
