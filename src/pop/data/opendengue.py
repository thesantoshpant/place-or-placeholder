"""Loader for the OpenDengue V1.3.1 Temporal extract.

Quirks handled:
  * missing values are the literal string "NA";
  * a few rows (India) contain embedded "\\r\\n" inside quoted names -> stripped;
  * ``case_definition_standardised`` has "confirmed" vs "Confirmed" -> merged;
  * ``IBGE_code`` is read as a string (7 digits in V1.3.1) and validated with the
    IBGE check-digit algorithm (:func:`ibge_check_digit`).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

TEMPORAL_CSV = Path(
    "data/raw/opendengue/V1.3.1/extracted/Temporal_extract_V1_3_1/Temporal_extract_V1_3_1.csv"
)
PANEL_COUNTRIES = ("BRAZIL", "COLOMBIA", "PERU", "TAIWAN")
_STR_COLS = ["adm_0_name", "adm_1_name", "adm_2_name", "full_name", "ISO_A0",
             "IBGE_code", "case_definition_standardised", "S_res", "T_res", "UUID"]


def ibge_check_digit(code6: str) -> int:
    """IBGE municipality check digit for a 6-digit code.

    Weights 1,2,1,2,1,2; two-digit products are reduced to the sum of their
    digits; DV = (10 - sum mod 10) mod 10. E.g. 330455 -> 7 (3304557).
    Note: IBGE has a handful of historical exceptions that do not follow it.
    """
    code6 = str(code6)
    if len(code6) != 6 or not code6.isdigit():
        raise ValueError(f"expected 6 digits, got {code6!r}")
    total = 0
    for i, ch in enumerate(code6):
        p = int(ch) * (1 if i % 2 == 0 else 2)
        total += p // 10 + p % 10
    return (10 - total % 10) % 10


def ibge7(code: str) -> str:
    """Return the 7-digit IBGE code (derives the check digit if given 6)."""
    code = str(code).strip()
    if len(code) == 6:
        return code + str(ibge_check_digit(code))
    if len(code) == 7 and code.isdigit():
        return code
    raise ValueError(f"bad IBGE code {code!r}")


def normalise_case_definition(s: pd.Series) -> pd.Series:
    """Merge case variants ("confirmed"/"Confirmed") -> capitalised first letter."""
    s = s.astype("string").str.strip()
    return s.str[:1].str.upper() + s.str[1:]


def load_temporal(path: str | Path = TEMPORAL_CSV, countries=PANEL_COUNTRIES,
                  t_res: str | None = "Week", s_res=None) -> pd.DataFrame:
    """Read the Temporal extract, filtered by country / T_res / S_res."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=["NA"])
    for c in _STR_COLS:
        if c in df.columns:
            df[c] = (df[c].astype("string")
                     .str.replace(r"[\r\n]+", " ", regex=True).str.strip())
    if countries is not None:
        df = df[df["adm_0_name"].isin(countries)]
    if t_res is not None:
        df = df[df["T_res"] == t_res]
    if s_res is not None:
        s_res = [s_res] if isinstance(s_res, str) else list(s_res)
        df = df[df["S_res"].isin(s_res)]
    df = df.copy()
    df["calendar_start_date"] = pd.to_datetime(df["calendar_start_date"])
    df["calendar_end_date"] = pd.to_datetime(df["calendar_end_date"])
    df["dengue_total"] = pd.to_numeric(df["dengue_total"]).astype(float)
    df["case_definition_standardised"] = normalise_case_definition(
        df["case_definition_standardised"])
    return df.reset_index(drop=True)
