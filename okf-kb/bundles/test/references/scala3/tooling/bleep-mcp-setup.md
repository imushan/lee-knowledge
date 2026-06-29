---
type: Reference
resource: sources/articles/bleep-mcp-setup-design.md
title: bleep mcp-setup 脚本：接入 ScalaSemantic MCP
description: 用 BleepScript 复刻 sbt-scalasemantic-mcp 插件的编排逻辑，在 bleep 项目里一条 bleep mcp-setup
  命令完成 ScalaSemantic MCP 服务器的接入：装 launcher、prefetch jar、合并写 .mcp.json。
tags:
- Scala
- bleep
- BleepScript
- ScalaSemantic
- MCP
- SemanticDB
timestamp: '2026-06-29T12:41:54Z'
---

# 用途

让一个 **bleep 构建**的 Scala 3 项目用上 [ScalaSemantic](../../../concepts/scala3/scalasemantic-mcp.md) MCP 服务器，使 AI 编程助手（Claude Code）能做精确语义查询（`find_usages` / `class_hierarchy` / `call_path` 等）而非依赖 grep。衡量标准：bleep 项目里一条 `bleep mcp-setup` 命令完成接入，且不破坏已有配置。

本脚本是 `bleep.scripts.McpSetup`（注册名 `mcp-setup`），源码：`McpSetup.scala`，目标 bleep 版本 `0.0.14`。

# 决定一切设计的两个事实

| 事实 | 含义 |
|------|------|
| ScalaSemantic 服务器**构建工具无关** | 它只读磁盘上的 `.semanticdb`，谁编译的都行。sbt 插件不是特殊通道，只是"便利包" |
| bleep 0.0.14 **没有插件机制** | 只有 BleepScript（编译后跑的程序），没有 autoplugin / variant。所以"一行 `enablePlugins`"在 bleep 不存在，必须用 script 编排 |

由此推导出：**接入 =（让 bleep 吐 .semanticdb）+（用 script 复刻 sbt 插件的编排逻辑）**。

# 三层职责切分

```
bleep 构建       bleep.yaml: -Xsemanticdb -sourceroot   ← 编译时产生数据
                 bleep compile → META-INF/semanticdb/*.semanticdb
                              │ 磁盘文件（唯一耦合点）
                              ▼
McpSetup script  ① 装 launcher ② prefetch jar ③ 合并 .mcp.json   ← 配置编排（一次性）
                              │ 写出 .mcp.json 指向 launcher
                              ▼
运行时（每次 AI 会话）  Claude Code → fork launcher → cs launch 服务器   ← 读取数据
                       服务器读 .semanticdb → 工具 → 返回 JSON
```

**关键边界**：下载 / 缓存 / 断点续传 / 版本解析那一整套复杂逻辑**全在官方 launcher 里**，script 一行不碰。script 只做编排——这正是"复用 launcher"相对"重写下载"的核心收益。

# 三步实现

`object McpSetup extends BleepScript("mcp-setup")` 的 `run` 做三件事：

1. **装 launcher** —— 从 `https://raw.githubusercontent.com/MercurieVV/ScalaSemantic/master/scripts/scalasemantic-mcp.sh` 下载 `.sh` 到 `~/.local/bin/scalasemantic-mcp`，`setExecutable(true)`。已存在则跳过。
2. **`launcher --prefetch`** —— 用 `ProcessBuilder` 调 `launcher --prefetch <root>` 预热服务器 fat jar（约 88MB，一次性）。下载全交给 launcher；返回非 0 只警告，留待首次连接时再下。
3. **circe 合并写 `.mcp.json`** —— 只替换 / 插入 `mcpServers.scala-semantic` 条目，**保留所有其它顶层键与服务器**（幂等）。

写入的 `scala-semantic` 条目结构：

```json
{
  "command": "<launcher 绝对路径>",
  "args": ["<项目根>", "--log", "--log-output"],
  "env": { "JAVA_HOME": "<由 java 反推的真实 JAVA_HOME>" }
}
```

# SemanticDB 产出（bleep.yaml 侧）

接入的前置是让 `bleep compile` 产出 `.semanticdb`：

- `template-common` 的 `scala.options` 加 `-Xsemanticdb -sourceroot:<根>`
- 产物输出到 `META-INF/semanticdb/`（加 `-sourceroot` 后路径可解析、不污染源码）
- SemanticDB **一直开**（bleep 0.0.14 无 variant，无法按需；开销极小）

# 踩坑与修复

| 坑 | 现象 | 根因 | 修复 |
|----|------|------|------|
| BleepScript 用 `class` 实例 main | `Main method is not static` | 0.0.14 的 `rawRun` 用 `java <mainClass>` 直接调，需 static main | `class` → `object`（Scala 为 object 生成 static forwarder）。详见 [bleep-scripts 版本差异](../../../concepts/scala3/tooling/bleep-scripts.md) |
| 全局 JAVA_HOME 损坏 | `cs launch` 启动失败：`Cannot run program .../bin/java` | `JAVA_HOME` 指向 coursier 的双重编码缓存路径（`%252B`），从未解压 | script 用 `readlink -f $(which java)` 反推真实 JAVA_HOME，写入 `.mcp.json` 的 `env.JAVA_HOME` |
| `flatMap(_.getParentFile)` 类型错误 | 编译失败 | `getParentFile` 返回 `File` 非 `Option` | `flatMap(bin => Option(bin.getParentFile))` |

> **教训**：这两个坑都不是"设计错"，而是 bleep 老版本机制差异 + 宿主环境污染。设计上 script 主动检测 / 推导（JAVA_HOME）而非依赖环境，正是为吸收这类宿主差异。

# 接入（bleep.yaml）

```yaml
projects:
  scripts:
    extends: template-common          # JVM 模板
    dependencies:
      - build.bleep::bleep-core:0.0.14
      - io.circe::circe-core:<版本>   # 合并 .mcp.json
      - io.circe::circe-parser:<版本>

scripts:
  mcp-setup:
    main: scripts.McpSetup
    project: scripts
```

运行：`bleep mcp-setup` → 重启 Claude Code → 试 `find_symbol`。

# 能力边界

**已实现**：一键 `bleep mcp-setup` 完成接入；SemanticDB 干净输出到 `META-INF`；`.mcp.json` 合并（保留已有服务器）；JAVA_HOME 自愈；所有 index-only 工具可用。

**有意延后**：PC 实时后端（需抽 app 的 classpath，解锁 `type_at_position` 查未编译脏 buffer）；规则文件 / CLAUDE.md；codex / gemini 等多客户端。

# 相关概念

- [ScalaSemantic：让 AI 理解 Scala 编译器语义](../../../concepts/scala3/scalasemantic-mcp.md) — 本脚本的接入目标，解释 SemanticDB / MCP / 工具列表
- [BleepScript 复用脚本姿势](../../../concepts/scala3/tooling/bleep-scripts.md) — 本脚本遵循的共性模式与版本差异

# Citations

- `bleep_scripts/mcp-setup/scalasemantic-integration-design.md`（已钉死到原料层：[bleep-mcp-setup-design](../../../../../sources/articles/bleep-mcp-setup-design.md)；原始位置 `/home/ai/lee/workspace/bleep_scripts/mcp-setup/scalasemantic-integration-design.md`）
- 源码：`bleep_scripts/mcp-setup/McpSetup.scala`
