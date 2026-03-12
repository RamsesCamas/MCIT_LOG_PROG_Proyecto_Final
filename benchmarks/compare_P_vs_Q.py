from __future__ import annotations

import csv
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent

SEQ_SCRIPT = ROOT / "CodigoSecuencial" / "run_p0.py"
CONC_DIR = ROOT / "CodigoConcurrente"

RESULTS_DIR = SCRIPT_DIR
RESULTS_CSV = RESULTS_DIR / "results.csv"

N_VALUES = [10, 25, 50, 100, 200]
CYCLES = 30
WORKERS_ASYNC = 1
WORKERS_FULL = 4

BASE_ARGS = {
    "cycles": CYCLES,
    "cpu_work": 30000,
    "seed": 1234,
}

SUMMARY_RE = re.compile(
    r"Summary:\s+cycles=(?P<cycles>\d+)\s+\|\s+avg=(?P<avg>[0-9.]+)s(?:\s+\|\s+min=(?P<min>[0-9.]+)s)?(?:\s+\|\s+max=(?P<max>[0-9.]+)s)?(?:\s+\|\s+std=(?P<std>[0-9.]+)s)?"
)


def run_command(cmd: List[str], cwd: Path | None = None) -> Tuple[str, float]:
    start = time.perf_counter()

    completed = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=True,
    )

    elapsed = time.perf_counter() - start

    return completed.stdout, elapsed


def parse_summary(stdout: str) -> Dict[str, float]:
    match = SUMMARY_RE.search(stdout)

    if not match:
        raise ValueError(f"No se pudo parsear el summary:\n{stdout}")

    def to_float(name: str) -> float:
        value = match.group(name)
        return float(value) if value is not None else 0.0

    return {
        "avg": to_float("avg"),
        "min": to_float("min"),
        "max": to_float("max"),
        "std": to_float("std"),
    }


def build_seq_cmd(n: int) -> List[str]:
    return [
        sys.executable,
        str(SEQ_SCRIPT),
        "--n", str(n),
        "--cycles", str(BASE_ARGS["cycles"]),
        "--cpu-work", str(BASE_ARGS["cpu_work"]),
        "--seed", str(BASE_ARGS["seed"]),
    ]


def build_q_cmd(n: int, workers: int) -> List[str]:
    return [
        sys.executable,
        "-m", "src.main",
        "--n", str(n),
        "--cycles", str(BASE_ARGS["cycles"]),
        "--workers", str(workers),
        "--cpu-work", str(BASE_ARGS["cpu_work"]),
        "--seed", str(BASE_ARGS["seed"]),
    ]


def safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def main() -> None:

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, float | int]] = []

    cpu_cores = os.cpu_count() or 1

    print("======================================")
    print(" Benchmark P vs Q")
    print("======================================")
    print(f"CPU cores detectados : {cpu_cores}")
    print(f"Cycles por prueba    : {CYCLES}")
    print(f"Workers async (Q1)   : {WORKERS_ASYNC}")
    print(f"Workers full  (Q4)   : {WORKERS_FULL}")
    print()

    for n in N_VALUES:

        stdout_p, wall_p = run_command(build_seq_cmd(n), cwd=ROOT)
        stdout_q_async, wall_q_async = run_command(build_q_cmd(n, WORKERS_ASYNC), cwd=CONC_DIR)
        stdout_q_full, wall_q_full = run_command(build_q_cmd(n, WORKERS_FULL), cwd=CONC_DIR)

        p_stats = parse_summary(stdout_p)
        q_async_stats = parse_summary(stdout_q_async)
        q_full_stats = parse_summary(stdout_q_full)

        t_p = p_stats["avg"]
        t_q_async = q_async_stats["avg"]
        t_q_full = q_full_stats["avg"]

        speedup_async = safe_div(t_p, t_q_async)
        speedup_full = safe_div(t_p, t_q_full)

        speedup_parallel = safe_div(t_q_async, t_q_full)
        efficiency = safe_div(speedup_parallel, WORKERS_FULL)

        row = {
            "n": n,
            "t_p": round(t_p, 6),
            "t_q_async": round(t_q_async, 6),
            "t_q_full": round(t_q_full, 6),
            "speedup_async": round(speedup_async, 6),
            "speedup_full": round(speedup_full, 6),
            "efficiency": round(efficiency, 6),
        }

        rows.append(row)

        print(f"n = {n}")
        print(f"  T_P avg       = {t_p:.6f}s")
        print(f"    min/max/std = {p_stats['min']:.6f}s / {p_stats['max']:.6f}s / {p_stats['std']:.6f}s")
        print(f"  T_Q_async avg = {t_q_async:.6f}s")
        print(f"    min/max/std = {q_async_stats['min']:.6f}s / {q_async_stats['max']:.6f}s / {q_async_stats['std']:.6f}s")
        print(f"  T_Q_full avg  = {t_q_full:.6f}s")
        print(f"    min/max/std = {q_full_stats['min']:.6f}s / {q_full_stats['max']:.6f}s / {q_full_stats['std']:.6f}s")
        print()
        print(f"  Speedup_arch  = {speedup_async:.6f}   (P / Q_async)")
        print(f"  Speedup_total = {speedup_full:.6f}   (P / Q_full)")
        print(f"  Speedup_par   = {speedup_parallel:.6f}   (Q_async / Q_full)")
        print(f"  Efficiency    = {efficiency:.6f}")
        print()
        print(f"  Wall_P        = {wall_p:.6f}s")
        print(f"  Wall_Q_async  = {wall_q_async:.6f}s")
        print(f"  Wall_Q_full   = {wall_q_full:.6f}s")
        print("--------------------------------------")
        print()

    with RESULTS_CSV.open("w", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "n",
                "t_p",
                "t_q_async",
                "t_q_full",
                "speedup_async",
                "speedup_full",
                "efficiency",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    print("======================================")
    print(f"CSV generado en: {RESULTS_CSV}")
    print("======================================")


if __name__ == "__main__":
    main()
