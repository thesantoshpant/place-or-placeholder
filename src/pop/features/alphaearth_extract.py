"""Production AlphaEarth district means (Brazil, Colombia, Peru, Taiwan): computePixels + local zonal sums.

Method (validated in docs/features/alphaearth_cheap_pilot.md; see
docs/features/alphaearth_extraction.md):

* Grid: GHSL native World Mollweide grid (origin X0, Y0 of GHS_POP, 100 m), so
  population pixels and embedding pixels coincide exactly.
* Population-weighted pass, 100 m: the annual AlphaEarth mosaic is fetched with
  ``ee.data.computePixels`` block by block, **only** for blocks whose
  coverage x population weight is > 0, cropped to the populated sub-rectangle.
  Weight of a pixel for a unit = exactextract coverage fraction x GHSL people
  (negative nodata masked to 0; epochs interpolated linearly in time).
* Unweighted pass, 300 m (exact for unweighted means, per the pilot): every
  block touched by a unit, cropped to the touched cells; weight = coverage.
* Per unit we keep raw sums (sum A*w, sum w, sum A*cov, sum cov); means are
  derived at the end (``sums_to_means``). No renormalisation here.
"""
from __future__ import annotations

import concurrent.futures as cf
import io
import math
import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from pop.features import alphaearth as ae

X0, Y0 = -18041000.0, 9000000.0  # GHS_POP native Mollweide grid origin
RES_W, RES_U = 100.0, 300.0
MOLL = "ESRI:54009"
EPOCHS = [2015, 2020, 2025]
UF = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO", "21": "MA",
      "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA",
      "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS",
      "51": "MT", "52": "GO", "53": "DF"}
WCOLS = [f"w_{b}" for b in ae.BANDS]
UCOLS = [f"u_{b}" for b in ae.BANDS]
I16 = 32767.0


# ---------------------------------------------------------------- pure helpers
def epoch_weights(year: int, mode: str = "interp") -> list[tuple[int, float]]:
    """GHSL epochs and weights for an image year: linear interpolation between
    the bracketing 5-year epochs (clamped to 2015..2025), or the nearest epoch."""
    if mode == "nearest":
        return [(min(EPOCHS, key=lambda e: (abs(e - year), e)), 1.0)]
    y = min(max(year, EPOCHS[0]), EPOCHS[-1])
    e0 = max(e for e in EPOCHS if e <= y)
    if e0 == y:
        return [(e0, 1.0)]
    e1 = e0 + 5
    t = (y - e0) / 5
    return [(e0, 1 - t), (e1, t)]


def grid_window(bounds, res: float, block: int) -> tuple[int, int, int, int]:
    """Global (col0, row0, ncol, nrow) of the ``res`` grid (origin X0, Y0) covering
    Mollweide ``bounds``, snapped outward to multiples of ``block``."""
    minx, miny, maxx, maxy = bounds
    c0 = math.floor((minx - X0) / res / block) * block
    c1 = math.ceil((maxx - X0) / res / block) * block
    r0 = math.floor((Y0 - maxy) / res / block) * block
    r1 = math.ceil((Y0 - miny) / res / block) * block
    return c0, r0, c1 - c0, r1 - r0


def sums_to_means(s: pd.DataFrame) -> pd.DataFrame:
    """Raw per-unit sums -> output frame (weighted/unweighted means, norms).
    ``s`` has unit_id, year, ws_A.. (sum A*w), pop_sum, us_A.. (sum A*cov),
    cov_sum (coverage-weighted count of valid 300 m pixels)."""
    W = s[[f"ws_{b}" for b in ae.BANDS]].to_numpy(float)
    U = s[[f"us_{b}" for b in ae.BANDS]].to_numpy(float)
    p, c = s.pop_sum.to_numpy(float), s.cov_sum.to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        wm = W / p[:, None]
        um = U / c[:, None]
    fb = ~(p > 0)  # no population: fall back to the unweighted mean (flagged)
    wm[fb] = um[fb]
    out = pd.DataFrame({"unit_id": s.unit_id.astype(str).values, "year": s.year.astype(int).values})
    out = pd.concat([out, pd.DataFrame(wm, columns=WCOLS), pd.DataFrame(um, columns=UCOLS)], axis=1)
    out["w_norm"] = np.linalg.norm(wm, axis=1)
    out["u_norm"] = np.linalg.norm(um, axis=1)
    out["w_fallback"] = fb
    out["pop_sum"] = p
    out["area_km2_covered"] = c * (RES_U / 1e3) ** 2
    out["n_pixels"] = c * (RES_U / RES_W) ** 2  # 100 m-equivalent valid pixels
    return out


