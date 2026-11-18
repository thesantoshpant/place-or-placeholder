#!/usr/bin/env bash
# Sync code/docs between the laptop repo and the GPU working folder.
# The laptop is the only machine that talks to GitHub; the GPU holds data and runs jobs.
#   scripts/dev/sync_gpu.sh pull   # GPU -> laptop (after agents edit code on the GPU)
#   scripts/dev/sync_gpu.sh push   # laptop -> GPU (after editing locally / git pull)
# Data, outputs, venv, caches and tool binaries are never synced.
set -euo pipefail
REMOTE="spant@epyc2.knoxds.org:/net/home/spant/0-100/group-research/place-or-placeholder/"
LOCAL="$(cd "$(dirname "$0")/../.." && pwd)/"
SSH="ssh -o BatchMode=yes -J jumper@math.knox.edu"
FILTER=(--update --exclude=.git/ --exclude=.venv/ --exclude=.tools/ --exclude=.cache/ --exclude=/tmp/
        --exclude=/data/ --exclude=/outputs/ --exclude=/runs/ --exclude=__pycache__/ --exclude=.DS_Store --exclude=._* --exclude=.pytest_cache/ --exclude=*.egg-info/
        --exclude=/docs/results/review/cells/ --exclude=/docs/results/review/*_cells/ --exclude=/docs/results/review/*.parquet --exclude=/docs/results/review/RB_distance_unit*.csv)
case "${1:-}" in
  pull) rsync -av "${FILTER[@]}" -e "$SSH" "$REMOTE" "$LOCAL" ;;
  push) rsync -av "${FILTER[@]}" -e "$SSH" "$LOCAL" "$REMOTE" ;;
  *) echo "usage: $0 pull|push" >&2; exit 1 ;;
esac
