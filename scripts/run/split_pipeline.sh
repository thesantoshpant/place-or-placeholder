#!/usr/bin/env bash
# Pipeline for one (country, split) of the spatial / leaky / cross-country splits.
#
#   bash scripts/run/split_pipeline.sh <country> <split> [--workers N] [--threads T]  # own tmux
#   bash scripts/run/split_pipeline.sh <country> <split> --gen-only   # write the base configs only
#   bash scripts/run/split_pipeline.sh <country> <split> --inside     # stage loop (tmux / queue)
#
# <split>: s0 | s2 | s3 | s4 | s5 (country = held-out country) | s1brp (Taiwan S1 sensitivity with
# Brazil's L1 params and C* = C1) | s1_shared (S1 rerun under the shared-params rule; a stage whose
# per-level S1 params already equal the L1 params reuses that S1 run, see runs/<c>_s1_shared/
# plan.json and stage_<name>.reuse). Valid pairs: brazil s0 s2 s3 s4 s5; colombia s0 s2 s3 s4 s5;
# peru s5; taiwan s0 s5 s1brp; any country s1_shared.
#
# Stages (skipped when runs/<c>_<s>/stage_<name>.done exists; run_experiment.py also resumes per
# chunk, so killing and relaunching is safe):
#   gen_configs     configs/<c>_<s>_{controls_2019,L3,L4}.yaml
#   controls_2019   L3 + C1 (not S5), C2, C5, C3 x3 seeds, C4 x3 seeds at the 2019 origin
#   select_control  scripts/run/select_control.py -> runs/<c>_<s>_controls_2019/selection.json
#   gen_cstar       configs/<c>_<s>_{L3,L4}_Cstar.yaml (1 seed, also when C* is C3 or C4)
#   L3, L4, L3_Cstar, L4_Cstar   all test years; h1-h4 for S1 (s1_shared, s1brp), h1 + h4 for
#                                the spatial splits S2-S5 (also in controls_2019)
# Scope cuts 2026-11-16: S0 is no longer queued; spatial splits use horizons {1, 4}; C* runs use
# one seed; S5 params = L1 of the largest training country (Brazil, or Colombia when Brazil is
# held out); C1 uses the matched leave-out (controls.py train_mode='matched').
# s1brp skips the controls stages (C* = C1 fixed).
# No tuning: ONE params set per country = its S1 L1 tuning (TW S0, s1brp: Brazil's L1; S5: the
# largest training country's L1 = Brazil's, Colombia's when Brazil is held out), for every level
# and control. Threads are always 4.
# Markers: runs/<c>_<s>/PIPELINE_DONE or PIPELINE_FAILED. Log: runs/<c>_<s>/pipeline.log.
# Workers: inside a queue lane (POP_LANE=A|B|C|D) the count comes from `queue.sh workers <lane>`,
# re-read at each stage start and every 20 s during a stage; when it rises, an extra
# run_experiment.py process is started on the same config (chunks are flock-claimed), followed by
# one final pass (leftover chunks + assembly) at the end of the stage. run_experiment.py processes
# already running on the config (left by a lane handover) are counted as workers, not waited out.
# Standalone: --workers N or WORKERS=N in
# runs/<c>_<s>/override.env.
set -uo pipefail
ROOT=/net/home/spant/0-100/group-research/place-or-placeholder
cd "$ROOT" || exit 1
source env.sh

C=${1:?usage: split_pipeline.sh <country> <split> [--workers N] [--inside|--gen-only]}
TOK=${2:?usage: split_pipeline.sh <country> <split>}
C=${C,,}; TOK=${TOK,,}
shift 2
case "$C/$TOK" in
  brazil/s0|brazil/s2|brazil/s3|brazil/s4|brazil/s5) ;;
  colombia/s0|colombia/s2|colombia/s3|colombia/s4|colombia/s5) ;;
  peru/s5|taiwan/s0|taiwan/s5|taiwan/s1brp) ;;
  brazil/s1_shared|colombia/s1_shared|peru/s1_shared|taiwan/s1_shared) ;;
  *) echo "unsupported pair $C $TOK"; exit 1;;
esac
WORKERS=2; THREADS=4; MODE=launch
while (( $# )); do
  case $1 in
    --workers) WORKERS=$2; shift 2;;
    --threads) THREADS=$2; shift 2;;
    --inside) MODE=inside; shift;;
    --gen-only) MODE=gen; shift;;
    *) echo "unknown arg $1"; exit 1;;
  esac
done
PD=runs/${C}_${TOK}
SESS=pop_${C}_${TOK}
mkdir -p "$PD"

