"""Train/test split machinery S0-S5 with rolling origins (Paper 1 frozen protocol).

A split instance = (unit set) x (year window):
    get_split(name, country, fold, origin) -> Split(train_units, test_units, train_years, test_years)
Rows are *target* rows (unit, week_start); lag features may use any earlier history.
For origin Y: train target years = 2018..Y-1, test target years = {Y} (all weeks, horizons 1-4 are
issued so that the target week falls in Y). Tuning origin = 2019 (train 2018, test 2019).

S0  random unit-weeks (leaky contrast): rows of 2018..Y hashed to 80/20; train = 80% part (incl. year Y),
    test = 20% part restricted to year Y.                                           BRAZIL, COLOMBIA, TAIWAN
S1  pure temporal, all units train and test.                                        all four countries
S2  leave-one-adm1-out; fold = adm1 index (sorted).                                 BRAZIL, COLOMBIA
S3  spatial k-means blocks; test block b, train = other blocks minus buffer units.  BRAZIL, COLOMBIA
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
}
SPLITS = tuple(SPLIT_COUNTRIES)


@dataclass(frozen=True)
class Split:
    name: str
    country: str          # test country
    fold: object          # None (S0/S1), adm1 index (S2), block (S3), fold (S4), country (S5)
    origin: int
    train_units: frozenset
    test_units: frozenset
    train_years: tuple
    test_years: tuple
    row_level: bool = False   # True for S0: unit sets overlap, row hash decides membership
    seed: int = DEFAULT_SEED


# ------------------------------------------------------------------------------------------- tables
@lru_cache(maxsize=4)
def load_unit_folds(split_dir: str | None = None) -> pd.DataFrame:
    return pd.read_parquet(Path(split_dir or SPLIT_DIR) / "unit_folds.parquet")


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
    col = {"S2": "s2_fold", "S3": "s3_block", "S4": "s4_fold"}[name]
    return sorted(int(x) for x in uf.loc[uf.country == country, col].dropna().unique())


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
        col = {"S2": "s2_fold", "S3": "s3_block", "S4": "s4_fold"}[name]
        test = frozenset(cu.unit_id[cu[col] == fold])
        if not test:
            raise ValueError(f"{name}/{country}: empty fold {fold}")
        train = allu - test
        if name == "S3":
            ex = load_buffer_exclusions(split_dir)
            ex = ex[(ex.country == country) & (ex.test_block == fold)]
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
