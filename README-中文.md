# Long Mission 中文说明

> 版本 1.0.2：增加视觉/UI 专项任务模式、真实页面截图验收和默认十次尝试上限。

> English version: [README.md](README.md)

**让 Agent 能持续完成复杂任务，同时保留探索和换路线的自由。**

Long Mission 是一个面向 AI Agent 的长任务控制协议，适用于 PRD 执行、复杂开发、UI 重构、迁移、调试和多阶段交付。

## 它解决什么问题

长任务通常有两种失败方式：

1. Agent 把第一版计划执行得过于死板，即使证据表明路线不对也不换方案；
2. Agent 自由发挥，但过程中丢失上下文、提前结束，或者没有证据就声称完成。

Long Mission 的原则是：

> **目标和验收要固定，技术路径要开放，完成必须有证据。**

## 核心逻辑

```text
用户目标
  ↓
任务契约
  ↓
结果目标 + 硬性约束 + 软路线建议
  ↓
有限探索
  ↓
选择当前最佳路线
  ↓
执行与验证
  ↓
必要时重规划
  ↓
双语报告 + 独立验收
  ↓
mission_close
```

## PRD 执行模式

如果用户要求“按照 PRD 执行”，Long Mission 会生成 `PRD-INTERPRETATION.md`，把 PRD 拆成：

- 结果目标；
- 硬性约束与不变量；
- 可替换的技术实现建议；
- 待探测或待确认的事项。

PRD 规定的是目标和约束时必须遵守；PRD 只是建议某个框架、渲染器、文件结构或执行顺序时，Agent 可以依据证据换路线。

## 普通任务模式

不提供 PRD 时，也可以直接运行：

```text
目标分析 → 任务契约 → 验收标准 → 探索 → 执行 → 验证 → 报告 → 关闭
```

普通模式不会生成 PRD 解读，但同样保留自主重规划和独立完成门。

## 自主探索和重规划

初始计划只是一个假设，不是铁轨。Agent 可以先做有限探针：

```text
假设 → 尝试路线 → 独立证据 → 结果 → 选路
```

如果出现以下情况，可以换技术路线：

- 两次尝试没有改善；
- DOM 正确但真实页面错误；
- 父子节点数据冲突；
- 源码、构建和运行版本不一致；
- 当前引擎无法实现关键要求；
- 临时补丁越来越多。

重规划必须记录原假设、失败证据、新路线、保留的不变量和下一步验证。

## 验收门

按任务需要启用：

- 普通代码和接口验收；
- 真实用户界面验收；
- 源码/构建/运行版本一致性验收；
- 父子回执和节点数据投影验收；
- Agent 过程记忆验收；
- 参考图结构、交互、视觉、响应式和可访问性验收。

`未观测`、`未测量`和`未知`不能被伪装成 0 或成功。

## 完成报告

每个任务最终必须生成 `MISSION-REPORT.md`，英文在前、中文在后，包含：

- 任务目标与结果；
- 验收标准；
- 探索和重规划；
- 测试、构建、截图、运行版本和回执证据；
- 失败、偏差、跳过项和未决项；
- 产物与后续动作。

只有通过独立 Gate 并执行：

```bash
python3 scripts/mission_close.py <mission-dir>
```

之后，任务才会生成 completion receipt 并标记为完成。

## 安装和使用

```bash
python3 scripts/mission_start.py .long-mission/my-task \
  --non-interactive \
  --objective "完成目标任务" \
  --deliverable "src/feature.ts" \
  --acceptance "测试通过"
```

如果是 PRD：

```bash
python3 scripts/mission_init.py .long-mission/my-prd \
  --objective "执行已批准的 PRD" \
  --prd docs/spec.md \
  --profile visual_ui
```

## 与传统长任务 Skill 的差异

普通长任务机制通常强调计划、进度和恢复。Long Mission 进一步区分：

- 目标和实现路线；
- 硬验收和软偏好；
- 探索和正式实施；
- 代码通过和真实用户通过；
- 返回候选和真正送达；
- 任务完成和仅仅写了 `done`。

它吸收了 Superpowers、Spec-Driven Planning、PLET、Planning with Files 等方案的优点，但不强制引入复杂的多 Agent、Worktree、角色编排或固定技术栈。

## 测试

```bash
python3 -m pytest -q tests test_long_mission_protocol.py
```

## 边界

Long Mission 能约束流程和完成声明，但不能让宿主进程在回合结束后无限运行。需要持续执行时，应使用 continuation prompt 或受限的 `mission_runner.py`。

## 1.0.2 更新

- **视觉/UI 专项模式：**涉及布局、间距、拓扑、箭头、遮挡、加载状态或交互显示时，使用 `--profile visual_ui`。
- **真实用户界面验收：**优先使用 Computer Use；不可用时才使用已经稳定加载的真实浏览器截图。单元测试、DOM 快照或旧页面截图不能单独通过视觉验收。
- **十次上限：**任务和视觉循环默认最多 10 次。可以通过 `--max-iterations` 显式覆盖任务总迭代数；视觉尝试仍由任务适配器单独限制。
- **独立视觉门：**每次尝试必须记录验证方式、异步稳定状态、代表性交互、截图证据及通过/失败结果。

## 1.0.1 更新

- 新增 PRD 审计门：存在 `Partial` 或 `Blocked` 项时，不能伪装成已完成。
- 新增 `scripts/runtime_truth.py`：核对真实 URL 标识、监听 PID 和进程工作目录，能发现旧端口、IPv4/IPv6 遮蔽和旧监管版本问题。
- 监控类任务必须同时验证正向回执和负向/未调用夹具，并把加载中、未知和 0 分开。
- 协议测试扩展到 31 项。

## 许可证

当前尚未声明许可证。对外分发前请由维护者补充许可证。
