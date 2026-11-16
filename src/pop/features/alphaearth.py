"""AlphaEarth (Google Satellite Embedding V1) district-mean features.

Design (Paper 1, frozen): population-weighted district means of the 64-d annual
embedding at ~100 m, renormalised to unit length (the raw, unnormalised mean is
kept via ``raw_norm`` as a sensitivity check). The embedding used for
epidemiological year y comes from image year y-1 (see ``lag_to_target_year``).

All reductions use a single ``ee.Reducer.sum()`` over a stacked image so that
population-weighted and unweighted means come out of one pass:

    weighted mean_k   = sum(A_k * w) / sum(w),   w = GHSL people per pixel
    unweighted mean_k = sum(A_k)     / sum(1)    (area-fraction weighted)

Sums are area-fraction aware (``reduceRegions`` weights boundary pixels by
coverage), so means are exact area/population integrals at the chosen scale.
"""
from __future__ import annotations

import os
from typing import Iterable

import ee
import numpy as np
import pandas as pd

EMB_COLLECTION = "GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL"
GHSL_POP = "JRC/GHSL/P2023A/GHS_POP"
BANDS = [f"A{i:02d}" for i in range(64)]
WBANDS = [f"w{b}" for b in BANDS]
ASSET_ROOT = "projects/ee-spant-scaleshift/assets/pop"


def init() -> None:
    ee.Initialize(project=os.environ["EE_PROJECT"])


# ---------------------------------------------------------------- images
def annual_mosaic(year: int) -> ee.Image:
    """Mosaic of all AlphaEarth tiles for one calendar year (bands A00..A63)."""
    col = ee.ImageCollection(EMB_COLLECTION).filterDate(f"{year}-01-01", f"{year + 1}-01-01")
    return col.mosaic().select(BANDS)


def pop_per_pixel(epoch: int = 2020) -> ee.Image:
    """GHSL people per output pixel: native density (people/m^2) x pixelArea.

    GHS_POP is 100 m Mollweide (1e4 m^2 pixels); converting to density first
    makes the weight correct at any reduction scale/projection.
    """
    pop = ee.Image(f"{GHSL_POP}/{epoch}").select("population_count")
    pop = pop.updateMask(pop.gte(0))  # unmasked negative nodata exists (e.g. -200)
    return pop.divide(1e4).multiply(ee.Image.pixelArea()).rename("pop_sum")


def stacked_image(year: int, pop_epoch: int = 2020, weighting: str = "both") -> ee.Image:
    """Image whose per-region *sums* give everything needed for the means."""
    emb = annual_mosaic(year)
    valid = emb.select(0).mask().gt(0)
    w = pop_per_pixel(pop_epoch).unmask(0).updateMask(valid)
    parts = []
    if weighting in ("pop", "both"):
        parts.append(emb.multiply(w).rename(WBANDS))
    if weighting in ("none", "both"):
        parts.append(emb)
    parts += [w, valid.selfMask().rename("n_pixels")]
    return ee.Image.cat(parts)


# ---------------------------------------------------------------- boundaries
def units_to_fc(gdf, id_col: str = "unit_id", simplify_deg: float = 5e-4) -> ee.FeatureCollection:
    """Client-side GeoDataFrame (EPSG:4326) -> ee.FeatureCollection.

    ``simplify_deg`` (default ~50 m) keeps request payloads small; for the full
    run upload once with ``export_units_asset`` and reuse the asset.
    """
    feats = []
    for uid, geom in zip(gdf[id_col], gdf.geometry):
        g = geom.simplify(simplify_deg, preserve_topology=True) if simplify_deg else geom
        feats.append(ee.Feature(ee.Geometry(g.__geo_interface__, "EPSG:4326", False), {"unit_id": str(uid)}))
    return ee.FeatureCollection(feats)


def export_units_asset(fc: ee.FeatureCollection, name: str) -> ee.batch.Task:
    task = ee.batch.Export.table.toAsset(collection=fc, description=f"units_{name}", assetId=f"{ASSET_ROOT}/{name}")
    task.start()
    return task


def ensure_asset_folder() -> None:
    try:
        ee.data.getAsset(ASSET_ROOT)
    except ee.EEException:
        ee.data.createAsset({"type": "FOLDER"}, ASSET_ROOT)


# ---------------------------------------------------------------- reductions
def reduce_units(fc: ee.FeatureCollection, year: int, scale: float = 100, weighting: str = "both",
                 pop_epoch: int = 2020, tile_scale: int = 4, crs: str | None = None,
                 centroid: bool = False) -> ee.FeatureCollection:
    """Server-side per-unit sums (one sum reducer over the stacked image).

    Geometry is dropped (or replaced by the centroid when ``centroid``, needed
    because Export.table.toAsset rejects null geometries)."""
    img = stacked_image(year, pop_epoch, weighting)
    out = img.reduceRegions(collection=fc, reducer=ee.Reducer.sum(), scale=scale, crs=crs, tileScale=tile_scale)
    return out.map(lambda f: f.setGeometry(f.geometry().centroid(1000) if centroid else None)
                   .set({"year": year, "scale": scale}))


