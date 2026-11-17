#!/usr/bin/env bash
# Pipeline for one (country, split) of the spatial / leaky / cross-country splits.
#
#   bash scripts/run/split_pipeline.sh <country> <split> [--workers N] [--threads T]  # own tmux
#   bash scripts/run/split_pipeline.sh <country> <split> --gen-only   # write the base configs only
#   bash scripts/run/split_pipeline.sh <country> <split> --gen-controls  # rewrite controls_2019 only
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
#   controls_2019   L3 + C1 (not S5), C2, C5, C3 x3 seeds, C4 x3 seeds, C4s x3 seeds at the 2019 origin
#   select_control  scripts/run/select_control.py -> runs/<c>_<s>_controls_2019/selection.json
#   gen_cstar       configs/<c>_<s>_{L3,L4}_Cstar.yaml (1 seed, also when C* is C3/C4/C4s). If C*
#                   (or the s1_shared reuse decision) differs from the existing final config, the
#                   L3_Cstar/L4_Cstar markers are cleared and old-C* chunks moved aside
#                   (scripts/run/supersede.py guard_final; control fixes 2026-11-16).
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
# Brazil S1 sensitivity items (global scheduler 2026-11-16), country = brazil, horizons {1, 4},
# shared Brazil params (L1 json), threads 4, test years 2020-24; outputs runs/brazil_s1_sens_<stage>/,
# configs configs/brazil_s1_sens_<stage>.yaml, pipeline state runs/brazil_s1_<split>/:
#   sens_seeds  seed{1,2}_{L3,L4,L3_Cstar,L4_Cstar}: the shared runs with seed 1 / 2 (C* = the BR
#               S1-shared selection; needs runs/brazil_s1_shared/stage_gen_cstar.done)
#   sens_yref   yref_{L3,L4}: yearly_ref = origin
#   sens_delay  delay2_{L3,L4}: report_delay = 2 (case history only up to origin - 2)
#   sens_ctrl   ctrl_{L3,L4}_{C3,C6}: controls panel on the test years
# C4s rule (2026-11-16): C4s range = min(D, fitted C4 range); where that equals the fitted range
# (Peru, Taiwan) C4s is identical to C4 and is not a C* candidate (docs/methods/controls.md).
# Workers: with POP_SCHED=1 (set by scripts/run/scheduler.py) a run stage starts no workers itself:
# it writes runs/<item>/current_cfg, waits until every chunk of the config is done (workers are
# started by the global scheduler), then runs one final pass (assembly). Standalone: --workers N
# or WORKERS=N in runs/<c>_<s>/override.env (read at each stage start).
# One pipeline per item: --inside takes a flock on runs/<item>/.pipeline.lock.
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
  brazil/sens_seeds|brazil/sens_yref|brazil/sens_delay|brazil/sens_ctrl) ;;
  colombia/l2_shared|peru/l2_shared|taiwan/l2_shared) ;;
  *) echo "unsupported pair $C $TOK"; exit 1;;
esac
WORKERS=2; THREADS=4; MODE=launch
while (( $# )); do
  case $1 in
    --workers) WORKERS=$2; shift 2;;
    --threads) THREADS=$2; shift 2;;
    --inside) MODE=inside; shift;;
    --gen-only) MODE=gen; shift;;
    --gen-controls) MODE=genctl; shift;;
    *) echo "unknown arg $1"; exit 1;;
  esac
done
PD=runs/${C}_${TOK}
CP=${C}_${TOK}_   # config / run-dir prefix of the stages
case $TOK in
  sens_seeds) SENS_STAGES="seed1_L3 seed1_L4 seed1_L3_Cstar seed1_L4_Cstar seed2_L3 seed2_L4 seed2_L3_Cstar seed2_L4_Cstar";;
  sens_yref) SENS_STAGES="yref_L3 yref_L4";;
  sens_delay) SENS_STAGES="delay2_L3 delay2_L4";;
  sens_ctrl) SENS_STAGES="ctrl_L3_C3 ctrl_L4_C3 ctrl_L3_C6 ctrl_L4_C6";;
  l2_shared) SENS_STAGES="L2";;
  *) SENS_STAGES="";;