def budget_state(ledger: pd.DataFrame, month: str, cap_h: float, other_h: dict) -> dict:
    """EECU-h used in ``month`` (YYYY-MM, UTC) = other work + ledger rows finished that month."""
    used = float(other_h.get(month, 0.0))
    if len(ledger):
        m = pd.to_datetime(ledger.finished, utc=True).dt.strftime("%Y-%m") == month
        used += ledger.loc[m, "eecu_s"].sum() / 3600
    return {"month": month, "used_h": used, "cap_h": cap_h, "left_h": cap_h - used}


def accumulate(acc: dict, part: dict) -> None:
    for k, (v, s) in part.items():
        if k in acc:
            acc[k][0] += v
            acc[k][1] += s
        else:
            acc[k] = [v.astype("float64").copy(), float(s)]


def block_coverage(geoms, x0: float, y0: float, nx: int, ny: int, res: float) -> list[tuple[int, np.ndarray, np.ndarray]]:
    """[(i, flat cell ids, coverage)] of geoms[i] on an (ny, nx) grid with top-left (x0, y0)."""
    import geopandas as gpd
    from exactextract import exact_extract
    from exactextract.raster import NumPyRasterSource
    src = NumPyRasterSource(np.zeros((ny, nx), "float32"), xmin=x0, ymin=y0 - ny * res,
                            xmax=x0 + nx * res, ymax=y0, name="z")
    vec = gpd.GeoDataFrame({"i": np.arange(len(geoms))}, geometry=list(geoms), crs=MOLL)
    df = exact_extract(src, vec, ["cell_id", "coverage"], include_cols=["i"], output="pandas")
    cid = df["z_cell_id"] if "z_cell_id" in df else df["cell_id"]
    cov = df["z_coverage"] if "z_coverage" in df else df["coverage"]
    out = []
    for i, c, f in zip(df["i"], cid, cov):
        c, f = np.asarray(c, np.int64), np.asarray(f, float)
        k = f > 0
        if k.any():
            out.append((int(i), c[k], f[k]))
    return out


# ---------------------------------------------------------------- EE access
_WKT: dict = {}


def ghsl_wkt() -> str:
    import ee
    if "w" not in _WKT:
        _WKT["w"] = ee.Image(f"{ae.GHSL_POP}/2020").projection().getInfo()["wkt"]
    return _WKT["w"]


def _profile_hook_call(fn):
    """(result, [profile ids]) of an interactive call (thread-local hooks)."""
    import ee
    ids: list[str] = []
    with ee.data.profiling(ids.append):
        res = fn()
    return res, ids


def resolve_profiles(ids, tries: int = 4) -> tuple[float, bool]:
    """(EECU-s, all_ok) summed over profile ids (profiles can lag a few seconds)."""
    import ee
    from pop.features.ee_utils import profile_eecu
    if not ids:
        return 0.0, False
    get = ee.ApiFunction.lookup("Profile.getProfiles").call
    eecu, ok = 0.0, True
    for pid in ids:
        for k in range(tries):
            try:
                eecu += profile_eecu(get(ids=[pid]).getInfo())
                break
            except Exception:
                if k == tries - 1:
                    ok = False
                else:
                    time.sleep(2 * (k + 1))
    return eecu, ok


def profiled(fn, tries: int = 3):
    """(result, EECU-s, profile_ok) of an interactive call (synchronous profile lookup)."""
    res, ids = _profile_hook_call(fn)
    eecu, ok = resolve_profiles(ids, tries)
    return res, eecu, ok