def sums_to_frame(rows: Iterable[dict], renormalise: bool = True) -> pd.DataFrame:
    """Convert per-unit sums to long DataFrame:
    unit_id, year, A00..A63, pop_sum, n_pixels, weighting, raw_norm, scale.

    A00..A63 are unit-length if ``renormalise`` (raw mean = A * raw_norm).
    """
    rows = list(rows)
    out = []
    for r in rows:
        base = {"unit_id": r["unit_id"], "year": int(r["year"]), "scale": r.get("scale"),
                "pop_sum": r.get("pop_sum"), "n_pixels": r.get("n_pixels")}
        for weighting, cols, denom in (("pop", WBANDS, "pop_sum"), ("none", BANDS, "n_pixels")):
            if cols[0] not in r:
                continue
            d = r.get(denom) or np.nan
            v = np.array([r.get(c, np.nan) for c in cols], float) / d
            n = float(np.linalg.norm(v))
            if renormalise and n > 0:
                v = v / n
            out.append({**base, **dict(zip(BANDS, v)), "weighting": weighting, "raw_norm": n})
    cols = ["unit_id", "year", *BANDS, "pop_sum", "n_pixels", "weighting", "raw_norm", "scale"]
    return pd.DataFrame(out, columns=cols)


def extract(gdf, year: int, scale: float = 100, weighting: str = "both", chunk: int = 25,
            tile_scale: int = 4, id_col: str = "unit_id", simplify_deg: float = 5e-4,
            renormalise: bool = True) -> pd.DataFrame:
    """Interactive (getInfo) extraction in chunks. Use for pilots / small sets;
    use ``export_extract`` (batch) for the full run."""
    frames = []
    for i in range(0, len(gdf), chunk):
        fc = units_to_fc(gdf.iloc[i:i + chunk], id_col, simplify_deg)
        info = reduce_units(fc, year, scale, weighting, tile_scale=tile_scale).getInfo()
        frames.append(sums_to_frame((f["properties"] for f in info["features"]), renormalise))
    return pd.concat(frames, ignore_index=True)


def export_extract(fc: ee.FeatureCollection, year: int, name: str, scale: float = 100,
                   weighting: str = "both", tile_scale: int = 4) -> ee.batch.Task:
    """Batch export of per-unit sums to an EE table asset under ASSET_ROOT."""
    sel = ["unit_id", "year", "scale", "pop_sum", "n_pixels"]
    if weighting in ("pop", "both"):
        sel += WBANDS
    if weighting in ("none", "both"):
        sel += BANDS
    coll = reduce_units(fc, year, scale, weighting, tile_scale=tile_scale, centroid=True).select(sel, None, True)
    task = ee.batch.Export.table.toAsset(collection=coll, description=name, assetId=f"{ASSET_ROOT}/{name}")
    task.start()
    return task


def task_cost(task_id: str) -> dict:
    """EECU-seconds and wall time of a finished batch task."""
    op = ee.data.getOperation(f"projects/{os.environ['EE_PROJECT']}/operations/{task_id}")
    md = op.get("metadata", {})
    st, en = pd.Timestamp(md.get("startTime")), pd.Timestamp(md.get("endTime"))
    return {"state": md.get("state"), "eecu_s": md.get("batchEecuUsageSeconds"),
            "wall_s": (en - st).total_seconds() if md.get("endTime") else None, "metadata": md}


# ---------------------------------------------------------------- diagnostics
def sample_pixel_norms(region: ee.Geometry, year: int, n: int = 1000, scale: float = 10, seed: int = 1) -> np.ndarray:
    emb = annual_mosaic(year)
    s = emb.sample(region=region, scale=scale, numPixels=n, seed=seed, geometries=False, tileScale=4)
    rows = s.limit(n).getInfo()["features"]
    X = np.array([[f["properties"][b] for b in BANDS] for f in rows], float)
    return np.linalg.norm(X, axis=1)


def cosine(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a, b = np.atleast_2d(a), np.atleast_2d(b)
    return (a * b).sum(1) / (np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1))


def lag_to_target_year(df: pd.DataFrame, lag: int = 1) -> pd.DataFrame:
    """Add ``target_year`` = image year + lag (embedding of y-1 used for year y)."""
    return df.assign(target_year=df["year"] + lag)