esac
if [[ -n $SENS_STAGES ]]; then PD=runs/brazil_s1_${TOK}; CP=brazil_s1_sens_; fi
if [[ $TOK == l2_shared ]]; then PD=runs/${C}_s1_l2shared; CP=${C}_s1_shared_; fi
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
         "s1_shared": "S1"}.get(tok, "S1")
TEST = {"brazil": [2020, 2021, 2022, 2023, 2024], "colombia": [2020, 2021, 2022],
        "peru": [2020, 2021, 2022, 2023], "taiwan": [2020, 2022, 2023, 2024]}[c]
# Shared-params rule (primary, 2026-11-16): ONE hyperparameter set per country, the S1 L1 tuning
# at the 2019 origin, used for every level and control (no re-tuning). BR/CO S0-S4 and S1-shared:
# the country's own L1 json. TW S0, all S5 and s1brp: Brazil's L1 json (127 leaves / 100).
L1JSON = lambda country: f"runs/{country}_s1_baselines/tuning_lgbm-L1.json"  # noqa: E731
PCOUNTRY = c if (tok in ("s2", "s3", "s4", "s1_shared", "l2_shared") or (tok == "s0" and c != "taiwan")) else "brazil"
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


def c4s_rng(country):
    # C4s range = min(D, fitted C4 range) (rule 2026-11-16; docs/methods/controls.md)
    from pop.features.controls import c4s_range
    return min(c4s_range(country.upper()), c4_range(country))


def c4s_is_c4(country):  # min(D, fitted) = fitted -> C4s is identical to C4 (Peru, Taiwan)
    return c4s_rng(country) == c4_range(country)


def ckw():
    r = ({k.upper(): c4_range(k) for k in ("brazil", "colombia", "peru", "taiwan")}
         if tok == "s5" else c4_range(c))
    rs = ({k.upper(): c4s_rng(k) for k in ("brazil", "colombia", "peru", "taiwan")}
          if tok == "s5" else c4s_rng(c))
    return {"C1": {"c1_period": "auto"}, "C4": {"range_km": r}, "C4s": {"range_km": rs}}


SEEDED = ("C3", "C4", "C4s")


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


def cstar_configs(k, modes=None):
    seeded = k in SEEDED
    import sys as _s
    _s.path.insert(0, "scripts/run")
    from supersede import guard_final
    for lvl in ("L3", "L4"):  # C*-changed guard before the config is overwritten
        guard_final(f"runs/{c}_{tok}", f"{lvl}_Cstar", f"configs/{c}_{tok}_{lvl}_Cstar.yaml",
                    f"runs/{c}_{tok}_{lvl}_Cstar", f"{lvl}+{k}", (modes or {}).get(f"{lvl}_Cstar", "run"),
                    log="runs/queue/invalidation_guard.md")
    for lvl in ("L3", "L4"):
        # 1 seed even for C3/C4 (scope cut 2026-11-16); the 2019 selection keeps 3 seeds
        write(f"{lvl}_Cstar", base(f"{lvl}_Cstar", TEST, [0],
              [lg(f"{lvl}+{k}", seeded)], {**FEAT, "alphaearth": AE, "control_kw": ckw()}),
              f"LightGBM {lvl}+C* with C* = {k}")


def controls_config():
    runs = [lg("L3")]
    for k in ("C1", "C2", "C5", "C3", "C4", "C4s"):
        if k == "C1" and SPLIT == "S5":
            continue  # C1 is not defined when the test country has no training units
        if k == "C4s" and c4s_is_c4(c):
            # C4s = C4 here (min(D, fitted) = fitted): not a separate candidate. In S5 the rule is
            # judged for the held-out (scored) country (2026-11-16b): PE/TW S5 drop C4s.
            continue
        runs.append(lg(f"L3+{k}", k in SEEDED))
    write("controls_2019", base("controls_2019", [2019], SEEDS3, runs,
          {**FEAT, "alphaearth": AE, "control_kw": ckw()}),
          "choice of C* on the 2019 origin only (C3/C4/C4s 3 seeds)")


