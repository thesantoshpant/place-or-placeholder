#!/usr/bin/env python
"""Invalidate the outputs affected by the control fixes of 2026-11-16 (deviations rows 13-15).

  python scripts/run/invalidate_control_fixes.py [--only NAME ...] [--skip NAME ...] [--dry-run]

NAME = pipeline name, e.g. brazil_s2, peru_s1_shared, colombia_s1, brazil_s1_nohist. Per pipeline
(runs/<NAME>/ holds its stage markers):
  * controls_2019 run (own, not a reuse): chunks of L3+C3 and L3+C4 (N-arm: N3+C3, N3+C4), plus
    L3+C1 in S2-S4, go to chunks_superseded_<date>/ (scripts/run/supersede.py); the old
    selection.{json,csv,md} go there too. Markers controls_2019/select_control/gen_cstar and
    PIPELINE_DONE are removed; the controls_2019 config is rewritten (now with C4s).
  * final L3_Cstar/L4_Cstar (N3_Cstar/N4_Cstar) whose C* is C3 or C4, or C1 in S2-S4: all chunks
    moved aside and markers removed. N-arm N3_C1/N4_C1 in S2-S3: the same.
  * finals with an unaffected C* are kept; gen_cstar keeps them if C* does not change.
Every move is logged to runs/queue/invalidation_2026-11-16.md. Run only while no process works
on these pipelines.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from supersede import supersede  # noqa: E402

LOG = Path("runs/queue/invalidation_2026-11-16.md")
PIPES = ["brazil_s1_shared", "peru_s1_shared", "taiwan_s1_shared", "colombia_s1_shared",
         "brazil_s2", "brazil_s3", "brazil_s4", "brazil_s5",
         "colombia_s2", "colombia_s3", "colombia_s4", "colombia_s5", "peru_s5", "taiwan_s5",
         "colombia_s1", "peru_s1", "taiwan_s1",
         "brazil_s1_nohist", "brazil_s2_nohist", "brazil_s3_nohist"]


def split_of(name: str) -> str:
    return name.split("_")[1].upper()  # S1..S5


def regen_controls(name: str) -> str:
    c, rest = name.split("_", 1)
    if name.endswith("_nohist"):
        cmd = ["bash", "scripts/run/nohist_pipeline.sh", rest.split("_")[0], "--gen-controls"]
    elif rest == "s1":
        cmd = ["bash", "scripts/run/s1_pipeline.sh", c, "--gen-controls"]
    else:
        cmd = ["bash", "scripts/run/split_pipeline.sh", c, rest, "--gen-controls"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"{' '.join(cmd)} failed:\n{r.stdout}\n{r.stderr}")
    return r.stdout.strip().splitlines()[-1]


def rm(p: Path, dry, notes):
    if p.exists():
        notes.append(f"rm {p.name}")
        if not dry:
            p.unlink()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--skip", nargs="*", default=[])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    dry = a.dry_run
    if not LOG.exists() and not dry:
        LOG.write_text("# Invalidation log, control fixes 2026-11-16\n\n"
                       "Deviations rows 13-15 (docs/plans/deviations_from_protocol.md); method notes in "
                       "docs/methods/controls.md, section \"Control fixes 2026-11-16\". Nothing was "
                       "deleted: chunks moved to `<run>/chunks_superseded_2026-11-16/` (assembled "
                       "outputs and old selection files under it too).\n\n"
                       "| Run | Superseded `.done` chunks by level | n | assembled files | Reason |\n"
                       "|---|---|---|---|---|\n")
    names = [n for n in (a.only or PIPES) if n not in a.skip]
    for name in names:
        pd_ = Path("runs") / name
        if not pd_.exists():
            print(f"{name}: no pipeline dir, nothing to do")
            continue
        S = split_of(name)
        nohist = name.endswith("_nohist")
        b3 = "N3" if nohist else "L3"
        spatial = S in ("S2", "S3", "S4")
        notes = []
        plan = {}
        if (pd_ / "plan.json").exists():
            import json
            plan = json.loads((pd_ / "plan.json").read_text())
        # ---- controls_2019
        ctrl_reuse = str(plan.get("controls_2019", "run")).startswith("reuse:")
        cdir = Path("runs") / f"{name}_controls_2019"
        if not ctrl_reuse:
            levels = [f"{b3}+C3", f"{b3}+C4"] + ([f"{b3}+C1"] if spatial and not nohist else [])
            if cdir.exists() and not dry:
                supersede(cdir, levels, f"{', '.join(levels)} affected (fixes 13-15)", LOG)
                tgt = cdir / "chunks_superseded_2026-11-16"
                for f in ("selection.json", "selection.csv", "selection.md"):
                    if (cdir / f).exists():
                        tgt.mkdir(exist_ok=True)
                        shutil.move(str(cdir / f), str(tgt / f))
            for m in ("controls_2019", "select_control", "gen_cstar"):
                rm(pd_ / f"stage_{m}.done", dry, notes)
            if (pd_ / "stage_gen_configs.done").exists() and not dry:
                notes.append(regen_controls(name))
        else:
            for m in ("gen_cstar",):  # C* is re-read from the reused (rerun) selection
                rm(pd_ / f"stage_{m}.done", dry, notes)
        rm(pd_ / "PIPELINE_DONE", dry, notes)
        # ---- finals
        finals = [f"{b3}_Cstar", f"{'N4' if nohist else 'L4'}_Cstar"]
        for st in finals:
            cfg = Path("configs") / f"{name}_{st}.yaml"
            lev = yaml.safe_load(cfg.read_text())["runs"][0]["level"] if cfg.exists() else None
            k = lev.split("+")[1] if lev else None
            reuse = pd_ / f"stage_{st}.reuse"
            if k is None:
                continue
            if k in ("C3", "C4") or (k == "C1" and spatial):
                rd = Path("runs") / f"{name}_{st}"
                if reuse.exists():
                    notes.append(f"{st}: was reuse of {reuse.read_text().strip()} (C*={k}); markers cleared")
                elif rd.exists() and not dry:
                    supersede(rd, None, f"final C* = {k} affected (fixes 13-15)", LOG)
                rm(pd_ / f"stage_{st}.done", dry, notes)
                rm(reuse, dry, notes)
            else:
                notes.append(f"{st}: C*={k} unaffected, kept")
        if nohist and S in ("S2", "S3"):
            for st in ("N3_C1", "N4_C1"):
                rd = Path("runs") / f"{name}_{st}"
                if rd.exists() and not dry:
                    supersede(rd, None, "C1 in S2-S3 affected (fix 14)", LOG)
                rm(pd_ / f"stage_{st}.done", dry, notes)
        print(f"{name}: {'; '.join(notes) or 'nothing'}")
        if not dry:
            with open(LOG, "a") as fh:
                fh.write(f"| `runs/{name}/` (pipeline) | markers: {'; '.join(notes) or 'none'} | | | |\n")


if __name__ == "__main__":
    main()
