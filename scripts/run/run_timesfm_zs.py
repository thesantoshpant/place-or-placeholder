"""TimesFM 2.5 zero-shot forecasts + scoring, Brazil split S1 (all units, temporal).

For test year Y, origins are all weeks o with o + h (h = 1..4) in Y; each forecast
uses log1p(cases) of the unit up to and including o. Rows whose target year != Y
are dropped, so each (unit, target_week, horizon) is forecast once per Y.

    python scripts/run/run_timesfm_zs.py --years 2023            # pilot
    python scripts/run/run_timesfm_zs.py --years 2020 2021 2022 2023 2024
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from pop.eval.scoring import aggregate_scores, score_forecasts  # noqa: E402
from pop.models import timesfm_zs as tz  # noqa: E402

H = 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", default="BRAZIL")
    ap.add_argument("--years", type=int, nargs="+", default=[2020, 2021, 2022, 2023, 2024])
    ap.add_argument("--batch", type=int, default=1024)
    ap.add_argument("--out", default=str(ROOT / "runs/brazil_s1_timesfm_zs"))
    ap.add_argument("--no-compile", action="store_true")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                        handlers=[logging.FileHandler(out / "run.log"), logging.StreamHandler()])
    log = logging.getLogger().info
    log(f"args {vars(a)}")

    p = pd.read_parquet(ROOT / "data/processed/panel_weekly_v1.parquet",
                        columns=["unit_id", "country", "week_start", "year", "cases", "flag_gap"])
    p = p[p.country == a.country].copy()
    p["week_start"] = pd.to_datetime(p.week_start)
    weeks = np.sort(p.week_start.unique())
    units = np.sort(p.unit_id.unique().astype(str))
    wide = p.pivot(index="unit_id", columns="week_start", values="cases").reindex(index=units, columns=weeks)
    assert not wide.isna().any().any(), "panel not complete"
    y_log = np.log1p(wide.to_numpy(np.float64).clip(min=0)).astype(np.float32)
    week_year = p.drop_duplicates("week_start").set_index("week_start").year.reindex(weeks).to_numpy()
    truth = p[["unit_id", "week_start", "cases", "flag_gap"]].rename(columns={"week_start": "target_week"})
    truth["unit_id"] = truth.unit_id.astype(str)
    gap = truth[truth.flag_gap][["unit_id", "target_week"]].assign(_gap=True)
    log(f"{len(units)} units, {len(weeks)} weeks {weeks[0]}..{weeks[-1]}, gap rows {len(gap)}")

    import torch
    log(f"torch {torch.__version__} cuda {torch.version.cuda} {torch.cuda.get_device_name(0)}")
    t0 = time.time()
    model = tz.load_model(max_context=len(weeks), batch_size=a.batch, horizon=H,
                          torch_compile=not a.no_compile)
    log(f"model loaded+compiled in {time.time() - t0:.1f}s, max_context={model.forecast_config.max_context}")

    fwriter, all_scores, stats_all = None, [], {}
    for Y in a.years:
        tgt = np.nonzero(week_year == Y)[0]
        org = np.arange(max(tgt[0] - H, 0), tgt[-1])  # column index of origin weeks
        log(f"Y={Y}: {len(tgt)} target weeks, {len(org)} origins")
        q, st = tz.forecast_origins(model, y_log, org, horizon=H, log=log)
        log(f"Y={Y}: {st}")
        stats_all[Y] = st
        fc = tz.to_long(q, units, weeks[org], horizon=H)
        del q
        fc["unit_id"] = fc.unit_id.astype(str)
        yr = pd.Series(week_year, index=pd.DatetimeIndex(weeks))
        fc = fc[fc.target_week.map(yr).to_numpy() == Y].reset_index(drop=True)
        fc.insert(0, "test_year", np.int16(Y))
        tab = pa.Table.from_pandas(fc, preserve_index=False)
        if fwriter is None:
            fwriter = pq.ParquetWriter(out / "forecasts.parquet", tab.schema, compression="zstd")
        fwriter.write_table(tab)
        base = fc.drop(columns=["value_log"])
        s_log = score_forecasts(base, truth, scale="log")
        s_case = score_forecasts(base, truth, scale="case", coverage_levels=())
        s = s_log.rename(columns={"wis": "wis_log", "ae_median": "ae_median_log"})
        s["wis_case"] = s_case["wis"].to_numpy()
        s["ae_median_case"] = s_case["ae_median"].to_numpy()
        s = s.merge(gap, on=["unit_id", "target_week"], how="left")
        s = s[s._gap.isna()].drop(columns="_gap")  # exclude flag_gap target weeks
        log(f"Y={Y}: scored {len(s)} rows; mean log-WIS by h:\n"
            f"{s.groupby('horizon')[['wis_log', 'cov_40', 'cov_80']].mean().round(4)}")
        all_scores.append(s)
        del fc, base, s_log, s_case
    fwriter.close()
    sc = pd.concat(all_scores, ignore_index=True)
    sc.to_parquet(out / "scores.parquet", index=False)
    met = ["wis_log", "wis_case", "ae_median_log", "cov_40", "cov_80"]
    by_y = aggregate_scores(sc, by=("test_year", "horizon"), metrics=met)
    pooled = aggregate_scores(sc, by=("horizon",), metrics=met).assign(test_year="pooled")
    summ = pd.concat([by_y, pooled], ignore_index=True)
    summ.insert(0, "model", "timesfm2.5_zs")
    summ.to_csv(out / "summary.csv", index=False)
    log(f"summary:\n{summ.round(4).to_string()}")
    with open(out / "runtime.json", "w") as f:
        json.dump({str(k): v for k, v in stats_all.items()}, f, indent=1)


if __name__ == "__main__":
    main()