if what == "sens" and tok == "l2_shared":  # L2 rung with the shared (L1) params, S1 h1-h4, 1 seed
    d = yaml.safe_load(Path(f"configs/{c}_s1_shared_L3.yaml").read_text())
    d["exp_name"] = f"{c}_s1_shared_L2"
    d["seeds"] = [0]
    d["runs"] = [lg("L2")]
    assert d["runs"][0]["params_from"] == f"runs/{c}_s1_baselines/tuning_lgbm-L1.json"
    hdr = (f"# {CU.title()} S1 ladder: L2 with the shared {c} L1 params (rung added 2026-11-16b)\n"
           "# Generated by scripts/run/split_pipeline.sh from configs/<c>_s1_shared_L3.yaml; h1-h4; 1 seed; 4 threads.\n")
    Path(f"configs/{c}_s1_shared_L2.yaml").write_text(hdr + yaml.safe_dump(d, sort_keys=False))
    print("wrote", f"configs/{c}_s1_shared_L2.yaml")
elif what == "sens":  # Brazil S1 sensitivity items: copies of the S1-shared configs
    SY = [2020, 2021, 2022, 2023, 2024]

    def src(n):
        return yaml.safe_load(Path(f"configs/brazil_s1_shared_{n}.yaml").read_text())

    def sens(stage, d, note):
        d.update(exp_name=f"brazil_s1_sens_{stage}", horizons=[1, 4], threads=4, test_years=SY)
        assert all(r["params_from"] == PF for r in d["runs"]), d["runs"]
        hdr = (f"# Brazil S1 sensitivity ({tok}): {note}\n# Generated by scripts/run/split_pipeline.sh "
               "from configs/brazil_s1_shared_*.yaml; shared Brazil L1 params; horizons 1, 4; 4 threads.\n")
        Path(f"configs/brazil_s1_sens_{stage}.yaml").write_text(hdr + yaml.safe_dump(d, sort_keys=False))
        print("wrote", f"configs/brazil_s1_sens_{stage}.yaml")

    if tok == "sens_seeds":
        assert Path("runs/brazil_s1_shared/stage_gen_cstar.done").exists(), "BR S1-shared C* not chosen yet"
        for s in (1, 2):
            for n in ("L3", "L4", "L3_Cstar", "L4_Cstar"):
                d = src(n)
                d["seeds"] = [s]
                sens(f"seed{s}_{n}", d, f"{d['runs'][0]['level']} with seed {s} (extra seed of brazil_s1_shared_{n})")
    elif tok in ("sens_yref", "sens_delay"):
        for n in ("L3", "L4"):
            d = src(n)
            d["seeds"] = [0]
            if tok == "sens_yref":
                d["features"]["yearly_ref"] = "origin"
                sens(f"yref_{n}", d, f"{n} with yearly_ref = origin")
            else:
                d["features"]["report_delay"] = 2
                sens(f"delay2_{n}", d, f"{n} with report_delay = 2 (case history up to origin - 2)")
    elif tok == "sens_ctrl":
        feat = src("controls_2019")["features"]
        for lvl in ("L3+C3", "L4+C3", "L3+C6", "L4+C6"):
            d = base(lvl.replace("+", "_"), SY, [0], [lg(lvl, lvl.endswith("C3"))], feat)
            sens(f"ctrl_{lvl.replace('+', '_')}", d, f"controls panel, {lvl} (seed 0)")
elif what == "controls":
    controls_config()
elif what == "base":
    write("L3", base("L3", TEST, [0], [lg("L3")], FEAT), "LightGBM L3")
    write("L4", base("L4", TEST, [0], [lg("L4")], {**FEAT, "alphaearth": AE}),
          "LightGBM L4 (L3 + AlphaEarth y-1, renormalised)")
    if tok == "s1brp":
        cstar_configs("C1")
    else:
        controls_config()
    if tok == "s1_shared":  # reuse an existing S1 run wherever its params already equal L1's
        r = lambda ok, d: f"reuse:{d}" if ok else "run"  # noqa: E731
        l3 = same_as_l1("L3")
        l3dir = f"runs/{c}_s1_L3"
        if not l3 and c == "brazil" and best("runs/brazil_s1_L2/tuning_lgbm-L2.json") == best(PF):
            l3, l3dir = True, "runs/brazil_s1_L3_leaves127"  # L3 already run with the L1/L2 params
        # controls_2019 always runs in its own dir (2026-11-16b: the per-level CO S1 controls had
        # NaN C4/C4s; valid per-level chunks may be copied in beforehand, see
        # runs/queue/invalidation_2026-11-16b.md)
        plan_set(L1_params=best(PF), L3=r(l3, l3dir), L4=r(same_as_l1("L4"), f"runs/{c}_s1_L4"),
                 controls_2019="run")
