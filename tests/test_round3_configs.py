"""Round-3 (EXP-B) configs: copies of the seed-0 configs except the declared keys
(docs/methods/round3_runs.md)."""
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/run"))
import round3_configs as R3  # noqa: E402

CHANGED = {"exp_name", "seeds", "horizons", "threads", "test_years"}


def _y(stem):
    p = ROOT / "configs" / f"{stem}.yaml"
    if not p.exists():
        pytest.skip(f"{p.name} not generated here")
    return yaml.safe_load(p.read_text())


@pytest.mark.parametrize("cell", list(R3.SEED_CELLS))
def test_seed_configs_are_copies(cell):
    src, _, roles, years, _ = R3.SEED_CELLS[cell]
    for s in (1, 2):
        for role in roles:
            a, b = _y(f"{src}{role}"), _y(R3.seed_stem(cell, s, role))
            assert {k: v for k, v in a.items() if k not in CHANGED} == \
                {k: v for k, v in b.items() if k not in CHANGED}
            assert b["seeds"] == [s] and b["horizons"] == [1, 4] and b["threads"] == 4
            assert b["test_years"] == (years or a["test_years"])
            assert set(a["test_years"]) <= set(b["test_years"])


def test_cstar_only_cells_skip_l3_l4():
    for cell in ("tw_s5", "pe_s5"):
        assert R3.SEED_CELLS[cell][2] == R3.CSTAR_ONLY
        assert not (ROOT / "configs" / f"{R3.seed_stem(cell, 1, 'L3')}.yaml").exists()


def test_tuned_grid_and_levels():
    for lvl in ("L3", "L4"):
        r = _y(f"colombia_s1_r3_tuned_{lvl}_Cstar")["runs"][0]
        assert r["level"] == f"{lvl}+C1" and "params_from" not in r
        g = r["tune"]["grid"]
        assert g == {"num_leaves": [15, 31, 127], "min_data_in_leaf": [100, 1000, 5000],
                     "feature_fraction": [0.3, 0.9]}
        assert r["params"]["num_boost_round"] == 400


def test_nohist_controls_candidates():
    y = _y("colombia_s2_nohist_controls_2019")
    assert [r["level"] for r in y["runs"]] == ["N3", "N3+C2", "N3+C3", "N3+C4", "N3+C4s"]
    assert y["split"]["name"] == "S2" and y["test_years"] == [2019] and y["seeds"] == [0, 1, 2]
    assert all(r["params_from"].endswith("colombia_s1_baselines/tuning_lgbm-L1.json") for r in y["runs"])


def test_manifest_order():
    ids = [it["id"] for it in R3.items() if not it["id"].startswith("r3a_")]
    assert ids[:3] == ["r3_co_s1_seeds", "r3_co_s2_seeds", "r3_br_s5_seeds"]
    assert ids[-1] == "r3_tw_s1_seeds"
    for it in R3.items():
        for k, n, arg in it["stages"]:
            if k == "run":
                assert arg == f"configs/{n}.yaml"
