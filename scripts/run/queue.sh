#!/usr/bin/env bash
# Two-lane queue for the split pipelines (scripts/run/split_pipeline.sh).
#
#   bash scripts/run/queue.sh launch       # start tmux sessions pop_qA and pop_qB
#   bash scripts/run/queue.sh status       # per-job markers + current worker counts
#   bash scripts/run/queue.sh workers A    # worker count lane A should use right now
#   bash scripts/run/queue.sh lane A       # lane loop (what tmux runs)
#
# Lane A (Brazil):  BR S1-shared -> BR S4 -> BR S3 -> BR S2 -> S5 with BR held out
# Lane B:           PE S1-shared -> TW S1-shared -> CO S4 -> CO S2 -> CO S3 -> S5 CO/PE/TW held out
#                   -> TW S1-BRparams -> CO S1-shared (waits for pop_s1_colombia)
# Scope cuts 2026-11-16: S0 dropped (BR, CO, TW); CO S4 moved before CO S2/S3.
# Jobs with runs/<c>_<s>/PIPELINE_DONE are skipped; a failed job is logged and the lane moves on.
#
# Workers (4 threads each, always): policy re-evaluated at every stage start and every 20 s
# inside a stage (split_pipeline.sh tops up with an extra process when the count rises):
#   any pop_s1_{colombia,peru,taiwan} tmux session alive -> budget 28 threads: A=5, B=2
#   otherwise                                             -> budget 52 threads: A=9, B=4
#   the other lane finished (runs/queue/lane_<X>.done)    -> this lane gets budget/4
# Manual pins: A_WORKERS=N / B_WORKERS=N in runs/queue/override.env (take precedence).
set -uo pipefail
ROOT=/net/home/spant/0-100/group-research/place-or-placeholder
cd "$ROOT" || exit 1
QD=runs/queue
mkdir -p "$QD"

LANE_A=("brazil s1_shared" "brazil s4" "brazil s3" "brazil s2" "brazil s5")
LANE_B=("peru s1_shared" "taiwan s1_shared" "colombia s4" "colombia s2" "colombia s3"
        "colombia s5" "peru s5" "taiwan s5" "taiwan s1brp" "colombia s1_shared")

s1_alive() {
  local s
  for s in pop_s1_colombia pop_s1_peru pop_s1_taiwan; do
    tmux has-session -t "$s" 2>/dev/null && return 0
  done
  return 1
}

workers() {  # $1 = A | B
  local L=$1 other budget A_WORKERS="" B_WORKERS=""
  [[ $L == A ]] && other=B || other=A
  [[ -f $QD/override.env ]] && source "$QD/override.env"
  local pin; [[ $L == A ]] && pin=$A_WORKERS || pin=$B_WORKERS
  if [[ -n $pin ]]; then echo "$pin"; return; fi
  if s1_alive; then budget=28; else budget=52; fi
  if [[ -f $QD/lane_$other.done ]]; then echo $((budget / 4)); return; fi
  if (( budget == 28 )); then [[ $L == A ]] && echo 5 || echo 2
  else [[ $L == A ]] && echo 9 || echo 4; fi
}

lane() {  # $1 = A | B
  local L=$1 jobs job c s
  if [[ $L == A ]]; then jobs=("${LANE_A[@]}"); else jobs=("${LANE_B[@]}"); fi
  rm -f "$QD/lane_$L.done"
  echo "$(date '+%F %T') lane $L start: ${jobs[*]}"
  for job in "${jobs[@]}"; do
    read -r c s <<< "$job"
    if [[ -f runs/${c}_${s}/PIPELINE_DONE ]]; then echo "$(date '+%F %T') skip $job (done)"; continue; fi
    mkdir -p "runs/${c}_${s}"
    echo "$(date '+%F %T') start $job (workers now $(workers "$L"))"
    POP_LANE=$L bash scripts/run/split_pipeline.sh "$c" "$s" --inside >> "runs/${c}_${s}/pipeline.log" 2>&1
    if [[ -f runs/${c}_${s}/PIPELINE_DONE ]]; then echo "$(date '+%F %T') done $job"
    else echo "$(date '+%F %T') FAILED $job (see runs/${c}_${s}/pipeline.log)"; fi
  done
  date '+%F %T' > "$QD/lane_$L.done"
  echo "$(date '+%F %T') lane $L finished"
}

case ${1:-} in
  workers) workers "${2:?lane}";;
  lane) lane "${2:?lane}";;
  launch)
    for L in A B; do
      if tmux has-session -t "pop_q$L" 2>/dev/null; then echo "pop_q$L already running"; continue; fi
      tmux new-session -d -s "pop_q$L" "bash $ROOT/scripts/run/queue.sh lane $L >> $ROOT/$QD/lane_$L.log 2>&1"
      echo "started pop_q$L (log $QD/lane_$L.log)"
    done;;
  status)
    for L in A B; do
      echo "lane $L: workers $(workers $L); session $(tmux has-session -t pop_q$L 2>/dev/null && echo up || echo down)"
      if [[ $L == A ]]; then jobs=("${LANE_A[@]}"); else jobs=("${LANE_B[@]}"); fi
      for job in "${jobs[@]}"; do
        read -r c s <<< "$job"; d=runs/${c}_${s}
        st=pending
        [[ -f $d/pipeline.log ]] && st="running: $(ls -t $d/stage_*.done 2>/dev/null | head -1 | sed 's/.*stage_//;s/.done//') done last"
        [[ -f $d/PIPELINE_FAILED ]] && st="FAILED ($(cat $d/PIPELINE_FAILED))"
        [[ -f $d/PIPELINE_DONE ]] && st=DONE
        echo "  $job: $st"
      done
    done;;
  *) sed -n 2,20p "$0"; exit 1;;
esac
