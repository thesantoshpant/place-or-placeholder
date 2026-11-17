"""Results kit: cell registry and completeness checks.

A *cell* is one analysis unit: four estimand roles (L3, L4, L3C, L4C -> run dirs), plus optional
extra ladder runs, the C* selection dir and stage markers. A role counts as complete only when
  (1) <run>/scores.parquet exists (written by the runner after the last chunk),
  (2) no file in <run>/chunks/ is newer than scores.parquet (else: stale, a rerun is going on),
  (3) its pipeline stage marker exists, when the cell names one and the pipeline dir exists
      (catches score files left behind by an invalidated stage).
Anything else is "pending"; partial runs are never read.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROLES = ("L3", "L4", "L3C", "L4C")
STAGE = {"L3": "L3", "L4": "L4", "L3C": "L3_Cstar", "L4C": "L4_Cstar"}
COUNTRY_CODE = {"brazil": "BR", "colombia": "CO", "peru": "PE", "taiwan": "TW"}


# ------------------------------------------------------------------ completeness
def run_state(d: str | Path, marker: str | Path | None = None) -> str:
    """'complete' | 'not started' | 'partial (n chunks)' | 'stale' | 'stage not done'."""
    d = Path(d)
    if not d.exists():
        return "not started"
    sc = d / "scores.parquet"
    ch = d / "chunks"
    n = len(list(ch.glob("*.done.json"))) if ch.is_dir() else 0
    if not sc.exists():
        return f"partial ({n} chunks)" if n else "not started"
    t = sc.stat().st_mtime
    if ch.is_dir() and any(p.stat().st_mtime > t + 1 for p in ch.iterdir() if p.is_file()):
        return "stale"
    if marker is not None:
        m = Path(marker)
        if m.parent.exists() and not m.exists():
            return "stage not done"
    return "complete"


def run_fingerprint(d: str | Path) -> list:
    p = Path(d) / "scores.parquet"
    s = p.stat()
    return [str(d), s.st_size, s.st_mtime_ns]


# ------------------------------------------------------------------ registry
def _plan(pdir: Path) -> dict:
    f = pdir / "plan.json"
    return json.loads(f.read_text()) if f.exists() else {}


SELECTION_RULE_VERSION = 2   # scripts/run/select_control.py RULE_VERSION
CSTAR_PENDING = "selection pending (stale)"
PRIMARY_HORIZONS = [1, 4]          # defaults; build_registry reads the manifest's values
SECONDARY_HORIZONS = [1, 2, 3, 4]


def selection_ok(sel_dir: Path | str) -> bool:
    """True only for a selection.json written under the current rule (rule_version 2)."""
    f = Path(sel_dir) / "selection.json"
    if not f.exists():
        return False
    try:
        return json.loads(f.read_text()).get("rule_version") == SELECTION_RULE_VERSION
    except (ValueError, OSError):
        return False


def _cstar(sel_dir: Path, plan: dict | None = None) -> str | None:
    """C* only from a rule_version-2 selection.json; anything else (missing file, older rule,
    plan.json c_star) -> None, shown as CSTAR_PENDING."""
    if not selection_ok(sel_dir):
        return None
    return json.loads((Path(sel_dir) / "selection.json").read_text()).get("c_star")


def cstar_label(cell: dict) -> str:
    if cell.get("cstar"):
        return cell["cstar"]
    if cell.get("selection") is None and cell.get("estimands"):
        return "n/a (no C* run)"
    return CSTAR_PENDING


def _role(d, marker=None):
    return {"dirs": [str(d)], "markers": [str(marker) if marker else None]}


def _pipeline_cell(cid, group, arm, country, split, desc, pdir, run_prefix, *, ref="L3",
                   plan_roles=True, ladder=(), note="", seeds=None):
    """Cell whose four roles live at runs/<run_prefix>_<stage> with markers in pdir."""
    pdir = Path(pdir)
    plan = _plan(pdir)
    roles = {}
    for r in ROLES:
        st = STAGE[r] if ref == "L3" else STAGE[r].replace("L", "N")
        d = f"{run_prefix}_{st}"
        p = plan.get(STAGE[r]) if plan_roles else None
        if isinstance(p, str) and p.startswith("reuse:"):
            d = p[len("reuse:"):]
        roles[r] = _role(d, pdir / f"stage_{st}.done")
    sel = Path(f"{run_prefix}_controls_2019")
    return {"id": cid, "group": group, "arm": arm, "country": country, "split": split,
            "desc": desc, "roles": roles, "ref": ref, "ladder": list(ladder),
            "selection": {"dir": str(sel), "marker": str(pdir / "stage_select_control.done")},
            "cstar": _cstar(sel, plan), "note": note, "estimands": None,
            "role_labels": None, "primary_horizons": list(PRIMARY_HORIZONS),
            "secondary_horizons": list(SECONDARY_HORIZONS) if split == "S1" else None}


def s1_ladder(country: str) -> list[dict]:
    """Extra ladder rungs L0-L2 for an S1 history cell."""
    return [{"label": "L0", "dir": f"runs/{country}_s1_baselines", "run": "naive-L0"},
            {"label": "L1", "dir": f"runs/{country}_s1_baselines", "run": "lgbm-L1"},
            {"label": "L2", "dir": f"runs/{country}_s1_L2", "run": "lgbm-L2"}]


def build_registry(manifest: str = "configs/primary_cells.yaml") -> list[dict]:
    global PRIMARY_HORIZONS, SECONDARY_HORIZONS
    cells = []
    man = yaml.safe_load(Path(manifest).read_text())
    PRIMARY_HORIZONS = sorted(int(h) for h in man.get("primary_horizons", [1, 4]))
    SECONDARY_HORIZONS = sorted(int(h) for h in man.get("secondary_horizons", [1, 2, 3, 4]))
    for c in man["cells"]:
        country, split = c["country"], c["split"]
        pdir = Path(c["plan"]).parent if c.get("plan") else Path(c["runs"]["L3"]).parent
        plan = _plan(pdir)
        roles = {}
        for r in ROLES:
            v = c["runs"][r]
            dirs = [v] if isinstance(v, str) else list(v)
            p = plan.get(STAGE[r])
            if isinstance(p, str) and p.startswith("reuse:"):
                dirs = [p[len("reuse:"):]] + dirs[1:]
            roles[r] = {"dirs": dirs, "markers": [str(pdir / f"stage_{STAGE[r]}.done")]
                        + [None] * (len(dirs) - 1)}
        l3 = c["runs"]["L3"]
        prefix = str(l3 if isinstance(l3, str) else l3[0]).rsplit("_L3", 1)[0]
        sel = Path(f"{prefix}_controls_2019")
        cells.append({
            "id": f"{COUNTRY_CODE[country]}_{split}", "group": "primary", "arm": "history",
            "country": country, "split": split,
            "desc": f"{country.title()} {split}, history arm (primary)",
            "roles": roles, "ref": "L3",
            "ladder": s1_ladder(country) if split == "S1" else [],
            "selection": {"dir": str(sel), "marker": str(pdir / "stage_select_control.done")},
            "cstar": _cstar(sel, plan), "note": "", "estimands": None, "role_labels": None,
            "primary_horizons": list(PRIMARY_HORIZONS),
            "secondary_horizons": list(SECONDARY_HORIZONS) if c.get("secondary") else None})
    by = {c["id"]: c for c in cells}

    # ---- secondary arms
    sec = []
    br = by.get("BR_S1")
    if br:
        # BR S1 with the 2 extra seeds (h1, h4) added to every role
        roles = {}
        for r in ROLES:
            st = STAGE[r]
            dirs = list(br["roles"][r]["dirs"])
            mk = list(br["roles"][r]["markers"])
            for k in (1, 2):   # skip seed runs the manifest already lists in BR_S1 (row 22)
                d = f"runs/brazil_s1_sens_seed{k}_{st}"
                if d not in dirs:
                    dirs.append(d)
                    mk.append(f"runs/brazil_s1_sens_seeds/stage_seed{k}_{st}.done")
            roles[r] = {"dirs": dirs, "markers": mk}
        sec.append({**br, "id": "BR_S1_3seeds", "group": "secondary", "arm": "sensitivity",
                    "desc": "Brazil S1, primary + 2 extra seeds (seed-averaged; extra seeds h1/h4)",
                    "roles": roles, "ladder": [], "selection": None})
        # yearly_ref: origin / report_delay 2: G_emb only (no C* run)
        for tok, desc in (("yref", "yearly features aligned to the origin year (strictly causal)"),
                          ("delay2", "2-week reporting delay")):
            grp = "yref" if tok == "yref" else "delay"
            l3 = _role(f"runs/brazil_s1_sens_{tok}_L3", f"runs/brazil_s1_sens_{grp}/stage_{tok}_L3.done")
            l4 = _role(f"runs/brazil_s1_sens_{tok}_L4", f"runs/brazil_s1_sens_{grp}/stage_{tok}_L4.done")
            sec.append({**br, "id": f"BR_S1_{tok}", "group": "secondary", "arm": "sensitivity",
                        "desc": f"Brazil S1 sensitivity: {desc} (G_emb only)",
                        "roles": {"L3": l3, "L4": l4, "L3C": l3, "L4C": l4}, "ladder": [],
                        "selection": None, "cstar": None, "estimands": ["G_emb"]})
        # controls panel on the test years
        for k in ("C3", "C6"):
            roles = {"L3": br["roles"]["L3"], "L4": br["roles"]["L4"],
                     "L3C": _role(f"runs/brazil_s1_sens_ctrl_L3_{k}",
                                  f"runs/brazil_s1_sens_ctrl/stage_ctrl_L3_{k}.done"),
                     "L4C": _role(f"runs/brazil_s1_sens_ctrl_L4_{k}",
                                  f"runs/brazil_s1_sens_ctrl/stage_ctrl_L4_{k}.done")}
            sec.append({**br, "id": f"BR_S1_ctrl{k}", "group": "secondary", "arm": "sensitivity",
                        "desc": f"Brazil S1 controls panel: {k} in place of C* (h1, h4)",
                        "roles": roles, "ladder": [], "selection": None, "cstar": k})
        # per-level tuning (old 31-leaf runs)
        sec.append({**br, "id": "BR_S1_perlevel", "group": "secondary", "arm": "sensitivity",
                    "desc": "Brazil S1, per-level tuning (L3/L4 31 leaves; superseded primary)",
                    "roles": {r: _role(f"runs/brazil_s1_{STAGE[r]}") for r in ROLES},
                    "ladder": s1_ladder("brazil"), "selection": {"dir": "runs/brazil_s1_controls_2019_C1fix",
                                                "marker": None},
                    "cstar": "C1"})
    # TW S1 with Brazil params
    sec.append(_pipeline_cell("TW_S1_BRparams", "secondary", "sensitivity", "taiwan", "S1",
                              "Taiwan S1 with Brazil's tuned params and C*", "runs/taiwan_s1brp",
                              "runs/taiwan_s1brp", plan_roles=False))
    sec[-1]["selection"] = None
    sec[-1]["cstar"] = by["BR_S1"]["cstar"] if "BR_S1" in by else None
    # no-history arm
    for s in ("s1", "s2"):
        cell = _pipeline_cell(f"BR_{s.upper()}_nohist", "secondary", "no-history", "brazil",
                              s.upper(), f"Brazil {s.upper()}, no-history arm (ref = N3)",
                              f"runs/brazil_{s}_nohist", f"runs/brazil_{s}_nohist", ref="N3",
                              plan_roles=False)
        cell["ladder"] = [{"label": "N2", "dir": f"runs/brazil_{s}_nohist_N2", "run": None,
                           "optional": True}] + [
            {"label": f"{lv}+C1", "dir": f"runs/brazil_{s}_nohist_{lv}_C1", "run": None,
             "marker": f"runs/brazil_{s}_nohist/stage_{lv}_C1.done"} for lv in ("N3", "N4")]
        cell["role_labels"] = {"L3": "N3", "L4": "N4", "L3C": "N3+C*", "L4C": "N4+C*"}
        sec.append(cell)
    return cells + sec


def cell_status(cell: dict) -> tuple[str, dict]:
    """('available' | 'pending', {role: state}) over the four roles."""
    st = {}
    for r in ROLES:
        rs = [run_state(d, m) for d, m in zip(cell["roles"][r]["dirs"], cell["roles"][r]["markers"])]
        bad = [f"{Path(d).name}: {s}" for d, s in zip(cell["roles"][r]["dirs"], rs) if s != "complete"]
        st[r] = "complete" if not bad else "; ".join(bad)
    return ("available" if all(v == "complete" for v in st.values()) else "pending"), st
