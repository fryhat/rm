# RM Moving Target

RoboMaster moving-target probability planning, visualization, and C++ rollout
planner experiments.

## Main Entry Points

- `sp_vision_moving_target_visualizer_full_compare.py`
- `cpp_rollout_planner/rollout_benchmark.py`
- `cpp_rollout_planner/random_strategy_ab.py`
- `cpp_rollout_planner/deterministic_distance_ab.py`
- `cpp_rollout_planner/warmup_zero_accel_distance_ab.py`

## Quick Validation

```powershell
python cpp_rollout_planner\rollout_planner.py
python sp_vision_moving_target_visualizer_full_compare.py --self-test
python cpp_rollout_planner\rollout_benchmark.py 10 --model-version rigorous
```

## Distance-Aware Benchmark

```powershell
python cpp_rollout_planner\rollout_benchmark.py 180 `
  --model-version rigorous --warmup 60 --distance 8

python cpp_rollout_planner\warmup_zero_accel_distance_ab.py `
  --seconds 180 --warmup 60 --seeds 20260903 20260904 `
  --distances 2 4 6 8
```

Current handoff notes are in `HANDOFF_MOVING_TARGET_NEXT_V10.md`; the full
history and earlier experiment records are kept in the `HANDOFF_*` files.
