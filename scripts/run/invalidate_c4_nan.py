#!/usr/bin/env python
"""Invalidate the outputs affected by the all-NaN C4/C4s bug (audit 3 C-1 / audit 4 C1, 2026-11-16b).

  python scripts/run/invalidate_c4_nan.py [--dry-run]

Units without geometry (CO 1, TW 2) made every C4/C4s field of Colombia and Taiwan NaN
(controls.random_smooth_fields, fixed 2026-11-16b). Every C4/C4s chunk of a run that contains CO or
TW units (CO/TW S1-S4 and every S5 cell) is moved to <run>/chunks_superseded_<date>/ (never
deleted; scripts/run/supersede.py), with the stale assembled outputs. The old selection.json is
copied to selection_v1.json. Stage markers controls_2019/select_control/gen_cstar/PIPELINE_DONE of
the affected pipelines are removed so they rerun the C4 chunks and reselect with rule v2.
Run only while no pipeline works on these runs. Log: runs/queue/invalidation_2026-11-16b.md.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from supersede import supersede  # noqa: E402

LOG = Path("runs/queue/invalidation_2026-11-16b.md")
C4 = ["L3+C4", "L3+C4s", "L4+C4", "L4+C4s", "N3+C4", "N3+C4s", "N4+C4", "N4+C4s"]
# run dir -> reason
RUNS = {
    "runs/colombia_s1_controls_2019": "CO S1 per-level selection: C4/C4s all-NaN",
    "runs/colombia_s1_L3_Cstar": "CO S1 per-level final with C* = C4s (all-NaN; stopped at 88/120)",
    "runs/taiwan_s1_controls_2019": "TW S1 per-level selection: C4/C4s all-NaN",
    "runs/taiwan_s1_shared_controls_2019": "TW S1-shared selection: C4/C4s all-NaN",
    "runs/brazil_s5_controls_2019": "S5 (BR held out): C4/C4s NaN for CO/TW training units",
    "runs/colombia_s5_controls_2019": "S5 (CO held out): C4/C4s NaN for CO test / TW training units",
    "runs/peru_s5_controls_2019": "S5 (PE held out): C4/C4s NaN for CO/TW training units",
    "runs/taiwan_s5_controls_2019": "S5 (TW held out): C4/C4s NaN for TW test / CO training units",
    "runs/colombia_s2_controls_2019": "CO S2: C4/C4s all-NaN",
    "runs/colombia_s3_controls_2019": "CO S3: C4/C4s all-NaN",
    "runs/colombia_s4_controls_2019": "CO S4: C4/C4s all-NaN",
    "runs/taiwan_s1brp_L3_Cstar": "TW S1-BRparams (C* = C1 fixed): checked, no C4 chunks",
}
# pipeline dir -> markers to remove
MARKERS = {
    "runs/taiwan_s1_shared": ["stage_controls_2019.done", "stage_select_control.done",
                              "stage_gen_cstar.done", "PIPELINE_DONE"],
    "runs/brazil_s5": ["stage_controls_2019.done", "stage_select_control.done", "stage_gen_cstar.done",
                       "PIPELINE_DONE"],
    "runs/colombia_s5": ["stage_controls_2019.done", "stage_select_control.done", "stage_gen_cstar.done",
                         "PIPELINE_DONE"],
}
REGEN = [("taiwan", "s1_shared"), ("peru", "s5"), ("taiwan", "s5"), ("brazil", "s5"), ("colombia", "s5")]


def seconds(run: Path, levels) -> float:
    s = 0.0
    for f in (run / "chunks").glob("*.done.json") if (run / "chunks").exists() else []:
        if f.name.split("__")[1] in levels:
            try:
                s += float(json.loads(f.read_text()).get("seconds", 0))
            except (ValueError, OSError):
                pass
    return s


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    dry = a.dry_run
    if not LOG.exists() and not dry:
        LOG.write_text(
            "# Invalidation log, all-NaN C4/C4s (2026-11-16b)\n\n"
            "Audit 3 C-1 / audit 4 C1: the units without geometry (CO `CHOCO|BELEN DE BAJIRA`, TW "
            "`HSINCHU CITY|OTHER`, `TAINAN CITY|OTHER`) have NaN lat/lon; `random_smooth_fields` put them "
            "into the Cholesky, so every C4/C4s field of Colombia and Taiwan was NaN (L3+C4 = plain L3 "
            "+ 64 NaN columns). Fixed in `src/pop/features/controls.py` (fields on finite-coordinate "
            "units only; BR/PE draws unchanged, tested). Nothing deleted: chunks moved to "
            "`<run>/chunks_superseded_2026-11-16/` by `scripts/run/invalidate_c4_nan.py`.\n\n"
            "| Run | Superseded `.done` chunks by level | n | assembled files | Reason | worker-h |\n"
            "|---|---|---|---|---|---|\n")
    tot_n, tot_s = 0, 0.0
    for rd, why in RUNS.items():
        run = Path(rd)
        if not run.exists():
            print("skip (missing)", rd)
            continue
        sel = run / "selection.json"
        if sel.exists() and not (run / "selection_v1.json").exists() and not dry:
            shutil.copy2(sel, run / "selection_v1.json")
        sec = seconds(run, C4)
        r = supersede(run, C4, reason=why, dry_run=dry)
        n = sum(r["moved_done_chunks"].values())
        tot_n += n
        tot_s += sec
        if not dry:
            with open(LOG, "a") as fh:
                what = ", ".join(f"{k} {v}" for k, v in sorted(r["moved_done_chunks"].items())) or "nothing"
                fh.write(f"| `{rd}` | {what} | {n} | {r['assembled']} | {why} | {sec / 3600:.2f} |\n")
        print(rd, r["moved_done_chunks"], f"{sec / 3600:.2f} worker-h")
    for pd_, ms in MARKERS.items():
        for m in ms:
            f = Path(pd_) / m
            if f.exists():
                print("rm", f)
                if not dry:
                    f.unlink()
    for c, tok in REGEN:
        cmd = ["bash", "scripts/run/split_pipeline.sh", c, tok, "--gen-controls"]
        if dry:
            print("would run", " ".join(cmd))
            continue
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f"{' '.join(cmd)} failed:\n{r.stdout}\n{r.stderr}")
        print(r.stdout.strip().splitlines()[-1])
    if not dry:
        with open(LOG, "a") as fh:
            fh.write(f"| **total** | | {tot_n} | | | {tot_s / 3600:.2f} |\n\n")
    print(f"total {tot_n} done chunks, {tot_s / 3600:.2f} worker-h")


if __name__ == "__main__":
    main()