gen_configs() {  # $1 = base | cstar
  python - "$C" "$TOK" "$1" <<'EOF'
import json, sys
from pathlib import Path
import yaml

c, tok, what = sys.argv[1:4]
CU = c.upper()
SPLIT = {"s0": "S0", "s2": "S2", "s3": "S3", "s4": "S4", "s5": "S5", "s1brp": "S1",
         "s1_shared": "S1"}[tok]
TEST = {"brazil": [2020, 2021, 2022, 2023, 2024], "colombia": [2020, 2021, 2022],
        "peru": [2020, 2021, 2022, 2023], "taiwan": [2020, 2022, 2023, 2024]}[c]
# Shared-params rule (primary, 2026-11-16): ONE hyperparameter set per country, the S1 L1 tuning
# at the 2019 origin, used for every level and control (no re-tuning). BR/CO S0-S4 and S1-shared:
# the country's own L1 json. TW S0, all S5 and s1brp: Brazil's L1 json (127 leaves / 100).
L1JSON = lambda country: f"runs/{country}_s1_baselines/tuning_lgbm-L1.json"  # noqa: E731
PCOUNTRY = c if (tok in ("s2", "s3", "s4", "s1_shared") or (tok == "s0" and c != "taiwan")) else "brazil"
if tok == "s5" and c == "brazil":  # S5: largest training country (2026-11-16)
    PCOUNTRY = "colombia"
PF = L1JSON(PCOUNTRY)
assert Path(PF).exists(), f"missing tuning {PF}"
best = lambda f: json.loads(Path(f).read_text())["best"]  # noqa: E731
# LST screen: on for CO/PE/TW (as their S1), off for Brazil (as its S1), on for S5 (mixed countries)
lst = tok == "s5" or c != "brazil"
FEAT = {"climate_lag_vars": ["tmean", "precip", "rh"], "yearly_ref": "target"}
if lst:
    FEAT["remote_sensing"] = {"lst_screen": True}
AE = {"weights": "w", "normalize": True}
SEEDS3 = [0, 1, 2]
# Scope cut 2026-11-16: spatial splits (S2-S5) score h1 and h4 only; S1 keeps h1-h4.
HORIZONS = [1, 4] if SPLIT in ("S2", "S3", "S4", "S5") else [1, 2, 3, 4]


def c4_range(country):
    if country == "brazil":  # fitted in configs/brazil_s1_controls_2019.yaml (2017-18 embeddings)
        y = yaml.safe_load(Path("configs/brazil_s1_controls_2019.yaml").read_text())
        return float(y["features"]["control_kw"]["C4"]["range_km"])
    return round(float(json.loads(Path(f"runs/{country}_s1/c4_range_km.json").read_text())["range_km"]), 2)


def ckw():
    r = ({k.upper(): c4_range(k) for k in ("brazil", "colombia", "peru", "taiwan")}
         if tok == "s5" else c4_range(c))
    return {"C1": {"c1_period": "auto"}, "C4": {"range_km": r}}


def base(name, test_years, seeds, runs, features):
    return {"exp_name": f"{c}_{tok}_{name}", "country": CU,
            "panel": "data/processed/panel_weekly_v1.parquet",
            "split": {"name": SPLIT, "folds": "all"}, "test_years": test_years, "tune_year": 2019,
            "horizons": HORIZONS, "quantiles": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
            "coverage_levels": [0.4, 0.8], "exclude_flag_gap": True, "seeds": seeds, "threads": 4,
            "features": features, "runs": runs}


def write(name, d, note):
    who = "held-out country" if SPLIT == "S5" else "country"
    hdr = (f"# {CU.title()} ({who}), split {SPLIT}" + (" (Brazil params sensitivity)" if tok == "s1brp" else "")
           + f": {note}\n# Generated by scripts/run/split_pipeline.sh. Params frozen from {PCOUNTRY} S1"
           f" (no re-tuning); LST screen {'on' if lst else 'off'}; 4 threads.\n")
    Path(f"configs/{c}_{tok}_{name}.yaml").write_text(hdr + yaml.safe_dump(d, sort_keys=False))
    print("wrote", f"configs/{c}_{tok}_{name}.yaml")


def lg(level, seeded=False):
    return {"model": "lgbm", "level": level, "name": f"lgbm-{level}", "seeded": seeded,
            "params_from": PF}


PLAN = Path(f"runs/{c}_{tok}/plan.json")


def plan_set(**kw):  # s1_shared: stage -> "run" | "reuse:<run dir>" (+ notes)
    d = json.loads(PLAN.read_text()) if PLAN.exists() else {}
    d.update(kw)
    PLAN.write_text(json.dumps(d, indent=1))


def same_as_l1(lvl):
    return best(f"runs/{c}_s1_{lvl}/tuning_lgbm-{lvl}.json") == best(PF)


def cstar_configs(k):
    seeded = k in ("C3", "C4")
    for lvl in ("L3", "L4"):
        # 1 seed even for C3/C4 (scope cut 2026-11-16); the 2019 selection keeps 3 seeds
        write(f"{lvl}_Cstar", base(f"{lvl}_Cstar", TEST, [0],
              [lg(f"{lvl}+{k}", seeded)], {**FEAT, "alphaearth": AE, "control_kw": ckw()}),
              f"LightGBM {lvl}+C* with C* = {k}")


if what == "base":
    write("L3", base("L3", TEST, [0], [lg("L3")], FEAT), "LightGBM L3")
    write("L4", base("L4", TEST, [0], [lg("L4")], {**FEAT, "alphaearth": AE}),
          "LightGBM L4 (L3 + AlphaEarth y-1, renormalised)")
    if tok == "s1brp":
        cstar_configs("C1")
    else:
        runs = [lg("L3")]
        for k in ("C1", "C2", "C5", "C3", "C4"):
            if k == "C1" and SPLIT == "S5":
                continue  # C1 is not defined when the test country has no training units
            runs.append(lg(f"L3+{k}", k in ("C3", "C4")))
        write("controls_2019", base("controls_2019", [2019], SEEDS3, runs,
              {**FEAT, "alphaearth": AE, "control_kw": ckw()}),
              "choice of C* on the 2019 origin only (C3/C4 3 seeds)")
    if tok == "s1_shared":  # reuse an existing S1 run wherever its params already equal L1's
        r = lambda ok, d: f"reuse:{d}" if ok else "run"  # noqa: E731
        l3 = same_as_l1("L3")
        l3dir = f"runs/{c}_s1_L3"
        if not l3 and c == "brazil" and best("runs/brazil_s1_L2/tuning_lgbm-L2.json") == best(PF):
            l3, l3dir = True, "runs/brazil_s1_L3_leaves127"  # L3 already run with the L1/L2 params
        plan_set(L1_params=best(PF), L3=r(l3, l3dir), L4=r(same_as_l1("L4"), f"runs/{c}_s1_L4"),
                 controls_2019=r(same_as_l1("L3"), f"runs/{c}_s1_controls_2019"))
else:
    pl = json.loads(PLAN.read_text()) if PLAN.exists() else {}
    cdir = pl.get("controls_2019", "run")
    cdir = cdir[6:] if cdir.startswith("reuse:") else f"runs/{c}_{tok}_controls_2019"
    k = json.loads(Path(cdir, "selection.json").read_text())["c_star"]
    cstar_configs(k)
    if tok == "s1_shared":
        s1k = json.loads(Path(f"runs/{c}_s1_controls_2019/selection.json").read_text())["c_star"]
        kw = {"c_star": k, "c_star_s1_perlevel": s1k}
        for lvl in ("L3", "L4"):
            ok = k == s1k and same_as_l1(lvl) and Path(f"runs/{c}_s1_{lvl}_Cstar").exists()
            kw[f"{lvl}_Cstar"] = f"reuse:runs/{c}_s1_{lvl}_Cstar" if ok else "run"
        plan_set(**kw)
EOF
}

