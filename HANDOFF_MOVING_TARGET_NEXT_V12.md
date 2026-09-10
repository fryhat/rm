# current 距离路径审查 V12

更新时间：2026-09-10

## 1. 结果

`current` 在 4 m / 8 m 明显变差，但在 6 m 正常，需要区分两件事：

1. 是否存在残留的 6 m 硬编码；
2. 自定义目标是否与 current 的预测模型一致。

结论：`current` 的异常不是 6 m 硬编码造成的。

## 2. 6 m 参数审查

正式 current 路径中的距离计算均为动态：

- 目标中心：`TargetState.x/y`
- 装甲位置：`armor_poses(state)`
- 飞行时间：`norm(armor.x, armor.y) / bullet_speed`
- planned range：`norm(planned_aim_x, planned_aim_y)`
- 碰撞：使用 `impact_at` 时刻的实际装甲位置

剩余 `6.0` 只出现在以下位置：

- GUI / benchmark 默认参数：显式传距离时不会使用；
- 自测和固定 6 m 诊断脚本：不参与正式 `--distance` 评估；
- C++ 旧 ABI 兼容封装：正式 Python 路径已使用 `_center` 接口；
- `CausalEvasionPredictor` / `DeterministicEvasionSchedule` 默认中心：
  本次 AB 已显式传入 `center_y=distance`。

## 3. current 差异的真正来源

`current` 使用上游 `Planner::plan()` 的语义：

1. 在延迟时刻选择最近装甲，用其径向距离计算飞行时间；
2. 按该飞行时间预测撞击状态；
3. 在撞击状态重新选择最近装甲并生成参考轨迹；
4. `plan.fire` 仅判断参考轨迹跟踪误差，不判断实际物理命中。

它不估计目标角加速度。因此当目标带 `1 rad/s²` 角加速度时，current
和“正常加速度概率”使用的信息集不同，4 m / 8 m 出现明显的相位差异。

将 current 强制改成“每块装甲各自固定点收敛”的实验已回滚，因为它偏离
上游语义且结果更差。

## 4. 本次修复

- `DeterministicEvasionSchedule._advance()` 增加 `alpha=0` 分支，避免除零；
- `fixed_model_distance_ab.py` 显式传入 `center_y=distance`，不再依赖默认 6 m。

验证：

```text
py_compile passed
self-test passed
alpha=0 schedule state query passed
```
