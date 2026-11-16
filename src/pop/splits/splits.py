"""Train/test split machinery S0-S5 with rolling origins (Paper 1 frozen protocol).

A split instance = (unit set) x (year window):
    get_split(name, country, fold, origin) -> Split(train_units, test_units, train_years, test_years)
Rows are *target* rows (unit, week_start); lag features may use any earlier history.
For origin Y: train target years = 2018..Y-1, test target years = {Y} (all weeks, horizons 1-4 are
issued so that the target week falls in Y). Tuning origin = 2019 (train 2018, test 2019).

S0  random unit-weeks (leaky contrast): rows of 2018..Y hashed to 80/20; train = 80% part (incl. year Y),
    test = 20% part restricted to year Y.                                           BRAZIL, COLOMBIA, TAIWAN
S1  pure temporal, all units train and test.                                        all four countries
S2  grouped leave-states-out: every adm1 in exactly one of 5 folds, folds balanced by unit
    count (seeded greedy); fold = group index.                                      BRAZIL, COLOMBIA
S2L legacy leave-one-adm1-out; fold = adm1 index (sorted). Kept, not run.           BRAZIL, COLOMBIA
S3  spatial k-means blocks grouped into folds (BR: 10 blocks -> 5 folds of 2, largest block
    paired with smallest; CO: 6 folds = 6 blocks); train = all other units minus those within
    D of any held-out unit of the fold.                                             BRAZIL, COLOMBIA
S3B legacy one-block-per-fold S3 (BR 10, CO 6). Kept, not run.                      BRAZIL, COLOMBIA
S4  cold-start: 5-fold random unit hold-out stratified by adm1.                     BRAZIL, COLOMBIA
S5  leave-one-country-out; fold = held-out country (TAIWAN first); `country` arg ignored.

Fold assignments are read from data/processed/splits_v1 (built by scripts/splits/build_splits.py).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
SPLIT_DIR = ROOT / "data/processed/splits_v1"

COUNTRIES = ("BRAZIL", "COLOMBIA", "PERU", "TAIWAN")
LAST_YEAR = {"BRAZIL": 2024, "COLOMBIA": 2022, "PERU": 2023, "TAIWAN": 2024}
TRAIN_START = 2018
TUNING_ORIGIN = 2019
FIRST_TEST_ORIGIN = 2020
HORIZONS = (1, 2, 3, 4)
S0_TEST_FRAC = 0.2
DEFAULT_SEED = 20240101
S5_ORDER = ("TAIWAN", "BRAZIL", "COLOMBIA", "PERU")

SPLIT_COUNTRIES = {
    "S0": ("BRAZIL", "COLOMBIA", "TAIWAN"),
    "S1": COUNTRIES,
    "S2": ("BRAZIL", "COLOMBIA"),
    "S3": ("BRAZIL", "COLOMBIA"),
    "S4": ("BRAZIL", "COLOMBIA"),
    "S5": S5_ORDER,  # held-out country
    "S2L": ("BRAZIL", "COLOMBIA"),  # legacy leave-one-adm1-out (not run)
    "S3B": ("BRAZIL", "COLOMBIA"),  # legacy one block per fold (not run)
}
SPLITS = tuple(SPLIT_COUNTRIES)
S2_GROUPS = 5                       # S2: adm1s grouped into 5 folds
S3_BLOCKS_PER_FOLD = {"BRAZIL": 2}  # S3: BR 10 blocks -> 5 folds of 2; others 1 block per fold
FOLD_COL = {"S2": "s2_fold", "S2L": "s2l_fold", "S3": "s3_fold", "S3B": "s3_block",
            "S4": "s4_fold"}


@dataclass(frozen=True)
class Split:
    name: str
    country: str          # test country
    fold: object          # None (S0/S1), group (S2/S3/S4), adm1 (S2L), block (S3B), country (S5)
    origin: int
    train_units: frozenset
    test_units: frozenset
    train_years: tuple
    test_years: tuple
    row_level: bool = False   # True for S0: unit sets overlap, row hash decides membership
    seed: int = DEFAULT_SEED


# ------------------------------------------------------------------------------------------- tables
def group_adm1_folds(units: pd.DataFrame, k: int = S2_GROUPS, seed: int = DEFAULT_SEED) -> pd.Series:
    """S2 fold per unit: each adm1 goes to exactly one of min(k, n_adm1) folds. Seeded greedy:
    adm1s in a seeded random order, then (stable) by unit count descending; each goes to the
    fold with the fewest units so far (ties -> lowest fold index)."""
    sizes = units.groupby("adm1").size()
    k = min(k, len(sizes))
    names = sizes.index.to_numpy()[np.random.default_rng(seed).permutation(len(sizes))]
    order = sorted(names, key=lambda a: -int(sizes[a]))
    load, fold = np.zeros(k, int), {}
    for a in order:
        f = int(np.argmin(load))
        fold[a] = f
        load[f] += int(sizes[a])
    return units["adm1"].map(fold).astype("Int16")


def group_blocks(blocks: pd.Series, per_fold: int) -> dict:
    """S3 fold per block: blocks sorted by unit count; the i-th largest is grouped with the
    i-th smallest (per_fold = 2). Folds are numbered by their smallest block id. Identity when the
    block count is not a multiple of per_fold."""
    sizes = blocks.value_counts()
    ids = sorted(int(b) for b in sizes.index)
    n = len(ids)
    if per_fold <= 1 or n % per_fold:
        return {b: b for b in ids}
    if per_fold != 2:
        raise NotImplementedError("only pairs of blocks are implemented")
    desc = sorted(ids, key=lambda b: (-int(sizes[b]), b))
    groups = sorted(sorted((desc[i], desc[n - 1 - i])) for i in range(n // 2))
    return {b: g for g, grp in enumerate(groups) for b in grp}


@lru_cache(maxsize=4)
def load_unit_folds(split_dir: str | None = None) -> pd.DataFrame:
    """unit_folds.parquet plus the derived fold columns. The file's ``s2_fold`` (adm1 index) is
    exposed as ``s2l_fold`` (S2L); ``s2_fold`` becomes the grouped S2 fold and ``s3_fold`` the
    grouped S3 fold (S3B keeps ``s3_block``)."""
    uf = pd.read_parquet(Path(split_dir or SPLIT_DIR) / "unit_folds.parquet")
    uf["s2l_fold"] = uf["s2_fold"]
    uf["s2_fold"] = pd.array([pd.NA] * len(uf), dtype="Int16")
    uf["s3_fold"] = pd.array([pd.NA] * len(uf), dtype="Int16")
    for c in SPLIT_COUNTRIES["S2"]:
        m = (uf.country == c).to_numpy()
        if m.any() and "adm1" in uf:
            uf.loc[m, "s2_fold"] = group_adm1_folds(uf[m]).to_numpy()
    for c in SPLIT_COUNTRIES["S3"]:
        m = (uf.country == c).to_numpy() & uf.s3_block.notna().to_numpy()
        if m.any():
            b = uf.s3_block[m].astype(int)
            uf.loc[m, "s3_fold"] = b.map(group_blocks(b, S3_BLOCKS_PER_FOLD.get(c, 1))).astype(
                "Int16").to_numpy()
    return uf


@lru_cache(maxsize=4)
def load_buffer_exclusions(split_dir: str | None = None) -> pd.DataFrame:
    return pd.read_parquet(Path(split_dir or SPLIT_DIR) / "s3_buffer_exclusions.parquet")


def origins(country: str, include_tuning: bool = False) -> list[int]:
    o = list(range(FIRST_TEST_ORIGIN, LAST_YEAR[country] + 1))
    return [TUNING_ORIGIN] + o if include_tuning else o


def year_window(origin: int) -> tuple[tuple, tuple]:
    if origin <= TRAIN_START:
        raise ValueError(f"origin {origin} leaves no training years (train starts {TRAIN_START})")
    return tuple(range(TRAIN_START, origin)), (origin,)


def folds(name: str, country: str, split_dir: str | None = None) -> list:
    if name in ("S0", "S1"):
        return [None]
    if name == "S5":
        return list(S5_ORDER)
    uf = load_unit_folds(split_dir)
    return sorted(int(x) for x in uf.loc[uf.country == country, FOLD_COL[name]].dropna().unique())


# ----------------------------------------------------------------------------------------------- API
def get_split(name: str, country: str, fold=None, origin: int = FIRST_TEST_ORIGIN,
              seed: int = DEFAULT_SEED, split_dir: str | None = None) -> Split:
    if name not in SPLITS:
        raise ValueError(f"unknown split {name}")
    if name == "S5":
        country = fold = fold if fold is not None else country
    if country not in SPLIT_COUNTRIES[name]:
        raise ValueError(f"{name} not defined for {country}")
    if origin > LAST_YEAR[country]:
        raise ValueError(f"origin {origin} beyond last year of {country}")
    train_years, test_years = year_window(origin)
    uf = load_unit_folds(split_dir)
    cu = uf[uf.country == country]
    allu = frozenset(cu.unit_id)
    row_level = False
    if name in ("S0", "S1"):
        train, test, row_level = allu, allu, name == "S0"
    elif name == "S5":
        train, test = frozenset(uf.unit_id[uf.country != country]), allu
    else:
        sel = (cu[FOLD_COL[name]] == fold).fillna(False).to_numpy(bool)
        test = frozenset(cu.unit_id[sel])
        if not test:
            raise ValueError(f"{name}/{country}: empty fold {fold}")
        train = allu - test
        if name in ("S3", "S3B"):  # buffer around every held-out unit = union over its blocks
            blocks = {int(b) for b in cu.s3_block[sel]}
            ex = load_buffer_exclusions(split_dir)
            ex = ex[(ex.country == country) & ex.test_block.isin(blocks)]
            train = train - frozenset(ex.excluded_unit_id)
    return Split(name, country, fold, origin, train, test, train_years, test_years, row_level, seed)


def iter_folds(name: str, countries=None, include_tuning: bool = False, seed: int = DEFAULT_SEED,
               split_dir: str | None = None) -> Iterator[Split]:
    """All (country, fold, origin) instances of a split. For S5, origins follow the held-out country."""
    for c in countries or SPLIT_COUNTRIES[name]:
        if c not in SPLIT_COUNTRIES[name]:
            continue
        for f in ([c] if name == "S5" else folds(name, c, split_dir)):
            for o in origins(c, include_tuning):
                yield get_split(name, c, f, o, seed, split_dir)


# ------------------------------------------------------------------------------------------ row masks
def _row_uniform(unit_id: pd.Series, week_start: pd.Series, seed: int) -> np.ndarray:
    """Deterministic U(0,1) per (unit, week, seed); stable across origins and row order."""
    key = (unit_id.astype(str) + "|" + pd.to_datetime(week_start).dt.strftime("%Y-%m-%d") + f"|{seed}")
    h = key.map(lambda s: int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "little"))
    return h.to_numpy(dtype=np.float64) / 2.0 ** 64


def row_masks(panel: pd.DataFrame, split: Split) -> dict[str, np.ndarray]:
    """Boolean masks over `panel` rows (target rows).

    train : training target rows; test : test target rows;
    score : test & ~flag_gap (flag_gap weeks are kept as inputs but never scored);
    train_target_ok : train & ~flag_gap (optional, for models that want clean targets).
    """
    uid, yr = panel.unit_id, panel.year
    train = uid.isin(split.train_units).to_numpy() & yr.isin(split.train_years).to_numpy()
    test = uid.isin(split.test_units).to_numpy() & yr.isin(split.test_years).to_numpy()
    if split.row_level:
        win = uid.isin(split.train_units).to_numpy() & yr.isin(split.train_years + split.test_years).to_numpy()
        u = np.full(len(panel), np.nan)
        u[win] = _row_uniform(uid[win], panel.week_start[win], split.seed)
        held = win & (u < S0_TEST_FRAC)
        train = win & ~held
        test = held & yr.isin(split.test_years).to_numpy()
    gap = panel.flag_gap.fillna(False).to_numpy(bool)
    return {"train": train, "test": test, "score": test & ~gap, "train_target_ok": train & ~gap}