TRANSIENT = ("429", "too many", "quota", "concurrent", "rate limit", "resource_exhausted", "resource exhausted",
             "500", "502", "503", "504", "unavailable", "deadline", "timed out", "timeout", "connection",
             "reset", "internal error", "backend error", "broken pipe", "ssl", "eof")


class RetryCounter:
    """Thread-safe count of retried attempts (by kind) for the ledger/log."""

    def __init__(self):
        import threading
        self.lock = threading.Lock()
        self.n = 0
        self.n_429 = 0

    def add(self, msg: str) -> None:
        m = msg.lower()
        with self.lock:
            self.n += 1
            if any(k in m for k in ("429", "too many", "quota", "concurrent", "rate limit", "exhausted")):
                self.n_429 += 1


def retry(fn, tries: int = 6, log=print, counter: RetryCounter | None = None, transient_tries: int = 10,
          max_sleep: float = 120.0):
    """Call ``fn`` with exponential backoff (+jitter). Rate-limit / quota / 5xx / network errors get
    ``transient_tries`` attempts, anything else ``tries``. The last exception is re-raised, so a block
    is never dropped silently (the chunk fails instead)."""
    import random
    k = 0
    while True:
        try:
            return fn()
        except Exception as e:
            msg = str(e)
            lim = transient_tries if any(t in msg.lower() for t in TRANSIENT) else tries
            k += 1
            if k >= lim:
                raise
            if counter is not None:
                counter.add(msg)
            log(f"  retry {k}/{lim - 1}: {msg[:160]}")
            time.sleep(min(max_sleep, 2.0 * 2 ** (k - 1)) * (0.75 + 0.5 * random.random()))


def emb_image(year: int, dtype: str = "float32"):
    img = ae.annual_mosaic(year)
    if dtype == "int16":
        return img.multiply(I16).round().unmask(-32768, False).toInt16()
    return img.unmask(-9, False).toFloat()


def _grid_req(img, col0: int, row0: int, nx: int, ny: int, res: float) -> dict:
    return {"expression": img, "fileFormat": "NPY",
            "grid": {"dimensions": {"width": int(nx), "height": int(ny)},
                     "affineTransform": {"scaleX": res, "shearX": 0, "translateX": X0 + int(col0) * res,
                                         "shearY": 0, "scaleY": -res, "translateY": Y0 - int(row0) * res},
                     "crsWkt": ghsl_wkt()}}


def _decode(raw, dtype: str) -> np.ndarray:
    arr = np.load(io.BytesIO(raw)) if isinstance(raw, (bytes, bytearray)) else raw
    a = np.stack([arr[b] for b in ae.BANDS]).astype("float32")
    if dtype == "int16":
        a = np.where(a <= -32768, np.nan, a / I16).astype("float32")
    else:
        a[a <= -1.5] = np.nan
    return a


def fetch_block_ids(img, col0: int, row0: int, nx: int, ny: int, res: float, dtype: str = "float32"):
    """computePixels of ``img`` on the global ``res`` grid window -> ((64, ny, nx) float32 with NaN where
    masked, profile ids, bytes). EECU is resolved later from the ids (off the request path)."""
    import ee
    req = _grid_req(img, col0, row0, nx, ny, res)
    raw, ids = _profile_hook_call(lambda: ee.data.computePixels(req))
    nbytes = len(raw) if isinstance(raw, (bytes, bytearray)) else 0
    return _decode(raw, dtype), ids, nbytes


def fetch_block(img, col0: int, row0: int, nx: int, ny: int, res: float, dtype: str = "float32"):
    """As ``fetch_block_ids`` but resolves the profile now -> (array, EECU-s, bytes, profile_ok)."""
    a, ids, nbytes = fetch_block_ids(img, col0, row0, nx, ny, res, dtype)
    eecu, ok = resolve_profiles(ids, 3)
    return a, eecu, nbytes, ok


