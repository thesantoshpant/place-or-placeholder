#!/usr/bin/env bash
# Round-3 post hoc runs (EXP-B, docs/methods/round3_runs.md): stage loop of ONE tier-T6 item.
#
#   bash scripts/run/r3_pipeline.sh <item> --inside [--workers N]   # (scheduler: POP_SCHED=1)
#
# Items and their stages come from scripts/run/round3_configs.py (`list`, `stages <item>`):
#   run <stem> <cfg>   run_experiment.py on configs/<stem>.yaml (with POP_SCHED=1 the workers come
#                      from scripts/run/scheduler.py; this script waits, then one assembly pass)
#   py  <name> <args>  python <args> (tuning only, C* selection, C* config generation)
# Stage markers runs/r3/<item>/stage_<name>.done; PIPELINE_DONE / PIPELINE_FAILED; log pipeline.log.
# Configs are written beforehand by `round3_configs.py gen`. --inside takes a flock on
# runs/r3/<item>/.pipeline.lock (one pipeline per item).
set -uo pipefail
ROOT=/net/home/spant/0-100/group-research/place-or-placeholder
cd "$ROOT" || exit 1
source env.sh

ITEM=${1:?usage: r3_pipeline.sh <item> --inside [--workers N]}
shift
WORKERS=2; THREADS=4
while (( $# )); do
  case $1 in
    --workers) WORKERS=$2; shift 2;;
    --inside) shift;;
    *) echo "unknown arg $1"; exit 1;;
  esac
done
PD=$(python scripts/run/round3_configs.py pd "$ITEM") || { echo "unknown item $ITEM"; exit 1; }
mkdir -p "$PD"
mapfile -t STAGES < <(python scripts/run/round3_configs.py stages "$ITEM")
(( ${#STAGES[@]} )) || { echo "no stages for $ITEM"; exit 1; }

say() { echo "$(date '+%F %T') [$ITEM] $*"; }
fail() { say "FAILED at stage $1"; echo "stage $1 failed $(date '+%F %T')" > "$PD/PIPELINE_FAILED"; exit 1; }
sched_run() {  # $1 = config, $2 = run dir: workers come from scripts/run/scheduler.py
  local cfg=$1 rd=$2 rem stem; stem=$(basename "$cfg" .yaml)
  local pat="[r]un_experiment.py $cfg "
  echo "$cfg" > "$PD/current_cfg.tmp" && mv "$PD/current_cfg.tmp" "$PD/current_cfg"
  say "scheduled stage $cfg (workers from the global scheduler)"
  while :; do
    if [[ -f runs/queue/state/failed_$stem ]]; then
      say "scheduler marked $cfg failed (runs/queue/state/exits.log)"; rm -f "$PD/current_cfg"; return 1
    fi
    rem=$(python scripts/run/scheduler.py remaining "$cfg" 9>&-)
    [[ $rem == 0 ]] && ! pgrep -u "$(id -u)" -f "$pat" >/dev/null && break
    sleep 30
  done
  rm -f "$PD/current_cfg"
  say "final pass $cfg (assembly)"
  python scripts/run/run_experiment.py "$cfg" --workers 1 --threads "$THREADS" >> "$rd/stdout.log" 2>&1 9>&-
}
run_cfg() {  # $1 = config path
  local cfg=$1 rd
  [[ -f $cfg ]] || { say "missing config $cfg"; return 1; }
  rd=runs/$(python -c "import yaml,sys; print(yaml.safe_load(open(sys.argv[1]))['exp_name'])" "$cfg")
  mkdir -p "$rd"
  if [[ -n ${POP_SCHED:-} ]]; then sched_run "$cfg" "$rd"; return; fi
  say "run $cfg (workers $WORKERS, threads $THREADS)"
  nice -n 19 python scripts/run/run_experiment.py "$cfg" --workers "$WORKERS" --threads "$THREADS" \
    >> "$rd/stdout.log" 2>&1 9>&-
}
stage() {  # $1 = name, rest = command
  local n=$1; shift
  if [[ -f $PD/stage_$n.done ]]; then say "skip $n (done)"; return 0; fi
  say "start $n"
  "$@" || fail "$n"
  date '+%F %T' > "$PD/stage_$n.done"
  say "done $n"
}
exec 9> "$PD/.pipeline.lock"
if ! flock -n 9; then say "another pipeline holds $PD/.pipeline.lock; exiting"; exit 3; fi
rm -f "$PD/PIPELINE_FAILED" "$PD/PIPELINE_DONE" "$PD/current_cfg"
say "pipeline start (${POP_SCHED:+global scheduler}${POP_SCHED:-standalone})"
for line in "${STAGES[@]}"; do
  read -r kind name arg <<< "$line"
  case $kind in
    run) stage "$name" run_cfg "$arg";;
    py) stage "$name" nice -n 19 python $arg 9>&-;;
    *) say "bad stage line: $line"; fail "$name";;
  esac
done
date '+%F %T' > "$PD/PIPELINE_DONE"
say "pipeline done"
