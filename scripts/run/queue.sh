#!/usr/bin/env bash
# Four-lane queue for the split pipelines (scripts/run/split_pipeline.sh).
#
#   bash scripts/run/queue.sh launch       # start the tmux sessions pop_q{A,B,C,D} (skips running ones)
#   bash scripts/run/queue.sh status       # per-job markers + current worker counts
#   bash scripts/run/queue.sh workers A    # worker count lane A should use right now
#   bash scripts/run/queue.sh budget       # thread budget of the queue right now (+ why)
#   bash scripts/run/queue.sh lane A       # lane loop (what tmux runs)
#   bash scripts/run/queue.sh reap         # close old dead lane sessions whose processes have exited
#
# Lane A: BR S1-shared -> BR S4
# Lane C: BR S3 -> S5 with BR held out
# Lane D: BR S2
# Lane B: PE S1-shared -> TW S1-shared -> CO S4 -> CO S2 -> CO S3 -> S5 CO/PE/TW held out
#         -> TW S1-BRparams -> CO S1-shared (waits for pop_s1_colombia)
# Scope cuts 2026-11-16: S0 dropped; CO S4 before CO S2/S3. Throughput 2026-11-16: Brazil split
# over lanes A/C/D (was one lane), budget 60 threads, work-weighted shares (docs/methods/split_pipeline.md).
# Jobs with runs/<c>_<s>/PIPELINE_DONE are skipped; a failed job is logged and the lane moves on.
#
# Workers (4 threads each, always). Re-evaluated at every stage start and every 20 s inside a
# stage (split_pipeline.sh tops up with an extra process when the count rises; it never kills):
#   budget = 60 threads, or 52 while other users use > 4 cores (back to 60 below 3 cores),
#            minus 4 x WORKERS of every live pop_s1_<country> session (runs/<c>_s1/override.env)
#   budget/4 workers are split over the lanes not yet finished (no runs/queue/lane_<L>.done),
#   in proportion to the lane weights (remaining worker-hours), largest remainder, >= 1 each.
# Manual pins: <L>_WORKERS=N, weights W_<L>=x, BUDGET=threads in runs/queue/override.env.
set -uo pipefail
ROOT=/net/home/spant/0-100/group-research/place-or-placeholder
cd "$ROOT" || exit 1
QD=runs/queue
mkdir -p "$QD"

LANES=(A B C D)
LANE_A=("brazil s1_shared" "brazil s4")
LANE_C=("brazil s3" "brazil s5")
LANE_D=("brazil s2")
LANE_B=("peru s1_shared" "taiwan s1_shared" "colombia s4" "colombia s2" "colombia s3"
        "colombia s5" "peru s5" "taiwan s5" "taiwan s1brp" "colombia s1_shared")
# remaining worker-hours per lane at the 2026-11-16 13:30 handover (tmp/eta2.py, C* = C1)
W_A=135; W_B=95; W_C=93; W_D=98
FULL=60; FALLBACK=52; OTHERS_HI=400; OTHERS_LO=300   # threads; other users' %CPU thresholds

jobs_of() { local -n arr=LANE_$1; printf '%s\n' "${arr[@]}"; }

