# 静态审查意见核对 V14

更新时间：2026-09-10

## 1. 已确认并修复

### C++ 曲线端点被错误清零

`interpolate()` 原来对 `yaw == grid[0]` 和 `yaw == grid[-1]` 返回 0，
与 Python `_cached_curve_value()` 的端点语义不一致。

已修改为：

```cpp
if (yaw < grid[0] || yaw > grid[grid_size - 1]) return 0.0;
if (yaw == grid[0]) return values[0];
if (yaw == grid[grid_size - 1]) return values[grid_size - 1];
```

### 主 benchmark 不结算尾部在途子弹

`sp_vision_moving_target_visualizer_full_compare.py::benchmark()` 原来在固定
步数结束后立即统计，而 `RolloutBenchmark` 会继续推进直至所有子弹结算。

已在主 benchmark 后增加不再开火的结算循环，使两种 benchmark 统计口径一致。

### 常量加速度历史压缩误差

`compress_history_entries()` 对单值历史使用直方图中心时会产生约
`3.9e-12` 的误差。在目标速度等于上限时会被 C++ 可行性容差错误过滤，
导致概率曲线全 0。已改为单值历史保留原始加速度。

### schedule 零角加速度除零

`DeterministicEvasionSchedule._advance()` 现在显式处理 `alpha == 0`。

## 2. 已核对但暂不直接修改

### 任意装甲概率 vs 指定装甲判定

事件定义确实不完全一致：

- 概率场对每个姿态样本取四块装甲的最大贡献；
- `evaluate_shot()` 在存在 `shot.armor_index` 时只检查该装甲。

30 s 消融把真实判定改为遍历四块装甲后，planned / any 的结果完全相同，
说明当前轨迹尚未触发该口径差异。保留该风险记录，不先扩大修改范围。

### 开火前 15 ms 的控制命令变化

当前门控确实使用当前控制加速度外推 15 ms，而真实发射角按实际 `_gimbal_step`
分段积分。两者可能不同。

该问题成立，但修复需要复用完整闭环重规划，不能在门控端单独冻结命令，否则
会引入新的非因果差异。

### TinyMPC B 矩阵没有 `0.5*dt^2`

C++ 使用：

```cpp
B << 0, kDt;
```

Python 执行使用：

```text
yaw += omega*dt + 0.5*alpha*dt^2
```

两者确有离散化差异，但上游 `Planner::plan()` 同样使用 `B << 0, DT`。
直接修改会偏离 current 的上游语义，必须作为独立模型变更实验。

### TinyMPC 初态使用参考轨迹起点

当前实现与上游一致，TinyMPC 作为轨迹求解器，外层 PD 负责从真实云台状态
跟踪。改成实际云台初态会改变 current 的基本定义，不能在没有 A/B 的情况下改。

### 零概率层只展开极端加速度

这是启发式剪枝，不构成数学上的安全剪枝。当前保留以维持性能；若继续优化
rollout，应使用合法的未来 reward 上界进行 branch-and-bound。

### 主循环顺序中的一帧控制回填

当前 `sim_time += dt -> advance_actual -> update_planner -> advance_gimbal`
的顺序可能存在时间标记不对称。调整会改变所有历史 benchmark，需要独立版本
和完整回归。

### 概率核使用中心距离而非每块装甲距离

这是近似，2 m 和斜置侧板下误差会增大。当前未直接修改，因为 Python 与 C++
概率核必须同步调整，并重新做静态命中率校准。

### `> MIN_NORMAL_HIT_SPEED`

概率过滤和真实判定都使用严格大于 12 m/s，二者一致。不是 bug。

## 3. 结论

采纳低风险且可直接证明的修复。装甲语义、15 ms 门控、MPC 动力学和主循环
顺序都成立但会改变 current 的定义，先不做盲目补丁，必须按独立 A/B 处理。
