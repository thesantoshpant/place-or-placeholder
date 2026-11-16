"""Cheaper estimators of AlphaEarth district means (pilot; see
docs/features/alphaearth_cheap_pilot.md).

1. Point sampling: draw N points per district with probability proportional to
   GHSL population (or uniformly over area), take the plain mean of the 10 m
   embedding at those points. Points are generated locally from the GHSL 100 m
   raster (native Mollweide grid, fetched with ``ee.data.getPixels``, which
   reads the asset directly), jittered uniformly inside the 100 m pixel.
   On the EE side each district is passed as one MultiPoint feature, exploded
   server-side, sampled at 10 m and averaged with a grouped reducer, so the
   batch output is one row per district.
2. Coarse reduction: embeddings at a coarse scale (pyramid read, or
   ``reduceResolution(mean)`` from 10 m), population aggregated by sum
   (``reduceResolution`` of density on the native GHSL grid, x pixelArea).
"""
from __future__ import annotations

import io

import ee
import numpy as np
import pandas as pd
from pyproj import Transformer
from rasterio import features as rfeatures
from rasterio.transform import Affine
from shapely.geometry import mapping
from shapely.ops import transform as shp_transform

from pop.features import alphaearth as ae

MOLL = "ESRI:54009"
X0, Y0, RES = -18041000.0, 9000000.0, 100.0  # GHS_POP 2020 native grid
_to_moll = Transformer.from_crs("EPSG:4326", MOLL, always_xy=True)
_to_ll = Transformer.from_crs(MOLL, "EPSG:4326", always_xy=True)


# ---------------------------------------------------------------- local GHSL raster
_WKT: dict = {}


def _ghsl_wkt(epoch: int) -> str:
    if epoch not in _WKT:
        _WKT[epoch] = ee.Image(f"{ae.GHSL_POP}/{epoch}").projection().getInfo()["wkt"]
    return _WKT[epoch]


def _get_block(c0: int, r0: int, w: int, h: int, epoch: int) -> np.ndarray:
    req = {
        "assetId": f"{ae.GHSL_POP}/{epoch}",
        "fileFormat": "NUMPY_NDARRAY",
        "bandIds": ["population_count"],
        "grid": {"dimensions": {"width": w, "height": h},
                 "affineTransform": {"scaleX": RES, "shearX": 0, "translateX": X0 + c0 * RES,
                                     "shearY": 0, "scaleY": -RES, "translateY": Y0 - r0 * RES},
                 "crsWkt": _ghsl_wkt(epoch)},
    }
    a = ee.data.getPixels(req)
    return np.asarray(a["population_count"], dtype="float64")


def pop_raster(geom_ll, epoch: int = 2020, block: int = 2048):
    """GHSL people per 100 m pixel inside ``geom_ll`` (pixel-centre rule).

    Returns (pop, mask, col0, row0) on the native Mollweide grid. Negative
    nodata is set to 0."""
    gm = shp_transform(lambda x, y: _to_moll.transform(x, y), geom_ll)
    minx, miny, maxx, maxy = gm.bounds
    c0, c1 = int(np.floor((minx - X0) / RES)), int(np.ceil((maxx - X0) / RES))
    r0, r1 = int(np.floor((Y0 - maxy) / RES)), int(np.ceil((Y0 - miny) / RES))
    W, H = c1 - c0, r1 - r0
    pop = np.zeros((H, W))
    for rr in range(0, H, block):
        for cc in range(0, W, block):
            h, w = min(block, H - rr), min(block, W - cc)
            pop[rr:rr + h, cc:cc + w] = _get_block(c0 + cc, r0 + rr, w, h, epoch)
    pop[~np.isfinite(pop) | (pop < 0)] = 0
    tr = Affine(RES, 0, X0 + c0 * RES, 0, -RES, Y0 - r0 * RES)
    mask = rfeatures.geometry_mask([mapping(gm)], (H, W), tr, invert=True, all_touched=False)
    if not mask.any():  # tiny unit: keep touched pixels
        mask = rfeatures.geometry_mask([mapping(gm)], (H, W), tr, invert=True, all_touched=True)
    return np.where(mask, pop, 0.0), mask, c0, r0


def draw_points(pop: np.ndarray, mask: np.ndarray, c0: int, r0: int, n: int, how: str = "pop",
                rng: np.random.Generator | None = None) -> np.ndarray:
    """n (lon, lat) points: ``how`` = 'pop' (iid, p ~ pop), 'pop_sys'
    (systematic PPS along a serpentine pixel order: spatially spread), or
    'area' (uniform over the unit's pixels). Jittered within the 100 m pixel."""
    rng = rng or np.random.default_rng(0)
    if how == "area" or pop.sum() <= 0:
        w = mask.astype(float)
    else:
        w = pop
    H, W = w.shape
    if how == "pop_sys":
        order = np.arange(H * W).reshape(H, W)
        order[1::2] = order[1::2, ::-1]  # serpentine rows
        order = order.ravel()
        cw = np.cumsum(w.ravel()[order])
        u = (rng.random() + np.arange(n)) / n * cw[-1]
        flat = order[np.searchsorted(cw, u, side="right").clip(0, H * W - 1)]
    else:
        flat_all = np.flatnonzero(w.ravel() > 0)
        p = w.ravel()[flat_all]
        flat = rng.choice(flat_all, size=n, replace=True, p=p / p.sum())
    r, c = np.divmod(flat, W)
    x = X0 + (c0 + c + rng.random(n)) * RES
    y = Y0 - (r0 + r + rng.random(n)) * RES
    lon, lat = _to_ll.transform(x, y)
    return np.column_stack([lon, lat])


