"""TimesFM 2.5 (200M, PyTorch) zero-shot quantile forecaster.

Not a ``QuantileModel`` (base.py): there is no fit step and no feature matrix.
Input is the raw log1p(cases) history of each unit up to and including the
origin week; output is the decile head (0.1..0.9) on the log1p scale, which is
sorted, clipped at >= 0 and returned on both the log1p and the case scale.

Package: ``timesfm==2.0.2`` (the 2.5 API; 3.x ships non-commercial weights).
Checkpoint: ``google/timesfm-2.5-200m-pytorch`` (Apache-2.0).
"""
from __future__ import annotations

import math
import time

import numpy as np
import pandas as pd

REPO_ID = "google/timesfm-2.5-200m-pytorch"
QUANTILES: tuple[float, ...] = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
PATCH = 32
CONTEXT_LIMIT = 16384 - 128  # model context limit minus one output patch


def load_model(max_context: int, batch_size: int = 1024, horizon: int = 4,
               torch_compile: bool = True):
    """Load the checkpoint and compile a decoder for a fixed context/batch size."""
    import timesfm
    import torch

    torch.set_float32_matmul_precision("high")
    max_context = min(CONTEXT_LIMIT, int(math.ceil(max_context / PATCH) * PATCH))
    m = timesfm.TimesFM_2p5_200M_torch.from_pretrained(REPO_ID, torch_compile=torch_compile)
    m.compile(timesfm.ForecastConfig(
        max_context=max_context, max_horizon=max(horizon, 128), normalize_inputs=True,
        per_core_batch_size=batch_size, use_continuous_quantile_head=True,
        force_flip_invariance=True, infer_is_positive=True, fix_quantile_crossing=True,
    ))
    m._pop_batch = batch_size
    return m


def context_window(y_log: np.ndarray, t: int, L: int) -> tuple[np.ndarray, np.ndarray]:
    """Rows of ``y_log[:, :t+1]`` (left-padded/truncated to L) and the pad mask.

    Only columns 0..t are read, so nothing after the origin week can leak in.
    """
    n, _ = y_log.shape
    lo = max(0, t + 1 - L)
    w = t + 1 - lo
    vals = np.zeros((n, L), dtype=np.float32)
    vals[:, L - w:] = y_log[:, lo:t + 1]
    mask = np.ones((n, L), dtype=bool)
    mask[:, L - w:] = False
    return vals, mask


def postprocess(q_log: np.ndarray) -> np.ndarray:
    """Sort deciles along the last axis and clip at 0 (log1p scale)."""
    return np.sort(np.clip(np.nan_to_num(q_log, nan=0.0), 0.0, None), axis=-1)


def forecast_origins(model, y_log: np.ndarray, origin_idx, horizon: int = 4, log=print):
    """Decile forecasts for every unit at every origin column index.

    Returns array (n_origins, n_units, horizon, 9) on the log1p scale (post-processed),
    plus a stats dict (series/s, peak GPU memory).
    """
    import torch

    L = model.forecast_config.max_context
    B = model._pop_batch
    n = y_log.shape[0]
    origin_idx = np.asarray(origin_idx)
    out = np.empty((len(origin_idx), n, horizon, len(QUANTILES)), dtype=np.float32)
    # flatten (origin, unit) jobs, fill fixed-size batches
    jobs_o = np.repeat(np.arange(len(origin_idx)), n)
    jobs_u = np.tile(np.arange(n), len(origin_idx))
    torch.cuda.reset_peak_memory_stats()
    t0, done = time.time(), 0
    cache_t, cache = None, None
    for s in range(0, len(jobs_o), B):
        jo, ju = jobs_o[s:s + B], jobs_u[s:s + B]
        vals = np.zeros((B, L), dtype=np.float32)
        mask = np.ones((B, L), dtype=bool)
        for k in np.unique(jo):
            if cache_t != k:
                cache_t, cache = k, context_window(y_log, int(origin_idx[k]), L)
            sel = jo == k
            idx = np.nonzero(sel)[0]
            vals[idx], mask[idx] = cache[0][ju[sel]], cache[1][ju[sel]]
        with torch.inference_mode():
            _, q = model.compiled_decode(horizon, vals, mask)
        m = len(jo)
        out[jo, ju] = postprocess(q[:m, :horizon, 1:10])
        done += m
        if (s // B) % 200 == 0:
            log(f"  {done}/{len(jobs_o)} series, {done / (time.time() - t0):.0f} series/s")
    el = time.time() - t0
    stats = {"n_series": int(done), "seconds": el, "series_per_s": done / el,
             "peak_gpu_mem_gb": torch.cuda.max_memory_allocated() / 1e9,
             "max_context": int(L), "batch_size": int(B)}
    return out, stats


def to_long(q_log: np.ndarray, unit_ids, origin_weeks, horizon: int = 4) -> pd.DataFrame:
    """Long format; ``value`` is case scale (expm1), ``value_log`` is the log1p decile."""
    no, nu, H, nq = q_log.shape
    o = np.repeat(np.arange(no), nu * H * nq)
    u = np.tile(np.repeat(np.arange(nu), H * nq), no)
    h = np.tile(np.repeat(np.arange(1, H + 1), nq), no * nu)
    ow = pd.to_datetime(pd.Series(origin_weeks)).to_numpy()[o]
    v = q_log.reshape(-1).astype(np.float64)
    return pd.DataFrame({
        "unit_id": pd.Categorical(np.asarray(unit_ids)[u]),
        "origin_week": ow,
        "target_week": ow + (h * 7).astype("timedelta64[D]"),
        "horizon": h.astype(np.int8),
        "quantile": np.tile(np.asarray(QUANTILES), no * nu * H),
        "value": np.expm1(v),
        "value_log": v.astype(np.float32),
    })
