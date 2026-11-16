#!/usr/bin/env python
"""Move superseded chunks of a run aside (never delete). Control fixes 2026-11-16.

  python scripts/run/supersede.py RUN_DIR [--levels L3+C3 L3+C4 ...] [--reason TEXT] [--log FILE]
                                          [--dry-run]

Chunk files (chunks/<model>__<level>[__f<k>]__s<seed>__<year>__h<h>.*) whose level is in --levels
(all chunks when --levels is omitted) go to RUN_DIR/chunks_superseded_<YYYY-MM-DD>/. The run's
assembled outputs (forecasts/scores parquet, summary/timing/dm csv) are stale once any chunk is
moved, so they go to RUN_DIR/chunks_superseded_<date>/assembled/ too; run_experiment.py rebuilds
them from the remaining + recomputed chunks. A name collision inside the target dir gets a
numeric suffix. One line per run is appended to --log (markdown table row).
"""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
from pathlib import Path

ASSEMBLED = ("forecasts.parquet", "scores.parquet", "summary.csv", "timing.csv", "dm.csv")


def chunk_level(name: str) -> str | None:
    parts = name.split("__")
    return parts[1] if len(parts) >= 5 else None


def _dest(d: Path, name: str) -> Path:
    p, k = d / name, 1
    while p.exists():
        p, k = d / f"{name}.dup{k}", k + 1
    return p


def supersede(run_dir, levels=None, reason="", log=None, dry_run=False) -> dict:
    run = Path(run_dir)
    cdir = run / "chunks"
    tgt = run / f"chunks_superseded_{dt.date.today().isoformat()}"
    levels = set(levels) if levels else None
    moved: dict[str, int] = {}
    files = sorted(cdir.iterdir()) if cdir.is_dir() else []
    for f in files:
        lv = chunk_level(f.name)
        if lv is None or (levels is not None and lv not in levels):
            continue
        if f.name.endswith(".done.json"):
            moved[lv] = moved.get(lv, 0) + 1
        if not dry_run:
            tgt.mkdir(exist_ok=True)
            shutil.move(str(f), str(_dest(tgt, f.name)))
    n_asm = 0
    if moved:
        for a in ASSEMBLED:
            if (run / a).exists():
                n_asm += 1
                if not dry_run:
                    (tgt / "assembled").mkdir(parents=True, exist_ok=True)
                    shutil.move(str(run / a), str(_dest(tgt / "assembled", a)))
    if log and not dry_run:
        with open(log, "a") as fh:
            what = ", ".join(f"{k} {v}" for k, v in sorted(moved.items())) or "nothing"
            fh.write(f"| `{run}` | {what} | {sum(moved.values())} | {n_asm} | {reason} |\n")
    return {"run": str(run), "moved_done_chunks": moved, "assembled": n_asm, "target": str(tgt)}


def guard_final(pd_dir, stage, cfg_path, run_dir, new_level, new_mode="run", log=None) -> bool:
    """C*-changed guard for a final stage (L3_Cstar, L4_Cstar, N3_Cstar, ...), called by the
    pipelines' gen_cstar step BEFORE the new config is written. If the stage is marked done but
    the existing config's level (e.g. L3+C1) or the reuse decision (stage_<s>.reuse) differs from
    the new one, the stage markers are removed so the stage reruns. When the stage runs itself
    (new_mode 'run'), chunks of any other level in run_dir are moved aside. Returns True when
    the stage was reset."""
    import yaml
    pdir, cfg = Path(pd_dir), Path(cfg_path)
    done, reuse = pdir / f"stage_{stage}.done", pdir / f"stage_{stage}.reuse"
    old_level = None
    if cfg.exists():
        runs = (yaml.safe_load(cfg.read_text()) or {}).get("runs") or []
        old_level = runs[0]["level"] if runs else None
    old_mode = f"reuse:{reuse.read_text().strip()}" if reuse.exists() else "run"
    reset = done.exists() and (old_level != new_level or old_mode != new_mode)
    if reset:
        done.unlink()
        reuse.unlink(missing_ok=True)
    if new_mode == "run" and (Path(run_dir) / "chunks").is_dir():
        other = {chunk_level(f.name) for f in (Path(run_dir) / "chunks").iterdir()} - {None, new_level}
        if other:
            supersede(run_dir, other, f"C* changed: {old_level} -> {new_level}", log)
    elif reset and old_mode == "run":
        supersede(run_dir, None, f"C* changed: {old_level} -> {new_level} (now {new_mode})", log)
    if reset:
        print(f"guard: stage {stage} reset ({old_level}/{old_mode} -> {new_level}/{new_mode})")
    return reset


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--levels", nargs="*", default=None)
    ap.add_argument("--reason", default="")
    ap.add_argument("--log", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    print(supersede(a.run_dir, a.levels, a.reason, a.log, a.dry_run))


if __name__ == "__main__":
    main()
