#!/usr/bin/env bash
# Experiment queue = ONE global priority scheduler (scripts/run/scheduler.py), since 2026-11-16.
# It replaces the four fixed lanes pop_q{A,B,C,D} and the separate pop_nohist session.
#
#   bash scripts/run/queue.sh launch     # start tmux pop_sched (the scheduler loop) if not running
#   bash scripts/run/queue.sh status     # tiers, items, current stage, workers held, unclaimed chunks
#   bash scripts/run/queue.sh eta        # event simulation of the queue -> ETA per item and tier
#   bash scripts/run/queue.sh stop       # stop the scheduler loop only (items and workers keep running)
#
# Priority tiers (high -> low; list order within a tier), see docs/methods/split_pipeline.md:
#   T1 BR S1-shared; PE/TW S1-shared; CO S1-shared (CO S1 per-level retired 2026-11-16b); TW S1-BRparams
#   T2 BR S1 extra seeds (sens_seeds); S5 BR/CO/PE/TW; CO S2/S3/S4; BR S2; BR S3
#   T3 no-history BR S1, then BR S2 (S3 dropped)
#   T4 BR S1 sensitivity: yearly_ref origin, report_delay 2, controls panel C3/C6; TW S1 L2 shared params
#   T5 BR S4
# Each item is one pipeline in tmux pop_q_<item> (split_pipeline.sh / nohist_pipeline.sh with
# POP_SCHED=1); the scheduler alone starts run_experiment.py workers (4 threads each; budget = 64 - 2 - others (incl. own non-pipeline jobs), cap 60
# threads, 52 while other users use > 4 cores; pin with BUDGET=<threads> in runs/queue/override.env).
# Log: runs/queue/scheduler.log; snapshot runs/queue/state/snapshot.json.
set -uo pipefail
ROOT=/net/home/spant/0-100/group-research/place-or-placeholder
cd "$ROOT" || exit 1
source env.sh
QD=runs/queue
mkdir -p "$QD/state"

case ${1:-} in
  launch)
    if tmux has-session -t pop_sched 2>/dev/null; then echo "pop_sched already running"; exit 0; fi
    tmux new-session -d -s pop_sched \
      "cd $ROOT && source env.sh && python scripts/run/scheduler.py run >> $ROOT/$QD/scheduler.log 2>&1"
    echo "started pop_sched (log $QD/scheduler.log)";;
  status) python scripts/run/scheduler.py status;;
  eta) python scripts/run/scheduler.py eta "${@:2}";;
  stop) tmux kill-session -t pop_sched 2>/dev/null && echo "stopped pop_sched (items keep running)";;
  *) sed -n 2,22p "$0"; exit 1;;
esac
