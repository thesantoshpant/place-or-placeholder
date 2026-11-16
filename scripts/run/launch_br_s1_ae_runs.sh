#!/usr/bin/env bash
# Launch the AlphaEarth-dependent Brazil S1 runs (only after the AlphaEarth data verification):
#   tmux pop_runner4 : configs/brazil_s1_L4.yaml            -> runs/brazil_s1_L4/
#   tmux pop_runner5 : configs/brazil_s1_controls_2019.yaml -> runs/brazil_s1_controls_2019/
# 16 threads each. Pre-flight checks: the L3 tuning file exists, the C4 range_km in the config
# matches a fresh fit (within 1%), at most one other runner session is active.
# Usage: bash scripts/run/launch_br_s1_ae_runs.sh [--force]
set -euo pipefail
ROOT=/net/home/spant/0-100/group-research/place-or-placeholder
cd "$ROOT"
source env.sh

FORCE=${1:-}
L3TUNE=runs/brazil_s1_L3/tuning_lgbm-L3.json
[[ -f $L3TUNE ]] || { echo "missing $L3TUNE (L3 tuning not finished)"; exit 1; }
[[ -f data/interim/alphaearth/brazil/verification_v1.json ]] || \
  { echo "AlphaEarth verification file missing"; [[ $FORCE == --force ]] || exit 1; }
for s in pop_runner4 pop_runner5; do
  if tmux has-session -t "$s" 2>/dev/null; then echo "tmux session $s already exists"; exit 1; fi
done
n_active=$(tmux ls 2>/dev/null | grep -c '^pop_runner' || true)
if (( n_active > 1 )) && [[ $FORCE != --force ]]; then
  echo "$n_active pop_runner sessions active; two more would exceed 3 x 16 threads (use --force)"
  exit 1
fi

# C4 range_km: re-fit on the renormalised 2017-2018 BR embeddings and compare with the config.
OMP_NUM_THREADS=8 python - <<'EOF'
import yaml
from pop.features import controls as C, levels as LV
cfg = yaml.safe_load(open("configs/brazil_s1_controls_2019.yaml"))
want = float(cfg["features"]["control_kw"]["C4"]["range_km"])
e = LV.Context(country="BRAZIL", options=cfg["features"]).embeddings()
r = C.fit_embedding_range(e[e.year.isin([2017, 2018])], C.load_unit_points())
print(f"C4 range_km: config {want:.2f}, refit {r:.2f}")
if abs(r - want) / want > 0.01:
    raise SystemExit("C4 range_km changed (AlphaEarth data changed?): update the config first")
EOF

for spec in "pop_runner4 configs/brazil_s1_L4.yaml runs/brazil_s1_L4" \
            "pop_runner5 configs/brazil_s1_controls_2019.yaml runs/brazil_s1_controls_2019"; do
  read -r sess cfg out <<<"$spec"
  mkdir -p "$out"
  tmux new-session -d -s "$sess" \
    "cd $ROOT && source env.sh && python scripts/run/run_experiment.py $cfg > $out/stdout.log 2>&1"
  echo "started $sess: $cfg -> $out (log $out/stdout.log, $out/run.log)"
done
echo "after pop_runner5 ends: python scripts/run/select_control.py runs/brazil_s1_controls_2019"
