from __future__ import annotations

import argparse
import contextlib
import io
import math
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import sp_vision_moving_target_visualizer_full_compare as sim
from deterministic_evasion_schedule import DeterministicEvasionSchedule
from rollout_benchmark import MODEL_VERSION_RIGOROUS, RolloutBenchmark


CURRENT_RE = re.compile(
    r"current:\s+shots=(\d+), valid=(\d+), low=(\d+), miss=(\d+), "
    r"valid_rate=([0-9.]+)%, valid_per_s=([0-9.]+)"
)
ROLLOUT_RE = re.compile(
    r"rollout_cpp\[rigorous\]:\s+shots=(\d+), valid=(\d+), low=(\d+), "
    r"miss=(\d+), valid_rate=([0-9.]+)%, valid_per_s=([0-9.]+)"
)


@dataclass
class RunResult:
    shots: int
    valid: int
    low: int
    miss: int
    valid_rate: float
    valid_per_s: float


def parse_result(text: str, pattern: re.Pattern[str]) -> RunResult:
    match = pattern.search(text)
    if match is None:
        raise RuntimeError(f"could not parse result from: {text[-500:]}")
    shots, valid, low, miss, valid_rate, valid_per_s = match.groups()
    return RunResult(
        shots=int(shots),
        valid=int(valid),
        low=int(low),
        miss=int(miss),
        valid_rate=float(valid_rate),
        valid_per_s=float(valid_per_s),
    )


def make_schedule(
    args: argparse.Namespace,
    distance: float,
) -> DeterministicEvasionSchedule:
    return DeterministicEvasionSchedule(
        initial_omega=math.radians(args.initial_omega_deg),
        omega_limit=math.radians(args.omega_limit_deg),
        alpha_limit=args.alpha_rad,
        switch_interval=args.switch_interval,
        center_x=0.0,
        center_y=distance,
    )


def make_advance(schedule: DeterministicEvasionSchedule):
    def advance(
        _angle: float,
        _omega: float,
        _direction: float,
        start_time: float,
        _next_switch: float,
        dt: float,
    ):
        end = schedule.state_at(start_time + dt)
        return (
            end.angle,
            end.omega,
            1.0 if end.alpha >= 0.0 else -1.0,
            end.alpha,
            schedule.switch_interval
            if start_time + dt < schedule.switch_interval
            else (
                math.floor((start_time + dt) / schedule.switch_interval) + 1
            )
            * schedule.switch_interval,
        )

    return advance


def run_current(
    args: argparse.Namespace,
    seed: int,
    distance: float,
) -> RunResult:
    schedule = make_schedule(args, distance)
    original_advance = sim.advance_optimized_evasion
    original_initial_omega = sim.INITIAL_OMEGA
    sim.advance_optimized_evasion = make_advance(schedule)
    sim.INITIAL_OMEGA = schedule.initial_omega
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            sim.benchmark(
                seconds=args.seconds,
                modes=("current",),
                seed=seed,
                distance=distance,
            )
    finally:
        sim.advance_optimized_evasion = original_advance
        sim.INITIAL_OMEGA = original_initial_omega
    return parse_result(output.getvalue(), CURRENT_RE)


def run_rollout(
    args: argparse.Namespace,
    seed: int,
    distance: float,
    *,
    zero_acceleration_history: bool,
) -> RunResult:
    schedule = make_schedule(args, distance)
    original_advance = sim.advance_optimized_evasion
    original_initial_omega = sim.INITIAL_OMEGA
    sim.advance_optimized_evasion = make_advance(schedule)
    sim.INITIAL_OMEGA = schedule.initial_omega
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            RolloutBenchmark(
                seconds=args.seconds,
                seed=seed,
                distance=distance,
                schedule=schedule,
                model_version=MODEL_VERSION_RIGOROUS,
                zero_acceleration_history=zero_acceleration_history,
            ).run()
    finally:
        sim.advance_optimized_evasion = original_advance
        sim.INITIAL_OMEGA = original_initial_omega
    return parse_result(output.getvalue(), ROLLOUT_RE)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=180.0)
    parser.add_argument("--seeds", type=int, nargs="+", default=(20260903,))
    parser.add_argument("--distances", type=float, nargs="+", default=(2.0, 4.0, 6.0, 8.0))
    parser.add_argument("--initial-omega-deg", type=float, default=500.0)
    parser.add_argument("--omega-limit-deg", type=float, default=700.0)
    parser.add_argument("--alpha-rad", type=float, default=1.0)
    parser.add_argument("--switch-interval", type=float, default=2.0)
    args = parser.parse_args()

    for seed in args.seeds:
        rows: dict[
            float,
            tuple[RunResult, RunResult, RunResult],
        ] = {}
        for distance in args.distances:
            zero = run_rollout(
                args,
                seed,
                distance,
                zero_acceleration_history=True,
            )
            normal = run_rollout(
                args,
                seed,
                distance,
                zero_acceleration_history=False,
            )
            current = run_current(args, seed, distance)
            rows[distance] = (zero, normal, current)
            print(
                f"seed={seed} distance={distance:g} "
                f"zero={zero.valid_per_s:.3f}/{zero.valid_rate:.2f}% "
                f"normal={normal.valid_per_s:.3f}/{normal.valid_rate:.2f}% "
                f"current={current.valid_per_s:.3f}/{current.valid_rate:.2f}%"
            )

        for distance in args.distances:
            zero, normal, current = rows[distance]
            print(
                f"aggregate seed={seed} distance={distance:g} "
                f"zero={zero.valid_per_s:.3f}/{zero.valid_rate:.2f}% "
                f"normal={normal.valid_per_s:.3f}/{normal.valid_rate:.2f}% "
                f"current={current.valid_per_s:.3f}/{current.valid_rate:.2f}%"
            )


if __name__ == "__main__":
    started = time.perf_counter()
    main()
    print(f"wall_seconds={time.perf_counter() - started:.3f}")
