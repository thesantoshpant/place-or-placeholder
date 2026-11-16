import numpy as np
import pandas as pd
import pytest
import shapely

from pop.features import alphaearth as ae
from pop.features import alphaearth_extract as X


def test_epoch_weights():
    assert X.epoch_weights(2020) == [(2020, 1.0)]
    (e0, a), (e1, b) = X.epoch_weights(2023)
    assert (e0, e1) == (2020, 2025) and a == pytest.approx(0.4) and b == pytest.approx(0.6)
    (e0, a), (e1, b) = X.epoch_weights(2017)
    assert (e0, e1) == (2015, 2020) and b == pytest.approx(0.4)
    assert X.epoch_weights(2017, "nearest") == [(2015, 1.0)]
    assert X.epoch_weights(2022, "nearest") == [(2020, 1.0)]
    assert X.epoch_weights(2023, "nearest") == [(2025, 1.0)]


def test_grid_window_aligned():
    b = (-4.5e6 + 37, -2.0e6 + 11, -4.4e6 - 5, -1.9e6 + 3)
    c0, r0, nx, ny = X.grid_window(b, 100, 128)
    assert c0 % 128 == 0 and r0 % 128 == 0 and nx % 128 == 0 and ny % 128 == 0
    assert X.X0 + c0 * 100 <= b[0] and X.X0 + (c0 + nx) * 100 >= b[2]
    assert X.Y0 - r0 * 100 >= b[3] and X.Y0 - (r0 + ny) * 100 <= b[1]
    # 300 m grid shares the origin: every 300 m edge is a 100 m edge
    c3, r3, _, _ = X.grid_window(b, 300, 256)
    assert ((X.X0 + c3 * 300) - X.X0) % 100 == 0


def _sums(ws, p, us, c):
    d = {"unit_id": ["1", "2"], "year": [2023, 2023], "pop_sum": p, "cov_sum": c}
    for k, bnd in enumerate(ae.BANDS):
        d[f"ws_{bnd}"] = ws[:, k]
        d[f"us_{bnd}"] = us[:, k]
    return pd.DataFrame(d)


def test_sums_to_means_and_fallback():
    rng = np.random.default_rng(0)
    ws, us = rng.normal(size=(2, 64)), rng.normal(size=(2, 64))
    m = X.sums_to_means(_sums(ws, np.array([4.0, 0.0]), us, np.array([2.0, 3.0])))
    np.testing.assert_allclose(m.loc[0, X.WCOLS].to_numpy(float), ws[0] / 4)
    np.testing.assert_allclose(m.loc[1, X.WCOLS].to_numpy(float), us[1] / 3)  # no pop -> unweighted
    assert m.w_fallback.tolist() == [False, True]
    assert m.area_km2_covered[1] == pytest.approx(3 * 0.09) and m.n_pixels[1] == pytest.approx(27)
    assert m.w_norm[0] == pytest.approx(np.linalg.norm(ws[0] / 4))


def test_budget_state():
    L = pd.DataFrame({"finished": ["2026-11-20T00:00:00+00:00", "2026-12-02T00:00:00+00:00"],
                      "eecu_s": [36000.0, 7200.0]})
    b = X.budget_state(L, "2026-11", 100, {"2026-11": 25})
    assert b["used_h"] == pytest.approx(35.0)
    assert X.budget_state(L, "2026-12", 100, {"2026-11": 25})["used_h"] == pytest.approx(2.0)


def test_accumulate():
    acc = {}
    X.accumulate(acc, {0: (np.ones(64), 2.0)})
    X.accumulate(acc, {0: (np.ones(64), 1.0), 1: (np.zeros(64), 5.0)})
    assert acc[0][1] == 3.0 and acc[0][0][0] == 2.0 and acc[1][1] == 5.0


def test_block_coverage_exact_area():
    # square of 250 x 250 m offset by 30 m on a 100 m grid: coverage sums to 6.25 cells
    x0, y0 = 1000.0, 2000.0
    g = shapely.box(x0 + 30, y0 - 280, x0 + 280, y0 - 30)
    cov = X.block_coverage([g], x0, y0, 5, 5, 100.0)
    assert len(cov) == 1 and cov[0][2].sum() == pytest.approx(6.25)
    # cell ids are row-major from the top-left
    i, cells, f = cov[0]
    assert cells.min() == 0 and f[cells == 0][0] == pytest.approx(0.49)


def test_retry_backoff_counts_and_raises(monkeypatch):
    monkeypatch.setattr(X.time, "sleep", lambda s: None)
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("429 Too Many Requests: too many concurrent aggregations")
        return "ok"
    rc = X.RetryCounter()
    assert X.retry(flaky, log=lambda m: None, counter=rc) == "ok"
    assert rc.n == 2 and rc.n_429 == 2

    def bad():
        raise RuntimeError("503 Service Unavailable")
    rc = X.RetryCounter()
    with pytest.raises(RuntimeError):
        X.retry(bad, log=lambda m: None, counter=rc, transient_tries=4)
    assert rc.n == 3  # never dropped silently: last failure re-raised