def fetch_ghsl(epoch: int, col0: int, row0: int, nx: int, ny: int, tile: int = 2048, workers: int = 6):
    """GHSL people per 100 m pixel for a window of the native grid (getPixels on the
    asset), negative nodata -> 0. Returns (float32 array, EECU-s, profile_ok)."""
    from pop.features.alphaearth_sampling import _get_block
    out = np.zeros((ny, nx), "float32")
    jobs = [(r, c) for r in range(0, ny, tile) for c in range(0, nx, tile)]

    def one(rc):
        r, c = rc
        h, w = min(tile, ny - r), min(tile, nx - c)
        a, e, ok = retry(lambda: profiled(lambda: _get_block(col0 + c, row0 + r, w, h, epoch)))
        return r, c, a, e, ok
    eecu, allok = 0.0, True
    with cf.ThreadPoolExecutor(workers) as ex:
        for r, c, a, e, ok in ex.map(one, jobs):
            out[r:r + a.shape[0], c:c + a.shape[1]] = a
            eecu += e
            allok &= ok or e == 0
    out[~np.isfinite(out) | (out < 0)] = 0
    return out, eecu, allok


# ---------------------------------------------------------------- one chunk (state x year)
@dataclass
class ChunkStats:
    eecu_w: float = 0.0
    eecu_u: float = 0.0
    eecu_ghsl: float = 0.0
    bytes: int = 0
    req_w: int = 0
    req_u: int = 0
    prof_missing: int = 0
    px_w: int = 0
    px_u: int = 0
    est_missing_eecu: float = 0.0
    retries: int = 0
    retries_429: int = 0
    notes: list = field(default_factory=list)


def _clip_geoms(tree, geoms, x0, y0, x1, y1, pad):
    import shapely
    box = shapely.box(x0 - pad, y1 - pad, x1 + pad, y0 + pad)
    idx = tree.query(box, predicate="intersects")
    if len(idx) == 0:
        return idx, []
    return idx, list(shapely.clip_by_rect(np.asarray(geoms)[idx], x0 - pad, y1 - pad, x1 + pad, y0 + pad))


