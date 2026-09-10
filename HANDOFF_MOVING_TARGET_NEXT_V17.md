# 移动靶当前版本与 warmup 数据交接 V17

更新时间：2026-09-10

## 1. 当前代码状态

- 原 current 规划算法保持不变。
- Python 中额外加入的 `35/10` PD 被确认为非上游仿真层。
- current 默认执行改为直接使用：
  - `plan.yaw`
  - `plan.yaw_velocity`
  - `plan.yaw_acceleration`
- 原 PD 仿真保留为 `--legacy-pd-gimbal`。
- 修复后 6 m 异常峰消失，current 命中率稳定在约 49%–56%。

## 2. 三模型数据

工况 A：初始 500 deg/s、上限 700 deg/s、1 rad/s²、每 2 s 换向。

| 距离 | zero-accel | normal | current |
|---:|---:|---:|---:|
| 2 m | 7.846 | 7.764 | 4.074 |
| 4 m | 7.268 | 7.115 | 5.636 |
| 6 m | 7.772 | 7.800 | 6.429 |
| 8 m | 8.276 | 8.415 | 6.418 |

工况 B：匀速 600 deg/s。

| 距离 | zero-accel | normal | current |
|---:|---:|---:|---:|
| 2 m | 8.283 | 8.283 | 3.396 |
| 4 m | 7.088 | 7.088 | 5.031 |
| 6 m | 7.354 | 7.354 | 5.699 |
| 8 m | 8.539 | 8.539 | 5.929 |

## 3. warmup 诊断

normal 在 2/4 m 略低于 zero-accel，不是 60 s warmup 不够。

单 seed normal：

| 距离 | 0 s | 60 s | 120 s |
|---:|---:|---:|---:|
| 2 m | 7.817 | 7.911 | 7.689 |
| 4 m | 7.211 | 7.456 | 7.494 |
| 6 m | 7.761 | 8.028 | 8.000 |
| 8 m | 8.294 | 8.406 | 8.572 |

四 seed，双方 warmup 60 s：

| 距离 | zero-accel | normal |
|---:|---:|---:|
| 2 m | 7.815 | 7.803 |
| 4 m | 7.364 | 7.316 |
| 6 m | 7.839 | 7.858 |
| 8 m | 8.275 | 8.420 |

原因：2/4 m 飞行时间短，`0.5*alpha*t^2` 相对装甲角宽很小，
zero prior 偏差小；normal 的离散历史分布此时主要是额外方差。
6/8 m 加速度位移增大后 normal 才产生收益。

多 horizon 独立分箱和加速度收缩试验均不能稳定改善四距离，已回滚。

## 4. 数据文件

整理后的实验数据：

```text
cpp_rollout_planner/experiment_results/latest_three_model_and_warmup.csv
```