else:
    pl = json.loads(PLAN.read_text()) if PLAN.exists() else {}
    cdir = pl.get("controls_2019", "run")
    cdir = cdir[6:] if cdir.startswith("reuse:") else f"runs/{c}_{tok}_controls_2019"
    k = json.loads(Path(cdir, "selection.json").read_text())["c_star"]
    kw = {}
    if tok == "s1_shared":
        s1sel = Path(f"runs/{c}_s1_controls_2019/selection.json")  # may be rerunning (2026-11-16)
        s1k = json.loads(s1sel.read_text())["c_star"] if s1sel.exists() else None
        kw = {"c_star": k, "c_star_s1_perlevel": s1k}
        for lvl in ("L3", "L4"):
            # reuse only a finished per-level S1 run whose config really is <lvl>+C* (2026-11-16)
            pcfg = Path(f"configs/{c}_s1_{lvl}_Cstar.yaml")
            plev = (yaml.safe_load(pcfg.read_text())["runs"][0]["level"] if pcfg.exists() else None)
            ok = (plev == f"{lvl}+{k}" and same_as_l1(lvl) and Path(f"runs/{c}_s1_{lvl}_Cstar").exists()
                  and Path(f"runs/{c}_s1/stage_{lvl}_Cstar.done").exists()
                  and not Path(f"runs/{c}_s1/stage_{lvl}_Cstar.done").read_text().startswith("PAUSE"))
            kw[f"{lvl}_Cstar"] = f"reuse:runs/{c}_s1_{lvl}_Cstar" if ok else "run"
    cstar_configs(k, kw)
    if tok == "s1_shared":
        plan_set(**kw)
EOF
}

if [[ $MODE == gen ]]; then gen_configs base; exit $?; fi
if [[ $MODE == genctl ]]; then gen_configs controls; exit $?; fi

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
  local WORKERS=$WORKERS
  [[ -f $PD/override.env ]] && source "$PD/override.env"
  echo "$WORKERS"
}
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
run_cfg() {  # $1 = stage name (config configs/<CP><stage>.yaml)
  local cfg=configs/${CP}$1.yaml rd=runs/${CP}$1
  local pat="[r]un_experiment.py $cfg "
  mkdir -p "$rd"
  if [[ -n ${POP_SCHED:-} ]]; then sched_run "$cfg" "$rd"; return; fi
  # run_experiment processes left running on this config by an earlier pipeline (lane handover)
  # keep their flock claims; they count as workers here, and new processes only add the rest.
  # (pgrep counts the parent and its pool workers, so workers ~ count - 1.)
  local left lw=0; left=$(pgrep -u "$(id -u)" -fc "$pat")
  (( left > 0 )) && { lw=$((left - 1)); say "$left earlier run_experiment processes on $cfg (~$lw workers) keep running"; }
  local cur=$lw want pids=() n=0 rc=0 p
  start_proc() {  # $1 = workers
    python scripts/run/run_experiment.py "$cfg" --workers "$1" --threads "$THREADS" \
      >> "$rd/stdout$( (( n > 0 )) && echo ".helper$n").log" 2>&1 9>&- &
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
    >> "$rd/stdout.log" 2>&1 9>&-
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
exec 9> "$PD/.pipeline.lock"
if ! flock -n 9; then say "another pipeline holds $PD/.pipeline.lock; exiting"; exit 3; fi
rm -f "$PD/PIPELINE_FAILED" "$PD/PIPELINE_DONE" "$PD/current_cfg"
say "pipeline start (${POP_SCHED:+global scheduler}${POP_SCHED:-standalone})"
if [[ -n $SENS_STAGES ]]; then
  stage gen_configs gen_configs sens
  for s in $SENS_STAGES; do stage "$s" run_cfg "$s"; done
  date '+%F %T' > "$PD/PIPELINE_DONE"
  say "pipeline done"
  exit 0
fi
# (2026-11-16b) CO S1-shared no longer waits for the per-level pop_s1_colombia pipeline (stopped;
# per-level CO S1 params equal the L1 params, so CO S1 runs once, here).
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
