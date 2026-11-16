"""Run a config-driven experiment.

    python scripts/run/run_experiment.py configs/<name>.yaml                    # serial (default)
    python scripts/run/run_experiment.py configs/<name>.yaml --workers 8 --threads 4

``--workers N`` runs chunks in N forked worker processes (each chunk is claimed with a file lock,
so several invocations on the same run dir never compute the same chunk; rerun to resume).
``--threads T`` overrides the config's ``threads`` (LightGBM threads per chunk). LightGBM output
depends on T, so keep T fixed across every level/control that will be compared.
"""
import argparse
import os
import sys

import yaml

ap = argparse.ArgumentParser()
ap.add_argument("config")
ap.add_argument("--root", default=".")
ap.add_argument("--workers", type=int, default=1, help="parallel chunk workers (default 1 = serial)")
ap.add_argument("--threads", type=int, default=None, help="threads per chunk (default: config)")
ap.add_argument("--start-method", default="fork", choices=["fork", "spawn"])
args = ap.parse_args()
threads = str(args.threads or yaml.safe_load(open(args.config)).get("threads", 16))
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[v] = threads  # set before numpy/lightgbm import

import logging  # noqa: E402

from pop.runner import run_experiment  # noqa: E402

logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format="%(asctime)s %(levelname)s %(processName)s %(message)s")
print(run_experiment(args.config, root=args.root, workers=args.workers, threads=args.threads,
                     start_method=args.start_method))