def footprint_geometry(geom_ll, block: int = 10, epoch: int = 2020):
    """Unit polygon intersected with the union of populated (pop > 0) blocks of
    ``block`` x 100 m. A pop-weighted mean over this geometry equals the
    full-area one (weights are zero elsewhere) while touching far less area."""
    from shapely.geometry import shape
    from shapely.ops import unary_union
    pop, mask, c0, r0 = pop_raster(geom_ll, epoch)
    H, W = (np.array(pop.shape) // block + 1) * block
    P = np.zeros((H, W)); P[:pop.shape[0], :pop.shape[1]] = pop
    occ = (P.reshape(H // block, block, W // block, block).sum((1, 3)) > 0).astype("uint8")
    tr = Affine(RES * block, 0, X0 + c0 * RES, 0, -RES * block, Y0 - r0 * RES)
    polys = [shape(g) for g, v in rfeatures.shapes(occ, mask=occ > 0, transform=tr) if v == 1]
    fp = shp_transform(lambda x, y: _to_ll.transform(x, y), unary_union(polys))
    return fp.intersection(geom_ll), float(occ.sum() * (block * RES / 1e3) ** 2)


# ---------------------------------------------------------------- EE point means
def points_fc(points: dict[str, np.ndarray]) -> ee.FeatureCollection:
    """{unit_id: (n,2) lon/lat} -> FC of one MultiPoint feature per unit."""
    feats = [ee.Feature(ee.Geometry.MultiPoint(np.round(xy, 6).tolist()), {"unit_id": uid})
             for uid, xy in points.items()]
    return ee.FeatureCollection(feats)


def point_means(mp_fc: ee.FeatureCollection, year: int, scale: float = 10) -> ee.FeatureCollection:
    """Per-unit plain mean (and count) of the embedding at the given points."""
    def explode(f):
        uid = f.get("unit_id")
        return ee.FeatureCollection(f.geometry().coordinates().map(
            lambda c: ee.Feature(ee.Geometry.Point(c), {"unit_id": uid})))
    pts = mp_fc.map(explode).flatten()
    emb = ae.annual_mosaic(year)
    s = emb.sampleRegions(collection=pts, properties=["unit_id"], scale=scale, geometries=False)
    red = ee.Reducer.mean().forEach(ae.BANDS)
    grp = s.reduceColumns(red.group(groupField=64, groupName="unit_id"), ae.BANDS + ["unit_id"])
    def to_feat(g):
        g = ee.Dictionary(g)
        return ee.Feature(ee.Geometry.Point([0, 0]), g.remove(["unit_id"])).set("unit_id", g.get("unit_id"))
    return ee.FeatureCollection(ee.List(grp.get("groups")).map(to_feat)).set("year", year)


# ---------------------------------------------------------------- coarse reduction
def coarse_stack(year: int, scale: float, emb_mode: str = "pyramid", epoch: int = 2020,
                 max_pixels: int = 1024) -> tuple[ee.Image, ee.Projection]:
    """Stack [A*w, A, w, valid] on a Mollweide grid at ``scale`` (multiple of
    100 m). Population: density reduceResolution(mean) x pixelArea = sum.
    Embedding: 'pyramid' (EE resamples on read, as in the 100 m reference) or
    'rr' (reduceResolution mean of the 10 m pixels)."""
    gp = ee.Image(f"{ae.GHSL_POP}/{epoch}").select("population_count")
    proj = gp.projection().atScale(scale)
    dens = gp.updateMask(gp.gte(0)).unmask(0).divide(1e4)
    w = dens.reduceResolution(ee.Reducer.mean(), maxPixels=max_pixels).reproject(proj) \
        .multiply(ee.Image.pixelArea())
    emb = ae.annual_mosaic(year)
    if emb_mode == "rr":
        emb = emb.setDefaultProjection(gp.projection().atScale(10)) \
            .reduceResolution(ee.Reducer.mean(), maxPixels=max_pixels).reproject(proj)
    valid = emb.select(0).mask().gt(0)
    w = w.updateMask(valid)
    img = ee.Image.cat([emb.multiply(w).rename(ae.WBANDS), emb, w.rename("pop_sum"),
                        valid.selfMask().rename("n_pixels")])
    return img, proj


def coarse_reduce(fc: ee.FeatureCollection, year: int, scale: float, emb_mode: str = "pyramid",
                  tile_scale: int = 4) -> ee.FeatureCollection:
    img, proj = coarse_stack(year, scale, emb_mode)
    out = img.reduceRegions(collection=fc, reducer=ee.Reducer.sum(), crs=proj, tileScale=tile_scale)
    return out.map(lambda f: f.setGeometry(f.geometry().centroid(1000)).set({"year": year, "scale": scale}))


# ---------------------------------------------------------------- metrics
def unit(X: np.ndarray) -> np.ndarray:
    return X / np.linalg.norm(X, axis=1, keepdims=True)


def compare(est: pd.DataFrame, ref: pd.DataFrame) -> dict:
    """est/ref indexed by unit_id with columns A00..A63 (unit length)."""
    ids = est.index.intersection(ref.index)
    E, R = unit(est.loc[ids, ae.BANDS].to_numpy()), unit(ref.loc[ids, ae.BANDS].to_numpy())
    cos = (E * R).sum(1)
    mse = ((E - R) ** 2).sum(1).mean()
    var = ((R - R.mean(0)) ** 2).sum(1).mean()
    retr = (np.argmax(E @ R.T, axis=1) == np.arange(len(ids))).mean()
    iu = np.triu_indices(len(ids), 1)
    from scipy.stats import spearmanr
    rho = spearmanr((1 - E @ E.T)[iu], (1 - R @ R.T)[iu]).statistic
    return {"n": len(ids), "cos_mean": cos.mean(), "cos_min": cos.min(), "mse_over_var": mse / var,
            "retrieval": retr, "dist_spearman": rho}


# ---------------------------------------------------------------- local zonal stats (computePixels)
def fetch_embedding(year: int, c0: int, r0: int, W: int, H: int, res: float = 100, block: int = 256,
                    int8: bool = False) -> tuple[np.ndarray, float]:
    """(64, H, W) float32 annual embedding on a Mollweide grid of ``res`` m aligned
    with the GHSL grid (origin at GHSL column c0*100/res ... in res units), fetched
    with ``ee.data.computePixels`` in ``block`` x ``block`` requests (64 x float32
    x 256^2 = 16.8 MB < 48 MB limit). Masked pixels are NaN. Returns (array, EECU-s)."""
    from pop.features.ee_utils import profiled
    img = ae.annual_mosaic(year).unmask(-2, False)
    # int8: round(127 x), nodata -128; 64 x 512^2 bytes = 16.8 MB per request
    img = img.multiply(127).round().max(-128).toInt8() if int8 else img.toFloat()
    out = np.full((64, H, W), np.nan, dtype="float32")
    eecu = 0.0
    for rr in range(0, H, block):
        for cc in range(0, W, block):
            h, w = min(block, H - rr), min(block, W - cc)
            req = {"expression": img, "fileFormat": "NPY",
                   "grid": {"dimensions": {"width": w, "height": h},
                            "affineTransform": {"scaleX": res, "shearX": 0, "translateX": X0 + (c0 + cc) * res,
                                                "shearY": 0, "scaleY": -res, "translateY": Y0 - (r0 + rr) * res},
                            "crsWkt": _ghsl_wkt(2020)}}
            raw, e = profiled(lambda: ee.data.computePixels(req))
            eecu += e
            arr = np.load(io.BytesIO(raw)) if isinstance(raw, (bytes, bytearray)) else raw
            a = np.stack([arr[b] for b in ae.BANDS]).astype("float32")
            if int8:
                a = np.where(a <= -128, np.nan, a / 127)
            a[a <= -1.5] = np.nan
            out[:, rr:rr + h, cc:cc + w] = a
    return out, eecu


def local_means(geom_ll, year: int, res: float = 100, quantize: bool = False, epoch: int = 2020,
                int8: bool = False, block: int = 256) -> dict:
    """Pop-weighted and unweighted unit means from a computePixels download.
    Weights: GHSL people per 100 m pixel split equally over its (100/res)^2
    sub-pixels; membership by pixel centre at ``res``. ``quantize`` emulates an
    int8 download (round(x*127))."""
    k = int(round(100 / res))
    pop, _, c0, r0 = pop_raster(geom_ll, epoch)
    H, W = pop.shape[0] * k, pop.shape[1] * k
    gm = shp_transform(lambda x, y: _to_moll.transform(x, y), geom_ll)
    tr = Affine(res, 0, X0 + c0 * 100, 0, -res, Y0 - r0 * 100)
    mask = rfeatures.geometry_mask([mapping(gm)], (H, W), tr, invert=True)
    wpop = np.kron(np.where(pop > 0, pop, 0), np.ones((k, k))) / k**2 * mask
    A, eecu = fetch_embedding(year, c0 * k, r0 * k, W, H, res, block, int8)
    if quantize:
        A = np.round(A * 127) / 127
    ok = np.isfinite(A[0])
    A = np.nan_to_num(A)
    res_ = {"eecu_s": eecu, "bbox_km2": H * W * (res / 1e3) ** 2, "mb": A.nbytes / 2**20 / (4 if int8 else 1)}
    for name, w in (("pop", wpop * ok), ("none", mask * ok)):
        v = (A.reshape(64, -1) @ w.ravel()) / w.sum()
        res_[name] = v / np.linalg.norm(v)
    return res_
