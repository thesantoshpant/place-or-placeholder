#!/usr/bin/env python
"""Global priority scheduler for the experiment queue (replaces the four fixed lanes, 2026-11-16).

    python scripts/run/scheduler.py run          # the loop (tmux pop_sched; scripts/run/queue.sh launch)
    python scripts/run/scheduler.py status       # items, tiers, current stage, workers held / target
    python scripts/run/scheduler.py remaining CFG   # chunks of CFG without .done.json (pipelines use it)
    python scripts/run/scheduler.py eta [--workers N]   # event simulation of the queue -> ETA per tier

Design (docs/methods/split_pipeline.md, "Global scheduler"):
* Items = one pipeline each (split_pipeline.sh / nohist_pipeline.sh / sensitivity items) in a
  priority list (tier T1 high .. T5 low, then list order). A pipeline keeps its stage order; in
  scheduled mode (POP_SCHED=1) it does not start workers itself: on entering a run stage it writes
  runs/<item>/current_cfg, waits until every chunk of that config has a .done.json, then runs one
  final assembly pass.
* This loop (every 20 s) is the only process that starts run_experiment.py workers for queue
  items. Budget = 60 threads (52 while other users use > 4 cores) / 4 threads = 15 workers, shared
  with every other run_experiment.py of this user (pop_s1_peru, pop_s1_colombia, leftovers).
  Workers held = in-flight chunks (live .lock files) per process tree, or the process's --workers
  during its first 5 minutes (data loading). Free workers go to items in priority order, each up to
  its current stage's unclaimed chunks; an item that is not started yet is started (tmux
  pop_q_<id>) when a worker is free for it.
* Flow to higher tiers (lossless preemption): when a higher-tier stage has had unmet demand for 2
  ticks and no worker is free, the scheduler "reserves" the unclaimed chunks of the lowest-priority
  running stage (it takes their flock, exactly as a worker would), so that stage's processes finish
  their in-flight chunks and then cannot claim new ones. Process trees with no in-flight chunk are
  then stopped (nothing is lost: no chunk is running) and the reservation is released. Completed
  chunks are never touched; results do not depend on which process computes a chunk.
* (2026-11-16b) The external CO S1 per-level item is retired (its C4/C4s were NaN; CO S1 runs once,
  via colombia_s1_shared). Budget: threads = 64 - 2 - (CPU of every process that is not one of our
  run_experiment.py workers, other users AND this user's other jobs) rounded down to a multiple
  of 4, capped at 60, floor 16; pin with BUDGET=<threads> in runs/queue/override.env.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import math
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path("/net/home/spant/0-100/group-research/place-or-placeholder")
QD = ROOT / "runs/queue"
SD = QD / "state"
THREADS = 4
FULL, FALLBACK, OTHERS_HI, OTHERS_LO = 60, 52, 400, 300  # threads; other users' %CPU thresholds
HW_THREADS, HEADROOM, FLOOR = 64, 2, 16  # budget = HW - HEADROOM - others (2026-11-16b)
TICK = 20
YOUNG = 300          # s: a process this young holds its full --workers (data loading)
MIN_MEM_GIB = 12
MAX_FAILS = 3        # non-signal failed exits of scheduler-started processes per config
UID = os.getuid()

SPLIT_STAGES = ["controls_2019", "L3", "L4", "L3_Cstar", "L4_Cstar"]
NOHIST_STAGES = ["controls_2019", "N3", "N4", "N3_Cstar", "N4_Cstar", "N3_C1", "N4_C1"]
SENS_STAGES = {
    "sens_seeds": [f"seed{s}_{l}" for s in (1, 2) for l in ("L3", "L4", "L3_Cstar", "L4_Cstar")],
    "sens_yref": ["yref_L3", "yref_L4"],
    "sens_delay": ["delay2_L3", "delay2_L4"],
    "sens_ctrl": ["ctrl_L3_C3", "ctrl_L4_C3", "ctrl_L3_C6", "ctrl_L4_C6"],
}


@dataclass
class Item:
    id: str
    tier: int
    kind: str                 # split | nohist | sens | external
    pd: str                   # pipeline state dir (runs/...)
    cfg_prefix: str           # configs/<cfg_prefix><stage>.yaml
    stages: list
    cmd: str = ""             # pipeline command (scheduled mode)
    blocked: object = None    # () -> reason or None
    session: str = ""
    st: dict = field(default_factory=dict)


def _sess(name):
    return subprocess.run(["tmux", "has-session", "-t", name], capture_output=True).returncode == 0


def split_item(c, tok, tier, blocked=None):
    st = SPLIT_STAGES[1:] if tok == "s1brp" else SPLIT_STAGES
    return Item(f"{c}_{tok}", tier, "split", f"runs/{c}_{tok}", f"{c}_{tok}_", st,
                f"bash {ROOT}/scripts/run/split_pipeline.sh {c} {tok} --inside", blocked)


def nohist_item(s, tier):
    return Item(f"brazil_{s}_nohist", tier, "nohist", f"runs/brazil_{s}_nohist", f"brazil_{s}_nohist_",
                NOHIST_STAGES, f"bash {ROOT}/scripts/run/nohist_pipeline.sh {s} --inside")


def sens_item(tok, tier, blocked=None):
    return Item(f"brazil_s1_{tok}", tier, "sens", f"runs/brazil_s1_{tok}", "brazil_s1_sens_",
                SENS_STAGES[tok], f"bash {ROOT}/scripts/run/split_pipeline.sh brazil {tok} --inside",
                blocked)


def _need(path, why):
    return lambda: None if (ROOT / path).exists() else why


def items() -> list[Item]:
    L = [
        # T1
        split_item("brazil", "s1_shared", 1),
        split_item("peru", "s1_shared", 1),
        split_item("taiwan", "s1_shared", 1),
        split_item("colombia", "s1_shared", 1),
        split_item("taiwan", "s1brp", 1),
        # T2
        sens_item("sens_seeds", 2, _need("runs/brazil_s1_shared/stage_gen_cstar.done",
                                         "waits for the BR S1-shared C* (gen_cstar)")),
        split_item("brazil", "s5", 2), split_item("colombia", "s5", 2),
        split_item("peru", "s5", 2), split_item("taiwan", "s5", 2),
        split_item("colombia", "s2", 2), split_item("colombia", "s3", 2),
        split_item("colombia", "s4", 2),
        split_item("brazil", "s2", 2), split_item("brazil", "s3", 2),
        # T3 (no-history arm; S3 dropped 2026-11-16)
        nohist_item("s1", 3), nohist_item("s2", 3),
        # T4
        sens_item("sens_yref", 4), sens_item("sens_delay", 4), sens_item("sens_ctrl", 4),
        # S1 ladder L2 rung with the shared params (2026-11-16b; only Taiwan's per-level L2 params
        # differ from its L1 params; CO/PE per-level L2 already equal L1, BR L2 = 127/100)
        Item("taiwan_s1_l2shared", 4, "sens", "runs/taiwan_s1_l2shared", "taiwan_s1_shared_", ["L2"],
             f"bash {ROOT}/scripts/run/split_pipeline.sh taiwan l2_shared --inside"),
        # T5
        split_item("brazil", "s4", 5),
    ]
    for it in L:
        if not it.session:
            it.session = f"pop_q_{it.id}"
    return L


# ------------------------------------------------------------------ configs, chunks, processes
_cfg_cache: dict = {}


def cfg_info(cfg: str):
    """(run dir, chunk names) of a config, cached by mtime; also written to state/tasks/."""
    p = ROOT / cfg
    m = p.stat().st_mtime
    hit = _cfg_cache.get(cfg)
    if hit and hit[0] == m:
        return hit[1], hit[2]
    import yaml
    y = yaml.safe_load(p.read_text())
    rd = ROOT / y.get("runs_dir", "runs") / y["exp_name"]
    tf = SD / "tasks" / f"{p.stem}.txt"
    if tf.exists() and tf.stat().st_mtime >= m:
        names = tf.read_text().split()
    else:
        from pop.runner import chunk_tasks, load_config
        names = [t[0] for t in chunk_tasks(load_config(str(p)))]
        tf.parent.mkdir(parents=True, exist_ok=True)
        tf.write_text("\n".join(names) + "\n")
    _cfg_cache[cfg] = (m, rd, names)
    return rd, names


def _alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def chunk_state(rd: Path, names):
    """(done, live locks {name: pid}) for a run dir."""
    cdir = rd / "chunks"
    done, locks = set(), {}
    if not cdir.exists():
        return done, locks
    for e in os.scandir(cdir):
        n = e.name
        if n.endswith(".done.json"):
            done.add(n[:-10])
        elif n.endswith(".lock"):
            try:
                pid = int(json.loads(Path(e.path).read_text() or "{}").get("pid", 0))
            except (ValueError, OSError):
                pid = 0
            if pid and pid != os.getpid() and _alive(pid):
                locks[n[:-5]] = pid
    for n in list(locks):
        if n in done:
            del locks[n]
    return done & set(names), locks


def remaining(cfg: str) -> int:
    rd, names = cfg_info(cfg)
    done, _ = chunk_state(rd, names)
    return len(set(names) - done)


def procs():
    """Top-level run_experiment.py processes of this user: list of dicts (pid, cfg, workers, age,
    tree pids)."""
    out = subprocess.run(["ps", "-u", str(UID), "-o", "pid=,ppid=,etimes=,args="],
                         capture_output=True, text=True).stdout
    rows = {}
    for line in out.splitlines():
        parts = line.split(None, 3)
        if len(parts) < 4 or "run_experiment.py" not in parts[3] or "python" not in parts[3].split()[0]:
            continue
        args = parts[3].split()
        try:
            cfg = args[args.index(next(a for a in args if a.endswith("run_experiment.py"))) + 1]
        except (StopIteration, IndexError):
            continue
        w = int(args[args.index("--workers") + 1]) if "--workers" in args else 1
        rows[int(parts[0])] = dict(pid=int(parts[0]), ppid=int(parts[1]), age=int(parts[2]), cfg=cfg,
                                   workers=w)
    tops = {}
    for pid, r in rows.items():
        top = pid
        while rows.get(top, {}).get("ppid") in rows:
            top = rows[top]["ppid"]
        t = tops.setdefault(top, dict(rows[top], tree=set()))
        t["tree"].add(pid)
    return list(tops.values())


def mem_avail_gib():
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable"):
            return int(line.split()[1]) / 1048576
    return 0.0


def others_cpu():
    f = QD / "others_cpu"
    try:
        if time.time() - f.stat().st_mtime < 60:
            return int(f.read_text().split()[0])
    except (OSError, ValueError, IndexError):
        pass
    # -c: full command lines. Everything except our own run_experiment.py workers counts as
    # "others": other users and this user's other jobs (audit 3 H-2, 2026-11-16b).
    out = subprocess.run(["top", "-b", "-c", "-n", "2", "-d", "2", "-w", "512"], capture_output=True,
                         text=True).stdout
    n, s = 0, 0.0
    for line in out.splitlines():
        if line.startswith("top -"):
            n += 1
            continue
        p = line.split()
        if n == 2 and p and p[0].isdigit() and len(p) > 11:
            if p[1] == "spant" and "run_experiment.py" in line:
                continue
            try:
                s += float(p[8])
            except ValueError:
                pass
    f.write_text(f"{int(s)} {time.strftime('%F %T')}\n")
    return int(s)


def budget():
    """(threads, why). Pins: BUDGET=<threads> in runs/queue/override.env."""
    ov = QD / "override.env"
    if ov.exists():
        m = re.search(r"^BUDGET=(\d+)", ov.read_text(), re.M)
        if m:
            return int(m.group(1)), "pinned in override.env"
    o = others_cpu()
    b = HW_THREADS - HEADROOM - int(math.ceil(o / 100.0))
    b = max(FLOOR, min(FULL, (b // THREADS) * THREADS))
    return b, f"others {o}% CPU (incl. own non-pipeline jobs)"


# ------------------------------------------------------------------ item state
def item_state(it: Item):
    pd = ROOT / it.pd
    if it.kind == "external":
        if not _sess(it.session):
            return "done" if (pd / "PIPELINE_DONE").exists() else "stopped"
        return "running"
    if (pd / "PIPELINE_DONE").exists():
        return "done"
    if _sess(it.session):
        return "running"
    if (pd / "PIPELINE_FAILED").exists() and (pd / ".sched_started").exists():
        return "failed"
    b = it.blocked() if it.blocked else None
    if b:
        return "blocked: " + b
    return "pending"


def current_cfg(it: Item, tops):
    pd = ROOT / it.pd
    if it.kind == "external":  # the config its own processes work on, else its next run stage
        for t in tops:
            if t["cfg"].startswith(f"configs/{it.cfg_prefix}") and \
                    Path(t["cfg"]).stem[len(it.cfg_prefix):] in it.stages:
                return t["cfg"]
        return None
    f = pd / "current_cfg"
    if f.exists():
        c = f.read_text().strip()
        return c if (ROOT / c).exists() else None
    return None


class Reservation:
    """flocks held on unclaimed chunks of one config (lossless drain of that stage)."""

    def __init__(self, cfg):
        self.cfg, self.fds, self.t0 = cfg, [], time.time()
        rd, names = cfg_info(cfg)
        done, locks = chunk_state(rd, names)
        (rd / "chunks").mkdir(parents=True, exist_ok=True)
        for n in names:
            if n in done or n in locks:
                continue
            p = rd / "chunks" / f"{n}.lock"
            fd = os.open(p, os.O_CREAT | os.O_RDWR, 0o644)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:  # a worker claimed it just now
                os.close(fd)
                continue
            if (rd / "chunks" / f"{n}.done.json").exists():
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
                continue
            self.fds.append(fd)

    def release(self):
        for fd in self.fds:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)
        self.fds = []


def log(msg):
    print(f"{time.strftime('%F %T')} {msg}", flush=True)


def kill_tree(t):
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in sorted(t["tree"], reverse=True):
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
        time.sleep(2)


# ------------------------------------------------------------------ the loop
def exits_failed(cfg, since):
    f = SD / "exits.log"
    if not f.exists():
        return 0
    n = 0
    for line in f.read_text().splitlines():
        p = line.split()
        if len(p) >= 3 and p[1] == cfg and float(p[0]) >= since:
            rc = int(p[2].split("=")[1])
            n += 0 < rc < 128
    return n


def launch_workers(cfg, rd, n):
    rd.mkdir(parents=True, exist_ok=True)
    cmd = (f"cd {ROOT} && source env.sh && python scripts/run/run_experiment.py {cfg} --workers {n} "
           f"--threads {THREADS} >> {rd}/stdout.sched.log 2>&1; rc=$?; "
           f"echo \"$(date +%s) {cfg} rc=$rc\" >> {SD}/exits.log")
    subprocess.Popen(["setsid", "bash", "-c", cmd], cwd=ROOT, stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


_not_started: set = set()


def launch_item(it: Item):
    pd = ROOT / it.pd
    pd.mkdir(parents=True, exist_ok=True)
    pat = it.cmd.split("scripts/run/")[1]  # e.g. split_pipeline.sh brazil s2 --inside
    r = subprocess.run(["pgrep", "-u", str(UID), "-f", "[" + pat[0] + "]" + pat[1:]], capture_output=True)
    if r.returncode == 0:
        if it.id not in _not_started:
            log(f"not starting {it.id}: a pipeline process for it is already running")
            _not_started.add(it.id)
        return False
    (pd / ".sched_started").write_text(time.strftime("%F %T\n"))
    env = {k: v for k, v in os.environ.items() if k not in ("TMUX", "TMUX_PANE")}
    subprocess.run(["tmux", "new-session", "-d", "-s", it.session,
                    f"cd {ROOT} && source env.sh && POP_SCHED=1 {it.cmd} >> {ROOT}/{it.pd}/pipeline.log 2>&1"],
                   check=True, env=env)
    log(f"started item {it.id} (tier T{it.tier}) in tmux {it.session}")
    return True


def reap_old():
    """Close the retired lane sessions (pop_qA..D_old, pop_nohist_old) once no live
    run_experiment.py is left in their process group (handover 2026-11-16): every process of the
    group (pane shell, stopped pipeline shells) is then killed and the session closed."""
    out = subprocess.run(["tmux", "ls", "-F", "#{session_name} #{pane_pid}"], capture_output=True,
                         text=True).stdout
    for line in out.splitlines():
        name, _, pid = line.partition(" ")
        if not re.fullmatch(r"pop_q[A-D]_old|pop_nohist_old", name) or not pid.isdigit():
            continue
        out = subprocess.run(["ps", "-g", pid, "-o", "pid=,stat=,args="], capture_output=True,
                             text=True).stdout.splitlines()
        if any("run_experiment.py" in l and " Z" not in f" {l.split()[1]}" for l in out if len(l.split()) > 2):
            continue
        for l in out:
            try:
                os.kill(int(l.split()[0]), signal.SIGKILL)
            except (ProcessLookupError, ValueError, IndexError):
                pass
        subprocess.run(["tmux", "kill-session", "-t", name], capture_output=True)
        if True:
            log(f"reaped retired session {name}")


def snapshot(L, tops):
    """Per config: held workers (busy chunks per tree, young trees count their --workers)."""
    by_cfg = {}
    for t in tops:
        by_cfg.setdefault(t["cfg"], []).append(t)
    held, unclaimed, busy_tree = {}, {}, {}
    cfgs = set(by_cfg)
    cur = {it.id: current_cfg(it, tops) for it in L}
    cfgs |= {c for c in cur.values() if c}
    for cfg in cfgs:
        try:
            rd, names = cfg_info(cfg)
        except Exception as e:  # noqa: BLE001
            log(f"cannot read {cfg}: {e!r}")
            continue
        done, locks = chunk_state(rd, names)
        pid2top = {p: t["pid"] for t in by_cfg.get(cfg, []) for p in t["tree"]}
        bt = {}
        for n, pid in locks.items():
            top = pid2top.get(pid, -1)
            bt[top] = bt.get(top, 0) + 1
        h = bt.get(-1, 0)
        for t in by_cfg.get(cfg, []):
            b = bt.get(t["pid"], 0)
            busy_tree[t["pid"]] = b
            h += max(b, t["workers"] if t["age"] < YOUNG else 0)
        held[cfg] = h
        unclaimed[cfg] = max(0, len(set(names) - done) - len(locks))
    return cur, held, unclaimed, busy_tree, by_cfg


def run_loop():
    SD.mkdir(parents=True, exist_ok=True)
    lockf = open(QD / ".scheduler.lock", "w")
    try:
        fcntl.flock(lockf, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit("another scheduler is running")
    sys.path.insert(0, str(ROOT / "src"))
    t_start = time.time()
    unmet_ticks: dict = {}
    reserved: dict = {}      # cfg -> Reservation
    idle_seen: dict = {}     # top pid -> ticks seen idle under a reservation
    last_alloc = None
    log(f"scheduler start (pid {os.getpid()})")
    while True:
        try:
            reap_old()
            L = items()
            bthreads, why = budget()
            W = bthreads // THREADS
            tops = procs()
            cur, held, unclaimed, busy_tree, by_cfg = snapshot(L, tops)
            total_held = sum(held.values())
            free = W - total_held
            states = {it.id: item_state(it) for it in L}
            alloc, unmet = {}, {}
            mem = mem_avail_gib()
            launched_item = False
            for it in L:
                s = states[it.id]
                c = cur[it.id]
                h = held.get(c, 0) if c else 0
                if s == "running" and c and c not in reserved:
                    want = unclaimed.get(c, 0)
                    if exits_failed(c, t_start) >= MAX_FAILS:
                        (SD / f"failed_{Path(c).stem}").write_text(time.strftime("%F %T\n"))
                        want = 0
                    g = max(0, min(free, want))
                    if it.kind == "external":
                        # its own pipeline starts the processes at each stage start
                        n = max(1, h + g if c else min(max(free, 1), 4))
                        ov = ROOT / it.pd / "override.env"
                        txt = f"WORKERS={n}\nTHREADS={THREADS}\n"
                        if not ov.exists() or ov.read_text() != txt:
                            ov.write_text(txt)
                        alloc[it.id] = (h, n)  # (free is not consumed: it applies at its next stage)
                        continue
                    if g > 0 and mem >= MIN_MEM_GIB:
                        rd, _ = cfg_info(c)
                        launch_workers(c, rd, g)
                        log(f"+{g} workers -> {it.id} {Path(c).stem} (held {h}, unclaimed {want}, "
                            f"free {free})")
                        free -= g
                        mem -= 4 * g
                        h += g
                    unmet[it.id] = max(0, want - g)
                    alloc[it.id] = (h, h)
                elif s == "running":
                    alloc[it.id] = (h, h)
                elif s == "pending" and not launched_item:
                    # start the pipeline (config / selection stages cost nothing); its run stages
                    # get workers by priority from the next tick on. One start per tick.
                    launched_item = launch_item(it)
            # ---------------- lossless preemption for higher tiers
            for it in L:
                unmet_ticks[it.id] = unmet_ticks.get(it.id, 0) + 1 if unmet.get(it.id, 0) > 0 else 0
            needy = [it for it in L if unmet_ticks.get(it.id, 0) >= 2 and free <= 0]
            if needy and not reserved:
                n0 = needy[0]
                need = unmet[n0.id]
                for v in reversed(L):  # lowest priority first
                    if v.tier <= n0.tier or need <= 0:
                        continue
                    c = cur[v.id]
                    if not c and states[v.id] != "running":  # leftover processes of a handover
                        c = next((f"configs/{v.cfg_prefix}{st}.yaml" for st in v.stages
                                  if held.get(f"configs/{v.cfg_prefix}{st}.yaml", 0) > 0), None)
                    if v.kind == "external" or not c or held.get(c, 0) == 0 or c in reserved:
                        continue
                    reserved[c] = Reservation(c)
                    log(f"reserve {Path(c).stem} ({len(reserved[c].fds)} unclaimed chunks) of {v.id} "
                        f"(T{v.tier}, holds {held[c]}) for {n0.id} (T{n0.tier}, unmet {need})")
                    need -= held[c]
            for c, r in list(reserved.items()):
                trees = by_cfg.get(c, [])
                for t in trees:
                    if busy_tree.get(t["pid"], 0) == 0 and t["age"] >= YOUNG:
                        idle_seen[t["pid"]] = idle_seen.get(t["pid"], 0) + 1
                        if idle_seen[t["pid"]] >= 2:
                            log(f"stop idle process tree {t['pid']} on {Path(c).stem} (no chunk in flight)")
                            kill_tree(t)
                    else:
                        idle_seen.pop(t["pid"], None)
                if not [t for t in procs() if t["cfg"] == c]:
                    r.release()
                    del reserved[c]
                    log(f"released {Path(c).stem}")
            snap = {"time": time.strftime("%F %T"), "budget_threads": bthreads, "why": why,
                    "workers": W, "held_total": total_held, "free": free,
                    "items": {it.id: {"tier": it.tier, "state": states[it.id], "cfg": cur[it.id],
                                      "held": alloc.get(it.id, (0, 0))[0],
                                      "unclaimed": unclaimed.get(cur[it.id], 0) if cur[it.id] else 0,
                                      "reserved": cur[it.id] in reserved}
                              for it in L},
                    "other_configs": {c: held[c] for c in held
                                      if c not in set(cur.values())}}
            (SD / "snapshot.json.tmp").write_text(json.dumps(snap, indent=1))
            (SD / "snapshot.json.tmp").replace(SD / "snapshot.json")
            a = json.dumps({k: v for k, v in alloc.items()})
            if a != last_alloc:
                log(f"held/target {a}; free {free} of {W}")
                last_alloc = a
        except Exception as e:  # noqa: BLE001
            log(f"tick error {e!r}")
        time.sleep(TICK)


# ------------------------------------------------------------------ status / eta
def status():
    f = SD / "snapshot.json"
    if not f.exists():
        print("no snapshot (scheduler not running?)")
        return
    s = json.loads(f.read_text())
    age = time.time() - f.stat().st_mtime
    print(f"snapshot {s['time']} ({age:.0f} s old); budget {s['budget_threads']} threads ({s['why']}) = "
          f"{s['workers']} workers; held {s['held_total']}; free {s['free']}")
    for k, v in s["items"].items():
        cfg = Path(v["cfg"]).stem if v["cfg"] else "-"
        print(f"  T{v['tier']} {k:28s} {v['state']:40s} {cfg:34s} held {v['held']:2d} "
              f"unclaimed {v['unclaimed']:3d}{' RESERVED' if v['reserved'] else ''}")
    if s["other_configs"]:
        print("  other run_experiment configs (counted in the budget):", s["other_configs"])


# ------------------------------------------------------------------ ETA (event simulation)
MULT = {"": 1.0, "C1": 1.0, "C2": 1.55, "C3": 2.35, "C4": 2.3, "C4s": 2.3, "C5": 1.35, "C6": 1.1}
TEST_YEARS = {"brazil": 5, "colombia": 3, "peru": 4, "taiwan": 4}
FOLDS = {("brazil", "s2"): 5, ("brazil", "s3"): 5, ("brazil", "s4"): 5, ("colombia", "s2"): 5,
         ("colombia", "s3"): 6, ("colombia", "s4"): 5}


def _mult(level):
    base, _, ctrl = level.partition("+")
    m = MULT.get(ctrl, 2.0)
    return m + (0.55 if base in ("L4", "N4") else 0.0) - (0.1 if base.startswith("N") else 0.0)


def _median(v):
    v = sorted(v)
    return v[len(v) // 2] if v else None


def _ref_secs():
    """Median seconds of plain-L3 chunks: (country, 'test' | '2019') from the S1 runs."""
    ref = {}
    for c in TEST_YEARS:
        for kind, dirs in (("test", [f"runs/{c}_s1_L3_leaves127", f"runs/{c}_s1_shared_L3", f"runs/{c}_s1_L3"]),
                           ("2019", [f"runs/{c}_s1_shared_controls_2019", f"runs/{c}_s1_controls_2019"])):
            for d in dirs:
                xs = [json.loads(f.read_text())["seconds"] for f in (ROOT / d / "chunks").glob("*__L3__*.done.json")] \
                    if (ROOT / d / "chunks").exists() else []
                if len(xs) >= 3:
                    ref[(c, kind)] = _median(xs)
                    break
    return ref


def _stage_chunks(it, stage, ref):
    """[(seconds, ...)] estimated for the not-done chunks of one stage."""
    cfg = f"configs/{it.cfg_prefix}{stage}.yaml"
    country = it.id.split("_")[0]
    tok = it.id[len(country) + 1:]
    spatial = tok in ("s2", "s3", "s4", "s5") or tok.startswith("s2_") or tok.startswith("s3_")
    kind = "2019" if stage == "controls_2019" else "test"
    if tok == "s5":
        base = ref.get(("colombia", kind), 60) * 1.5 if country == "brazil" else ref.get(("brazil", kind), 900) * 1.1
    else:
        base = ref.get((country, kind), 600) * (0.8 if spatial else 1.0)
    if (ROOT / cfg).exists():
        rd, names = cfg_info(cfg)
        done, _ = chunk_state(rd, names)
        own = {}
        for f in (rd / "chunks").glob("*.done.json") if (rd / "chunks").exists() else []:
            try:
                d = json.loads(f.read_text())
                own.setdefault(d["run"], []).append(d["seconds"])
            except (ValueError, KeyError, OSError):
                pass
        out = []
        for n in names:
            if n in done:
                continue
            lvl = n.split("__")[1]
            m = _median(own.get(f"lgbm-{lvl}", []))
            out.append(m if m else base * _mult(lvl))
        return out
    # not generated yet: count from the split layout
    hz = 2 if (spatial or it.kind in ("nohist", "sens")) else 4
    years = 1 if kind == "2019" else TEST_YEARS[country]
    folds = FOLDS.get((country, tok), 1)
    if stage == "controls_2019":
        k = [("L3", 1)] + [(f"L3+{c}", 1) for c in ("C1", "C2", "C5")] + [(f"L3+{c}", 3) for c in ("C3", "C4", "C4s")]
        return [base * _mult(l) for l, s in k for _ in range(s * folds * years * hz)]
    lvl = {"L3_Cstar": "L3+C1", "L4_Cstar": "L4+C1", "N3_Cstar": "N3+C2", "N4_Cstar": "N4+C2",
           "N3_C1": "N3+C1", "N4_C1": "N4+C1"}.get(stage)
    if lvl is None:
        st = stage.split("_", 1)[-1] if it.kind == "sens" else stage
        lvl = {"L3_Cstar": "L3+C1", "L4_Cstar": "L4+C1"}.get(st, st.replace("_", "+"))
    return [base * _mult(lvl)] * (folds * years * hz)


def eta(L, W):
    import heapq
    ref = _ref_secs()
    print("reference L3 chunk seconds:", {f"{k[0]}/{k[1]}": round(v) for k, v in ref.items()})
    plan = []
    for it in L:
        s = item_state(it)
        if s in ("done", "failed"):
            continue
        stages = []
        for st in it.stages:
            if (ROOT / it.pd / f"stage_{st}.done").exists():
                continue
            ch = _stage_chunks(it, st, ref)
            if ch:
                stages.append((st, ch))
        plan.append([it, stages])
    # event simulation: chunk-level, priority order, stages sequential within an item
    t, free, busy, done_at = 0.0, W, [], {}
    pos = {p[0].id: 0 for p in plan}            # current stage index
    left = {p[0].id: [list(c) for _, c in p[1]] for p in plan}
    running = {p[0].id: 0 for p in plan}
    deps = {"brazil_s1_sens_seeds": ("brazil_s1_shared", "controls_2019")}

    def ready(it):
        d = deps.get(it.id)
        if not d:
            return True
        o = next((p for p in plan if p[0].id == d[0]), None)
        if o is None:
            return True
        if d[1] is None:
            return d[0] in done_at
        names = [s for s, _ in o[1]]
        return d[1] not in names or pos[d[0]] > names.index(d[1])

    while True:
        for it, stages in plan:
            while free > 0 and it.id not in done_at and ready(it) and pos[it.id] < len(stages) \
                    and left[it.id][pos[it.id]]:
                dur = left[it.id][pos[it.id]].pop()
                heapq.heappush(busy, (t + dur, it.id))
                running[it.id] += 1
                free -= 1
            if it.id not in done_at and pos[it.id] >= len(stages):
                done_at[it.id] = t
        if not busy:
            break
        t, iid = heapq.heappop(busy)
        free += 1
        running[iid] -= 1
        stg = next(p[1] for p in plan if p[0].id == iid)
        if running[iid] == 0 and not left[iid][pos[iid]]:
            pos[iid] += 1
            if pos[iid] >= len(stg):
                done_at[iid] = t
    now = time.time()
    tiers = {}
    for it, stages in plan:
        wh = sum(sum(c) for _, c in stages) / 3600
        f = done_at.get(it.id, t)
        tiers[it.tier] = max(tiers.get(it.tier, 0), f)
        print(f"  T{it.tier} {it.id:28s} {wh:7.1f} worker-h  done +{f / 3600:5.1f} h "
              f"({time.strftime('%a %H:%M', time.localtime(now + f))})")
    for k in sorted(tiers):
        print(f"T{k} complete: +{tiers[k] / 3600:.1f} h ({time.strftime('%a %b %d %H:%M', time.localtime(now + tiers[k]))})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "status", "remaining", "eta", "dry"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--workers", type=int, default=15)
    a = ap.parse_args()
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT / "src"))
    if a.cmd == "run":
        run_loop()
    elif a.cmd == "status":
        status()
    elif a.cmd == "remaining":
        if not a.arg:
            ap.error("remaining needs a config path (configs/<name>.yaml)")
        print(remaining(a.arg))
    elif a.cmd == "dry":  # what the loop sees right now (no action)
        L = items()
        tops = procs()
        cur, held, unclaimed, busy_tree, by_cfg = snapshot(L, tops)
        print("budget", budget(), "held total", sum(held.values()))
        for it in L:
            c = cur[it.id]
            print(f"T{it.tier} {it.id:28s} {item_state(it):45s} {c or '-':45s} held {held.get(c, 0)} "
                  f"unclaimed {unclaimed.get(c, 0)}")
        for c, h in held.items():
            print("  cfg", c, "held", h, "unclaimed", unclaimed.get(c),
                  "trees", [(t['pid'], t['workers'], t['age'], busy_tree.get(t['pid'])) for t in by_cfg.get(c, [])])
    elif a.cmd == "eta":
        sys.path.insert(0, str(ROOT / "scripts/run"))
        eta(items(), a.workers)


if __name__ == "__main__":
    main()