def run_chunk(units_moll, year: int, pop: np.ndarray, pop_win: tuple, block_w: int = 128, block_u: int = 256,
              dtype: str = "float32", workers: int = 12, log=print, rate_w: float = 0.01, rate_u: float = 0.002,
              sub: int = 32, max_sub: int = 3, prof_workers: int = 32, prof_tries: int = 3):
    """Raw sums for one state's units (GeoDataFrame in Mollweide, column unit_id).

    ``pop``: interpolated GHSL people on the global 100 m window ``pop_win`` = (c0, r0, nx, ny)
    that covers the units, snapped to ``block_w``. Returns (sums DataFrame, ChunkStats).

    Concurrency: ``workers`` threads issue computePixels requests (both passes are queued at once);
    EE profiles (EECU) are looked up on a separate small pool, off the request path. Block results are
    accumulated in job order, so the sums are bitwise independent of ``workers``. Any block that still
    fails after retries raises (the chunk fails; nothing is dropped)."""
    import shapely
    geoms = units_moll.geometry.values
    tree = shapely.STRtree(geoms)
    n = len(geoms)
    st = ChunkStats()
    img = emb_image(year, dtype)
    acc_w: dict = {}
    acc_u: dict = {}

    # ---- weighted pass (100 m, populated blocks only)
    pc0, pr0, pnx, pny = pop_win
    jobs_w = []
    for r in range(0, pny, block_w):
        for c in range(0, pnx, block_w):
            if pop[r:r + block_w, c:c + block_w].max() > 0:
                jobs_w.append((r, c))

    def job_w(rc):
        r, c = rc
        P = pop[r:r + block_w, c:c + block_w]
        h, w = P.shape
        x0, y0 = X0 + (pc0 + c) * RES_W, Y0 - (pr0 + r) * RES_W
        idx, cg = _clip_geoms(tree, geoms, x0, y0, x0 + w * RES_W, y0 - h * RES_W, RES_W)
        if not len(idx):
            return None
        parts = []
        for i, cell, f in block_coverage(cg, x0, y0, w, h, RES_W):
            wt = f * P.ravel()[cell]
            k = wt > 0
            if k.any():
                parts.append((int(idx[i]), cell[k], wt[k]))
        if not parts:
            return None
        allc = np.concatenate([p[1] for p in parts])
        rr, cc = np.divmod(allc, w)
        # sparse blocks: fetch only the populated sub-blocks (each request has a ~0.4 EECU-s floor,
        # a full 128 block costs ~1-3 EECU-s, so this pays when <= max_sub sub-blocks are populated)
        sb = np.unique((rr // sub) * 1000 + cc // sub)
        if len(sb) <= max_sub:
            rects = []
            for q in sb:
                k = (rr // sub) * 1000 + cc // sub == q
                rects.append((rr[k].min(), rr[k].max() + 1, cc[k].min(), cc[k].max() + 1))
        else:
            rects = [(rr.min(), rr.max() + 1, cc.min(), cc.max() + 1)]
        A = np.full((64, h, w), np.nan, "float32")
        ids: list = []
        nb = npx = 0
        for ra, rb, ca, cb in rects:
            a, ids1, nb1 = retry(lambda: fetch_block_ids(img, pc0 + c + ca, pr0 + r + ra, cb - ca, rb - ra, RES_W, dtype),
                                 log=log, counter=rc_)
            A[:, ra:rb, ca:cb] = a
            ids.append(ids1); nb += nb1; npx += (rb - ra) * (cb - ca)
        A = A.reshape(64, -1)
        out = {}
        for u, cell, wt in parts:
            v = A[:, cell]
            good = np.isfinite(v[0])
            out[u] = (v[:, good].astype("float64") @ wt[good], float(wt[good].sum()))
        return out, ids, nb, npx

    # ---- unweighted pass (300 m, every touched block)
    bounds = units_moll.total_bounds
    uc0, ur0, unx, uny = grid_window(bounds, RES_U, block_u)
    jobs_u = [(r, c) for r in range(0, uny, block_u) for c in range(0, unx, block_u)]

    def job_u(rc):
        r, c = rc
        x0, y0 = X0 + (uc0 + c) * RES_U, Y0 - (ur0 + r) * RES_U
        x1, y1 = x0 + block_u * RES_U, y0 - block_u * RES_U
        idx, cg = _clip_geoms(tree, geoms, x0, y0, x1, y1, RES_U)
        if not len(idx):
            return None
        parts = [(int(idx[i]), cell, f) for i, cell, f in block_coverage(cg, x0, y0, block_u, block_u, RES_U)]
        if not parts:
            return None
        allc = np.concatenate([p[1] for p in parts])
        rr, cc = np.divmod(allc, block_u)
        ra, rb, ca, cb = rr.min(), rr.max() + 1, cc.min(), cc.max() + 1
        A, ids1, nb = retry(lambda: fetch_block_ids(img, uc0 + c + ca, ur0 + r + ra, cb - ca, rb - ra, RES_U, dtype),
                            log=log, counter=rc_)
        A = A.reshape(64, -1)
        out = {}
        for u, cell, f in parts:
            pr, pcc = np.divmod(cell, block_u)
            v = A[:, (pr - ra) * (cb - ca) + (pcc - ca)]
            good = np.isfinite(v[0])
            out[u] = (v[:, good].astype("float64") @ f[good], float(f[good].sum()))
        return out, [ids1], nb, (rb - ra) * (cb - ca)

    rc_ = RetryCounter()
    t0 = time.time()

    def prof(id_lists):
        """Resolve each request's profile; (EECU-s, all requests profiled)."""
        e, ok = 0.0, True
        for ids in id_lists:
            e1, ok1 = resolve_profiles(ids, prof_tries)
            e += e1
            ok &= ok1
        return e, ok

    ex = cf.ThreadPoolExecutor(workers)
    px = cf.ThreadPoolExecutor(prof_workers)
    pfuts = []
    try:
        futs = {"w100": [ex.submit(job_w, j) for j in jobs_w], "u300": [ex.submit(job_u, j) for j in jobs_u]}
        for name, acc in (("w100", acc_w), ("u300", acc_u)):
            fl = futs[name]
            for done, f in enumerate(fl, 1):
                res = f.result()  # in job order -> deterministic accumulation
                fl[done - 1] = None
                if res is not None:
                    part, ids, nb, npx = res
                    accumulate(acc, part)
                    st.bytes += nb
                    km2 = npx * ((RES_W if name == "w100" else RES_U) / 1e3) ** 2
                    pfuts.append((name, km2, len(ids), px.submit(prof, ids)))
                    if name == "w100":
                        st.req_w += len(ids); st.px_w += npx
                    else:
                        st.req_u += len(ids); st.px_u += npx
                if done % 500 == 0:
                    log(f"  {name} {done}/{len(fl)} blocks, req={st.req_w}+{st.req_u} retries={rc_.n} "
                        f"{time.time() - t0:.0f}s")
            log(f"  {name} pass done: {len(fl)} blocks, req={st.req_w}+{st.req_u} retries={rc_.n} "
                f"{time.time() - t0:.0f}s")
        for name, km2, nreq, pf in pfuts:
            e, ok = pf.result()
            if not ok:
                st.prof_missing += nreq
                e = km2 * (rate_w if name == "w100" else rate_u)
                st.est_missing_eecu += e
            if name == "w100":
                st.eecu_w += e
            else:
                st.eecu_u += e
    except BaseException:
        ex.shutdown(wait=False, cancel_futures=True)
        px.shutdown(wait=False, cancel_futures=True)
        raise
    ex.shutdown()
    px.shutdown()
    log(f"  profiles resolved {time.time() - t0:.0f}s (missing {st.prof_missing})")
    st.retries, st.retries_429 = rc_.n, rc_.n_429
    rows = []
    for u in range(n):
        ws, ps = acc_w.get(u, [np.zeros(64), 0.0])
        us, cs = acc_u.get(u, [np.full(64, np.nan), 0.0])
        rows.append([units_moll.unit_id.iloc[u], year, *ws, ps, *us, cs])
    cols = ["unit_id", "year", *[f"ws_{b}" for b in ae.BANDS], "pop_sum", *[f"us_{b}" for b in ae.BANDS], "cov_sum"]
    return pd.DataFrame(rows, columns=cols), st


# ---------------------------------------------------------------- EE reference (verification)
def ee_reference(geoms_ll, unit_ids, year: int, epochs: list[tuple[int, float]], scale: float = 100):
    """Fresh EE reduceRegions sums at ``scale`` on the GHSL grid (pop interpolated like the
    local run). Returns DataFrame of ws_*, pop_sum, us_*, cnt and EECU-s."""
    import ee
    pop = None
    for e, t in epochs:
        p = ee.Image(f"{ae.GHSL_POP}/{e}").select("population_count")
        p = p.updateMask(p.gte(0)).unmask(0).multiply(t)
        pop = p if pop is None else pop.add(p)
    emb = ae.annual_mosaic(year)
    valid = emb.select(0).mask().gt(0)
    w = pop.updateMask(valid)
    img = ee.Image.cat([emb.multiply(w).rename([f"ws_{b}" for b in ae.BANDS]), w.rename("pop_sum"),
                        emb.rename([f"us_{b}" for b in ae.BANDS]), valid.selfMask().rename("cnt")])
    feats = [ee.Feature(ee.Geometry(g.__geo_interface__, "EPSG:4326", False), {"unit_id": str(u)})
             for u, g in zip(unit_ids, geoms_ll)]
    tr = [scale, 0, X0, 0, -scale, Y0]
    fc = img.reduceRegions(collection=ee.FeatureCollection(feats), reducer=ee.Reducer.sum(),
                           crs=ee.Projection(ghsl_wkt()), crsTransform=tr, tileScale=4) \
        .map(lambda f: f.setGeometry(None))
    info, eecu, ok = profiled(lambda: fc.getInfo())
    return pd.DataFrame([f["properties"] for f in info["features"]]), eecu
