"""Run a config-driven experiment: python scripts/run/run_experiment.py configs/<name>.yaml"""
import argparse
import os
import sys

import yaml

ap = argparse.ArgumentParser()
ap.add_argument("config")
ap.add_argument("--root", default=".")
args = ap.parse_args()
threads = str(yaml.safe_load(open(args.config)).get("threads", 16))
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[v] = threads  # set before numpy/lightgbm import

import logging  # noqa: E402

from pop.runner import run_experiment  # noqa: E402

logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format="%(asctime)s %(levelname)s %(message)s")
print(run_experiment(args.config, root=args.root))