if [[ $MODE == gen ]]; then gen_configs base; exit $?; fi

if [[ $MODE == launch ]]; then
  if tmux has-session -t "$SESS" 2>/dev/null; then echo "tmux session $SESS already exists"; exit 1; fi
  rm -f "$PD/PIPELINE_FAILED"
  tmux new-session -d -s "$SESS" \
    "bash $ROOT/scripts/run/split_pipeline.sh $C $TOK --inside --workers $WORKERS --threads $THREADS >> $ROOT/$PD/pipeline.log 2>&1"
  echo "started $SESS ($WORKERS workers x $THREADS threads); log $PD/pipeline.log"
  exit 0
fi

# ------------------------------------------------------------------ inside
say() { echo "$(date '+%F %T') [$C $TOK] $*"; }
fail() { say "FAILED at stage $1"; echo "stage $1 failed $(date '+%F %T')" > "$PD/PIPELINE_FAILED"; exit 1; }
want_workers() {
  if [[ -n ${POP_LANE:-} ]]; then
    bash "$ROOT/scripts/run/queue.sh" workers "$POP_LANE"
  else
    local WORKERS=$WORKERS
    [[ -f $PD/override.env ]] && source "$PD/override.env"
    echo "$WORKERS"
  fi
}
run_cfg() {  # $1 = config name
  local cfg=configs/${C}_${TOK}_$1.yaml rd=runs/${C}_${TOK}_$1
  local pat="[r]un_experiment.py $cfg "
  mkdir -p "$rd"
  # run_experiment processes left running on this config by an earlier pipeline (lane handover)
  # keep their flock claims; they count as workers here, and new processes only add the rest.
  # (pgrep counts the parent and its pool workers, so workers ~ count - 1.)
  local left lw=0; left=$(pgrep -u "$(id -u)" -fc "$pat")
  (( left > 0 )) && { lw=$((left - 1)); say "$left earlier run_experiment processes on $cfg (~$lw workers) keep running"; }
  local cur=$lw want pids=() n=0 rc=0 p
  start_proc() {  # $1 = workers
    python scripts/run/run_experiment.py "$cfg" --workers "$1" --threads "$THREADS" \
      >> "$rd/stdout$( (( n > 0 )) && echo ".helper$n").log" 2>&1 &
    pids+=($!); n=$((n + 1))
  }
  want=$(want_workers)
  if [[ $want =~ ^[0-9]+$ ]] && (( want > cur )); then
    say "run $cfg (workers $((want - cur)) new + $lw earlier, threads $THREADS)"
    start_proc $((want - cur)); cur=$want
  fi
  while pgrep -u "$(id -u)" -f "$pat" >/dev/null; do
    sleep 20
    pgrep -u "$(id -u)" -f "$pat" >/dev/null || break
    want=$(want_workers)
    local mem; mem=$(awk '/^MemAvailable/ {print int($2 / 1048576)}' /proc/meminfo)
    if [[ $want =~ ^[0-9]+$ ]] && (( want > cur && mem >= 12 )); then
      say "top-up: +$((want - cur)) workers on $cfg (now $want; MemAvailable ${mem} GiB)"
      start_proc $((want - cur)); cur=$want
    fi
  done
  for p in "${pids[@]}"; do wait "$p" || { rc=$?; say "run_experiment $p exited $rc"; }; done
  if (( n == 1 && lw == 0 )); then return $rc; fi
  # several processes (helpers, earlier ones) may have written the outputs concurrently: one
  # final pass computes anything left (e.g. chunks of a crashed process) and assembles
  want=$(want_workers); [[ $want =~ ^[0-9]+$ ]] || want=1
  say "final pass for $cfg (workers $want)"
  python scripts/run/run_experiment.py "$cfg" --workers "$want" --threads "$THREADS" \
    >> "$rd/stdout.log" 2>&1
}
plan_of() {  # s1_shared: run | reuse:<dir> (from runs/<c>_<s>/plan.json); others: run
  [[ -f $PD/plan.json ]] || { echo run; return; }
  python -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], 'run'))" "$PD/plan.json" "$1"
}
stage() {  # $1 = name, rest = command
  local n=$1; shift
  if [[ -f $PD/stage_$n.done ]]; then say "skip $n (done)"; return 0; fi
  local pl; pl=$(plan_of "$n")
  if [[ $pl == reuse:* ]]; then
    say "reuse $n: ${pl#reuse:} (same params as L1)"
    echo "${pl#reuse:}" > "$PD/stage_$n.reuse"; date '+%F %T' > "$PD/stage_$n.done"; return 0
  fi
  say "start $n"
  "$@" || fail "$n"
  date '+%F %T' > "$PD/stage_$n.done"
  say "done $n"
}
rm -f "$PD/PIPELINE_FAILED" "$PD/PIPELINE_DONE"
say "pipeline start (lane ${POP_LANE:-none})"
if [[ $C/$TOK == colombia/s1_shared ]]; then  # wait for the live per-level CO S1 pipeline
  while tmux has-session -t pop_s1_colombia 2>/dev/null; do sleep 120; done
fi
stage gen_configs gen_configs base
if [[ $TOK != s1brp ]]; then
  stage controls_2019 run_cfg controls_2019
  if [[ $(plan_of controls_2019) == run ]]; then
    stage select_control python scripts/run/select_control.py "runs/${C}_${TOK}_controls_2019"
  fi
  stage gen_cstar gen_configs cstar
fi
for s in L3 L4 L3_Cstar L4_Cstar; do stage "$s" run_cfg "$s"; done
date '+%F %T' > "$PD/PIPELINE_DONE"
say "pipeline done"
