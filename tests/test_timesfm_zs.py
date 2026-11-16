"""TimesFM 2.5 zero-shot sanity checks (skipped without timesfm or a GPU)."""
import numpy as np
import pytest

from pop.models import timesfm_zs as tz


def test_context_window_never_reads_future():
    y = np.arange(20, dtype=np.float32)[None, :].repeat(2, 0)
    v, m = tz.context_window(y, t=9, L=16)
    assert v.max() == 9 and (~m).sum(1).tolist() == [10, 10]
    v, m = tz.context_window(y, t=19, L=8)
    assert v[0].tolist() == list(range(12, 20)) and not m.any()


def test_postprocess_sorted_nonnegative():
    q = np.array([[0.5, -1.0, 0.2, np.nan, 3, 2, 1, 0, 4]])
    p = tz.postprocess(q)
    assert np.all(np.diff(p, axis=-1) >= 0) and p.min() >= 0


def test_seasonal_series_sensible():
    torch = pytest.importorskip("torch")
    pytest.importorskip("timesfm")
    if not torch.cuda.is_available():
        pytest.skip("no GPU")
    rng = np.random.default_rng(0)
    T = 52 * 8
    t = np.arange(T)
    lam = np.exp(2.5 + 1.5 * np.sin(2 * np.pi * t / 52))
    y = np.log1p(rng.poisson(lam)).astype(np.float32)[None, :]
    # poison the future: values after the origin must not affect the forecast
    origin = T - 30
    y_bad = y.copy()
    y_bad[:, origin + 1:] = 1e3
    model = tz.load_model(max_context=T, batch_size=8, torch_compile=False)
    q, _ = tz.forecast_origins(model, y, [origin], horizon=4, log=lambda *_: None)
    q2, _ = tz.forecast_origins(model, y_bad, [origin], horizon=4, log=lambda *_: None)
    np.testing.assert_allclose(q, q2, atol=1e-5)
    q = q[0, 0]  # (4, 9)
    assert np.all(np.diff(q, axis=-1) >= 0) and q.min() >= 0
    truth = np.log1p(lam[origin + 1: origin + 5])
    assert np.all(np.abs(q[:, 4] - truth) < 0.75)
    assert np.all(q[:, 8] - q[:, 0] > 0.05) and np.all(q[:, 8] - q[:, 0] < 3)
