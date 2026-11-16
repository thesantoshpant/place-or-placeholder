"""Shared Earth Engine helpers: init, polygon upload, task waiting, EECU accounting.

Polygon assets live at ``projects/ee-spant-scaleshift/assets/pop/units_v1_<iso3>``.
Large countries are uploaded in chunks (client-side FeatureCollections are capped
by the request size), each chunk to ``..._partNN``; a second, server-side export
merges the parts into the final asset and the parts are deleted.
"""
from __future__ import annotations

import json
import os
import time

import ee
import pandas as pd

ASSET_ROOT = "projects/ee-spant-scaleshift/assets/pop"
ISO3 = {"BRAZIL": "bra", "COLOMBIA": "col", "PERU": "per", "TAIWAN": "twn"}


def init() -> None:
    ee.Initialize(project=os.environ["EE_PROJECT"])


def units_asset_id(country: str, version: str = "v1") -> str:
    return f"{ASSET_ROOT}/units_{version}_{ISO3[country.upper()]}"


def asset_exists(asset_id: str) -> bool:
    try:
        ee.data.getAsset(asset_id)
        return True
    except ee.EEException:
        return False


def delete_asset(asset_id: str) -> None:
    if asset_exists(asset_id):
        ee.data.deleteAsset(asset_id)


# ---------------------------------------------------------------- upload
def _round_coords(obj, nd: int = 5):
    if isinstance(obj, (list, tuple)):
        return [_round_coords(o, nd) for o in obj]
    return round(obj, nd)


def gdf_to_fc(gdf, props=("unit_id", "country", "adm1", "adm2"), nd: int = 5) -> ee.FeatureCollection:
    feats = []
    for row in gdf.itertuples(index=False):
        gj = row.geometry.__geo_interface__
        gj = {"type": gj["type"], "coordinates": _round_coords(gj["coordinates"], nd)}
        p = {k: (None if pd.isna(getattr(row, k)) else str(getattr(row, k))) for k in props if hasattr(row, k)}
        feats.append(ee.Feature(ee.Geometry(gj, "EPSG:4326", False), p))
    return ee.FeatureCollection(feats)


def _chunks(gdf, max_bytes: int):
    """Split rows so each chunk's GeoJSON is below ``max_bytes`` (approx)."""
    sizes = gdf.geometry.apply(lambda g: len(json.dumps(g.__geo_interface__["coordinates"])) * 0.75)
    start, acc = 0, 0.0
    for i, s in enumerate(sizes):
        if acc + s > max_bytes and i > start:
            yield gdf.iloc[start:i]
            start, acc = i, 0.0
        acc += s
    yield gdf.iloc[start:]


def upload_units(gdf, country: str, max_bytes: int = 2_000_000, overwrite: bool = True, log=print) -> dict:
    """Upload one country's polygons as a table asset; returns asset id + EECU used."""
    asset = units_asset_id(country)
    if asset_exists(asset):
        if not overwrite:
            return {"asset": asset, "skipped": True}
        delete_asset(asset)
    parts, tasks = [], []
    for k, ch in enumerate(_chunks(gdf, max_bytes)):
        pid = f"{asset}_part{k:02d}"
        delete_asset(pid)
        t = ee.batch.Export.table.toAsset(collection=gdf_to_fc(ch), description=f"{asset.split('/')[-1]}_p{k:02d}", assetId=pid)
        t.start()
        parts.append(pid)
        tasks.append(t.id)
        log(f"  part {k}: {len(ch)} units -> {pid} ({t.id})")
    costs = [wait(t, log=log) for t in tasks]
    if len(parts) == 1:
        ee.data.renameAsset(parts[0], asset)
    else:
        merged = ee.FeatureCollection([ee.FeatureCollection(p) for p in parts]).flatten()
        t = ee.batch.Export.table.toAsset(collection=merged, description=f"{asset.split('/')[-1]}_merge", assetId=asset)
        t.start()
        costs.append(wait(t.id, log=log))
        for p in parts:
            delete_asset(p)
    n = ee.FeatureCollection(asset).size().getInfo()
    return {"asset": asset, "n": n, "eecu_s": sum(c["eecu_s"] or 0 for c in costs), "tasks": len(costs)}


# ---------------------------------------------------------------- tasks
def task_cost(task_id: str) -> dict:
    """State, EECU-seconds and wall time of a batch task from its operation metadata."""
    op = ee.data.getOperation(f"projects/{os.environ['EE_PROJECT']}/operations/{task_id}")
    md = op.get("metadata", {})
    st, en = md.get("startTime"), md.get("endTime")
    wall = (pd.Timestamp(en) - pd.Timestamp(st)).total_seconds() if st and en else None
    eecu = md.get("batchEecuUsageSeconds")
    return {"id": task_id, "state": md.get("state"), "eecu_s": float(eecu) if eecu is not None else None,
            "wall_s": wall, "error": op.get("error")}


def wait(task_id: str, poll: float = 15, log=print) -> dict:
    while True:
        c = task_cost(task_id)
        if c["state"] in ("SUCCEEDED", "FAILED", "CANCELLED"):
            log(f"  task {task_id}: {c['state']} eecu_s={c['eecu_s']} wall_s={c['wall_s']}")
            if c["state"] != "SUCCEEDED":
                raise RuntimeError(f"task {task_id} {c['state']}: {c['error']}")
            return c
        time.sleep(poll)


# ---------------------------------------------------------------- interactive EECU
def profile_eecu(text: str) -> float:
    """Sum the EECU-s column of an EE profile table."""
    tot = 0.0
    for line in text.splitlines()[1:]:
        tok = line.split()
        try:
            tot += float(tok[0])
        except (ValueError, IndexError):
            pass
    return tot


def profiled(fn):
    """Run ``fn()`` with EE profiling on; returns (result, EECU-seconds of interactive calls)."""
    ids: list[str] = []
    with ee.data.profiling(ids.append):
        res = fn()
    if not ids:
        return res, 0.0
    get = ee.ApiFunction.lookup("Profile.getProfiles").call
    eecu = 0.0
    for pid in ids:  # one id per call: a bad/expired id otherwise fails the whole batch
        for k in range(3):
            try:
                eecu += profile_eecu(get(ids=[pid]).getInfo())
                break
            except ee.EEException as e:
                if k == 2:
                    print(f"  profile {pid} unavailable: {e}")
                time.sleep(3)
    return res, eecu
