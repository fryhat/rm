# current 6 m 峰定位与修复 V15

更新时间：2026-09-10

## 1. 真正问题

原 current 规划算法保持不变。6 m 峰来自 Python 仿真新增了一层
非上游 PD 控制器：

```text
control_acceleration + 35 * yaw_error + 10 * velocity_error
```

上游 `standard_mpc.cpp` 发送的是：

```text
plan.yaw, plan.yaw_vel, plan.yaw_acc
```

也就是位置、速度和加速度前馈，由下位机控制器执行。Python 中的 35/10
PD 是未标定仿真层，产生距离相关相位共振；6 m 时偶然形成高分。

## 2. 修复

原 current 规划算法完全保留，只修正 current 的执行仿真：

- 默认直接采用 `plan.yaw`、`plan.yaw_velocity`、`plan.yaw_acceleration`；
- 原 35/10 PD 仿真保留为 `--legacy-pd-gimbal` 兼容选项。

## 3. 修复后的 current

模型 A：初始 500°/s、上限 700°/s、1 rad/s²、每 2 s 换向。

| 距离 | valid/s | 命中率 |
|---:|---:|---:|
| 2 m | 4.074 | 56.19% |
| 4 m | 5.636 | 54.93% |
| 6 m | 6.429 | 54.92% |
| 8 m | 6.418 | 54.37% |

模型 B：匀速 600°/s。

| 距离 | valid/s | 命中率 |
|---:|---:|---:|
| 2 m | 3.396 | 50.94% |
| 4 m | 5.031 | 50.31% |
| 6 m | 5.699 | 49.48% |
| 8 m | 5.929 | 51.46% |

修复后 6 m 峰消失，current 命中率稳定在约 49%–56%。
