from __future__ import annotations

import csv
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent
SEQ_SCRIPT = ROOT / "CodigoSecuencial" / "run_p0.py"
CONC_DIR = ROOT / "CodigoConcurrente"
RESULTS_DIR = ROOT / "benchmarks"
RESULTS_CSV = RESULTS_DIR / "results.csv"

N_VALUES = [10, 25, 50, 100, 200]
CYCLES = 3
WORKERS_FULL = 4
BASE_ARGS = {
    "cycles": CYCLES,
    "cpu_work": 30000,
    "seed": 1234,
}

SUMMARY_RE = re.compile(r"Summary:\s+cycles=(?P<cycles>\d+)\s+\|\s+avg=(?P<avg>[0-9.]+)s")


def run_command(cmd: List[str], cwd: Path | None = None) -> str:
    with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", delete=True) as tmp:
        subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            stdout=tmp,
            stderr=subprocess.STDOUT,
            text=True,
            check=True,
        )
        tmp.seek(0)
        return tmp.read()


def parse_avg(stdout: str) -> float:
    match = SUMMARY_RE.search(stdout)
    if not match:
        raise ValueError(f"No se pudo parsear el tiempo promedio desde stdout:\n{stdout}")
    return float(match.group("avg"))


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

    cpu_cores = os.cpu_count() or 1
    rows: List[Dict[str, float | int]] = []

    print(f"Detected CPU cores: {cpu_cores}")
    print(f"Using workers for Q full: {WORKERS_FULL}")
    print()

    for n in N_VALUES:
        stdout_p = run_command(build_seq_cmd(n), cwd=ROOT)
        stdout_q_async = run_command(build_q_cmd(n, workers=1), cwd=CONC_DIR)
        stdout_q_full = run_command(build_q_cmd(n, workers=WORKERS_FULL), cwd=CONC_DIR)

        t_p = parse_avg(stdout_p)
        t_q_async = parse_avg(stdout_q_async)
        t_q_full = parse_avg(stdout_q_full)

        speedup_async = safe_div(t_p, t_q_async)
        speedup_full = safe_div(t_p, t_q_full)
        efficiency = safe_div(speedup_full, WORKERS_FULL)

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

        print(f"n={n}")
        print(f"  T_P        = {t_p:.6f}s")
        print(f"  T_Q async  = {t_q_async:.6f}s")
        print(f"  T_Q full   = {t_q_full:.6f}s")
        print(f"  Speedup async = {speedup_async:.6f}")
        print(f"  Speedup full  = {speedup_full:.6f}")
        print(f"  Efficiency    = {efficiency:.6f} (S/p, p={WORKERS_FULL})")
        print(f"  CPU cores     = {cpu_cores}")
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

    print(f"CSV generado en: {RESULTS_CSV}")


if __name__ == "__main__":
    main()
