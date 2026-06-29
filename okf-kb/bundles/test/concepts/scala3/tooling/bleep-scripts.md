---
type: Concept
resource: sources/articles/bleep-scripts-readme.md
title: BleepScript 复用脚本姿势
description: bleep 构建工具用 BleepScript（编译后跑的 JVM 程序）替代 sbt 插件实现项目自动化——独立 scripts 子项目
  + bleep.yaml 注册 + object X extends BleepScript 的统一模式，及其跨版本差异。
tags:
- Scala
- bleep
- 构建工具
- BleepScript
- 工程化
- Scala.js
- MCP
timestamp: '2026-06-29T12:41:33Z'
---

# 是什么

[bleep](https://github.com/akashnama/bleep) 是一个 Scala 构建工具。它**没有 sbt 那样的 autoplugin / variant 机制**，项目自动化的唯一载体是 **BleepScript**——一段编译后在 JVM 里运行的程序，由 bleep 反射调用。本概念总结一组可直接复用的 BleepScript 脚本所共享的「接入姿势」，是下列三个具体脚本的共同抽象：

- [bleep-mcp-setup](../../../references/scala3/tooling/bleep-mcp-setup.md) — 把 ScalaSemantic MCP 服务器接入项目
- [bleep-link-vite](../../../references/scala3/tooling/bleep-link-vite.md) — Scala.js + Vite 统一开发流水线
- [bleep-custom-dist](../../../references/scala3/tooling/bleep-custom-dist.md) — 封装内置 Dist 命令搬运产物

# 共性三件套

所有 BleepScript 都遵循同一个结构：

1. **独立 JVM 子项目**：`bleep.yaml` 里声明一个 `scripts` 项目，`platform: jvm`，依赖 `build.bleep::bleep-core`（暴露 `BleepScript / Started / Commands`）。它**不继承**业务项目的模板——业务项目可能是 Scala.js 的，而脚本必须在 JVM 上跑。
2. **`bleep.yaml` 注册**：在 `scripts:` 段下声明 `{ main: <全限定对象名>, project: scripts }`。bleep 会把脚本名提升为顶层命令（`bleep <script-name>`）。
3. **`object X extends BleepScript(name)`**：实现 `run(started, commands, args)`，bleep 反射注入构建上下文。

```yaml
projects:
  scripts:
    extends: template-common          # 必须是 JVM 模板，不能继承 Scala.js 模板
    dependencies:
      - build.bleep::bleep-core:<你的bleep版本>

scripts:
  my-script:
    main: scripts.MyScript            # 全限定对象名
    project: scripts
```

# 注入的运行时上下文

`run(started, commands, args)` 的三个参数是脚本访问 bleep 内部模型的统一入口：

| 参数 | 类型 | 用途 |
|------|------|------|
| `started` | `Started` | 构建上下文：完整项目模型、路径解析器、logger。读产物路径靠它 |
| `commands` | `Commands` | 命令门面：`compile / run / test / script / publishLocal / publish` |
| `args` | `List[String]` | CLI 透传参数 |

最常用的两个路径 API（三个脚本都用到了）：

- `started.projectPaths(crossName).targetDir` — 定位项目的构建产物目录（`.bleep/builds/normal/.bloop/<project>`）
- `started.buildPaths.buildDir` — 项目根目录

# 关键认知：内置 API vs 子进程

脚本编排外部动作时有两条路，取舍决定了每个脚本的写法：

| 方式 | 条件 | 代表脚本 |
|------|------|----------|
| 调用内置命令 API（`new bleep.commands.X(...).run(started)`） | 该命令是 bleep-core 公开 API | [bleep-custom-dist](../../../references/scala3/tooling/bleep-custom-dist.md)（`bleep.commands.Dist`） |
| spawn 子进程（`bleep <cmd>`） | `Commands` 门面没有该方法 | [bleep-link-vite](../../../references/scala3/tooling/bleep-link-vite.md)（`Commands` 无 `link`，被迫用子进程 `bleep link --watch`） |

**原则：能用内置 API 就用内置 API**——无额外进程开销，且语义与 CLI 完全一致。`Commands` 只暴露 `compile/run/test/script/publish*`，链接（`link`）由 CLI / BSP 内部实现，故脚本只能以子进程方式触发链接。

# 版本差异（移植时必读）

bleep 的 script 调用机制跨版本有 breaking change，直接决定脚本必须用 `object` 还是可用 `class`：

| bleep 版本 | script 调用方式 | 约束 |
|-----------|----------------|------|
| `0.0.14` | `java <mainClass>` 直接调 | 必须 **static main**，故必须用 `object`（Scala 为 object 生成 static forwarder） |
| `1.0.0-M10` 起 | 放宽 | `class` / `object` 均可 |

> ⚠️ 在 0.0.14 上用 `class` 会报 `Main method is not static`。三个脚本因目标项目版本不同而写法略有差异（`CustomDist` / `McpSetup` 用 `object` 兼容 0.0.14；`LinkVite` 面向 1.0.0-M10）。移植时按你的 bleep 版本调整。

# 接入任意 bleep 项目

1. 把脚本源码（`.scala`）复制到 `<项目>/scripts/src/scala/scripts/`。
2. 在 `bleep.yaml` 加 `scripts` 子项目 + `scripts:` 注册段（见上）。
3. `bleep <script-name>` 即可运行。

> 设计文档中的相对链接（如 `../scripts/...`）指向原始项目的源码位置，复制后会失效；以同目录下的 `.scala` 源码为准。

# Citations

- bleep_scripts 仓库 `README.md`（已钉死到原料层：[bleep-scripts-readme](../../../../../sources/articles/bleep-scripts-readme.md)；原始位置 `/home/ai/lee/workspace/bleep_scripts/README.md`）