others_cpu() {  # %CPU of all non-spant users (top, 2 s sample), cached 60 s in $QD/others_cpu
  local f=$QD/others_cpu now; now=$(date +%s)
  if [[ -f $f ]] && (( now - $(stat -c %Y "$f") < 60 )); then cut -d' ' -f1 "$f"; return; fi
  (
    flock -n 9 || exit 0
    v=$(top -b -n 2 -d 2 -w 200 | awk '/^top -/{n++} n==2 && $1 ~ /^[0-9]+$/ && $2 != "spant" {s+=$9}
                                        END {printf "%d", s}')
    echo "${v:-0} $(date '+%F %T')" > "$f.tmp" && mv "$f.tmp" "$f"
  ) 9> "$QD/.others_cpu.lock"
  if [[ -f $f ]]; then cut -d' ' -f1 "$f"; else echo 0; fi
}

budget() {  # threads available to the queue; with "why" as $1 also prints the reasoning
  local BUDGET="" o b s n
  [[ -f $QD/override.env ]] && source "$QD/override.env"
  if [[ -n $BUDGET ]]; then b=$BUDGET
  else
    o=$(others_cpu)
    if [[ -f $QD/fallback ]]; then
      if (( o < OTHERS_LO )); then rm -f "$QD/fallback"; b=$FULL; else b=$FALLBACK; fi
    elif (( o > OTHERS_HI )); then date '+%F %T' > "$QD/fallback"; b=$FALLBACK
    else b=$FULL; fi
  fi
  local why="base $b (others ${o:-?}% CPU)"
  for s in colombia peru taiwan; do
    if tmux has-session -t "pop_s1_$s" 2>/dev/null; then
      n=3; [[ -f runs/${s}_s1/override.env ]] && n=$(sed -n 's/^WORKERS=//p' "runs/${s}_s1/override.env")
      b=$((b - 4 * ${n:-3})); why+=" - pop_s1_$s ${n:-3}x4"
    fi
  done
  (( b < 4 * ${#LANES[@]} )) && b=$((4 * ${#LANES[@]}))
  if [[ ${1:-} == why ]]; then echo "$b threads: $why"; else echo "$b"; fi
}

workers() {  # $1 = lane
  local L=$1 A_WORKERS="" B_WORKERS="" C_WORKERS="" D_WORKERS=""
  [[ -f $QD/override.env ]] && source "$QD/override.env"
  local pin=${L}_WORKERS
  if [[ -n ${!pin} ]]; then echo "${!pin}"; return; fi
  local n alive=() l
  n=$(( $(budget) / 4 ))
  for l in "${LANES[@]}"; do [[ -f $QD/lane_$l.done ]] || alive+=("$l"); done
  [[ " ${alive[*]} " == *" $L "* ]] || alive+=("$L")
  local spec=""; for l in "${alive[@]}"; do local w=W_$l; spec+="$l=${!w} "; done
  # largest-remainder split of n workers by weight, >= 1 per lane
  echo "$spec" | awk -v L="$L" -v n="$n" '
    { for (i = 1; i <= NF; i++) { split($i, p, "="); k[i] = p[1]; w[i] = p[2]; tot += p[2] }; m = NF }
    END { s = 0
          for (i = 1; i <= m; i++) { r = n * w[i] / tot; if (r < 1) r = 1; a[i] = int(r); f[i] = r - a[i]; s += a[i] }
          for (rest = n - s; rest > 0; rest--) {
            b = 0; for (i = 1; i <= m; i++) if (!(i in u) && (b == 0 || f[i] > f[b])) b = i
            if (b == 0) break; a[b]++; u[b] = 1 }
          for (i = 1; i <= m; i++) if (k[i] == L) print a[i] }'
}

reap() {  # close lane sessions renamed *_old at a handover once their process group is empty
  local s pg
  for s in $(tmux ls -F '#{session_name}' 2>/dev/null | grep -E '^pop_q[A-Z]_old'); do
    pg=$(tmux display -p -t "$s" '#{pane_pid}' 2>/dev/null) || continue
    if [[ -n $pg ]] && ! pgrep -g "$pg" >/dev/null 2>&1; then
      tmux kill-session -t "$s" && echo "$(date '+%F %T') reaped $s"
    fi
  done
}

lane() {  # $1 = lane
  local L=$1 job c s jobs
  mapfile -t jobs < <(jobs_of "$L")
  rm -f "$QD/lane_$L.done"
  echo "$(date '+%F %T') lane $L start: ${jobs[*]}"
  for job in "${jobs[@]}"; do
    read -r c s <<< "$job"
    reap
    if [[ -f runs/${c}_${s}/PIPELINE_DONE ]]; then echo "$(date '+%F %T') skip $job (done)"; continue; fi
    while pgrep -f "[s]plit_pipeline.sh $c $s " >/dev/null; do  # never two pipelines on one job
      echo "$(date '+%F %T') waiting: another split_pipeline.sh runs $job"; sleep 60
    done
    mkdir -p "runs/${c}_${s}"
    echo "$(date '+%F %T') start $job (workers now $(workers "$L"))"
    POP_LANE=$L bash scripts/run/split_pipeline.sh "$c" "$s" --inside >> "runs/${c}_${s}/pipeline.log" 2>&1
    if [[ -f runs/${c}_${s}/PIPELINE_DONE ]]; then echo "$(date '+%F %T') done $job"
    else echo "$(date '+%F %T') FAILED $job (see runs/${c}_${s}/pipeline.log)"; fi
  done
  date '+%F %T' > "$QD/lane_$L.done"
  reap
  echo "$(date '+%F %T') lane $L finished"
}

case ${1:-} in
  workers) workers "${2:?lane}";;
  budget) budget why;;
  reap) reap;;
  lane) lane "${2:?lane}";;
  launch)
    for L in "${LANES[@]}"; do
      if tmux has-session -t "pop_q$L" 2>/dev/null; then echo "pop_q$L already running"; continue; fi
      tmux new-session -d -s "pop_q$L" "bash $ROOT/scripts/run/queue.sh lane $L >> $ROOT/$QD/lane_$L.log 2>&1"
      echo "started pop_q$L (log $QD/lane_$L.log)"
    done;;
  status)
    budget why
    for L in "${LANES[@]}"; do
      echo "lane $L: workers $(workers "$L"); session $(tmux has-session -t "pop_q$L" 2>/dev/null && echo up || echo down)"
      mapfile -t jobs < <(jobs_of "$L")
      for job in "${jobs[@]}"; do
        read -r c s <<< "$job"; d=runs/${c}_${s}
        st=pending
        [[ -f $d/pipeline.log ]] && st="running: $(ls -t "$d"/stage_*.done 2>/dev/null | head -1 | sed 's/.*stage_//;s/.done//') done last"
        [[ -f $d/PIPELINE_FAILED ]] && st="FAILED ($(cat "$d/PIPELINE_FAILED"))"
        [[ -f $d/PIPELINE_DONE ]] && st=DONE
        echo "  $job: $st"
      done
    done
    echo "run_experiment processes (parents+pool workers) per config:"
    ps -u spant -o args= | grep '[r]un_experiment.py' | awk '{print $3}' | sort | uniq -c;;
  *) sed -n 2,28p "$0"; exit 1;;
esac
